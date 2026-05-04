"""Phase 5 — pair count + ranking method sweep.

Build full ranked list of cross-group pairs from lagged_coint_fast.csv:
  - filter ADF p < 0.05 AND min_fold_sharpe ≥ 0.7

Sweep N ∈ {20, 30, 50, 75, 100, 125, 150, 171} × ranking method ∈ {pnl, sharpe, sharpe_x_sqrt_pnl}.

Always include the 9 within-group COINT_PAIRS as fixed.
"""
from __future__ import annotations

import sys
import json
from pathlib import Path
from itertools import product

import pandas as pd
import numpy as np
from joblib import Parallel, delayed

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _harness.harness import eval_config

OUT = Path(__file__).resolve().parent
OUT.mkdir(parents=True, exist_ok=True)

LAGGED = Path("ROUND_5/autoresearch/14_lag_research/C_lagged_coint/lagged_coint_fast.csv").resolve()

# 9 within-group pairs (locked, always included)
COINT_PAIRS = [
    ("MICROCHIP_RECTANGLE", "MICROCHIP_SQUARE", -0.401, 14119.0),
    ("ROBOT_LAUNDRY", "ROBOT_VACUUMING", 0.334, 7072.0),
    ("SLEEP_POD_COTTON", "SLEEP_POD_POLYESTER", 0.519, 5144.0),
    ("GALAXY_SOUNDS_DARK_MATTER", "GALAXY_SOUNDS_PLANETARY_RINGS", 0.183, 8285.0),
    ("SNACKPACK_RASPBERRY", "SNACKPACK_VANILLA", 0.013, 9962.0),
    ("SNACKPACK_CHOCOLATE", "SNACKPACK_STRAWBERRY", -0.106, 11051.0),
    ("UV_VISOR_AMBER", "UV_VISOR_MAGENTA", -1.238, 21897.0),
    ("TRANSLATOR_ECLIPSE_CHARCOAL", "TRANSLATOR_VOID_BLUE", 0.456, 4954.0),
    ("SLEEP_POD_POLYESTER", "SLEEP_POD_SUEDE", 0.756, 2977.0),
]

TIER1 = Path(__file__).resolve().parents[1] / "02_tier1_universal" / "tier1_winner.json"
TIER2_PEB = Path(__file__).resolve().parents[1] / "03_tier2_group" / "tier2_pebbles_winner.json"
TIER2_SNK = Path(__file__).resolve().parents[1] / "03_tier2_group" / "tier2_snackpack_winner.json"
TIER3 = Path(__file__).resolve().parents[1] / "04_tier3_product" / "tier3_winner.json"


def load_base():
    base_params = {"PAIR_TILT_DIVISOR": 3.0, "PAIR_TILT_CLIP": 7.0,
                   "INV_SKEW_BETA": 0.20, "QUOTE_BASE_SIZE_CAP": 8,
                   "QUOTE_AGGRESSIVE_SIZE": 2,
                   "PEBBLES_SKEW_DIVISOR": 5.0, "PEBBLES_SKEW_CLIP": 3.0,
                   "PEBBLES_BIG_SKEW": 1.8,
                   "SNACKPACK_SKEW_DIVISOR": 5.0, "SNACKPACK_SKEW_CLIP": 5.0,
                   "SNACKPACK_BIG_SKEW": 3.5}
    gate = 0.25
    prod_cap = None
    if TIER1.exists():
        w = json.loads(TIER1.read_text())
        base_params.update(w.get("params", {}))
        gate = float(w.get("fair_quote_gate", gate))
    if TIER2_PEB.exists():
        base_params.update(json.loads(TIER2_PEB.read_text()).get("params", {}))
    if TIER2_SNK.exists():
        base_params.update(json.loads(TIER2_SNK.read_text()).get("params", {}))
    if TIER3.exists():
        prod_cap = json.loads(TIER3.read_text()).get("prod_cap")
    return base_params, gate, prod_cap


def build_pair_pool() -> pd.DataFrame:
    """Read lagged_coint_fast and return surviving cross-group pairs ranked."""
    df = pd.read_csv(LAGGED)
    df = df[df.adf_p < 0.05].copy()
    df = df[df.min_fold_sharpe >= 0.7].copy()
    df = df[df.group_i != df.group_j].copy()
    # combined PnL = sum of fA + fB on the lag-100 fit
    df["combined_pnl"] = df["fA_pnl"] + df["fB_pnl"]
    df["combined_sharpe"] = (df["fA_sharpe"] + df["fB_sharpe"]) / 2
    df["sharpe_x_sqrt_pnl"] = df["combined_sharpe"] * np.sqrt(np.maximum(df["combined_pnl"], 0))
    return df.sort_values("combined_pnl", ascending=False).reset_index(drop=True)


def main():
    base, gate, prod_cap = load_base()
    pool = build_pair_pool()
    print(f"[N-pairs] pool size after filter: {len(pool)}")
    pool.to_csv(OUT / "pair_ranking.csv", index=False)

    n_grid = [20, 30, 50, 75, 100, 150, len(pool)]
    rank_methods = ["combined_pnl", "combined_sharpe"]

    jobs = list(product(n_grid, rank_methods))
    print(f"[N-pairs] sweeping {len(jobs)} configurations")

    def _one(n, rk):
        ranked = pool.sort_values(rk, ascending=False).head(n)
        cross_pairs = [(r["i"], r["j"], float(r["slope"]), float(r["intercept"]))
                       for _, r in ranked.iterrows()]
        all_pairs = COINT_PAIRS + cross_pairs
        kw = dict(pairs=all_pairs, fair_quote_gate=gate,
                  capture_ticks=False, n_bootstrap=0)
        if prod_cap:
            kw["prod_cap"] = prod_cap
        res = eval_config(base, **kw)
        return {
            "N": n, "rank_method": rk,
            "fold_median": res.fold_median, "fold_mean": res.fold_mean,
            "fold_min": res.fold_min, "fold_pos": res.fold_positive_count,
            "total_3day": res.total_pnl_3day, "sharpe": res.sharpe_3day,
            "max_dd": res.max_dd_3day,
        }

    from concurrent.futures import ThreadPoolExecutor, as_completed
    rows = []
    with ThreadPoolExecutor(max_workers=3) as ex:
        futs = [ex.submit(_one, n, rk) for n, rk in jobs]
        for fut in as_completed(futs):
            rows.append(fut.result())
    df = pd.DataFrame(rows).sort_values("fold_median", ascending=False)
    df.to_csv(OUT / "n_sweep_results.csv", index=False)
    print(df.to_string(index=False))

    # Pick winner: passes gates AND maximize fold_median; tie-break by lower N (less complexity)
    BASELINE_MEAN = 362034
    BASELINE_MEDIAN = 363578
    cand = df[(df.fold_min > 0)
              & (df.fold_median >= BASELINE_MEDIAN)
              & (df.fold_mean >= BASELINE_MEAN + 2000)]
    winner_path = OUT / "pair_count_winner.json"
    if cand.empty:
        winner = {
            "decision": "revert_to_baseline",
            "rationale": "no (N, ranking_method) cell passed gates (a)+(b)+(c)",
            "N": 39, "rank_method": "default (9 within + 30 cross)",
        }
    else:
        cand = cand.sort_values(["fold_median", "N"], ascending=[False, True])
        top = cand.iloc[0]
        ranked = pool.sort_values(top.rank_method, ascending=False).head(int(top.N))
        cross_pairs = [(r["i"], r["j"], float(r["slope"]), float(r["intercept"]))
                       for _, r in ranked.iterrows()]
        winner = {
            "decision": "tier4_pair_count_uplift",
            "N": int(top.N),
            "rank_method": top.rank_method,
            "delta_fold_mean": float(top.fold_mean - BASELINE_MEAN),
            "delta_fold_median": float(top.fold_median - BASELINE_MEDIAN),
            "pairs": [list(c) for c in (COINT_PAIRS + cross_pairs)],
        }
    import json as _json
    winner_path.write_text(_json.dumps(winner, indent=2, default=str))
    print(f"[N-pairs] winner → {winner_path}: {winner['decision']}")


if __name__ == "__main__":
    main()
