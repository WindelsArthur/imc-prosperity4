"""Phase 2d — bootstrap re-eval for Tier-1 candidates.

Take the top 5 fold_median candidates from LHS+TPE, re-eval with capture_ticks=True
+ n_bootstrap=1000. Filter by gate (d): bootstrap_q05 ≥ baseline_q05.

Then write tier1_winner.json with the surviving candidate that has the widest
plateau (from plateau_summary).
"""
from __future__ import annotations

import sys
import json
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _harness.harness import eval_config

OUT = Path(__file__).resolve().parent
LHS = OUT / "coarse_sweep" / "lhs_results.csv"
TPE = OUT / "tpe_results" / "tpe_trials.csv"
PLATEAU_DIR = OUT / "fine_sweep"
WINNER = OUT / "tier1_winner.json"

BASELINE = {
    "fold_mean": 362034, "fold_median": 363578, "fold_min": 354448,
    "max_dd": 24692, "boot_q05": 943838,
}


def main():
    pieces = []
    if LHS.exists():
        d = pd.read_csv(LHS)
        d = d[d.error == ""] if "error" in d.columns else d
        d = d.dropna(subset=["fold_median"])
        d["source"] = "lhs"
        cols = ["PAIR_TILT_DIVISOR", "PAIR_TILT_CLIP", "INV_SKEW_BETA",
                "QUOTE_BASE_SIZE_CAP", "fair_quote_gate",
                "fold_median", "fold_mean", "fold_min", "fold_max", "fold_pos",
                "total_3day", "sharpe", "max_dd", "source"]
        pieces.append(d[cols])
    if TPE.exists():
        d = pd.read_csv(TPE)
        d["source"] = "tpe"
        cols = ["PAIR_TILT_DIVISOR", "PAIR_TILT_CLIP", "INV_SKEW_BETA",
                "QUOTE_BASE_SIZE_CAP", "fair_quote_gate",
                "fold_median", "fold_mean", "fold_min", "fold_max", "fold_pos",
                "total_3day", "sharpe", "max_dd", "source"]
        pieces.append(d[cols])
    if not pieces:
        raise RuntimeError("No LHS or TPE results found")
    combined = pd.concat(pieces, ignore_index=True)
    # Apply gates (a)-(c) BEFORE picking top 5 — only consider configs that
    # already pass the basic robustness gates
    mask = (
        (combined.fold_min > 0)
        & (combined.fold_median >= BASELINE["fold_median"])
        & (combined.fold_mean >= BASELINE["fold_mean"] + 2000)
    )
    surviving = combined[mask].copy()
    if "max_dd" in surviving.columns:
        surviving = surviving[surviving.max_dd <= BASELINE["max_dd"] * 1.20]
    surviving = surviving.sort_values("fold_median", ascending=False).head(10)
    print(f"[bootstrap-top] {len(surviving)} configs survive gates (a)-(b)-(c)-(e)")
    if len(surviving) == 0:
        print("[bootstrap-top] no candidates pass gates — Tier-1 will revert to baseline")
        WINNER.write_text(json.dumps({
            "decision": "revert_to_baseline",
            "params": {"PAIR_TILT_DIVISOR": 3.0, "PAIR_TILT_CLIP": 7.0,
                       "INV_SKEW_BETA": 0.20, "QUOTE_BASE_SIZE_CAP": 8},
            "fair_quote_gate": 0.25,
            "rationale": "no LHS/TPE config passed gates (a)+(b)+(c)+(e) vs locked baseline",
        }, indent=2))
        return

    # Bootstrap re-eval top-5 — force re-run with ticks (cache may have skipped them)
    from _harness.harness import _CACHE_DIR, _config_hash  # noqa
    rows = []
    for _, r in surviving.head(5).iterrows():
        p = {
            "PAIR_TILT_DIVISOR": float(r.PAIR_TILT_DIVISOR),
            "PAIR_TILT_CLIP":    float(r.PAIR_TILT_CLIP),
            "INV_SKEW_BETA":     float(r.INV_SKEW_BETA),
            "QUOTE_BASE_SIZE_CAP": int(r.QUOTE_BASE_SIZE_CAP),
        }
        gate = float(r.fair_quote_gate)
        # Invalidate cache to force capture_ticks=True re-run
        chash = _config_hash(p, None, None, gate, "worse", 10, False)
        for ext in (".json", ".npz"):
            cf = _CACHE_DIR / f"{chash}_l10_mworse{ext}"
            if cf.exists() and ext == ".json":
                # Check if this cached entry has tick data
                tick_blob = _CACHE_DIR / f"{chash}_l10_mworse.npz"
                if not tick_blob.exists():
                    cf.unlink()  # force re-run
        res = eval_config(p, fair_quote_gate=gate, capture_ticks=True, n_bootstrap=1000)
        rows.append({
            **p, "fair_quote_gate": gate,
            "fold_mean": res.fold_mean, "fold_median": res.fold_median,
            "fold_min": res.fold_min, "fold_max": res.fold_max,
            "total_3day": res.total_pnl_3day, "sharpe": res.sharpe_3day,
            "max_dd": res.max_dd_3day,
            "boot_q05": res.bootstrap_q05, "boot_q50": res.bootstrap_q50,
            "boot_q95": res.bootstrap_q95,
            "passes_d": res.bootstrap_q05 >= BASELINE["boot_q05"],
        })
    df = pd.DataFrame(rows).sort_values("fold_median", ascending=False)
    df.to_csv(OUT / "bootstrap_top5.csv", index=False)
    print(df.to_string(index=False))

    # Pick the winner: passes (d), then maximize plateau width if available
    pass_d = df[df.passes_d]
    if pass_d.empty:
        print("[bootstrap-top] no candidate passes gate (d) bootstrap_q05 — revert")
        WINNER.write_text(json.dumps({
            "decision": "revert_to_baseline",
            "params": {"PAIR_TILT_DIVISOR": 3.0, "PAIR_TILT_CLIP": 7.0,
                       "INV_SKEW_BETA": 0.20, "QUOTE_BASE_SIZE_CAP": 8},
            "fair_quote_gate": 0.25,
            "rationale": "top-5 candidates failed gate (d) bootstrap_q05 vs baseline",
            "candidates_tested": rows,
        }, indent=2))
        return

    winner = pass_d.iloc[0]
    decision = {
        "decision": "tier1_uplift",
        "params": {
            "PAIR_TILT_DIVISOR": float(winner.PAIR_TILT_DIVISOR),
            "PAIR_TILT_CLIP":    float(winner.PAIR_TILT_CLIP),
            "INV_SKEW_BETA":     float(winner.INV_SKEW_BETA),
            "QUOTE_BASE_SIZE_CAP": int(winner.QUOTE_BASE_SIZE_CAP),
        },
        "fair_quote_gate": float(winner.fair_quote_gate),
        "metrics": {
            "fold_median": float(winner.fold_median),
            "fold_mean": float(winner.fold_mean),
            "fold_min": int(winner.fold_min),
            "boot_q05": float(winner.boot_q05),
        },
        "uplift_vs_baseline": {
            "delta_fold_mean": float(winner.fold_mean - BASELINE["fold_mean"]),
            "delta_fold_median": float(winner.fold_median - BASELINE["fold_median"]),
            "delta_boot_q05": float(winner.boot_q05 - BASELINE["boot_q05"]),
        },
    }
    WINNER.write_text(json.dumps(decision, indent=2))
    print(f"[bootstrap-top] winner written to {WINNER}")


if __name__ == "__main__":
    main()
