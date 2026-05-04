"""Phase B — pair leave-one-out (LOO).

For each of the 127 added pairs (tuned ALL_PAIRS[39..165]), run a 3-day merged
backtest with that pair REMOVED and record:
  - per-day pnl[2,3,4]
  - fold_min, fold_median, fold_mean
  - delta_median: PnL change vs full tuned (positive = pair was hurting median;
                  negative = pair was helping)
  - delta_fold_min: same for worst-case fold

A pair is HARMFUL if delta_median ≥ +1,000 AND delta_fold_min ≥ 0 (removing
helps in both aggregate and worst case).

Joblib n_jobs=4, ~24s per run × 127 / 4 ≈ 13 min.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import pandas as pd
from joblib import Parallel, delayed

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _audit_lib import (run_algo_text, render_with_pairs, FOLDS, DAYS)  # noqa: E402

OUT = Path(__file__).resolve().parent
PT_DIR = Path(__file__).resolve().parents[2]
TUNED_ALGO_PATH = PT_DIR / "07_assembly" / "algo1_tuned.py"

# Pairs at indices 0..8 are within-group COINT (kept).
# Indices 9..38 are top-30 of cross-group ranking (≈ baseline cross-group).
# Indices 39..165 are the 127 NEW pairs (rank 31..157).
LOO_START_IDX = 39
LOO_END_IDX = 166  # exclusive


def _load_tuned_pairs() -> list[list]:
    spec = PT_DIR / "07_assembly" / "distilled_params_tuned.py"
    ns: dict = {}
    exec(spec.read_text(), ns)
    return ns["ALL_PAIRS"]


def _one_loo(pair_idx: int, all_pairs: list, tuned_src: str) -> dict:
    """Render algo with ALL_PAIRS minus index `pair_idx`, run 3-day, return record."""
    new_pairs = all_pairs[:pair_idx] + all_pairs[pair_idx + 1:]
    src = render_with_pairs(tuned_src, new_pairs)
    res = run_algo_text(src)
    a, b, slope, intercept = all_pairs[pair_idx][:4]
    return {
        "pair_idx": pair_idx,
        "rank_in_ranking": pair_idx - 8,    # rank 1 = index 9 (after 9 within-group)
        "a": a, "b": b, "slope": slope, "intercept": intercept,
        "day2_pnl": res.per_day_pnl.get(2, 0),
        "day3_pnl": res.per_day_pnl.get(3, 0),
        "day4_pnl": res.per_day_pnl.get(4, 0),
        "total_3day": res.total_3day,
        "fold_min": res.fold_min,
        "fold_median": res.fold_median,
        "fold_mean": res.fold_mean,
        "sharpe_3day": res.sharpe_3day,
        "elapsed_s": res.elapsed_s,
        # carry per-product PnL on each day for follow-up (compact: only nonzero deltas vs tuned)
        "per_day_per_product": json.dumps(res.per_day_per_product),
    }


def main():
    tuned_src = TUNED_ALGO_PATH.read_text()
    all_pairs = _load_tuned_pairs()
    print(f"[Phase B] tuned ALL_PAIRS has {len(all_pairs)} entries")
    assert len(all_pairs) == 166, f"expected 166 pairs, got {len(all_pairs)}"

    # Reference: full tuned baseline
    print("[Phase B] running full tuned (reference) ...")
    full_src = render_with_pairs(tuned_src, all_pairs)  # round-trip the substitution
    full_res = run_algo_text(full_src)
    print(f"  full tuned: total_3day={full_res.total_3day:,} fold_min={full_res.fold_min:,} median={full_res.fold_median:,.0f}")
    full_ref = {
        "day2_pnl": full_res.per_day_pnl.get(2, 0),
        "day3_pnl": full_res.per_day_pnl.get(3, 0),
        "day4_pnl": full_res.per_day_pnl.get(4, 0),
        "total_3day": full_res.total_3day,
        "fold_min": full_res.fold_min,
        "fold_median": full_res.fold_median,
        "fold_mean": full_res.fold_mean,
        "sharpe_3day": full_res.sharpe_3day,
    }
    (OUT / "_full_tuned_reference.json").write_text(json.dumps(full_ref, indent=2, default=str))

    # LOO
    indices = list(range(LOO_START_IDX, LOO_END_IDX))
    print(f"[Phase B] running LOO over {len(indices)} pairs (indices {LOO_START_IDX}..{LOO_END_IDX-1}), n_jobs=4")
    t0 = time.time()
    rows = Parallel(n_jobs=4, verbose=10)(
        delayed(_one_loo)(i, all_pairs, tuned_src) for i in indices
    )
    elapsed = time.time() - t0
    print(f"[Phase B] LOO done in {elapsed:.1f}s ({elapsed/60:.1f}min)")

    # add deltas
    for r in rows:
        r["delta_total"] = r["total_3day"] - full_ref["total_3day"]
        r["delta_fold_min"] = r["fold_min"] - full_ref["fold_min"]
        r["delta_fold_median"] = r["fold_median"] - full_ref["fold_median"]
        r["delta_day2"] = r["day2_pnl"] - full_ref["day2_pnl"]
        r["delta_day3"] = r["day3_pnl"] - full_ref["day3_pnl"]
        r["delta_day4"] = r["day4_pnl"] - full_ref["day4_pnl"]

    df = pd.DataFrame(rows)
    df = df.sort_values("delta_total", ascending=False)
    df.to_csv(OUT / "pair_loo_full.csv", index=False)

    # compact (drop heavy per_day_per_product)
    df_cols = [c for c in df.columns if c != "per_day_per_product"]
    df[df_cols].to_csv(OUT / "pair_loo.csv", index=False)

    # ── HARMFUL pairs ──────────────────────────────────────────────────────
    # Mission def: removing pair INCREASES median by ≥ 1K AND INCREASES fold_min by ≥ 0
    harmful = df[(df["delta_total"] >= 1000) & (df["delta_fold_min"] >= 0)]
    helpful_strong = df[(df["delta_total"] <= -2000) & (df["delta_fold_min"] <= 0)]
    print(f"[Phase B] HARMFUL pairs (removing helps): {len(harmful)}")
    print(f"[Phase B] STRONGLY HELPFUL pairs (removing hurts ≥2K and fold_min): {len(helpful_strong)}")

    harmful_cols = ["pair_idx", "rank_in_ranking", "a", "b",
                    "delta_total", "delta_fold_min", "delta_fold_median",
                    "delta_day2", "delta_day3", "delta_day4"]
    harmful[harmful_cols].to_csv(OUT / "harmful_pairs.csv", index=False)
    helpful_strong[harmful_cols].to_csv(OUT / "helpful_strong_pairs.csv", index=False)

    summary = {
        "n_pairs_tested": len(rows),
        "indices_tested": [LOO_START_IDX, LOO_END_IDX - 1],
        "full_tuned_reference": full_ref,
        "n_harmful": len(harmful),
        "n_helpful_strong": len(helpful_strong),
        "harmful_total_uplift_if_dropped": int(harmful["delta_total"].sum()),
        "harmful_min_fold_uplift_if_dropped": int(harmful["delta_fold_min"].sum()),
        "elapsed_s": elapsed,
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2, default=str))
    print(f"[Phase B] wrote pair_loo.csv, pair_loo_full.csv, harmful_pairs.csv, helpful_strong_pairs.csv, summary.json")


if __name__ == "__main__":
    main()
