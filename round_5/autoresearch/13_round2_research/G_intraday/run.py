"""Phase G — intraday seasonality.

For each product, bin timestamp%10000 into 100 bins; per bin compute mean
return and vol. F-test on whether bin means differ. Build OOS overlay:
fit on day 2, test on day 3 (and 2+3 → day 4) by predicting next-tick
mean return from the per-bin curve.
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


def append_log(msg):
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    with LOG.open("a") as f:
        f.write(f"- [{ts}] {msg}\n")


def main():
    days = available_days()
    print("Phase G start.")
    prices_by_day = {d: load_prices(d) for d in days}

    rows = []
    for prod in ROUND5_PRODUCTS:
        # Stitch per-day; bin timestamps into 100 bins
        per_day_curves = {}
        for d in days:
            df = prices_by_day[d]
            sub = df.loc[df["product"] == prod].sort_values("timestamp").reset_index(drop=True)
            mid = sub["mid_price"].astype(float).ffill().bfill().to_numpy()
            ts = sub["timestamp"].to_numpy()
            rets = np.diff(mid)
            # Bins for r_t correspond to bin of t_{t+1}
            bins = (ts[1:] // 10000).astype(int)
            cur = pd.DataFrame({"bin": bins, "ret": rets})
            curve = cur.groupby("bin").agg(mean_ret=("ret", "mean"),
                                            vol=("ret", "std"),
                                            n=("ret", "size")).reindex(range(100), fill_value=np.nan)
            per_day_curves[d] = curve

        # F-test per day: variance of bin-means ÷ pooled within-bin variance
        # Use day 2 as primary
        cur2 = per_day_curves[2]
        valid = cur2.dropna()
        if len(valid) < 5:
            continue
        between_ss = valid["mean_ret"].var() * len(valid)
        within_ss = (valid["vol"] ** 2 * valid["n"]).sum() / max(valid["n"].sum(), 1)
        f_stat = float(between_ss / max(within_ss, 1e-9))

        # OOS test: use day 2 curve to predict day 3 returns
        def oos_corr(train_d, test_d):
            tr = per_day_curves[train_d]["mean_ret"]
            te = per_day_curves[test_d]
            joined = te.join(tr.rename("predicted"), how="inner").dropna()
            if len(joined) < 8:
                return float("nan")
            return float(np.corrcoef(joined["predicted"], joined["mean_ret"])[0, 1])

        oos23 = oos_corr(2, 3)
        oos34 = oos_corr(3, 4)
        oos24 = oos_corr(2, 4)

        # Persistence across all 3 days: avg pairwise corr of curves
        ds = [d for d in days if d in per_day_curves]
        corr_pairs = []
        for i in range(len(ds)):
            for j in range(i + 1, len(ds)):
                a = per_day_curves[ds[i]]["mean_ret"]
                b = per_day_curves[ds[j]]["mean_ret"]
                joined = pd.concat([a.rename("a"), b.rename("b")], axis=1).dropna()
                if len(joined) > 8:
                    corr_pairs.append(float(np.corrcoef(joined["a"], joined["b"])[0, 1]))
        cross_day_avg_corr = float(np.mean(corr_pairs)) if corr_pairs else float("nan")

        rows.append({
            "product": prod, "group": group_of(prod),
            "f_stat": f_stat,
            "oos_corr_2to3": oos23, "oos_corr_2to4": oos24, "oos_corr_3to4": oos34,
            "cross_day_avg_corr": cross_day_avg_corr,
            "max_abs_mean_ret_d2": float(cur2["mean_ret"].abs().max()),
        })

    df = pd.DataFrame(rows)
    df.to_csv(OUT / "intraday_summary.csv", index=False)

    md = ["# Phase G — Intraday Seasonality\n\n",
          "## Most cross-day stable seasonality (avg pairwise corr of bin-mean curves)\n\n",
          df.sort_values("cross_day_avg_corr", ascending=False).head(15)[
              ["product", "group", "cross_day_avg_corr", "oos_corr_2to3", "oos_corr_3to4",
               "f_stat", "max_abs_mean_ret_d2"]
          ].to_markdown(index=False) + "\n\n",
          "## Decision rule\n",
          "- Adopt intraday overlay only for products with cross_day_avg_corr ≥ 0.30.\n",
          "- Apply as a small fair-value tilt: `fair += alpha * curve[bin]` with α=0.5.\n",
    ]
    (OUT / "decision.md").write_text("".join(md))
    append_log(f"PhaseG DONE — top corr products: {df.sort_values('cross_day_avg_corr',ascending=False).head(5)['product'].tolist()}")
    print("Phase G done.")


if __name__ == "__main__":
    main()
