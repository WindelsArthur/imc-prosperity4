"""Phase C — fast version. Focus on top-200 pairs from Phase A's price-CCF
peak (where contemporaneous |ρ| > 0.4) and lags ∈ {1, 5, 20, 100}.
"""
from __future__ import annotations

import sys
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from utils.data_loader import load_prices, available_days
from utils.round5_products import ROUND5_PRODUCTS, group_of

warnings.filterwarnings("ignore")
OUT = Path(__file__).resolve().parent
LOG = ROOT / "logs" / "progress.md"

LAGS = [1, 5, 20, 100]
SAMPLE = 10  # subsample for ADF


def append_log(msg):
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    with LOG.open("a") as f:
        f.write(f"- [{ts}] {msg}\n")


def load_pivot():
    days = available_days()
    parts = []
    for d in days:
        df = load_prices(d)
        sub = df.loc[df["product"].isin(ROUND5_PRODUCTS),
                     ["day", "timestamp", "product", "mid_price"]].copy()
        sub["mid_price"] = sub["mid_price"].astype(float)
        parts.append(sub)
    full = pd.concat(parts, ignore_index=True).sort_values(["day", "timestamp"])
    pivot = full.pivot_table(index=["day", "timestamp"], columns="product", values="mid_price")
    pivot = pivot[ROUND5_PRODUCTS].ffill().bfill()
    return pivot


def adf_p(x):
    from statsmodels.tsa.stattools import adfuller
    if len(x) < 100:
        return float("nan")
    try:
        return float(adfuller(x, autolag="AIC")[1])
    except Exception:
        return float("nan")


def ou_half_life(x):
    if len(x) < 4:
        return float("inf")
    x_lag = x[:-1]; dx = np.diff(x)
    X = np.column_stack([np.ones_like(x_lag), x_lag])
    coef, *_ = np.linalg.lstsq(X, dx, rcond=None)
    beta = float(coef[1])
    if beta >= 0:
        return float("inf")
    return float(-np.log(2.0) / np.log(1.0 + beta))


def z_strategy(spread, mu, sd, z_entry=1.5, z_exit=0.3):
    if sd <= 0 or len(spread) < 100:
        return {"sharpe": float("nan"), "n_trades": 0, "total_pnl": 0.0}
    z = (spread - mu) / sd
    pos = np.zeros_like(z); cur = 0.0; n_trades = 0
    for k, zv in enumerate(z):
        if cur == 0.0:
            if zv > z_entry: cur = -1.0; n_trades += 1
            elif zv < -z_entry: cur = 1.0; n_trades += 1
        else:
            if abs(zv) < z_exit: cur = 0.0
        pos[k] = cur
    pnl = pos[:-1] * np.diff(spread)
    if pnl.std() <= 0:
        return {"sharpe": float("nan"), "n_trades": int(n_trades), "total_pnl": float(pnl.sum())}
    return {
        "sharpe": float(pnl.mean() / pnl.std() * np.sqrt(10000)),
        "n_trades": int(n_trades),
        "total_pnl": float(pnl.sum()),
    }


def main():
    print("Phase C-fast start.")
    pivot = load_pivot()
    days_marker = pivot.index.get_level_values("day").to_numpy()
    t0 = time.time()

    # Load Phase A peak summary; pick pairs with high |peak_rho_prices|
    peaks = pd.read_csv(OUT.parent / "A_atlas" / "peak_summary.csv")
    peaks["abs_pr"] = peaks["peak_rho_prices"].abs()
    top = peaks.sort_values("abs_pr", ascending=False).head(300)
    print(f"  testing {len(top)} pairs × {len(LAGS)} lags")

    rows = []
    for _, row in top.iterrows():
        pi, pj = row["i"], row["j"]
        yi = pivot[pi].to_numpy()
        yj = pivot[pj].to_numpy()
        for k in LAGS:
            yi_t = yi[k:]; yj_t = yj[:-k]
            n = min(len(yi_t), len(yj_t))
            if n < 1000:
                continue
            yi_t, yj_t = yi_t[:n], yj_t[:n]
            X = np.column_stack([np.ones(n), yj_t])
            coef, *_ = np.linalg.lstsq(X, yi_t, rcond=None)
            slope, intercept = float(coef[1]), float(coef[0])
            resid = yi_t - (intercept + slope * yj_t)

            ap = adf_p(resid[::SAMPLE])
            if not np.isfinite(ap) or ap > 0.05:
                continue
            hl = ou_half_life(resid)
            if not (5 <= hl <= 1000):
                continue

            day_marker_t = days_marker[k:][:n]
            tr = day_marker_t == 2
            te = day_marker_t == 3
            if tr.sum() < 1000 or te.sum() < 1000:
                continue
            mu_tr = float(resid[tr].mean()); sd_tr = float(resid[tr].std())
            wf_a = z_strategy(resid[te], mu_tr, sd_tr)
            tr2 = (day_marker_t == 2) | (day_marker_t == 3)
            te2 = day_marker_t == 4
            mu_tr2 = float(resid[tr2].mean()); sd_tr2 = float(resid[tr2].std())
            wf_b = z_strategy(resid[te2], mu_tr2, sd_tr2)

            if not np.isfinite(wf_a["sharpe"]) or not np.isfinite(wf_b["sharpe"]):
                continue
            rows.append({
                "i": pi, "j": pj, "lag": k,
                "group_i": group_of(pi), "group_j": group_of(pj),
                "slope": slope, "intercept": intercept,
                "adf_p": ap, "ou_hl": hl,
                "fA_sharpe": wf_a["sharpe"], "fA_pnl": wf_a["total_pnl"],
                "fB_sharpe": wf_b["sharpe"], "fB_pnl": wf_b["total_pnl"],
                "min_fold_sharpe": min(wf_a["sharpe"], wf_b["sharpe"]),
            })

    df = pd.DataFrame(rows)
    df.to_csv(OUT / "lagged_coint_fast.csv", index=False)
    surv = df[df["min_fold_sharpe"] >= 0.7].sort_values("min_fold_sharpe", ascending=False) if not df.empty else pd.DataFrame()
    if not surv.empty:
        surv.to_csv(OUT / "lagged_coint_surviving.csv", index=False)

    md = ["# Phase C — Lagged Cointegration (fast)\n\n",
          f"- Pairs × lags tested: {len(top) * len(LAGS)}\n",
          f"- Passing ADF<0.05 + HL∈[5,1000]: {len(df)}\n",
          f"- Min-fold OOS Sharpe ≥ 0.7: {len(surv)}\n\n",
          "## Top 30 surviving pairs\n\n",
          (surv.head(30).to_markdown(index=False) if not surv.empty else "_None_") + "\n",
    ]
    (OUT / "decision.md").write_text("".join(md))
    elapsed = time.time() - t0
    append_log(f"PhaseC DONE — surviving lagged-coint pairs: {len(surv)} ({elapsed:.0f}s)")
    print(f"Phase C done in {elapsed:.0f}s. {len(surv)} survivors.")


if __name__ == "__main__":
    main()
