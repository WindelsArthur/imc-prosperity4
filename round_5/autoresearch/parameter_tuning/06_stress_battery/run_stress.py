"""Phase 6 — stress battery on the assembled winner.

Stresses (Phase 6 a-f):
  (a) match_mode='all' instead of 'worse'
  (b) latency: shift signals by 1 tick (use_lagged_signal=True)
  (c) limit-8: position limit 8 instead of 10
  (d) perturbation LHS ±20% on shipped params (50 samples)
  (e) day-removal: 3 day-only configurations
"""
from __future__ import annotations

import sys
import json
from pathlib import Path

import numpy as np
import pandas as pd
from joblib import Parallel, delayed
from scipy.stats import qmc

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _harness.harness import eval_config, _FOLDS

OUT = Path(__file__).resolve().parent

ASSEMBLY = Path(__file__).resolve().parents[1] / "07_assembly" / "winning_config.json"
TIER1 = Path(__file__).resolve().parents[1] / "02_tier1_universal" / "tier1_winner.json"
TIER2_PEB = Path(__file__).resolve().parents[1] / "03_tier2_group" / "tier2_pebbles_winner.json"
TIER2_SNK = Path(__file__).resolve().parents[1] / "03_tier2_group" / "tier2_snackpack_winner.json"
TIER3 = Path(__file__).resolve().parents[1] / "04_tier3_product" / "tier3_winner.json"
TIER4 = Path(__file__).resolve().parents[1] / "05_pair_count" / "pair_count_winner.json"


def load_winner():
    """Compose the winning config from per-tier winners."""
    base_params = {"PAIR_TILT_DIVISOR": 3.0, "PAIR_TILT_CLIP": 7.0,
                   "INV_SKEW_BETA": 0.20, "QUOTE_BASE_SIZE_CAP": 8,
                   "QUOTE_AGGRESSIVE_SIZE": 2,
                   "PEBBLES_SKEW_DIVISOR": 5.0, "PEBBLES_SKEW_CLIP": 3.0,
                   "PEBBLES_BIG_SKEW": 1.8,
                   "SNACKPACK_SKEW_DIVISOR": 5.0, "SNACKPACK_SKEW_CLIP": 5.0,
                   "SNACKPACK_BIG_SKEW": 3.5}
    gate = 0.25
    prod_cap = None
    pairs = None
    for fp, k in [(TIER1, "tier1"), (TIER2_PEB, "tier2_pebbles"), (TIER2_SNK, "tier2_snackpack")]:
        if fp.exists():
            d = json.loads(fp.read_text())
            base_params.update(d.get("params", {}))
            if "fair_quote_gate" in d:
                gate = float(d["fair_quote_gate"])
    if TIER3.exists():
        prod_cap = json.loads(TIER3.read_text()).get("prod_cap")
    if TIER4.exists():
        pairs = json.loads(TIER4.read_text()).get("pairs")
    return base_params, gate, prod_cap, pairs


def stress_match_mode(base, gate, prod_cap, pairs):
    rows = []
    for mm in ("worse", "all"):
        kw = dict(fair_quote_gate=gate, capture_ticks=False, n_bootstrap=0,
                  match_mode=mm)
        if prod_cap:
            kw["prod_cap"] = prod_cap
        if pairs:
            kw["pairs"] = pairs
        res = eval_config(base, **kw)
        rows.append({"stress": "match_mode", "mode": mm,
                     "fold_median": res.fold_median, "fold_mean": res.fold_mean,
                     "fold_min": res.fold_min, "total_3day": res.total_pnl_3day,
                     "max_dd": res.max_dd_3day, "sharpe": res.sharpe_3day})
    return rows


def stress_latency(base, gate, prod_cap, pairs):
    rows = []
    for lag in (False, True):
        kw = dict(fair_quote_gate=gate, capture_ticks=False, n_bootstrap=0,
                  use_lagged_signal=lag)
        if prod_cap:
            kw["prod_cap"] = prod_cap
        if pairs:
            kw["pairs"] = pairs
        res = eval_config(base, **kw)
        rows.append({"stress": "latency", "lagged": lag,
                     "fold_median": res.fold_median, "fold_mean": res.fold_mean,
                     "fold_min": res.fold_min, "total_3day": res.total_pnl_3day,
                     "max_dd": res.max_dd_3day, "sharpe": res.sharpe_3day})
    return rows


def stress_limit(base, gate, prod_cap, pairs):
    rows = []
    for lim in (10, 8):
        kw = dict(fair_quote_gate=gate, capture_ticks=False, n_bootstrap=0,
                  limit=lim)
        if prod_cap:
            kw["prod_cap"] = prod_cap
        if pairs:
            kw["pairs"] = pairs
        res = eval_config(base, **kw)
        rows.append({"stress": "limit", "limit": lim,
                     "fold_median": res.fold_median, "fold_mean": res.fold_mean,
                     "fold_min": res.fold_min, "total_3day": res.total_pnl_3day,
                     "max_dd": res.max_dd_3day, "sharpe": res.sharpe_3day})
    return rows


def stress_perturbation(base, gate, prod_cap, pairs, n_samples: int = 30):
    """LHS-perturb every base param by ±20% simultaneously."""
    keys = list(base.keys())
    sampler = qmc.LatinHypercube(d=len(keys) + 1, seed=0)
    raw = sampler.random(n_samples)

    def _one(idx, vec):
        new_p = {}
        for i, k in enumerate(keys):
            v = base[k]
            mult = 0.8 + 0.4 * float(vec[i])  # uniform in [0.8, 1.2]
            if isinstance(v, int) and not isinstance(v, bool):
                new_p[k] = max(1, int(round(v * mult)))
            else:
                new_p[k] = float(v) * mult
        new_gate = float(gate) * (0.8 + 0.4 * float(vec[-1]))
        kw = dict(fair_quote_gate=new_gate, capture_ticks=False, n_bootstrap=0)
        if prod_cap:
            kw["prod_cap"] = prod_cap
        if pairs:
            kw["pairs"] = pairs
        try:
            res = eval_config(new_p, **kw)
            return {
                "stress": "perturbation", "sample": idx,
                "fold_median": res.fold_median, "fold_mean": res.fold_mean,
                "fold_min": res.fold_min, "total_3day": res.total_pnl_3day,
                "max_dd": res.max_dd_3day,
                **{f"d_{k}": new_p[k] for k in keys},
                "fair_quote_gate": new_gate,
            }
        except Exception as e:
            return {"stress": "perturbation", "sample": idx, "error": str(e)[:200]}

    from concurrent.futures import ThreadPoolExecutor, as_completed
    rows = []
    with ThreadPoolExecutor(max_workers=3) as ex:
        futs = [ex.submit(_one, i, vec) for i, vec in enumerate(raw)]
        for fut in as_completed(futs):
            rows.append(fut.result())
    return rows


def stress_day_removal(base, gate, prod_cap, pairs):
    """Already encoded in folds — but check single-day evaluation per day."""
    kw = dict(fair_quote_gate=gate, capture_ticks=False, n_bootstrap=0)
    if prod_cap:
        kw["prod_cap"] = prod_cap
    if pairs:
        kw["pairs"] = pairs
    res = eval_config(base, **kw)
    rows = []
    for d, dr in res.days.items():
        rows.append({"stress": "day_only", "day": d, "pnl": dr.total_pnl})
    return rows


def main():
    base, gate, prod_cap, pairs = load_winner()
    print(f"[stress] base={base}\ngate={gate}\nprod_cap={prod_cap}\nn_pairs={len(pairs) if pairs else 'default'}")

    all_rows = []
    print("\n--- match-mode stress ---")
    all_rows.extend(stress_match_mode(base, gate, prod_cap, pairs))
    print("\n--- latency stress ---")
    all_rows.extend(stress_latency(base, gate, prod_cap, pairs))
    print("\n--- limit stress ---")
    all_rows.extend(stress_limit(base, gate, prod_cap, pairs))
    print("\n--- day-removal ---")
    all_rows.extend(stress_day_removal(base, gate, prod_cap, pairs))
    print("\n--- perturbation (LHS ±20%) ---")
    all_rows.extend(stress_perturbation(base, gate, prod_cap, pairs, n_samples=15))

    df = pd.DataFrame(all_rows)
    df.to_csv(OUT / "stress_results.csv", index=False)
    print("\n=== STRESS SUMMARY ===")
    print(df[df.stress.isin(["match_mode", "latency", "limit", "day_only"])].to_string(index=False))

    pert = df[df.stress == "perturbation"].copy()
    if not pert.empty and "fold_median" in pert.columns:
        med = pert.fold_median.dropna()
        print(f"\nperturbation (n={len(med)}): "
              f"q05={med.quantile(0.05):,.0f} median={med.median():,.0f} q95={med.quantile(0.95):,.0f}")

    # Stress summary table
    summary_rows = []
    for stress in ["match_mode", "latency", "limit", "day_only"]:
        sub = df[df.stress == stress]
        if not sub.empty:
            summary_rows.append({
                "stress": stress,
                "n_runs": len(sub),
                "min_fold_median": sub.fold_median.min() if "fold_median" in sub.columns else None,
                "min_total_3day": sub.total_3day.min() if "total_3day" in sub.columns else None,
                "min_pnl": sub.pnl.min() if "pnl" in sub.columns else None,
            })
    if not pert.empty:
        med = pert.fold_median.dropna()
        summary_rows.append({
            "stress": "perturbation",
            "n_runs": len(pert),
            "q05_fold_median": float(med.quantile(0.05)) if len(med) else None,
            "median_fold_median": float(med.median()) if len(med) else None,
        })
    pd.DataFrame(summary_rows).to_csv(OUT / "stress_summary.csv", index=False)


if __name__ == "__main__":
    main()
