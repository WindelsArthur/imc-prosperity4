"""Phase F — lagged OFI / lagged-flow predictors.

For each product:
- IC of OFI(t-k) → return(t) for k=1..50.
For each pair (i, j) with high contemporaneous |ρ|:
- IC of OFI_i(t-k) → return_j(t) for k=1..50. Cross-product flow leakage.

Outputs:
    14_lag_research/F_flow_lag/own_ofi_lag_ic.csv
    14_lag_research/F_flow_lag/cross_ofi_lag_ic.csv
    14_lag_research/F_flow_lag/decision.md
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

LAGS = list(range(1, 51))


def append_log(msg):
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    with LOG.open("a") as f:
        f.write(f"- [{ts}] {msg}\n")


def build_per_day(prices_by_day, prod):
    out = {}
    for d, df in prices_by_day.items():
        sub = df.loc[df["product"] == prod].sort_values("timestamp").reset_index(drop=True)
        bp = sub["bid_price_1"].ffill().to_numpy()
        bv = sub["bid_volume_1"].fillna(0).to_numpy().astype(float)
        ap = sub["ask_price_1"].ffill().to_numpy()
        av = sub["ask_volume_1"].fillna(0).to_numpy().astype(float)
        mid = sub["mid_price"].astype(float).ffill().bfill().to_numpy()
        n = len(bp)
        e_bid = np.zeros(n)
        e_ask = np.zeros(n)
        for k in range(1, n):
            if bp[k] > bp[k - 1]: e_bid[k] = bv[k]
            elif bp[k] == bp[k - 1]: e_bid[k] = bv[k] - bv[k - 1]
            else: e_bid[k] = -bv[k - 1]
            if ap[k] < ap[k - 1]: e_ask[k] = av[k]
            elif ap[k] == ap[k - 1]: e_ask[k] = av[k] - av[k - 1]
            else: e_ask[k] = -av[k - 1]
        out[d] = {"ofi": e_bid - e_ask, "rets": np.diff(mid), "mid": mid}
    return out


def lag_ic(x, y, k):
    """IC of x(t-k) → y(t). x and y are 1D arrays of equal length."""
    if k <= 0 or k >= len(x):
        return float("nan"), 0
    x_lag = x[:-k]
    y_t = y[k:]
    n = min(len(x_lag), len(y_t))
    x_lag, y_t = x_lag[:n], y_t[:n]
    mask = np.isfinite(x_lag) & np.isfinite(y_t) & (np.abs(x_lag) + np.abs(y_t) > 0)
    if mask.sum() < 50:
        return float("nan"), int(mask.sum())
    rx = pd.Series(x_lag[mask]).rank(method="average").to_numpy()
    ry = pd.Series(y_t[mask]).rank(method="average").to_numpy()
    return float(np.corrcoef(rx, ry)[0, 1]), int(mask.sum())


def main():
    days = available_days()
    print("Phase F start.")
    prices_by_day = {d: load_prices(d) for d in days}

    print("Building per-day OFI/returns...")
    cache = {}
    for prod in ROUND5_PRODUCTS:
        cache[prod] = build_per_day(prices_by_day, prod)

    own_rows = []
    for prod in ROUND5_PRODUCTS:
        # Per-day average IC
        for k in LAGS:
            ics = []; ns = []
            for d in days:
                x = cache[prod][d]["ofi"][1:]
                y = cache[prod][d]["rets"]
                # rets length = mid length - 1; ofi length = mid length. Align.
                ic, n = lag_ic(x, y, k)
                if np.isfinite(ic):
                    ics.append(ic); ns.append(n)
            if ics:
                own_rows.append({"product": prod, "lag": k, "ic": np.mean(ics), "n_avg": int(np.mean(ns))})
    df_own = pd.DataFrame(own_rows)
    df_own.to_csv(OUT / "own_ofi_lag_ic.csv", index=False)

    # Cross-product OFI: take top 30 pairs by |peak_rho_ofi| from Phase A's parquet
    try:
        ccf_ofi = pd.read_parquet(OUT.parent / "A_atlas" / "ccf_ofi.parquet")
        # peak |rho| per pair
        ccf_ofi["abs"] = ccf_ofi["rho"].abs()
        peak = ccf_ofi.loc[ccf_ofi.groupby(["i", "j"])["abs"].idxmax()]
        top_pairs = peak.sort_values("abs", ascending=False).head(60)
    except Exception:
        top_pairs = pd.DataFrame()

    cross_rows = []
    for _, r in top_pairs.iterrows():
        i, j = r["i"], r["j"]
        if i == j:
            continue
        for k in [1, 2, 3, 5, 10, 20, 50]:
            ics = []
            for d in days:
                x = cache[i][d]["ofi"][1:]
                y = cache[j][d]["rets"]
                ic, n = lag_ic(x, y, k)
                if np.isfinite(ic):
                    ics.append(ic)
            if ics:
                cross_rows.append({"i": i, "j": j, "lag": k,
                                    "ic": float(np.mean(ics)),
                                    "abs_ic": float(abs(np.mean(ics)))})
    df_cross = pd.DataFrame(cross_rows)
    df_cross.to_csv(OUT / "cross_ofi_lag_ic.csv", index=False)

    md = ["# Phase F — lagged OFI / cross-flow IC\n\n",
          "## Top 20 own OFI lag-IC peaks per product\n\n"]
    own_top = df_own.copy()
    own_top["abs_ic"] = own_top["ic"].abs()
    own_top = own_top.sort_values("abs_ic", ascending=False).head(20)
    md.append(own_top.to_markdown(index=False) + "\n\n")
    if not df_cross.empty:
        md.append("## Top 20 cross-product OFI(i)→ret(j) lag-IC\n\n")
        md.append(df_cross.sort_values("abs_ic", ascending=False).head(20).to_markdown(index=False) + "\n")
    (OUT / "decision.md").write_text("".join(md))
    append_log("PhaseF DONE")
    print("Phase F done.")


if __name__ == "__main__":
    main()
