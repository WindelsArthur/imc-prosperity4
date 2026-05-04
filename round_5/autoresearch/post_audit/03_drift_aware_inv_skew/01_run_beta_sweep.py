"""Phase 3 — Drift-aware per-product inv_skew β.

10 KS-flagged products from prior findings:
  ROBOT_DISHES, OXYGEN_SHAKE_CHOCOLATE, MICROCHIP_OVAL, MICROCHIP_SQUARE,
  UV_VISOR_AMBER, SLEEP_POD_POLYESTER, MICROCHIP_TRIANGLE,
  OXYGEN_SHAKE_EVENING_BREATH, PANEL_1X4, GALAXY_SOUNDS_BLACK_HOLES.

Sweep β ∈ {0.05, 0.10, 0.15, 0.20, 0.30, 0.40, 0.60} per product, holding
others at 0.20. 10 × 7 = 70 cells.

Step 3c: per-product decision = β maximising fold_min PnL of that product
(per-product attribution); must pass total-PnL gate AND not regress that
product's fold_min.

Step 3d: combined run with all winning per-product βs.
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

_PA = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_PA))
from _pa_lib import run_algo_text, FOLDS, progress_log, write_csv

OUT = _PA / "03_drift_aware_inv_skew"
BASELINE_SRC = (_PA.parent / "parameter_tuning" / "audit" / "07_final"
                / "algo1_drop_harmful_only.py").read_text()
BASELINE_JSON = json.loads((_PA / "00_baseline_lock" / "baseline.json").read_text())

KS_FLAGGED = [
    "ROBOT_DISHES",
    "OXYGEN_SHAKE_CHOCOLATE",
    "MICROCHIP_OVAL",
    "MICROCHIP_SQUARE",
    "UV_VISOR_AMBER",
    "SLEEP_POD_POLYESTER",
    "MICROCHIP_TRIANGLE",
    "OXYGEN_SHAKE_EVENING_BREATH",
    "PANEL_1X4",
    "GALAXY_SOUNDS_BLACK_HOLES",
]
BETAS = [0.05, 0.10, 0.15, 0.20, 0.30, 0.40, 0.60]


def make_variant(beta_overrides: dict) -> str:
    """Replace global INV_SKEW_BETA usage with a per-product override map.

    We inject a `INV_BETA_MAP` global and modify `_fair` to look up the
    product's β (default 0.20). The global INV_SKEW_BETA stays as a fallback.
    """
    src = BASELINE_SRC
    map_lit = "{" + ", ".join(f'"{p}": {b}' for p, b in beta_overrides.items()) + "}"
    inject = f"\n# Phase-3 per-product inv_skew β\nINV_BETA_MAP = {map_lit}\n"
    src = src.replace("INV_SKEW_BETA = 0.2",
                      "INV_SKEW_BETA = 0.2" + inject, 1)

    # Replace the inv = -pos * INV_SKEW_BETA line in _fair
    old = "    inv = -pos * INV_SKEW_BETA"
    new = "    inv = -pos * INV_BETA_MAP.get(prod, INV_SKEW_BETA)"
    if old not in src:
        raise RuntimeError("expected inv_skew line not found in baseline")
    src = src.replace(old, new, 1)
    return src


def run_one(label: str, beta_overrides: dict, target_prod: str = None) -> dict:
    src = make_variant(beta_overrides)
    t0 = time.time()
    res = run_algo_text(src, save_log_as=f"phase3_{label}")
    elapsed = time.time() - t0
    row = {
        "label": label,
        "beta_overrides": json.dumps(beta_overrides),
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


def baseline_target_3day(prod: str) -> int:
    return sum(BASELINE_JSON["per_day_per_product"][str(d)].get(prod, 0)
               for d in (2, 3, 4))


def baseline_target_per_fold(prod: str) -> dict:
    pp_d = {d: BASELINE_JSON["per_day_per_product"][str(d)].get(prod, 0)
            for d in (2, 3, 4)}
    return {"F1": pp_d[3], "F2": pp_d[4], "F3": pp_d[3],
            "F4": pp_d[2], "F5": pp_d[3]}


def main(serial: bool = False) -> int:
    progress_log("Phase 3 Step 3b — per-product β sweep")

    cells = []
    for prod in KS_FLAGGED:
        for b in BETAS:
            label = f"3b_{prod}_b{b}"
            cells.append((label, dict(beta_overrides={prod: b}, target_prod=prod)))
    progress_log(f"Phase 3 — {len(cells)} cells")

    rows = []
    if serial:
        for lab, p in cells:
            rows.append(run_one(lab, **p))
    else:
        with ThreadPoolExecutor(max_workers=4) as ex:
            futs = {ex.submit(run_one, lab, **p): lab for lab, p in cells}
            done = 0
            for fut in as_completed(futs):
                lab = futs[fut]
                try:
                    rows.append(fut.result())
                except Exception as e:
                    progress_log(f"Phase 3 ERROR — {lab}: {e}")
                done += 1
                if done % 10 == 0:
                    progress_log(f"Phase 3 — {done}/{len(cells)} done")

    rows.sort(key=lambda r: r["label"])
    write_csv(rows, OUT / "per_product_beta_sweep.csv")
    progress_log("Phase 3 Step 3b — per_product_beta_sweep.csv saved")

    # Step 3c: pick best β per product
    base_folds = BASELINE_JSON["fold_pnls"]
    base_fm = BASELINE_JSON["fold_min"]
    base_fmed = BASELINE_JSON["fold_median"]
    base_fmean = BASELINE_JSON["fold_mean"]

    decisions = []
    retained_betas = {}
    for prod in KS_FLAGGED:
        prod_rows = [r for r in rows if r["label"].startswith(f"3b_{prod}_")]
        prod_rows.sort(key=lambda r: float(r["label"].rsplit("_b", 1)[-1]))
        base_target = baseline_target_3day(prod)
        base_target_per_fold = baseline_target_per_fold(prod)

        candidates = []
        for r in prod_rows:
            beta = float(r["label"].rsplit("_b", 1)[-1])
            deltas = [r[f"F{i}_pnl"] - base_folds[f"F{i}"] for i in range(1, 6)]
            target_per_fold = {
                "F1": r[f"{prod}_d3"], "F2": r[f"{prod}_d4"],
                "F3": r[f"{prod}_d3"], "F4": r[f"{prod}_d2"],
                "F5": r[f"{prod}_d3"],
            }
            target_fold_min = min(target_per_fold.values())
            base_target_fold_min = min(base_target_per_fold.values())
            target_delta = r[f"{prod}_3day"] - base_target

            passed_total = (
                r["fold_min"] >= base_fm
                and r["fold_mean"] >= base_fmean - 500  # mild slack OK if target wins
            )
            target_not_regressed = target_fold_min >= base_target_fold_min
            passed = passed_total and target_not_regressed and target_delta >= 0

            candidates.append({
                "product": prod, "beta": beta,
                "fold_min": r["fold_min"],
                "fold_mean": r["fold_mean"],
                "delta_fold_min": r["fold_min"] - base_fm,
                "delta_fold_mean": r["fold_mean"] - base_fmean,
                "target_3day_delta": target_delta,
                "target_fold_min": target_fold_min,
                "target_fold_min_delta": target_fold_min - base_target_fold_min,
                "passed_gate": passed,
                "passed_total": passed_total,
                "target_not_regressed": target_not_regressed,
                "sharpe": r["sharpe_3day"],
            })
        # decision: maximize THIS product's fold_min, then total fold_min, then sharpe
        if any(c["passed_gate"] for c in candidates):
            best = max(
                (c for c in candidates if c["passed_gate"]),
                key=lambda c: (c["target_fold_min"], c["fold_min"], c["sharpe"] or 0),
            )
            chosen = best["beta"]
            retained = chosen != 0.20
        else:
            best = max(candidates, key=lambda c: (c["target_fold_min"], c["fold_min"]))
            chosen = 0.20
            retained = False
        if retained:
            retained_betas[prod] = chosen
        decisions.append({
            "product": prod, "chosen_beta": chosen, "retained": retained,
            "best_passed_gate": best["passed_gate"],
            "best_target_fold_min_delta": best["target_fold_min_delta"],
            "best_total_fold_min_delta": best["delta_fold_min"],
            "best_target_3day_delta": best["target_3day_delta"],
        })

    write_csv(decisions, OUT / "decisions.csv")
    progress_log(f"Phase 3 — decisions: retained {len(retained_betas)} products")

    # Step 3d: combined
    if retained_betas:
        combined = run_one("3d_combined", beta_overrides=retained_betas, target_prod=None)
        write_csv([combined], OUT / "combined_run.csv")
        progress_log(f"Phase 3 Step 3d — combined fold_min={combined['fold_min']:,} "
                     f"(Δ={combined['fold_min']-base_fm:+,})")
    else:
        combined = None
        progress_log("Phase 3 Step 3d — no products retained; combined skipped")

    # ablation.csv
    ablation = [{
        "label": "v00_baseline", "beta_overrides": "{}",
        "F1_pnl": base_folds["F1"], "F2_pnl": base_folds["F2"],
        "F3_pnl": base_folds["F3"], "F4_pnl": base_folds["F4"],
        "F5_pnl": base_folds["F5"],
        "fold_min": base_fm, "fold_median": base_fmed, "fold_mean": base_fmean,
        "total_3day": BASELINE_JSON["total_3day"],
        "sharpe_3day": BASELINE_JSON["sharpe_3day"],
        "max_dd_3day": BASELINE_JSON["max_dd_3day"],
    }]
    ablation.extend(rows)
    if combined:
        ablation.append(combined)
    write_csv(ablation, OUT / "ablation.csv")

    print(f"\nBaseline fold_min={base_fm:,}\n")
    print("Per-product β decisions:")
    for d in decisions:
        flag = "✓" if d["retained"] else "✗"
        print(f"  {flag} {d['product']:32s} β={d['chosen_beta']}  "
              f"target_fold_min_Δ={d['best_target_fold_min_delta']:+,}  "
              f"total_fold_min_Δ={d['best_total_fold_min_delta']:+,}")
    if combined:
        print(f"\nCombined: fold_min={combined['fold_min']:,} "
              f"(Δ={combined['fold_min']-base_fm:+,})")
    return 0


if __name__ == "__main__":
    sys.exit(main(serial=False))
