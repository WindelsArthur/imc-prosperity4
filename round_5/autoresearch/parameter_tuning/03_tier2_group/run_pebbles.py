"""Phase 3a — PEBBLES sweep (3-param joint grid).

7 × 6 × 5 = 210 cells. Tier-1 fixed at the Tier-2 winner from 02_/tier1_winner.json.
"""
from __future__ import annotations

import sys
import json
from pathlib import Path
from itertools import product

import pandas as pd
from joblib import Parallel, delayed

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _harness.harness import eval_config

OUT = Path(__file__).resolve().parent / "pebbles_sweep"
OUT.mkdir(parents=True, exist_ok=True)
TIER1_WINNER = Path(__file__).resolve().parents[1] / "02_tier1_universal" / "tier1_winner.json"

GRID = {
    "PEBBLES_SKEW_DIVISOR": [3, 5, 8],
    "PEBBLES_SKEW_CLIP":    [2, 3, 5],
    "PEBBLES_BIG_SKEW":     [1.0, 1.8, 2.5, 3.5],
}


def load_tier1_base() -> tuple[dict, float]:
    if TIER1_WINNER.exists():
        w = json.loads(TIER1_WINNER.read_text())
        params = w.get("params", {})
        gate = w.get("fair_quote_gate", 0.25)
        return params, float(gate)
    print("[Pebbles] no tier1_winner.json — using baseline values")
    return {"PAIR_TILT_DIVISOR": 3.0, "PAIR_TILT_CLIP": 7.0,
            "INV_SKEW_BETA": 0.20, "QUOTE_BASE_SIZE_CAP": 8}, 0.25


def main():
    base, gate = load_tier1_base()
    print(f"[Pebbles] Tier-1 base: {base}, gate={gate}")

    cells = list(product(GRID["PEBBLES_SKEW_DIVISOR"], GRID["PEBBLES_SKEW_CLIP"], GRID["PEBBLES_BIG_SKEW"]))
    print(f"[Pebbles] {len(cells)} cells")

    def _one(div, clip, big):
        p = dict(base)
        p["PEBBLES_SKEW_DIVISOR"] = float(div)
        p["PEBBLES_SKEW_CLIP"] = float(clip)
        p["PEBBLES_BIG_SKEW"] = float(big)
        res = eval_config(p, fair_quote_gate=gate, capture_ticks=False, n_bootstrap=0)
        return {
            "PEBBLES_SKEW_DIVISOR": div, "PEBBLES_SKEW_CLIP": clip, "PEBBLES_BIG_SKEW": big,
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
    df.to_csv(OUT / "pebbles_sweep.csv", index=False)
    print(df.head(15).to_string(index=False))

    # Pick winner: passes gates (a)+(b)+(c) vs baseline=362034 mean / 363578 median
    BASELINE_MEAN = 362034
    BASELINE_MEDIAN = 363578
    cand = df[(df.fold_min > 0)
              & (df.fold_median >= BASELINE_MEDIAN)
              & (df.fold_mean >= BASELINE_MEAN + 2000)]
    winner_path = Path(__file__).resolve().parent / "tier2_pebbles_winner.json"
    if cand.empty:
        # revert
        winner = {
            "decision": "revert_to_baseline",
            "params": {"PEBBLES_SKEW_DIVISOR": 5.0, "PEBBLES_SKEW_CLIP": 3.0,
                       "PEBBLES_BIG_SKEW": 1.8},
            "rationale": "no PEBBLES grid cell passed gates (a)+(b)+(c)",
        }
    else:
        top = cand.iloc[0]
        winner = {
            "decision": "tier2_pebbles_uplift",
            "params": {"PEBBLES_SKEW_DIVISOR": float(top.PEBBLES_SKEW_DIVISOR),
                       "PEBBLES_SKEW_CLIP": float(top.PEBBLES_SKEW_CLIP),
                       "PEBBLES_BIG_SKEW": float(top.PEBBLES_BIG_SKEW)},
            "delta_fold_mean": float(top.fold_mean - BASELINE_MEAN),
            "delta_fold_median": float(top.fold_median - BASELINE_MEDIAN),
        }
    import json as _json
    winner_path.write_text(_json.dumps(winner, indent=2))
    print(f"[Pebbles] winner → {winner_path}: {winner['decision']}")


if __name__ == "__main__":
    main()
