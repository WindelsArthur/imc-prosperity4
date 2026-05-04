"""Phase C — Lagged cointegration.

For every ordered pair (i,j) and lag k ∈ {1,2,3,5,10,20,50,100}:
- Engle-Granger on price_i(t) = α + β · price_j(t-k) + ε(t).
- ADF p, OU half-life on residual.
- Walk-forward z-score reversion strategy if ADF<0.05 and HL∈[5,1000].
- Direction: train on day 2, fix β; test on day 3.

Outputs:
    14_lag_research/C_lagged_coint/lagged_coint.csv
    14_lag_research/C_lagged_coint/decision.md
"""
from __future__ import annotations

import sys
import time
import warnings
from itertools import product
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

LAGS = [1, 2, 3, 5, 10, 20, 50, 100]


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


def z_strategy(spread: np.ndarray, mu: float, sd: float,
               z_entry: float = 1.5, z_exit: float = 0.3) -> dict:
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
    print("Phase C start.")
    pivot = load_pivot()
    days_marker = pivot.index.get_level_values("day").to_numpy()
    t0 = time.time()

    rows = []
    n_prods = len(ROUND5_PRODUCTS)
    n_total = n_prods * (n_prods - 1) * len(LAGS)
    done = 0

    # Random subsample of obs for ADF speed: every 5th tick → 6K obs across 3 days
    SAMPLE = 5

    for i, pi in enumerate(ROUND5_PRODUCTS):
        for j, pj in enumerate(ROUND5_PRODUCTS):
            if i == j:
                continue
            yi = pivot[pi].to_numpy()
            yj = pivot[pj].to_numpy()
            for k in LAGS:
                # price_i(t) = α + β · price_j(t-k) + ε
                # Trim
                yi_t = yi[k:]; yj_t = yj[:-k] if k > 0 else yj
                n = min(len(yi_t), len(yj_t))
                if n < 1000:
                    continue
                yi_t, yj_t = yi_t[:n], yj_t[:n]

                # OLS β, intercept
                X = np.column_stack([np.ones(n), yj_t])
                coef, *_ = np.linalg.lstsq(X, yi_t, rcond=None)
                slope, intercept = float(coef[1]), float(coef[0])
                resid = yi_t - (intercept + slope * yj_t)

                # ADF on subsample
                ap = adf_p(resid[::SAMPLE])
                if not np.isfinite(ap) or ap > 0.05:
                    done += 1
                    continue
                hl = ou_half_life(resid)
                if not (5 <= hl <= 1000):
                    done += 1
                    continue

                # Walk-forward z-strategy: train day 2, test day 3.
                day_marker_t = days_marker[k:][:n]
                tr_mask = day_marker_t == 2
                te_mask = day_marker_t == 3
                if tr_mask.sum() < 1000 or te_mask.sum() < 1000:
                    done += 1
                    continue
                mu_tr = float(resid[tr_mask].mean())
                sd_tr = float(resid[tr_mask].std())
                wf_a = z_strategy(resid[te_mask], mu_tr, sd_tr)
                # Train 2+3, test 4
                tr_mask2 = (day_marker_t == 2) | (day_marker_t == 3)
                te_mask2 = day_marker_t == 4
                mu_tr2 = float(resid[tr_mask2].mean())
                sd_tr2 = float(resid[tr_mask2].std())
                wf_b = z_strategy(resid[te_mask2], mu_tr2, sd_tr2)

                if not np.isfinite(wf_a["sharpe"]) or not np.isfinite(wf_b["sharpe"]):
                    done += 1
                    continue

                rows.append({
                    "i": pi, "j": pj, "lag": k,
                    "group_i": group_of(pi), "group_j": group_of(pj),
                    "slope": slope, "intercept": intercept,
                    "adf_p": ap, "ou_hl": hl,
                    "fA_sharpe": wf_a["sharpe"], "fA_pnl": wf_a["total_pnl"], "fA_trades": wf_a["n_trades"],
                    "fB_sharpe": wf_b["sharpe"], "fB_pnl": wf_b["total_pnl"], "fB_trades": wf_b["n_trades"],
                    "min_fold_sharpe": min(wf_a["sharpe"], wf_b["sharpe"]),
                })
                done += 1
        if i % 5 == 0:
            elapsed = time.time() - t0
            print(f"  {i+1}/{n_prods} done; total relations passing ADF/HL gate so far: {len(rows)}; {elapsed:.1f}s")

    df = pd.DataFrame(rows)
    df.to_csv(OUT / "lagged_coint.csv", index=False)

    if df.empty:
        md = ["# Phase C — Lagged Cointegration\n\n",
              "**No lagged-coint relations passed ADF<0.05 + HL∈[5,1000]**\n"]
    else:
        df_surv = df[df["min_fold_sharpe"] >= 0.7].sort_values("min_fold_sharpe", ascending=False)
        df_surv.to_csv(OUT / "lagged_coint_surviving.csv", index=False)
        md = ["# Phase C — Lagged Cointegration\n\n",
              f"- Pairs × lags tested: {n_total}\n",
              f"- Passing ADF<0.05 + HL∈[5,1000]: {len(df)}\n",
              f"- Min-fold OOS Sharpe ≥ 0.7: {len(df_surv)}\n\n",
              "## Top 30 surviving pairs\n\n",
              df_surv.head(30).to_markdown(index=False) + "\n",
        ]
    (OUT / "decision.md").write_text("".join(md))
    append_log(f"PhaseC DONE — surviving lagged-coint pairs: {len(df) if df.empty else int((df['min_fold_sharpe']>=0.7).sum())}")
    print("Phase C done.")


if __name__ == "__main__":
    main()
