"""Phase 2c — plateau analysis for Tier-1 params.

For each Tier-1 param, holding others at the TPE optimum, sweep 9 values.
Save plateau_plots/{param}.png and per-param sensitivity csv.
"""
from __future__ import annotations

import sys
import json
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from joblib import Parallel, delayed

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _harness.harness import eval_config

OUT = Path(__file__).resolve().parent
TPE_RESULTS = OUT / "tpe_results" / "best_params.json"
PLOT_DIR = OUT / "plateau_plots"
SWEEP_DIR = OUT / "fine_sweep"
PLOT_DIR.mkdir(parents=True, exist_ok=True)
SWEEP_DIR.mkdir(parents=True, exist_ok=True)

# Plateau sweep ranges (around the TPE optimum)
PLATEAU_GRID = {
    "PAIR_TILT_DIVISOR": [2.0, 2.5, 3.0, 4.0, 5.0, 6.0],
    "PAIR_TILT_CLIP":    [4, 5, 6, 7, 8, 10],
    "INV_SKEW_BETA":     [0.10, 0.15, 0.20, 0.25, 0.30],
    "QUOTE_BASE_SIZE_CAP": [4, 6, 8, 10],
    "fair_quote_gate":   [0.0, 0.1, 0.25, 0.5, 0.75],
}

BASELINE = {"fold_mean": 362034, "fold_median": 363578, "fold_min": 354448}


def run_one(param_name: str, value, base_params: dict, base_gate: float):
    p = dict(base_params)
    gate = base_gate
    if param_name == "fair_quote_gate":
        gate = float(value)
    elif param_name == "QUOTE_BASE_SIZE_CAP":
        p[param_name] = int(value)
    else:
        p[param_name] = float(value)
    res = eval_config(p, fair_quote_gate=gate, capture_ticks=False, n_bootstrap=0)
    return {
        "param": param_name,
        "value": value,
        "fold_mean": res.fold_mean,
        "fold_median": res.fold_median,
        "fold_min": res.fold_min,
        "fold_max": res.fold_max,
        "fold_pos": res.fold_positive_count,
        "total_3day": res.total_pnl_3day,
        "sharpe": res.sharpe_3day,
        "max_dd": res.max_dd_3day,
    }


def main():
    if not TPE_RESULTS.exists():
        print(f"[plateau] no TPE results at {TPE_RESULTS}; aborting")
        return
    best = json.loads(TPE_RESULTS.read_text())["best_params"]
    print(f"[plateau] anchored at TPE best: {best}")

    base_params = {
        "PAIR_TILT_DIVISOR": float(best["PAIR_TILT_DIVISOR"]),
        "PAIR_TILT_CLIP":    float(best["PAIR_TILT_CLIP"]),
        "INV_SKEW_BETA":     float(best["INV_SKEW_BETA"]),
        "QUOTE_BASE_SIZE_CAP": int(best["QUOTE_BASE_SIZE_CAP"]),
    }
    base_gate = float(best["fair_quote_gate"])

    # Build job list
    jobs = []
    for pname, values in PLATEAU_GRID.items():
        for v in values:
            jobs.append((pname, v))
    print(f"[plateau] {len(jobs)} configs total")

    from concurrent.futures import ThreadPoolExecutor, as_completed
    rows = []
    with ThreadPoolExecutor(max_workers=3) as ex:
        futs = [ex.submit(run_one, pn, v, base_params, base_gate) for pn, v in jobs]
        for fut in as_completed(futs):
            rows.append(fut.result())
    df = pd.DataFrame(rows)
    df.to_csv(SWEEP_DIR / "plateau_sweep.csv", index=False)

    # Plateau plots — one per param
    plateau_summary = []
    for pname in PLATEAU_GRID:
        sub = df[df.param == pname].sort_values("value").reset_index(drop=True)
        fig, ax = plt.subplots(1, 1, figsize=(8, 4.5))
        ax.plot(sub.value.astype(float), sub.fold_median, "o-", label="fold_median")
        ax.plot(sub.value.astype(float), sub.fold_min, "s--", color="orange", label="fold_min")
        ax.plot(sub.value.astype(float), sub.fold_mean, "x:", color="green", label="fold_mean")
        ax.axhline(BASELINE["fold_median"], ls=":", color="gray", label=f"baseline median ({BASELINE['fold_median']:,})")
        ax.axhline(BASELINE["fold_min"], ls=":", color="lightgray", label=f"baseline min ({BASELINE['fold_min']:,})")
        anchor_val = base_gate if pname == "fair_quote_gate" else base_params.get(pname)
        if anchor_val is not None:
            ax.axvline(float(anchor_val), ls="-", color="red", alpha=0.4, label=f"TPE optimum ({anchor_val})")
        ax.set_xlabel(pname)
        ax.set_ylabel("PnL")
        ax.set_title(f"Plateau: {pname}")
        ax.legend(fontsize=8, loc="best")
        ax.grid(True, alpha=0.3)
        fig.tight_layout()
        fig.savefig(PLOT_DIR / f"{pname}.png", dpi=110)
        plt.close(fig)

        # plateau width = count of contiguous values where fold_min > 0 AND fold_median ≥ baseline
        passes = (sub.fold_min > 0) & (sub.fold_median >= BASELINE["fold_median"]) & (sub.fold_mean >= BASELINE["fold_mean"])
        contig = []
        cur = []
        for i, ok in enumerate(passes):
            if ok:
                cur.append(i)
            else:
                if cur:
                    contig.append(cur)
                cur = []
        if cur:
            contig.append(cur)
        max_run = max((len(c) for c in contig), default=0)
        plateau_summary.append({
            "param": pname, "n_values": len(sub),
            "n_pass_a_b_c": int(passes.sum()),
            "max_contig_pass": max_run,
            "best_value": sub.loc[sub.fold_median.idxmax(), "value"],
            "best_fold_median": float(sub.fold_median.max()),
            "anchor": anchor_val,
        })

    summary_df = pd.DataFrame(plateau_summary)
    summary_df.to_csv(SWEEP_DIR / "plateau_summary.csv", index=False)
    print("\n[plateau] summary:")
    print(summary_df.to_string(index=False))


if __name__ == "__main__":
    main()
