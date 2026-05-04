"""Phase 3b — SNACKPACK sweep (3-param joint grid)."""
from __future__ import annotations

import sys
import json
from pathlib import Path
from itertools import product

import pandas as pd
from joblib import Parallel, delayed

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _harness.harness import eval_config

OUT = Path(__file__).resolve().parent / "snackpack_sweep"
OUT.mkdir(parents=True, exist_ok=True)
TIER1_WINNER = Path(__file__).resolve().parents[1] / "02_tier1_universal" / "tier1_winner.json"

GRID = {
    "SNACKPACK_SKEW_DIVISOR": [3, 5, 8],
    "SNACKPACK_SKEW_CLIP":    [2, 3, 5],
    "SNACKPACK_BIG_SKEW":     [2.0, 3.5, 5.0],
}


def load_tier1_base():
    if TIER1_WINNER.exists():
        w = json.loads(TIER1_WINNER.read_text())
        return w.get("params", {}), float(w.get("fair_quote_gate", 0.25))
    return {"PAIR_TILT_DIVISOR": 3.0, "PAIR_TILT_CLIP": 7.0,
            "INV_SKEW_BETA": 0.20, "QUOTE_BASE_SIZE_CAP": 8}, 0.25


def main():
    base, gate = load_tier1_base()
    cells = list(product(GRID["SNACKPACK_SKEW_DIVISOR"], GRID["SNACKPACK_SKEW_CLIP"], GRID["SNACKPACK_BIG_SKEW"]))
    print(f"[Snackpack] {len(cells)} cells, base={base} gate={gate}")

    def _one(div, clip, big):
        p = dict(base)
        p["SNACKPACK_SKEW_DIVISOR"] = float(div)
        p["SNACKPACK_SKEW_CLIP"] = float(clip)
        p["SNACKPACK_BIG_SKEW"] = float(big)
        res = eval_config(p, fair_quote_gate=gate, capture_ticks=False, n_bootstrap=0)
        return {
            "SNACKPACK_SKEW_DIVISOR": div, "SNACKPACK_SKEW_CLIP": clip, "SNACKPACK_BIG_SKEW": big,
            "fold_mean": res.fold_mean, "fold_median": res.fold_median,
            "fold_min": res.fold_min, "fold_pos": res.fold_positive_count,
            "total_3day": res.total_pnl_3day, "sharpe": res.sharpe_3day, "max_dd": res.max_dd_3day,
        }

    from concurrent.futures import ThreadPoolExecutor, as_completed
    rows = []
    with ThreadPoolExecutor(max_workers=3) as ex:
        futs = [ex.submit(_one, d, c, b) for d, c, b in cells]
        for fut in as_completed(futs):
            rows.append(fut.result())
    df = pd.DataFrame(rows).sort_values("fold_median", ascending=False)
    df.to_csv(OUT / "snackpack_sweep.csv", index=False)
    print(df.head(15).to_string(index=False))

    BASELINE_MEAN = 362034
    BASELINE_MEDIAN = 363578
    cand = df[(df.fold_min > 0)
              & (df.fold_median >= BASELINE_MEDIAN)
              & (df.fold_mean >= BASELINE_MEAN + 2000)]
    winner_path = Path(__file__).resolve().parent / "tier2_snackpack_winner.json"
    if cand.empty:
        winner = {
            "decision": "revert_to_baseline",
            "params": {"SNACKPACK_SKEW_DIVISOR": 5.0, "SNACKPACK_SKEW_CLIP": 5.0,
                       "SNACKPACK_BIG_SKEW": 3.5},
            "rationale": "no SNACKPACK grid cell passed gates (a)+(b)+(c)",
        }
    else:
        top = cand.iloc[0]
        winner = {
            "decision": "tier2_snackpack_uplift",
            "params": {"SNACKPACK_SKEW_DIVISOR": float(top.SNACKPACK_SKEW_DIVISOR),
                       "SNACKPACK_SKEW_CLIP": float(top.SNACKPACK_SKEW_CLIP),
                       "SNACKPACK_BIG_SKEW": float(top.SNACKPACK_BIG_SKEW)},
            "delta_fold_mean": float(top.fold_mean - BASELINE_MEAN),
            "delta_fold_median": float(top.fold_median - BASELINE_MEDIAN),
        }
    import json as _json
    winner_path.write_text(_json.dumps(winner, indent=2))
    print(f"[Snackpack] winner → {winner_path}: {winner['decision']}")


if __name__ == "__main__":
    main()
