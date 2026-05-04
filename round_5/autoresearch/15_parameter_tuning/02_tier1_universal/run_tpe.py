"""Phase 2b — Optuna TPE on the Tier-1 cube, seeded from LHS top-10.

Objective: MEDIAN fold PnL across 5 folds.
Constraints (gate (a)-(d)) → returned as NaN when violated.
"""
from __future__ import annotations

import sys
from pathlib import Path
import json

import numpy as np
import optuna
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _harness.harness import eval_config

OUT = Path(__file__).resolve().parent / "tpe_results"
OUT.mkdir(parents=True, exist_ok=True)
LHS_RESULTS = Path(__file__).resolve().parent / "coarse_sweep" / "lhs_results.csv"

# Locked baseline (Phase 0) — gate reference
BASELINE = {
    "fold_mean": 362034,
    "fold_median": 363578,
    "fold_min": 354448,
    "fold_max": 364990,
    "max_dd": 24692,
    "boot_q05": 943838,
    "boot_q50": 1085215,
}


def objective(trial: optuna.Trial) -> float:
    div = trial.suggest_float("PAIR_TILT_DIVISOR", 1.5, 10.0)
    clip = trial.suggest_float("PAIR_TILT_CLIP", 3.0, 12.0)
    beta = trial.suggest_float("INV_SKEW_BETA", 0.05, 0.40)
    qbsc = trial.suggest_categorical("QUOTE_BASE_SIZE_CAP", [4, 6, 8, 10])
    gate = trial.suggest_float("fair_quote_gate", 0.0, 1.0)

    p = {
        "PAIR_TILT_DIVISOR": round(div, 2),
        "PAIR_TILT_CLIP":    round(clip, 2),
        "INV_SKEW_BETA":     round(beta, 3),
        "QUOTE_BASE_SIZE_CAP": int(qbsc),
    }
    res = eval_config(p, fair_quote_gate=round(gate, 3),
                      capture_ticks=False, n_bootstrap=0)

    trial.set_user_attr("fold_mean", res.fold_mean)
    trial.set_user_attr("fold_min", res.fold_min)
    trial.set_user_attr("fold_max", res.fold_max)
    trial.set_user_attr("fold_pos", res.fold_positive_count)
    trial.set_user_attr("total_3day", res.total_pnl_3day)
    trial.set_user_attr("sharpe", res.sharpe_3day)
    trial.set_user_attr("max_dd", res.max_dd_3day)

    # Constraints (a)-(c). q05 (d) deferred to final bootstrap re-eval.
    if res.fold_min <= 0:                                     # gate (c)
        return float("nan")
    # No need to enforce (a)/(b) here — let TPE see the landscape; we filter later.
    return float(res.fold_median)


def seed_from_lhs(study: optuna.Study, n: int = 10):
    if not LHS_RESULTS.exists():
        print(f"[TPE] no LHS results at {LHS_RESULTS}; skipping enqueue")
        return
    df = pd.read_csv(LHS_RESULTS)
    df = df.dropna(subset=["fold_median"]).sort_values("fold_median", ascending=False)
    seeded = 0
    for _, r in df.head(n).iterrows():
        params = {
            "PAIR_TILT_DIVISOR": float(r["PAIR_TILT_DIVISOR"]),
            "PAIR_TILT_CLIP":    float(r["PAIR_TILT_CLIP"]),
            "INV_SKEW_BETA":     float(r["INV_SKEW_BETA"]),
            "QUOTE_BASE_SIZE_CAP": int(r["QUOTE_BASE_SIZE_CAP"]),
            "fair_quote_gate":   float(r["fair_quote_gate"]),
        }
        study.enqueue_trial(params, skip_if_exists=True)
        seeded += 1
    print(f"[TPE] enqueued {seeded} LHS top configs as seed trials")


def main(n_trials: int = 80):
    sampler = optuna.samplers.TPESampler(
        multivariate=True, group=True, seed=0, n_startup_trials=10,
    )
    study = optuna.create_study(direction="maximize", sampler=sampler,
                                study_name="tier1_universal")
    seed_from_lhs(study, n=10)
    study.optimize(objective, n_trials=n_trials, show_progress_bar=False)

    print(f"\n[TPE] best value (fold_median): {study.best_value:,.0f}")
    print(f"[TPE] best params: {study.best_params}")
    print(f"[TPE] baseline median: {BASELINE['fold_median']:,}")

    # dump trials
    rows = []
    for t in study.trials:
        if t.state != optuna.trial.TrialState.COMPLETE:
            continue
        rows.append({
            "trial": t.number,
            **t.params,
            "fold_median": t.value,
            "fold_mean": t.user_attrs.get("fold_mean"),
            "fold_min": t.user_attrs.get("fold_min"),
            "fold_max": t.user_attrs.get("fold_max"),
            "fold_pos": t.user_attrs.get("fold_pos"),
            "total_3day": t.user_attrs.get("total_3day"),
            "sharpe": t.user_attrs.get("sharpe"),
            "max_dd": t.user_attrs.get("max_dd"),
        })
    df = pd.DataFrame(rows).sort_values("fold_median", ascending=False, na_position="last")
    df.to_csv(OUT / "tpe_trials.csv", index=False)
    (OUT / "best_params.json").write_text(json.dumps({
        "best_value_fold_median": study.best_value,
        "best_params": study.best_params,
        "n_trials": len(study.trials),
    }, indent=2))
    print(f"[TPE] wrote {OUT}/tpe_trials.csv ({len(df)} rows)")


if __name__ == "__main__":
    import sys as _s
    n = int(_s.argv[1]) if len(_s.argv) > 1 else 80
    main(n_trials=n)
