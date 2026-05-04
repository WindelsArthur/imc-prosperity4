"""Phase 2a — Latin Hypercube Sampling on the Tier-1 universal cube.

5 dimensions:
  PAIR_TILT_DIVISOR ∈ [1.5, 10.0] (continuous)
  PAIR_TILT_CLIP    ∈ [3.0, 12.0] (continuous)
  INV_SKEW_BETA     ∈ [0.05, 0.40] (continuous)
  QUOTE_BASE_SIZE_CAP ∈ {4, 6, 8, 10} (discrete)
  fair_quote_gate   ∈ [0.0, 1.0] (continuous)

n=100 samples. No bootstrap (faster). Results → coarse_sweep/lhs_results.csv.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from scipy.stats import qmc

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

OUT = Path(__file__).resolve().parent / "coarse_sweep"
OUT.mkdir(parents=True, exist_ok=True)


def build_lhs_configs(n: int = 100, seed: int = 0) -> list[dict]:
    sampler = qmc.LatinHypercube(d=5, seed=seed)
    raw = sampler.random(n)
    # bounds for each dim:
    lo = np.array([1.5, 3.0, 0.05, 0.0, 0.0])     # divisor, clip, beta, qbsc_idx, gate
    hi = np.array([10.0, 12.0, 0.40, 1.0, 1.0])
    scaled = qmc.scale(raw, lo, hi)
    qbsc_choices = [4, 6, 8, 10]
    cfgs = []
    for row in scaled:
        div, clip, beta, qbsc_u, gate = row
        qbsc = qbsc_choices[min(int(qbsc_u * 4), 3)]
        # Critical constraint: clip should be at least 1× the divisor scale,
        # but we let LHS explore freely; downstream sweep is faithful to spec.
        cfgs.append({
            "PAIR_TILT_DIVISOR": round(float(div), 2),
            "PAIR_TILT_CLIP":    round(float(clip), 2),
            "INV_SKEW_BETA":     round(float(beta), 3),
            "QUOTE_BASE_SIZE_CAP": int(qbsc),
            "_fair_quote_gate":  round(float(gate), 3),
        })
    return cfgs


def main():
    cfgs = build_lhs_configs(n=50, seed=42)

    # always include the baseline cfg as cfg #0 so we can sanity-check rank order
    baseline = {
        "PAIR_TILT_DIVISOR": 3.0, "PAIR_TILT_CLIP": 7.0,
        "INV_SKEW_BETA": 0.20, "QUOTE_BASE_SIZE_CAP": 8,
        "_fair_quote_gate": 0.25,
    }
    cfgs = [baseline] + cfgs

    # call eval_config with fair_quote_gate split out (it's a kwarg, not a param)
    def extras_fn(i, p):
        return {"_label": "baseline" if i == 0 else f"lhs_{i:03d}"}

    from _harness.harness import eval_config  # noqa
    from concurrent.futures import ThreadPoolExecutor, as_completed
    import time, json
    import pandas as pd

    print(f"[Tier-1 LHS] {len(cfgs)} configs (1 baseline + {len(cfgs)-1} LHS)")
    t0 = time.time()

    def _one(i, cfg):
        p = {k: v for k, v in cfg.items() if not k.startswith("_")}
        gate = cfg.get("_fair_quote_gate")
        try:
            res = eval_config(p, fair_quote_gate=gate, capture_ticks=False, n_bootstrap=0)
            return {
                "cfg_id": i,
                "label": "baseline" if i == 0 else f"lhs_{i:03d}",
                "PAIR_TILT_DIVISOR": cfg["PAIR_TILT_DIVISOR"],
                "PAIR_TILT_CLIP":    cfg["PAIR_TILT_CLIP"],
                "INV_SKEW_BETA":     cfg["INV_SKEW_BETA"],
                "QUOTE_BASE_SIZE_CAP": cfg["QUOTE_BASE_SIZE_CAP"],
                "fair_quote_gate":   cfg["_fair_quote_gate"],
                "fold_mean":   res.fold_mean,
                "fold_median": res.fold_median,
                "fold_min":    res.fold_min,
                "fold_max":    res.fold_max,
                "fold_pos":    res.fold_positive_count,
                "total_3day":  res.total_pnl_3day,
                "sharpe":      res.sharpe_3day,
                "max_dd":      res.max_dd_3day,
                "cache_key":   res.cache_key,
                "error":       "",
            }
        except Exception as e:
            return {
                "cfg_id": i, "label": f"err_{i:03d}",
                "PAIR_TILT_DIVISOR": cfg.get("PAIR_TILT_DIVISOR"),
                "PAIR_TILT_CLIP":    cfg.get("PAIR_TILT_CLIP"),
                "INV_SKEW_BETA":     cfg.get("INV_SKEW_BETA"),
                "QUOTE_BASE_SIZE_CAP": cfg.get("QUOTE_BASE_SIZE_CAP"),
                "fair_quote_gate":   cfg.get("_fair_quote_gate"),
                "error": f"{type(e).__name__}: {e}",
            }

    rows = []
    n_workers = 2
    print(f"[Tier-1 LHS] launching with {n_workers} threads (subprocess parallelism)", flush=True)
    with ThreadPoolExecutor(max_workers=n_workers) as ex:
        futures = {ex.submit(_one, i, c): i for i, c in enumerate(cfgs)}
        completed = 0
        for fut in as_completed(futures):
            r = fut.result()
            rows.append(r)
            completed += 1
            if completed % 3 == 0 or completed == len(cfgs):
                elapsed = time.time() - t0
                rate = elapsed / completed
                eta = rate * (len(cfgs) - completed)
                print(f"[Tier-1 LHS] {completed}/{len(cfgs)} done, "
                      f"{rate:.1f}s/cfg, ETA {eta/60:.1f}m", flush=True)
    df = pd.DataFrame(rows).sort_values("fold_median", ascending=False, na_position="last")
    df.to_csv(OUT / "lhs_results.csv", index=False)
    elapsed = time.time() - t0
    print(f"\n[Tier-1 LHS] done in {elapsed:.0f}s ({elapsed/len(cfgs):.1f}s/cfg avg)")
    print(f"[Tier-1 LHS] top 10 by fold_median:")
    cols = ["label", "PAIR_TILT_DIVISOR", "PAIR_TILT_CLIP", "INV_SKEW_BETA",
            "QUOTE_BASE_SIZE_CAP", "fair_quote_gate",
            "fold_median", "fold_mean", "fold_min", "fold_pos", "total_3day"]
    print(df[cols].head(10).to_string(index=False))
    print(f"\nbaseline rank: {df.reset_index(drop=True).query('label==\"baseline\"').index.tolist()}")


if __name__ == "__main__":
    main()
