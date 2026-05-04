"""Phase 2 Steps 2b/2c — per-product α sweep + combined.

For each surviving product (passed cross-day-stability filter in 01_ar1_per_product),
hold all OTHERS at baseline and sweep α ∈ {0.5, 1.0, 1.5, 2.0} (α=0 == baseline).

Per-product attribution: TARGET product per-day PnL must improve (or at least
not regress on fold_min terms) for the gate to pass.

Step 2c: combined run with the chosen best α per surviving product applied
simultaneously. If individual products help but combined does not, fall back
to top-3 by individual contribution.
"""
from __future__ import annotations

import csv
import json
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from itertools import product as iproduct
from pathlib import Path

import pandas as pd

_PA = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_PA))
from _pa_lib import run_algo_text, ablation_gate, FOLDS, progress_log, write_csv

OUT = _PA / "02_mr_skew_overlay"
BASELINE_SRC = (_PA.parent / "parameter_tuning" / "audit" / "07_final"
                / "algo1_drop_harmful_only.py").read_text()
BASELINE_JSON = json.loads((_PA / "00_baseline_lock" / "baseline.json").read_text())

# load AR(1) summary
AR1 = pd.read_csv(OUT / "ar1_coefs_per_product.csv")


def survivors_with_phi():
    """Return [(product, mean_phi)] for cross-day-stable products."""
    summary = AR1[AR1["day"] == "summary"]
    survs = summary[summary["survives_filter"] == True]
    return [(r["product"], float(r["phi"])) for _, r in survs.iterrows()]


def make_variant(coef_map: dict, alpha_map: dict) -> str:
    """Inject AR(1) overlay into baseline source.

    Adds a function `_ar1_skew(prod, mid_now, prev_map)` that returns
    -coef * (mid - prev) * alpha for products in coef_map / alpha_map. Stores
    prev_map in traderData under key "pmm". Modifies `_fair` to add the AR(1)
    skew. Modifies `run` to thread prev_map through traderData.

    Anything not in coef_map gets 0 skew.
    """
    src = BASELINE_SRC

    # 1. Add AR1 globals after `INV_SKEW_BETA = 0.2` line
    coef_lit = "{" + ", ".join(f'"{k}": {v:.6f}' for k, v in coef_map.items()) + "}"
    alpha_lit = "{" + ", ".join(f'"{k}": {v:.4f}' for k, v in alpha_map.items()) + "}"
    inject = (
        f"\n# Phase-2 AR(1) MR overlay parameters\n"
        f"AR1_COEF_MAP = {coef_lit}\n"
        f"AR1_ALPHA_MAP = {alpha_lit}\n"
    )
    src = src.replace("INV_SKEW_BETA = 0.2",
                      "INV_SKEW_BETA = 0.2" + inject, 1)

    # 2. Modify `_fair` to add AR(1) skew. The original signature is
    # `_fair(prod, mids, pair_skews, pos)`; we change it to take prev_map and
    # add an AR(1) term.
    old_fair = '''def _fair(prod: str, mids: Dict[str, float], pair_skews: Dict[str, float], pos: int) -> Tuple[float, float]:
    """Total fair value = mid + basket_skew + pair_skew + inv_skew.
    Returns (fair, basket_skew_only) so trade() can decide aggressive crossing."""
    if prod not in mids:
        return None, 0.0
    bsk = _basket_skew(prod, mids)
    psk = pair_skews.get(prod, 0.0)
    inv = -pos * INV_SKEW_BETA
    fair = mids[prod] + bsk + psk + inv
    return fair, bsk'''
    new_fair = '''def _fair(prod: str, mids: Dict[str, float], pair_skews: Dict[str, float], pos: int, prev_map: dict) -> Tuple[float, float]:
    """Total fair value = mid + basket_skew + pair_skew + inv_skew + ar1_skew."""
    if prod not in mids:
        return None, 0.0
    bsk = _basket_skew(prod, mids)
    psk = pair_skews.get(prod, 0.0)
    inv = -pos * INV_SKEW_BETA
    ar1 = 0.0
    coef = AR1_COEF_MAP.get(prod)
    alpha = AR1_ALPHA_MAP.get(prod, 0.0)
    if coef is not None and alpha != 0.0:
        prev = prev_map.get(prod)
        if prev is not None:
            ar1 = -coef * (mids[prod] - prev) * alpha
    fair = mids[prod] + bsk + psk + inv + ar1
    return fair, bsk'''
    if old_fair not in src:
        raise RuntimeError("expected _fair signature not found in baseline")
    src = src.replace(old_fair, new_fair, 1)

    # 3. Modify `trade` to pass prev_map to _fair
    old_trade_call = "fair, basket_skew = _fair(prod, mids, pair_skews, pos)"
    new_trade_call = "fair, basket_skew = _fair(prod, mids, pair_skews, pos, prev_map)"
    if old_trade_call not in src:
        raise RuntimeError("expected _fair call in trade() not found")
    src = src.replace(old_trade_call, new_trade_call, 1)

    # 4. Modify trade signature to accept prev_map
    old_trade_sig = "def trade(self, prod, state, mids, pair_skews):"
    new_trade_sig = "def trade(self, prod, state, mids, pair_skews, prev_map):"
    if old_trade_sig not in src:
        raise RuntimeError("expected trade() signature not found")
    src = src.replace(old_trade_sig, new_trade_sig, 1)

    # 5. Modify run() to thread prev_map (read+write traderData under "pmm")
    old_run_loop = """        for prod in ALL_PRODUCTS:
            orders = self.trade(prod, state, mids, pair_skews)"""
    new_run_loop = """        prev_map = td.get("pmm", {})
        for prod in ALL_PRODUCTS:
            orders = self.trade(prod, state, mids, pair_skews, prev_map)"""
    if old_run_loop not in src:
        raise RuntimeError("expected run() loop not found")
    src = src.replace(old_run_loop, new_run_loop, 1)

    # update prev_map AFTER decisions, before encoding
    old_td_encode = """        trader_data = jsonpickle.encode(td)"""
    new_td_encode = """        td["pmm"] = {p: m for p, m in mids.items() if p in AR1_COEF_MAP}
        trader_data = jsonpickle.encode(td)"""
    src = src.replace(old_td_encode, new_td_encode, 1)

    return src


def run_one(label: str, coef_map: dict, alpha_map: dict,
            target_prod: str = None) -> dict:
    src = make_variant(coef_map, alpha_map)
    t0 = time.time()
    res = run_algo_text(src, save_log_as=f"phase2_{label}")
    elapsed = time.time() - t0
    row = {
        "label": label,
        "alpha_map": json.dumps(alpha_map),
        "elapsed_s": round(elapsed, 1),
        "F1_pnl": res.fold_pnls["F1"],
        "F2_pnl": res.fold_pnls["F2"],
        "F3_pnl": res.fold_pnls["F3"],
        "F4_pnl": res.fold_pnls["F4"],
        "F5_pnl": res.fold_pnls["F5"],
        "fold_min": res.fold_min,
        "fold_median": res.fold_median,
        "fold_mean": round(res.fold_mean, 1),
        "total_3day": res.total_3day,
        "sharpe_3day": res.sharpe_3day,
        "max_dd_3day": res.max_dd_3day,
    }
    if target_prod:
        row[f"{target_prod}_3day"] = sum(
            res.per_day_per_product.get(d, {}).get(target_prod, 0)
            for d in (2, 3, 4)
        )
        for d in (2, 3, 4):
            row[f"{target_prod}_d{d}"] = res.per_day_per_product.get(d, {}).get(target_prod, 0)
    return row


def baseline_for_product(prod: str) -> dict:
    """Baseline per-product PnL for the 3 test days from Phase-0 snapshot."""
    return {d: BASELINE_JSON["per_day_per_product"][str(d)].get(prod, 0)
            for d in (2, 3, 4)}


def main(serial: bool = False) -> int:
    progress_log("Phase 2 Step 2b — per-product α sweep")

    survs = survivors_with_phi()
    progress_log(f"Phase 2 — {len(survs)} survivors: " +
                 ", ".join(f"{p}({phi:+.3f})" for p, phi in survs))

    alphas = [0.5, 1.0, 1.5, 2.0]

    # Step 2b: per-product sweep, holding others at baseline
    cells_2b = []
    for prod, phi in survs:
        coef_map = {prod: phi}  # only this product gets AR(1)
        for a in alphas:
            label = f"2b_{prod}_a{a}"
            cells_2b.append((label, dict(
                coef_map=coef_map,
                alpha_map={prod: a},
                target_prod=prod
            )))

    rows_2b = []
    if serial:
        for label, p in cells_2b:
            rows_2b.append(run_one(label, **p))
    else:
        with ThreadPoolExecutor(max_workers=4) as ex:
            futs = {ex.submit(run_one, label, **p): label for label, p in cells_2b}
            for fut in as_completed(futs):
                lab = futs[fut]
                try:
                    rows_2b.append(fut.result())
                except Exception as e:
                    progress_log(f"Phase 2 ERROR — {lab}: {e}")
                    print(f"[ERROR] {lab}: {e}")

    # sort then save
    rows_2b.sort(key=lambda r: r["label"])
    write_csv(rows_2b, OUT / "per_product_alpha_sweep.csv")
    progress_log(f"Phase 2 Step 2b — wrote per_product_alpha_sweep.csv ({len(rows_2b)} rows)")

    # Per-product decisions: choose best α by:
    # 1) gate must pass (fold_min ≥ baseline + 0; all 5 deltas ≥ 0; mean ≥ +1K)
    # 2) tie-break by Sharpe
    base_fm = BASELINE_JSON["fold_min"]
    base_fmed = BASELINE_JSON["fold_median"]
    base_fmean = BASELINE_JSON["fold_mean"]
    base_folds = BASELINE_JSON["fold_pnls"]
    decisions = []
    for prod, phi in survs:
        prod_rows = [r for r in rows_2b if f"_{prod}_" in r["label"]]
        prod_rows.sort(key=lambda r: r["label"])
        # individual Δs
        candidates = []
        for r in prod_rows:
            deltas = [r[f"F{i}_pnl"] - base_folds[f"F{i}"] for i in range(1, 6)]
            mean_delta = r["fold_mean"] - base_fmean
            target_delta = r.get(f"{prod}_3day", 0) - sum(baseline_for_product(prod).values())
            passed = (
                all(d >= 0 for d in deltas)
                and r["fold_min"] >= base_fm
                and r["fold_mean"] >= base_fmean + 1000
                and target_delta > 0
            )
            candidates.append({
                "product": prod,
                "alpha": float(r["label"].rsplit("_a", 1)[-1]),
                "fold_min": r["fold_min"],
                "fold_mean": r["fold_mean"],
                "delta_fold_min": r["fold_min"] - base_fm,
                "delta_fold_median": r["fold_median"] - base_fmed,
                "delta_mean": mean_delta,
                "target_delta_3day": target_delta,
                "all_folds_positive": all(d >= 0 for d in deltas),
                "min_fold_delta": min(deltas),
                "passed_gate": passed,
                "sharpe": r["sharpe_3day"],
            })
        if any(c["passed_gate"] for c in candidates):
            best = max(
                (c for c in candidates if c["passed_gate"]),
                key=lambda c: (c["fold_min"], c["sharpe"] or 0),
            )
            chosen_alpha = best["alpha"]
            retained = True
        else:
            best = max(candidates, key=lambda c: (c["fold_min"], c["sharpe"] or 0))
            chosen_alpha = 0.0
            retained = False
        decisions.append({
            "product": prod,
            "phi": phi,
            "best_alpha": chosen_alpha,
            "individual_delta_fold_min": best["delta_fold_min"] if retained else 0,
            "individual_delta_median": best["delta_fold_median"] if retained else 0,
            "individual_delta_target_3day": best["target_delta_3day"] if retained else 0,
            "retained_in_combined": retained,
            "best_row_passed_gate": best["passed_gate"],
            "best_row_alpha": best["alpha"],
            "best_row_fold_min": best["fold_min"],
        })

    write_csv(decisions, OUT / "per_product_decisions.csv")
    progress_log("Phase 2 — per-product decisions written")

    # Step 2c: combined run with all retained best-α
    coef_map = {d["product"]: float(AR1[(AR1["product"] == d["product"]) & (AR1["day"] == "summary")]["phi"].iloc[0])
                for d in decisions if d["retained_in_combined"]}
    alpha_map = {d["product"]: d["best_alpha"] for d in decisions if d["retained_in_combined"]}
    if alpha_map:
        progress_log(f"Phase 2 Step 2c — combined sweep with {len(alpha_map)} retained products")
        combined_row = run_one("2c_combined", coef_map=coef_map,
                               alpha_map=alpha_map, target_prod=None)
        write_csv([combined_row], OUT / "combined_run.csv")
    else:
        progress_log("Phase 2 Step 2c — no products retained; combined run skipped")

    # ablation.csv: aggregate
    ablation_rows = []
    base_row = {
        "label": "v00_baseline",
        "alpha_map": "{}",
        "F1_pnl": base_folds["F1"], "F2_pnl": base_folds["F2"],
        "F3_pnl": base_folds["F3"], "F4_pnl": base_folds["F4"],
        "F5_pnl": base_folds["F5"],
        "fold_min": base_fm, "fold_median": base_fmed, "fold_mean": base_fmean,
        "total_3day": BASELINE_JSON["total_3day"],
        "sharpe_3day": BASELINE_JSON["sharpe_3day"],
        "max_dd_3day": BASELINE_JSON["max_dd_3day"],
    }
    ablation_rows.append(base_row)
    ablation_rows.extend(rows_2b)
    if alpha_map:
        ablation_rows.append(combined_row)
    write_csv(ablation_rows, OUT / "ablation.csv")

    # quick summary print
    print(f"\nBaseline fold_min={base_fm:,}, fold_mean={base_fmean:,}\n")
    print("Per-product decisions:")
    for d in decisions:
        flag = "✓" if d["retained_in_combined"] else "✗"
        print(f"  {flag} {d['product']:32s} α={d['best_alpha']}  "
              f"Δfold_min={d['individual_delta_fold_min']:+,}  "
              f"Δtarget3d={d['individual_delta_target_3day']:+,}")
    if alpha_map:
        print(f"\nCombined run: fold_min={combined_row['fold_min']:,} "
              f"(Δ={combined_row['fold_min']-base_fm:+,})")

    return 0


if __name__ == "__main__":
    sys.exit(main(serial=False))
