"""Phase E — build the conservative variant.

algo1_conservative = algo1_tuned MINUS:
  1. All HARMFUL pairs (Phase B): removing each individually improves median ≥1K
     AND fold_min ≥ 0.
  2. All HIGHLY-UNSTABLE pairs (Phase C): β-shift >50%. We use the strict bar
     to avoid over-pruning.
  3. Restored / tightened caps on top fragility-flagged + worst-loss products:
        - PANEL_1X4:        10 → 5  (fragility, fold_min Δ=-2.4K)
        - UV_VISOR_YELLOW:  10 → 5  (fragility, fold_min Δ=-1.7K)
        - PANEL_1X2:         3 → 3  (already capped — kept)
     Plus an explicit cap to address the worst single-product loss:
        - OXYGEN_SHAKE_CHOCOLATE: 10 → 4

We test 4 variants:
  v_full_tuned          (reference, all pairs, original caps)
  v_drop_harmful        (drop only HARMFUL; original caps)
  v_drop_harmful_unstable (drop HARMFUL + β>50% unstable; original caps)
  v_conservative        (drop HARMFUL + β>50% + tightened caps)

For each, run merged 3-day backtest, record fold metrics. Decide ship-rule:
ship conservative if fold_min ≥ tuned fold_min AND fold_median ≥ tuned-30K AND
sharpe ≥ 30.
"""
from __future__ import annotations

import json
import re
import sys
import shutil
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _audit_lib import run_algo_text, render_with_pairs  # noqa: E402

OUT = Path(__file__).resolve().parent
PT_DIR = Path(__file__).resolve().parents[2]
TUNED_ALGO_PATH = PT_DIR / "07_assembly" / "algo1_tuned.py"
HARMFUL_CSV = PT_DIR / "audit" / "02_pair_loo" / "harmful_pairs.csv"
STABILITY_CSV = PT_DIR / "audit" / "03_pair_stability" / "pair_stability.csv"


def _load_tuned_pairs() -> list[list]:
    spec = PT_DIR / "07_assembly" / "distilled_params_tuned.py"
    ns: dict = {}
    exec(spec.read_text(), ns)
    return ns["ALL_PAIRS"]


def _patch_caps(src: str, new_caps: dict[str, int]) -> str:
    """Rewrite the PROD_CAP literal block to inject extra/updated caps."""
    pat = re.compile(r"^PROD_CAP\s*=\s*\{[^}]*\}", re.MULTILINE | re.DOTALL)
    m = pat.search(src)
    if not m:
        raise RuntimeError("PROD_CAP block not found")
    # Parse existing caps using exec
    ns: dict = {}
    exec(m.group(0), ns)
    caps = dict(ns["PROD_CAP"])
    caps.update(new_caps)
    new_block = "PROD_CAP = {\n" + "\n".join(f'    "{k}": {int(v)},' for k, v in caps.items()) + "\n}"
    return src[: m.start()] + new_block + src[m.end():]


def main():
    tuned_src = TUNED_ALGO_PATH.read_text()
    all_pairs = _load_tuned_pairs()
    print(f"[Phase E] tuned ALL_PAIRS: {len(all_pairs)}")

    # ── load harmful + unstable indices ────────────────────────────────────
    harmful_df = pd.read_csv(HARMFUL_CSV)
    harmful_idx = set(harmful_df["pair_idx"].astype(int))
    print(f"[Phase E] HARMFUL (Phase B): {len(harmful_idx)} pairs")

    stab_df = pd.read_csv(STABILITY_CSV)
    highly_unstable_idx = set(stab_df[stab_df["beta_shift_pct"] > 0.50]["pair_idx"].astype(int))
    # Restrict to ADDED pairs (idx ≥ 39) — never drop within-group COINT
    highly_unstable_idx = {i for i in highly_unstable_idx if i >= 39}
    print(f"[Phase E] HIGHLY UNSTABLE (β>50%, idx≥39): {len(highly_unstable_idx)} pairs")

    overlap = harmful_idx & highly_unstable_idx
    print(f"[Phase E] HARMFUL ∩ UNSTABLE: {len(overlap)} pairs (high-confidence overfit)")

    # ── caps ───────────────────────────────────────────────────────────────
    extra_caps = {
        "PANEL_1X4": 5,
        "UV_VISOR_YELLOW": 5,
        "OXYGEN_SHAKE_CHOCOLATE": 4,
    }

    # ── helper: build candidate ────────────────────────────────────────────
    def candidate_pairs(drop: set[int]) -> list:
        return [p for i, p in enumerate(all_pairs) if i not in drop]

    variants = []

    # full tuned reference
    print("\n[Phase E] running full tuned (reference) …")
    full_src = render_with_pairs(tuned_src, all_pairs)
    full_res = run_algo_text(full_src)
    print(f"  full tuned: total={full_res.total_3day:,} fold_min={full_res.fold_min:,} "
          f"sharpe={full_res.sharpe_3day:.2f}")
    variants.append({"name": "v_full_tuned", "n_pairs": len(all_pairs), "caps_added": {}, "res": full_res})

    # v_drop_harmful
    drop_h = harmful_idx
    pairs_h = candidate_pairs(drop_h)
    print(f"\n[Phase E] v_drop_harmful: drop {len(drop_h)} pairs → {len(pairs_h)} pairs …")
    res_h = run_algo_text(render_with_pairs(tuned_src, pairs_h))
    print(f"  total={res_h.total_3day:,} fold_min={res_h.fold_min:,} median={res_h.fold_median:,.0f} "
          f"sharpe={res_h.sharpe_3day:.2f}")
    variants.append({"name": "v_drop_harmful", "n_pairs": len(pairs_h),
                     "caps_added": {}, "res": res_h})

    # v_drop_harmful_unstable
    drop_hu = harmful_idx | highly_unstable_idx
    pairs_hu = candidate_pairs(drop_hu)
    print(f"\n[Phase E] v_drop_harmful_unstable: drop {len(drop_hu)} pairs → {len(pairs_hu)} pairs …")
    res_hu = run_algo_text(render_with_pairs(tuned_src, pairs_hu))
    print(f"  total={res_hu.total_3day:,} fold_min={res_hu.fold_min:,} median={res_hu.fold_median:,.0f} "
          f"sharpe={res_hu.sharpe_3day:.2f}")
    variants.append({"name": "v_drop_harmful_unstable", "n_pairs": len(pairs_hu),
                     "caps_added": {}, "res": res_hu})

    # v_conservative
    drop_cons = drop_hu
    pairs_cons = candidate_pairs(drop_cons)
    src_cons = render_with_pairs(tuned_src, pairs_cons)
    src_cons = _patch_caps(src_cons, extra_caps)
    print(f"\n[Phase E] v_conservative: drop {len(drop_cons)} pairs + caps {extra_caps} …")
    res_cons = run_algo_text(src_cons)
    print(f"  total={res_cons.total_3day:,} fold_min={res_cons.fold_min:,} median={res_cons.fold_median:,.0f} "
          f"sharpe={res_cons.sharpe_3day:.2f}")
    variants.append({"name": "v_conservative", "n_pairs": len(pairs_cons),
                     "caps_added": extra_caps, "res": res_cons})

    # save the conservative algo file
    cons_algo_path = OUT / "algo1_conservative.py"
    cons_algo_path.write_text(src_cons)
    print(f"\n[Phase E] saved {cons_algo_path}")

    # ── summary ────────────────────────────────────────────────────────────
    rows = []
    for v in variants:
        r = v["res"]
        rows.append({
            "variant": v["name"],
            "n_pairs": v["n_pairs"],
            "caps_added": json.dumps(v["caps_added"]) if v["caps_added"] else "{}",
            "day2": r.per_day_pnl.get(2, 0),
            "day3": r.per_day_pnl.get(3, 0),
            "day4": r.per_day_pnl.get(4, 0),
            "total_3day": r.total_3day,
            "fold_min": r.fold_min,
            "fold_median": r.fold_median,
            "fold_mean": r.fold_mean,
            "sharpe_3day": r.sharpe_3day,
            "max_dd": r.max_dd_3day,
        })
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "variants.csv", index=False)

    # Ship rule:
    # ship CONSERVATIVE if fold_median ≥ tuned_median - 30K AND Sharpe ≥ 30
    #                    AND fold_min ≥ tuned fold_min
    tuned_med = full_res.fold_median
    tuned_min = full_res.fold_min
    cons = res_cons
    ship_a = cons.fold_median >= tuned_med - 30000
    ship_b = (cons.sharpe_3day or 0) >= 30
    ship_c = cons.fold_min >= tuned_min
    ship_pass = ship_a and ship_b and ship_c

    summary = {
        "n_harmful_dropped": len(harmful_idx),
        "n_unstable_dropped": len(highly_unstable_idx),
        "n_harmful_intersect_unstable": len(overlap),
        "extra_caps": extra_caps,
        "tuned_reference": {
            "fold_median": tuned_med, "fold_min": tuned_min,
            "sharpe_3day": full_res.sharpe_3day, "total_3day": full_res.total_3day,
        },
        "conservative": {
            "fold_median": cons.fold_median, "fold_min": cons.fold_min,
            "sharpe_3day": cons.sharpe_3day, "total_3day": cons.total_3day,
            "n_pairs": len(pairs_cons),
        },
        "ship_rule": {
            "median_within_30k": (ship_a, cons.fold_median, tuned_med - 30000),
            "sharpe_ge_30": (ship_b, cons.sharpe_3day),
            "fold_min_ge_tuned": (ship_c, cons.fold_min, tuned_min),
            "PASS": ship_pass,
        },
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2, default=str))

    md = [
        "# Phase E — conservative variant\n",
        f"- HARMFUL dropped: {len(harmful_idx)}",
        f"- HIGHLY UNSTABLE dropped (β>50%, idx≥39): {len(highly_unstable_idx)}",
        f"- Overlap (HARMFUL ∩ UNSTABLE): {len(overlap)}",
        f"- Extra caps added: {extra_caps}",
        "",
        "## Variants compared\n",
        df.to_markdown(index=False),
        "",
        "## Ship rule (CONSERVATIVE vs full TUNED)",
        f"- median ≥ tuned_median - 30K? **{ship_a}** ({cons.fold_median:,.0f} vs {tuned_med - 30000:,.0f})",
        f"- sharpe ≥ 30? **{ship_b}** (sharpe = {cons.sharpe_3day:.2f})",
        f"- fold_min ≥ tuned_fold_min? **{ship_c}** ({cons.fold_min:,} vs {tuned_min:,})",
        f"- **OVERALL: {'SHIP CONSERVATIVE' if ship_pass else 'KEEP TUNED'}**",
    ]
    (OUT / "summary.md").write_text("\n".join(md))
    print(f"\n[Phase E] ship rule decision: {'SHIP CONSERVATIVE' if ship_pass else 'KEEP TUNED'}")


if __name__ == "__main__":
    main()
