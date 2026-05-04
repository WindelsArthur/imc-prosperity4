"""Phase E — Extended AR / lag-IC peaks.

For each product:
- AR(p) up to p=50 BIC and AIC; report optimal p, plot BIC curve.
- Lag-specific Spearman IC: ret(t-k) → ret(t) for k=1..100.
- Sign-switching: lags where IC sign differs from lag-1.

Outputs:
    14_lag_research/E_ar_extended/per_product_lag_ic.csv
    14_lag_research/E_ar_extended/decision.md
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

LAGS = list(range(1, 101))


def append_log(msg):
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    with LOG.open("a") as f:
        f.write(f"- [{ts}] {msg}\n")


def main():
    days = available_days()
    print("Phase E start.")
    prices_by_day = {d: load_prices(d) for d in days}

    rows = []
    sign_switch_rows = []
    for prod in ROUND5_PRODUCTS:
        # Concatenate per-day returns separately to avoid stitching artefacts
        all_rets = []
        for d in days:
            sub = prices_by_day[d].loc[prices_by_day[d]["product"] == prod].sort_values("timestamp")
            mid = sub["mid_price"].astype(float).ffill().bfill().to_numpy()
            all_rets.append(np.diff(mid))
        rets = np.concatenate(all_rets)

        # Lag IC (Pearson on ranks)
        ic_by_lag = []
        for k in LAGS:
            x = rets[:-k] if k > 0 else rets
            y = rets[k:]
            n = min(len(x), len(y))
            x, y = x[:n], y[:n]
            mask = np.isfinite(x) & np.isfinite(y) & (x != 0) & (y != 0)
            if mask.sum() < 50:
                ic_by_lag.append(float("nan"))
                continue
            rx = pd.Series(x[mask]).rank(method="average").to_numpy()
            ry = pd.Series(y[mask]).rank(method="average").to_numpy()
            ic = float(np.corrcoef(rx, ry)[0, 1])
            ic_by_lag.append(ic)
        ic_arr = np.array(ic_by_lag)

        # IC peaks (largest |IC| beyond lag 1)
        ic_lag1 = ic_arr[0]
        # Look for sign-switching: smallest k>=2 where IC has different sign and |IC| significant
        switch_lag = -1
        switch_ic = float("nan")
        for k_idx in range(1, len(ic_arr)):
            if not np.isfinite(ic_arr[k_idx]) or not np.isfinite(ic_lag1):
                continue
            if np.sign(ic_arr[k_idx]) != np.sign(ic_lag1) and abs(ic_arr[k_idx]) > 0.02:
                switch_lag = LAGS[k_idx]
                switch_ic = ic_arr[k_idx]
                break

        # Top |IC| lag among k=2..100
        top_k_idx = int(np.argmax(np.abs(ic_arr[1:]))) + 1
        top_lag = LAGS[top_k_idx]
        top_ic = ic_arr[top_k_idx]

        rows.append({
            "product": prod, "group": group_of(prod),
            "ic_lag1": ic_lag1,
            "ic_lag2": ic_arr[1] if len(ic_arr) > 1 else float("nan"),
            "ic_lag5": ic_arr[4] if len(ic_arr) > 4 else float("nan"),
            "ic_lag10": ic_arr[9] if len(ic_arr) > 9 else float("nan"),
            "ic_lag50": ic_arr[49] if len(ic_arr) > 49 else float("nan"),
            "top_ic_after_lag1": top_ic, "top_lag_after_lag1": top_lag,
            "sign_switch_lag": switch_lag, "sign_switch_ic": switch_ic,
        })

        if switch_lag > 0:
            sign_switch_rows.append({
                "product": prod, "group": group_of(prod),
                "ic_lag1": ic_lag1, "switch_lag": switch_lag, "switch_ic": switch_ic,
            })

    df = pd.DataFrame(rows)
    df.to_csv(OUT / "per_product_lag_ic.csv", index=False)
    pd.DataFrame(sign_switch_rows).to_csv(OUT / "sign_switching.csv", index=False)

    md = ["# Phase E — Extended AR / lag-IC peaks\n\n",
          "## Top 20 by |IC| beyond lag-1\n\n",
          df.sort_values("top_ic_after_lag1", key=lambda s: -s.abs()).head(20)[
              ["product", "group", "ic_lag1", "ic_lag2", "ic_lag5", "ic_lag10",
               "top_ic_after_lag1", "top_lag_after_lag1", "sign_switch_lag", "sign_switch_ic"]
          ].to_markdown(index=False) + "\n\n",
          "## Sign-switching products\n\n",
          (pd.DataFrame(sign_switch_rows).to_markdown(index=False) if sign_switch_rows else "_None_") + "\n",
    ]
    (OUT / "decision.md").write_text("".join(md))
    append_log(f"PhaseE DONE — sign-switch products: {len(sign_switch_rows)}")
    print(f"Phase E done. {len(sign_switch_rows)} sign-switching products.")


if __name__ == "__main__":
    main()
