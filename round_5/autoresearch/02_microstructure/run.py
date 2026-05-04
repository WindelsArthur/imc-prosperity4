"""Phase 2 — Microstructure.

For each product:
- L1/L2/L3 imbalance and IC vs forward mid moves at horizons 1,5,20.
- OFI (Cont-Kukanov style) and IC.
- Effective spread, realised spread (5-tick), Kyle lambda proxy.
- Quote update rate per side.
- Stale-quote / near-cross frequency.

Outputs
    02_microstructure/microstructure_summary.csv
    02_microstructure/details/{product}.json
"""
from __future__ import annotations

import json
import sys
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from utils.data_loader import load_prices, available_days
from utils.round5_products import ROUND5_PRODUCTS, group_of

warnings.filterwarnings("ignore")
OUT = Path(__file__).resolve().parent
DETAILS = OUT / "details"
DETAILS.mkdir(parents=True, exist_ok=True)
LOG = ROOT / "logs" / "progress.md"


def append_log(msg: str) -> None:
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    with LOG.open("a") as f:
        f.write(f"- [{ts}] {msg}\n")


def imbalance_l(df: pd.DataFrame, levels: int) -> np.ndarray:
    bv = df[[f"bid_volume_{i}" for i in range(1, levels + 1)]].fillna(0).sum(axis=1).to_numpy()
    av = df[[f"ask_volume_{i}" for i in range(1, levels + 1)]].fillna(0).sum(axis=1).to_numpy()
    tot = bv + av
    out = np.where(tot > 0, (bv - av) / tot, 0.0)
    return out


def ofi(df: pd.DataFrame) -> np.ndarray:
    """Cont-Kukanov L1 OFI series."""
    bp = df["bid_price_1"].ffill().to_numpy()
    bv = df["bid_volume_1"].fillna(0).to_numpy().astype(float)
    ap = df["ask_price_1"].ffill().to_numpy()
    av = df["ask_volume_1"].fillna(0).to_numpy().astype(float)
    n = len(bp)
    e_bid = np.zeros(n)
    e_ask = np.zeros(n)
    for k in range(1, n):
        if bp[k] > bp[k - 1]:
            e_bid[k] = bv[k]
        elif bp[k] == bp[k - 1]:
            e_bid[k] = bv[k] - bv[k - 1]
        else:
            e_bid[k] = -bv[k - 1]
        if ap[k] < ap[k - 1]:
            e_ask[k] = av[k]
        elif ap[k] == ap[k - 1]:
            e_ask[k] = av[k] - av[k - 1]
        else:
            e_ask[k] = -av[k - 1]
    return e_bid - e_ask


def stitch(prices_by_day: dict[int, pd.DataFrame], product: str) -> pd.DataFrame:
    parts = []
    for d in sorted(prices_by_day.keys()):
        df = prices_by_day[d]
        parts.append(df.loc[df["product"] == product].copy())
    out = pd.concat(parts, ignore_index=True).sort_values(["day", "timestamp"]).reset_index(drop=True)
    return out


def spearman(x: np.ndarray, y: np.ndarray) -> float:
    n = min(len(x), len(y))
    x = x[:n]; y = y[:n]
    mask = np.isfinite(x) & np.isfinite(y)
    if mask.sum() < 8:
        return float("nan")
    rx = pd.Series(x[mask]).rank(method="average").to_numpy()
    ry = pd.Series(y[mask]).rank(method="average").to_numpy()
    return float(np.corrcoef(rx, ry)[0, 1])


def main() -> None:
    days = available_days()
    append_log(f"Phase2 START — products={len(ROUND5_PRODUCTS)}")
    prices_by_day = {d: load_prices(d) for d in days}

    rows = []
    for i, product in enumerate(ROUND5_PRODUCTS, start=1):
        df = stitch(prices_by_day, product)
        mid = df["mid_price"].astype(float).ffill().bfill().to_numpy()
        bp1 = df["bid_price_1"].ffill().to_numpy()
        ap1 = df["ask_price_1"].ffill().to_numpy()
        spread = ap1 - bp1

        imb1 = imbalance_l(df, 1)
        imb2 = imbalance_l(df, 2)
        imb3 = imbalance_l(df, 3)
        of = ofi(df)

        # Forward mid changes
        fr1 = np.concatenate([np.diff(mid), [np.nan]])
        fr5 = np.concatenate([mid[5:] - mid[:-5], [np.nan] * 5])
        fr20 = np.concatenate([mid[20:] - mid[:-20], [np.nan] * 20])

        # IC (Spearman) of signal vs forward returns
        ic_imb1_1 = spearman(imb1, fr1)
        ic_imb1_5 = spearman(imb1, fr5)
        ic_imb1_20 = spearman(imb1, fr20)
        ic_imb2_5 = spearman(imb2, fr5)
        ic_imb3_5 = spearman(imb3, fr5)
        ic_ofi_1 = spearman(of, fr1)
        ic_ofi_5 = spearman(of, fr5)

        # Effective spread (mid->trade not directly available, approximate)
        # Use top-of-book spread mean
        eff_spread = float(np.nanmean(spread))
        eff_spread_med = float(np.nanmedian(spread))

        # Realised spread: 5-tick mid drift after a sign — proxy via L1-imb sign as trade direction
        sign = np.sign(imb1)
        rs5 = sign[:-5] * (mid[5:] - mid[:-5])
        rs5_mean = float(np.nanmean(rs5))

        # Kyle lambda proxy: mid changes regressed on OFI
        of_clean = of[1:]
        dr = np.diff(mid)
        n = min(len(of_clean), len(dr))
        if n > 100:
            X = of_clean[:n]
            Y = dr[:n]
            mask = np.isfinite(X) & np.isfinite(Y)
            if mask.sum() > 50:
                slope, intercept = np.polyfit(X[mask], Y[mask], 1)
                kyle_lambda = float(slope)
            else:
                kyle_lambda = float("nan")
        else:
            kyle_lambda = float("nan")

        # Quote update rate
        bp_changes = int((np.diff(bp1) != 0).sum())
        ap_changes = int((np.diff(ap1) != 0).sum())
        n_obs = len(df)

        # Anchor / stickiness: longest run of constant bid_price_1
        def longest_run(a):
            if len(a) == 0:
                return 0
            best = 1; cur = 1
            for k in range(1, len(a)):
                if a[k] == a[k - 1]:
                    cur += 1
                    if cur > best:
                        best = cur
                else:
                    cur = 1
            return best
        bp_run = longest_run(bp1)
        ap_run = longest_run(ap1)

        # Stale / near-cross: how often bid > best ask of previous tick (rare exploitable)
        near_cross = int(((bp1[1:] >= ap1[:-1] - 1) & (bp1[1:] <= ap1[:-1])).sum())
        crossed = int((bp1 >= ap1).sum())  # impossible normally

        rows.append({
            "product": product,
            "group": group_of(product),
            "n_obs": n_obs,
            "ic_imb1_h1": ic_imb1_1,
            "ic_imb1_h5": ic_imb1_5,
            "ic_imb1_h20": ic_imb1_20,
            "ic_imb2_h5": ic_imb2_5,
            "ic_imb3_h5": ic_imb3_5,
            "ic_ofi_h1": ic_ofi_1,
            "ic_ofi_h5": ic_ofi_5,
            "eff_spread_mean": eff_spread,
            "eff_spread_med": eff_spread_med,
            "realised_spread_5": rs5_mean,
            "kyle_lambda": kyle_lambda,
            "bp_changes": bp_changes,
            "ap_changes": ap_changes,
            "bp_change_rate": bp_changes / max(n_obs - 1, 1),
            "ap_change_rate": ap_changes / max(n_obs - 1, 1),
            "longest_bp_run": bp_run,
            "longest_ap_run": ap_run,
            "near_cross_count": near_cross,
            "crossed_count": crossed,
        })
        if i % 10 == 0 or i == len(ROUND5_PRODUCTS):
            print(f"[{i}/{len(ROUND5_PRODUCTS)}] {product}")

    df_out = pd.DataFrame(rows)
    df_out.to_csv(OUT / "microstructure_summary.csv", index=False)
    append_log(f"Phase2 DONE — wrote microstructure_summary.csv rows={len(df_out)}")
    print("Phase 2 done.")


if __name__ == "__main__":
    main()
