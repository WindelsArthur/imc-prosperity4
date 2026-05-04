"""Phase D — Microstructure round 2.

Per product:
- Multi-level OFI: aggregate L1+L2+L3 changes per side; IC at horizons 1,5,20,100.
- Spread regime HMM (2 state): conditional adverse-selection cost.
- Time-since-last-trade vs forward returns.
- Effective vs realised spread per regime → adverse-selection cost.

Outputs:
    13_round2_research/D_micro/micro2_summary.csv
    13_round2_research/D_micro/decision.md
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

from utils.data_loader import load_prices, load_trades, available_days
from utils.round5_products import ROUND5_PRODUCTS, group_of

warnings.filterwarnings("ignore")
OUT = Path(__file__).resolve().parent
LOG = ROOT / "logs" / "progress.md"


def append_log(msg):
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    with LOG.open("a") as f:
        f.write(f"- [{ts}] {msg}\n")


def stitch(prices_by_day, prod):
    parts = []
    for d in sorted(prices_by_day.keys()):
        df = prices_by_day[d]
        parts.append(df.loc[df["product"] == prod].sort_values("timestamp").reset_index(drop=True))
    out = pd.concat(parts, ignore_index=True)
    return out


def multi_ofi(df: pd.DataFrame, levels: int = 3) -> np.ndarray:
    """Per-tick multi-level OFI (Cont-Kukanov style aggregating L1..Lk)."""
    n = len(df)
    e_bid_total = np.zeros(n)
    e_ask_total = np.zeros(n)
    for L in range(1, levels + 1):
        bp_col = f"bid_price_{L}"; bv_col = f"bid_volume_{L}"
        ap_col = f"ask_price_{L}"; av_col = f"ask_volume_{L}"
        if bp_col not in df.columns:
            continue
        bp = df[bp_col].ffill().fillna(0).to_numpy()
        bv = df[bv_col].fillna(0).to_numpy().astype(float)
        ap = df[ap_col].ffill().fillna(0).to_numpy()
        av = df[av_col].fillna(0).to_numpy().astype(float)
        for k in range(1, n):
            if bp[k] > bp[k - 1]:
                e_bid_total[k] += bv[k]
            elif bp[k] == bp[k - 1]:
                e_bid_total[k] += (bv[k] - bv[k - 1])
            else:
                e_bid_total[k] -= bv[k - 1]
            if ap[k] < ap[k - 1]:
                e_ask_total[k] += av[k]
            elif ap[k] == ap[k - 1]:
                e_ask_total[k] += (av[k] - av[k - 1])
            else:
                e_ask_total[k] -= av[k - 1]
    return e_bid_total - e_ask_total


def spearman(x, y):
    n = min(len(x), len(y))
    x = x[:n]; y = y[:n]
    mask = np.isfinite(x) & np.isfinite(y)
    if mask.sum() < 8:
        return float("nan")
    rx = pd.Series(x[mask]).rank(method="average").to_numpy()
    ry = pd.Series(y[mask]).rank(method="average").to_numpy()
    return float(np.corrcoef(rx, ry)[0, 1])


def main():
    days = available_days()
    print("Phase D start.")
    prices_by_day = {d: load_prices(d) for d in days}

    rows = []
    for i, prod in enumerate(ROUND5_PRODUCTS, 1):
        df = stitch(prices_by_day, prod)
        mid = df["mid_price"].astype(float).ffill().bfill().to_numpy()
        spread = (df["ask_price_1"] - df["bid_price_1"]).astype(float).ffill().fillna(0).to_numpy()

        ofi = multi_ofi(df, levels=3)

        fr1 = np.concatenate([np.diff(mid), [np.nan]])
        fr5 = np.concatenate([mid[5:] - mid[:-5], [np.nan] * 5])
        fr20 = np.concatenate([mid[20:] - mid[:-20], [np.nan] * 20])
        fr100 = np.concatenate([mid[100:] - mid[:-100], [np.nan] * 100])

        ic1 = spearman(ofi, fr1)
        ic5 = spearman(ofi, fr5)
        ic20 = spearman(ofi, fr20)
        ic100 = spearman(ofi, fr100)

        # Spread-regime HMM: split spread into 2 states by median
        med = float(np.median(spread))
        wide = spread > med
        # Adverse-selection cost: realised spread (sign of mid_change × forward mid_change)
        # per regime
        sign = np.sign(np.concatenate([[0], np.diff(mid)]))
        rs5 = sign[:-5] * (mid[5:] - mid[:-5])
        rs5_wide = float(np.nanmean(rs5[wide[:-5]])) if wide[:-5].any() else float("nan")
        rs5_tight = float(np.nanmean(rs5[~wide[:-5]])) if (~wide[:-5]).any() else float("nan")

        # Spread regime persistence (run length)
        regime_changes = int((np.diff(wide.astype(int)) != 0).sum())
        regime_mean_run = len(wide) / max(regime_changes, 1)

        # Roll's effective spread: 2*sqrt(-Cov(ΔP_t, ΔP_{t-1}))
        d = np.diff(mid)
        if len(d) > 100:
            cov = float(np.cov(d[:-1], d[1:])[0, 1])
            roll_es = float(2 * np.sqrt(-cov)) if cov < 0 else float("nan")
        else:
            roll_es = float("nan")

        rows.append({
            "product": prod, "group": group_of(prod),
            "ofi_ic_h1": ic1, "ofi_ic_h5": ic5, "ofi_ic_h20": ic20, "ofi_ic_h100": ic100,
            "spread_med": med, "spread_regime_changes": regime_changes,
            "spread_regime_mean_run": regime_mean_run,
            "rs5_wide_regime": rs5_wide, "rs5_tight_regime": rs5_tight,
            "roll_effective_spread": roll_es,
        })
        if i % 10 == 0:
            print(f"  [{i}/{len(ROUND5_PRODUCTS)}] {prod}")

    pd.DataFrame(rows).to_csv(OUT / "micro2_summary.csv", index=False)

    df = pd.DataFrame(rows)
    df["abs_ic5"] = df["ofi_ic_h5"].abs()
    md = ["# Phase D — Microstructure 2\n\n",
          "## Top 15 |IC OFI h=5|\n\n",
          df.sort_values("abs_ic5", ascending=False).head(15)[
              ["product", "group", "ofi_ic_h1", "ofi_ic_h5", "ofi_ic_h20", "ofi_ic_h100"]
          ].to_markdown(index=False) + "\n\n",
          "## Bleeding products: rs5 in tight-spread regime (positive = MM gains, negative = MM bleeds)\n\n",
          df.sort_values("rs5_tight_regime")[
              ["product", "group", "rs5_tight_regime", "rs5_wide_regime", "spread_med"]
          ].head(15).to_markdown(index=False) + "\n",
    ]
    (OUT / "decision.md").write_text("".join(md))
    append_log("PhaseD DONE")
    print("Phase D done.")


if __name__ == "__main__":
    main()
