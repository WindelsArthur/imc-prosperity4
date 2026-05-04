"""Phase B — Bleeder forensics.

For each bleeder we cannot easily replay v1 fills, so we approximate the
strategy's behaviour from the order book + price series and decompose:

- Trend exposure: sign of mid-drift over rolling 200-tick windows.  When
  v1 quotes inside-spread MM, it gets adversely selected on trends; we
  measure how much of the bleeder's daily move is unidirectional vs
  oscillatory.
- Spread-vs-volatility ratio:  if sigma(mid) over 100 ticks > spread,
  MM loses to informed flow.
- Per-day-of-data trend.  Helps pick "idle vs MM-only vs hedge".

The output is a recipe per product (idle / cap=N / wider-spread-filter /
asymmetric-skew) used by the v2 strategy in Phase K.
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

warnings.filterwarnings("ignore")
OUT = Path(__file__).resolve().parent
LOG = ROOT / "logs" / "progress.md"

BLEEDERS = [
    "SLEEP_POD_LAMB_WOOL", "UV_VISOR_MAGENTA", "PANEL_1X2", "TRANSLATOR_SPACE_GRAY",
    "PEBBLES_M", "PEBBLES_L", "SNACKPACK_RASPBERRY", "SNACKPACK_CHOCOLATE",
    "ROBOT_MOPPING", "PANEL_4X4", "GALAXY_SOUNDS_SOLAR_FLAMES",
]


def append_log(msg: str) -> None:
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    with LOG.open("a") as f:
        f.write(f"- [{ts}] {msg}\n")


def main() -> None:
    days = available_days()
    print("Phase B start. Days:", days)
    prices_by_day = {d: load_prices(d) for d in days}

    rows = []
    for prod in BLEEDERS:
        for d in days:
            df = prices_by_day[d]
            sub = df.loc[df["product"] == prod].copy()
            if sub.empty:
                continue
            sub = sub.sort_values("timestamp").reset_index(drop=True)
            mid = sub["mid_price"].astype(float).ffill().bfill().to_numpy()
            spread = (sub["ask_price_1"] - sub["bid_price_1"]).astype(float).ffill().bfill().to_numpy()

            # Daily trend: end - start
            day_drift = float(mid[-1] - mid[0])
            day_drift_pct = day_drift / mid[0] * 100

            # Volatility per 100-tick window
            n = len(mid)
            if n < 200:
                continue
            rolls = pd.Series(mid).rolling(100).std().to_numpy()
            mean_vol = float(np.nanmean(rolls))
            mean_spread = float(np.nanmean(spread))
            spread_vol_ratio = mean_spread / max(mean_vol, 1e-6)

            # Trend dominance: |sum(returns)| / sum(|returns|)
            rets = np.diff(mid)
            trend_dom = abs(rets.sum()) / max(np.abs(rets).sum(), 1)

            # Largest 100-tick directional swing
            max_swing = float(np.max(mid[100:] - mid[:-100]))
            min_swing = float(np.min(mid[100:] - mid[:-100]))

            rows.append({
                "product": prod, "day": d, "n_ticks": n,
                "day_drift": day_drift, "day_drift_pct": day_drift_pct,
                "mean_vol_100": mean_vol, "mean_spread": mean_spread,
                "spread_to_vol": spread_vol_ratio,
                "trend_dominance": trend_dom,
                "max_up_swing_100": max_swing, "max_dn_swing_100": min_swing,
            })

    df = pd.DataFrame(rows)
    df.to_csv(OUT / "forensics.csv", index=False)

    # Aggregate per product
    summary = df.groupby("product").agg(
        avg_drift=("day_drift", "mean"),
        max_abs_drift=("day_drift", lambda s: float(s.abs().max())),
        avg_vol=("mean_vol_100", "mean"),
        avg_spread=("mean_spread", "mean"),
        avg_spread_to_vol=("spread_to_vol", "mean"),
        avg_trend_dom=("trend_dominance", "mean"),
    ).reset_index()
    summary.to_csv(OUT / "forensics_summary.csv", index=False)

    # Recipe assignment
    recipe_rows = []
    for _, r in summary.iterrows():
        prod = r["product"]
        # Heuristic: high trend dominance + high vol relative to spread → adverse selection
        if r["avg_trend_dom"] > 0.10 and r["avg_spread_to_vol"] < 1.0:
            recipe = "idle"  # MM loses to trend
        elif r["avg_spread_to_vol"] < 0.6:
            recipe = "cap_3"  # cap position to ±3 to limit drift exposure
        elif r["avg_trend_dom"] > 0.05:
            recipe = "wider_spread_filter"
        else:
            recipe = "keep_v1"
        recipe_rows.append({"product": prod, "recipe": recipe,
                            "avg_trend_dom": float(r["avg_trend_dom"]),
                            "avg_spread_to_vol": float(r["avg_spread_to_vol"])})
    pd.DataFrame(recipe_rows).to_csv(OUT / "recipes.csv", index=False)

    md = ["# Phase B — Bleeder Forensics\n\n",
          "## Forensics summary\n\n",
          summary.to_markdown(index=False) + "\n\n",
          "## Recipes\n\n",
          pd.DataFrame(recipe_rows).to_markdown(index=False) + "\n\n",
          "## Interpretation\n",
          "- `avg_trend_dom`: ratio of net drift to total absolute movement. >0.1 = strong directional day.\n",
          "- `avg_spread_to_vol`: bid-ask spread ÷ rolling mid vol (100-tick). <1 means moves outpace spread → MM loses to informed flow.\n",
          "- `idle`: do not quote (set position cap = 0).\n",
          "- `cap_3`: cap position at ±3 to limit downside.\n",
          "- `wider_spread_filter`: only quote when spread ≥ 4.\n",
          "- `keep_v1`: leave behavior unchanged.\n",
    ]
    (OUT / "decision.md").write_text("".join(md))
    append_log("PhaseB DONE — bleeder recipes generated")
    print("Phase B done.")


if __name__ == "__main__":
    main()
