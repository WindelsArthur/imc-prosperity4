"""Phase F — re-plateau with stability filter.

The original Tier-4 pair-count sweep ranked 157 cross-group pairs by
combined_pnl using FULL-stitch (day 2+3+4) fits. This re-runs the sweep with
two changes:

  1. Drop pairs flagged as **β-shift >30%** in Phase C (unstable parameters).
  2. Re-sweep N ∈ {30, 50, 75, 100, 125, 150} on the surviving pairs.

For each N, build the candidate algo with 9 within-group COINT_PAIRS plus
top-N surviving cross-group pairs (in original combined_pnl order), then run a
merged 3-day backtest.

Goal: find the N that maximizes fold_min (the day-5 floor), with Sharpe as
tiebreak.

6 backtests × ~24s = ~2-3 min wall-clock.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _audit_lib import run_algo_text, render_with_pairs, FOLDS  # noqa: E402

OUT = Path(__file__).resolve().parent
PT_DIR = Path(__file__).resolve().parents[2]
TUNED_ALGO_PATH = PT_DIR / "07_assembly" / "algo1_tuned.py"
RANKING_CSV = PT_DIR / "05_pair_count" / "pair_ranking.csv"
STABILITY_CSV = PT_DIR / "audit" / "03_pair_stability" / "pair_stability.csv"

N_SWEEP = [30, 50, 75, 100, 125, 150]
BETA_SHIFT_THRESHOLD = 0.30  # >30% means UNSTABLE


def _load_tuned_pairs() -> list[list]:
    spec = PT_DIR / "07_assembly" / "distilled_params_tuned.py"
    ns: dict = {}
    exec(spec.read_text(), ns)
    return ns["ALL_PAIRS"]


def _load_within_group_coint(all_pairs) -> list[list]:
    """First 9 entries of distilled ALL_PAIRS = within-group COINT pairs."""
    return all_pairs[:9]


def _load_cross_group_ranking(all_pairs) -> list[list]:
    """Pairs at indices 9..165 (157 total) are the ranked cross-group set,
    already in combined_pnl order from pair_ranking.csv."""
    return all_pairs[9:]


def _stable_mask() -> dict[tuple[str, str, float, float], bool]:
    """Return dict (a, b, slope, intercept) -> is_stable (β-shift ≤ 30%)."""
    df = pd.read_csv(STABILITY_CSV)
    out = {}
    for _, row in df.iterrows():
        # Stability is keyed off (a, b, slope_full, intercept_full).
        # The slope_full/intercept_full come from the distilled tuned ALL_PAIRS.
        key = (row["a"], row["b"], float(row["slope_full"]),
               float(row["intercept_full"]))
        is_stable = bool(row["beta_shift_pct"] <= BETA_SHIFT_THRESHOLD)
        out[key] = is_stable
    return out


def main():
    tuned_src = TUNED_ALGO_PATH.read_text()
    all_pairs = _load_tuned_pairs()
    within = _load_within_group_coint(all_pairs)
    cross_ranked = _load_cross_group_ranking(all_pairs)
    stable = _stable_mask()

    # Filter cross-group pairs: keep only those with β-shift ≤ 30%
    cross_stable = []
    cross_dropped = []
    for tup in cross_ranked:
        key = (tup[0], tup[1], float(tup[2]), float(tup[3]))
        if stable.get(key, False):
            cross_stable.append(tup)
        else:
            cross_dropped.append(tup)
    print(f"[Phase F] cross-group pairs: total={len(cross_ranked)}, "
          f"stable={len(cross_stable)}, dropped={len(cross_dropped)}")

    # Reference: full tuned (157 cross pairs unfiltered)
    print("[Phase F] reference run: full tuned …")
    full_src = render_with_pairs(tuned_src, all_pairs)
    full_res = run_algo_text(full_src)
    print(f"  full tuned: total_3day={full_res.total_3day:,}, "
          f"fold_min={full_res.fold_min:,}, sharpe={full_res.sharpe_3day:.2f}")

    # Sweep
    rows = []
    for N in N_SWEEP:
        if N > len(cross_stable):
            print(f"  N={N}: only {len(cross_stable)} stable cross pairs — capping")
            N_eff = len(cross_stable)
        else:
            N_eff = N
        pairs = list(within) + list(cross_stable[:N_eff])
        src = render_with_pairs(tuned_src, pairs)
        res = run_algo_text(src)
        rows.append({
            "N_target": N,
            "N_used": N_eff,
            "total_pairs": len(pairs),
            "day2": res.per_day_pnl.get(2, 0),
            "day3": res.per_day_pnl.get(3, 0),
            "day4": res.per_day_pnl.get(4, 0),
            "total_3day": res.total_3day,
            "fold_min": res.fold_min,
            "fold_median": res.fold_median,
            "fold_mean": res.fold_mean,
            "sharpe_3day": res.sharpe_3day,
        })
        print(f"  N={N}/{N_eff} ({len(pairs)} total pairs): total={res.total_3day:,}, "
              f"fold_min={res.fold_min:,}, median={res.fold_median:,.0f}, "
              f"sharpe={res.sharpe_3day:.2f}")

    df = pd.DataFrame(rows)
    df.to_csv(OUT / "n_sweep_filtered.csv", index=False)

    # Find optimum: max fold_min, tiebreak by Sharpe
    df_sorted = df.sort_values(["fold_min", "sharpe_3day"], ascending=[False, False])
    best = df_sorted.iloc[0].to_dict()

    summary = {
        "n_cross_total": len(cross_ranked),
        "n_cross_stable": len(cross_stable),
        "n_cross_dropped": len(cross_dropped),
        "beta_shift_threshold": BETA_SHIFT_THRESHOLD,
        "full_tuned_reference": {
            "total_3day": full_res.total_3day,
            "fold_min": full_res.fold_min,
            "fold_median": full_res.fold_median,
            "sharpe_3day": full_res.sharpe_3day,
        },
        "sweep": rows,
        "best_by_fold_min": best,
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2, default=str))

    md = [
        "# Phase F — re-plateau with stability filter\n",
        f"- {len(cross_ranked)} cross-group pairs total → {len(cross_stable)} survive β-shift ≤ 30% filter (dropped {len(cross_dropped)}).",
        f"- Full tuned reference: total_3day={full_res.total_3day:,}, "
        f"fold_min={full_res.fold_min:,}, sharpe={full_res.sharpe_3day:.2f}",
        "",
        "## Sweep (with β-shift ≤ 30% filter)",
        df.to_markdown(index=False),
        "",
        f"### Best by fold_min: N_target={best['N_target']}, "
        f"N_used={best['N_used']}, total_3day={best['total_3day']:,}, "
        f"fold_min={best['fold_min']:,}, sharpe={best['sharpe_3day']:.2f}",
    ]
    (OUT / "summary.md").write_text("\n".join(md))
    print(f"\n[Phase F] best N (fold_min): N_target={best['N_target']}/N_used={best['N_used']} → "
          f"fold_min={best['fold_min']:,}, total={best['total_3day']:,}, sharpe={best['sharpe_3day']:.2f}")
    print(f"[Phase F] wrote n_sweep_filtered.csv, summary.json, summary.md")


if __name__ == "__main__":
    main()
