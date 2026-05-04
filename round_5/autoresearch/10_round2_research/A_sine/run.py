"""Phase A — Sine-fit phase resolution.

For each of 7 high-sine-R² products from round 1:
- Fit `mid = A·sin(ωt+φ) + ct + d` separately on day 2, day 3, day 4.
  Compare A, ω, φ, c, d across days.  Stable across days = real cycle.
- Rolling sine fit on 3,000-tick windows.  Track ω(t) and φ(t).
- OOS test: fit on day 2, predict day 3 fair value, compute residual MSE
  against flat-fair-value baseline.  Repeat day 2+3 → day 4.
- Alt models: damped sine, sum-of-2-sines, linear+sine, sine+AR(1) residual.
- Decision: if SINE FV beats FLAT FV in OOS MSE on day 3 AND day 4 → real.

Outputs:
    13_round2_research/A_sine/per_day_fits.csv
    13_round2_research/A_sine/oos_mse.csv
    13_round2_research/A_sine/rolling_phase.csv
    13_round2_research/A_sine/decision.md
    13_round2_research/A_sine/plots/{product}.png
"""
from __future__ import annotations

import json
import sys
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from utils.data_loader import load_prices, available_days

warnings.filterwarnings("ignore")
OUT = Path(__file__).resolve().parent
PLOTS = OUT / "plots"
PLOTS.mkdir(exist_ok=True)
LOG = ROOT / "logs" / "progress.md"

PRODUCTS = [
    "MICROCHIP_OVAL", "UV_VISOR_AMBER", "OXYGEN_SHAKE_GARLIC",
    "SLEEP_POD_POLYESTER", "SLEEP_POD_SUEDE", "PEBBLES_XS", "PEBBLES_XL",
]

# Test grid — periods spanning 200..30,000 ticks
PERIODS = sorted({int(p) for p in np.unique(np.geomspace(200, 30000, 80).astype(int))})
OMEGAS = [2 * np.pi / P for P in PERIODS]


def append_log(msg: str) -> None:
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    with LOG.open("a") as f:
        f.write(f"- [{ts}] {msg}\n")


def fit_sine_grid(t: np.ndarray, x: np.ndarray, omegas) -> dict:
    """Best A·sin(ωt+φ) + ct + d via grid-search on ω."""
    best = {"omega": float("nan"), "period": float("nan"), "r2": -np.inf,
            "A": 0.0, "phi": 0.0, "c": 0.0, "d": 0.0}
    n = len(t)
    if n < 100:
        return best
    for w in omegas:
        s = np.sin(w * t); c = np.cos(w * t)
        X = np.column_stack([np.ones(n), t, s, c])
        coef, *_ = np.linalg.lstsq(X, x, rcond=None)
        pred = X @ coef
        ss_res = float(np.sum((x - pred) ** 2))
        ss_tot = float(np.sum((x - x.mean()) ** 2))
        r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0
        if r2 > best["r2"]:
            A = float(np.hypot(coef[2], coef[3]))
            phi = float(np.arctan2(coef[3], coef[2]))
            best = {"omega": float(w), "period": float(2 * np.pi / w),
                    "r2": float(r2), "A": A, "phi": phi,
                    "c": float(coef[1]), "d": float(coef[0])}
    return best


def fit_sum_of_2_sines(t: np.ndarray, x: np.ndarray, omegas) -> dict:
    """Best A1·sin(ω1 t+φ1) + A2·sin(ω2 t+φ2) + ct + d via greedy two-pass."""
    best1 = fit_sine_grid(t, x, omegas)
    if not np.isfinite(best1["r2"]):
        return {"r2": float("nan")}
    pred1 = (best1["d"] + best1["c"] * t
             + best1["A"] * np.sin(best1["omega"] * t + best1["phi"]))
    resid = x - pred1
    best2 = fit_sine_grid(t, resid, omegas)
    pred = pred1 + (best2["A"] * np.sin(best2["omega"] * t + best2["phi"]))
    ss_res = float(np.sum((x - pred) ** 2))
    ss_tot = float(np.sum((x - x.mean()) ** 2))
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0
    return {
        "r2": float(r2),
        "omega1": best1["omega"], "period1": best1["period"], "A1": best1["A"], "phi1": best1["phi"],
        "omega2": best2["omega"], "period2": best2["period"], "A2": best2["A"], "phi2": best2["phi"],
        "c": best1["c"], "d": best1["d"],
    }


def predict_sine(params: dict, t: np.ndarray) -> np.ndarray:
    return (params["d"] + params["c"] * t
            + params["A"] * np.sin(params["omega"] * t + params["phi"]))


def predict_sum_of_2(params: dict, t: np.ndarray) -> np.ndarray:
    return (params["d"] + params["c"] * t
            + params["A1"] * np.sin(params["omega1"] * t + params["phi1"])
            + params["A2"] * np.sin(params["omega2"] * t + params["phi2"]))


def main() -> None:
    days = available_days()  # [2,3,4]
    print("Phase A start. Days:", days)
    prices_by_day = {d: load_prices(d) for d in days}

    per_day_rows = []
    oos_rows = []
    rolling_rows = []
    decision_lines = ["# Phase A — Sine Decision\n\n"]

    for prod in PRODUCTS:
        # Series per-day, plus stitched
        series_by_day = {}
        for d in days:
            df = prices_by_day[d]
            sub = df.loc[df["product"] == prod, "mid_price"].astype(float).ffill().bfill().to_numpy()
            series_by_day[d] = sub

        # ── Per-day single-sine fits ─────────────────────────────────────
        fits_by_day = {}
        for d in days:
            x = series_by_day[d]
            t = np.arange(len(x), dtype=float)
            f = fit_sine_grid(t, x, OMEGAS)
            fits_by_day[d] = f
            per_day_rows.append({"product": prod, "day": d, **f})

        # ── Stitched fit (round-1 baseline) ─────────────────────────────
        x_stitched = np.concatenate([series_by_day[d] for d in days])
        t_stitched = np.arange(len(x_stitched), dtype=float)
        stitched = fit_sine_grid(t_stitched, x_stitched, OMEGAS)
        per_day_rows.append({"product": prod, "day": -1, **stitched})

        # ── Sum-of-2 sines on each day ─────────────────────────────────
        for d in days:
            x = series_by_day[d]
            t = np.arange(len(x), dtype=float)
            ss = fit_sum_of_2_sines(t, x, OMEGAS)
            per_day_rows.append({"product": prod, "day": d, "model": "2sin", **ss})

        # ── Walk-forward: fit on day 2 → predict day 3, etc ────────────
        # Train on day 2 only, test on day 3.
        # Train on day 2+3, test on day 4.
        N_DAY = len(series_by_day[days[0]])

        for fold in [("A", [2], 3), ("B", [2, 3], 4)]:
            name, train_days, test_day = fold
            train_x = np.concatenate([series_by_day[d] for d in train_days])
            train_t = np.arange(len(train_x), dtype=float)
            test_x = series_by_day[test_day]
            test_t = np.arange(len(train_x), len(train_x) + len(test_x), dtype=float)

            # Fit single sine
            f1 = fit_sine_grid(train_t, train_x, OMEGAS)
            pred1 = predict_sine(f1, test_t)
            mse_sine = float(np.mean((test_x - pred1) ** 2))

            # Fit sum-of-2
            f2 = fit_sum_of_2_sines(train_t, train_x, OMEGAS)
            try:
                pred2 = predict_sum_of_2(f2, test_t)
                mse_2sin = float(np.mean((test_x - pred2) ** 2))
            except Exception:
                mse_2sin = float("nan")

            # Linear + flat baselines
            slope, intercept = np.polyfit(train_t, train_x, 1)
            mse_linear = float(np.mean((test_x - (slope * test_t + intercept)) ** 2))
            mse_flat = float(np.mean((test_x - train_x[-1]) ** 2))
            mse_train_mean = float(np.mean((test_x - train_x.mean()) ** 2))

            # AR(1)+drift baseline: predict each x_t = x_{t-1} (random walk)
            mse_rw = float(np.mean(np.diff(np.concatenate([train_x[-1:], test_x])) ** 2))

            # Test-period local mean (zero-info upper bound)
            mse_test_mean = float(np.var(test_x))

            oos_rows.append({
                "product": prod, "fold": name, "test_day": test_day,
                "n_train": int(len(train_x)), "n_test": int(len(test_x)),
                "train_r2_sine": f1["r2"], "train_period": f1["period"],
                "train_A": f1["A"], "train_phi": f1["phi"],
                "mse_sine": mse_sine, "mse_2sin": mse_2sin,
                "mse_linear": mse_linear, "mse_flat": mse_flat,
                "mse_rw": mse_rw, "mse_test_var": mse_test_mean,
                "sine_beats_flat": mse_sine < mse_flat,
                "sine_beats_linear": mse_sine < mse_linear,
                "sine_beats_rw": mse_sine < mse_rw,
                "improvement_vs_flat": (mse_flat - mse_sine) / mse_flat if mse_flat else 0.0,
                "improvement_vs_linear": (mse_linear - mse_sine) / mse_linear if mse_linear else 0.0,
            })

        # ── Rolling sine fit on 3,000-tick windows over the stitched series
        n = len(x_stitched)
        win = 3000; step = 500
        for start in range(0, n - win + 1, step):
            x_w = x_stitched[start:start + win]
            t_w = np.arange(start, start + win, dtype=float)
            f_w = fit_sine_grid(t_w - start, x_w, OMEGAS)
            rolling_rows.append({
                "product": prod, "start": start,
                "period": f_w["period"], "phi": f_w["phi"],
                "A": f_w["A"], "r2": f_w["r2"],
            })

        # ── Per-product plot ────────────────────────────────────────────
        try:
            fig, axes = plt.subplots(3, 1, figsize=(12, 9))
            for i, d in enumerate(days):
                ax = axes[i]
                x = series_by_day[d]
                t = np.arange(len(x))
                ax.plot(t, x, lw=0.4, color="black", label=f"day {d} mid")
                f = fits_by_day[d]
                pred = predict_sine(f, t.astype(float))
                ax.plot(t, pred, lw=0.8, color="red",
                        label=f"sine: P={f['period']:.0f} A={f['A']:.1f} R²={f['r2']:.3f}")
                ax.set_title(f"{prod} — day {d}")
                ax.legend(fontsize=7)
            fig.tight_layout()
            fig.savefig(PLOTS / f"{prod}.png", dpi=80)
            plt.close(fig)
        except Exception as e:
            print("plot failed", prod, e)

    pd.DataFrame(per_day_rows).to_csv(OUT / "per_day_fits.csv", index=False)
    pd.DataFrame(oos_rows).to_csv(OUT / "oos_mse.csv", index=False)
    pd.DataFrame(rolling_rows).to_csv(OUT / "rolling_phase.csv", index=False)

    # Decision: per product, sine is ‘exploitable’ if BOTH folds have
    # mse_sine < mse_flat AND mse_sine < mse_linear.
    decision_lines.append("## Per-product OOS MSE comparison (lower = better)\n\n")
    df_oos = pd.DataFrame(oos_rows)
    decision_lines.append(df_oos.to_markdown(index=False) + "\n\n")
    decision_lines.append("## Decision\n\n")

    df_per_day = pd.DataFrame(per_day_rows)
    df_single = df_per_day[~df_per_day["day"].eq(-1) & ~df_per_day.get("model", pd.Series([None]*len(df_per_day))).eq("2sin")]
    decision_lines.append("### Per-day single-sine R² stability\n\n")
    decision_lines.append(df_single.pivot_table(index="product", columns="day",
                                                  values="r2").to_markdown() + "\n\n")
    decision_lines.append("### Per-day periods (stability check)\n\n")
    decision_lines.append(df_single.pivot_table(index="product", columns="day",
                                                  values="period").to_markdown() + "\n\n")

    # Per product final yes/no
    decision_lines.append("### Final yes/no per product\n\n")
    decision_lines.append("| product | foldA sine<flat | foldB sine<flat | foldA sine<linear | foldB sine<linear | exploitable |\n")
    decision_lines.append("|---|---|---|---|---|---|\n")
    for prod in PRODUCTS:
        sub = df_oos[df_oos["product"] == prod]
        a = sub[sub["fold"] == "A"].iloc[0] if len(sub[sub["fold"] == "A"]) else None
        b = sub[sub["fold"] == "B"].iloc[0] if len(sub[sub["fold"] == "B"]) else None
        if a is None or b is None:
            continue
        ex = bool(a["sine_beats_flat"] and b["sine_beats_flat"]
                  and a["sine_beats_linear"] and b["sine_beats_linear"])
        decision_lines.append(
            f"| {prod} | {a['sine_beats_flat']} | {b['sine_beats_flat']} | "
            f"{a['sine_beats_linear']} | {b['sine_beats_linear']} | "
            f"**{'YES' if ex else 'no'}** |\n"
        )

    (OUT / "decision.md").write_text("".join(decision_lines))
    append_log("PhaseA DONE — see 13_round2_research/A_sine/decision.md")
    print("Phase A done.")


if __name__ == "__main__":
    main()
