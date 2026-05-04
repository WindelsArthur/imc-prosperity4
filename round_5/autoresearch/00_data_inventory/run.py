"""Phase 0 — Data inventory.

Loads R5 prices/trades for days 2,3,4. Confirms schema, row counts, NaN map,
gap detection, tick spacing, distinct counterparties.

Outputs
    inventory.md
    sanity_checks.csv
    counterparties.csv
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from utils.data_loader import load_prices, load_trades, available_days
from utils.round5_products import ROUND5_PRODUCTS, ROUND5_GROUPS

OUT = Path(__file__).resolve().parent
LOG = ROOT / "logs" / "progress.md"


def append_log(msg: str) -> None:
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a") as f:
        f.write(f"- [{ts}] {msg}\n")


def main() -> None:
    days = available_days()
    append_log(f"Phase0 START — days available: {days}")

    rows_summary = []
    nan_summary = []
    counterparties: set[str] = set()
    cp_per_product: dict[str, set[str]] = {p: set() for p in ROUND5_PRODUCTS}
    trade_volume_per_cp: dict[str, int] = {}

    expected_products = set(ROUND5_PRODUCTS)

    for d in days:
        prices = load_prices(d)
        trades = load_trades(d)

        # Schema sanity
        price_products = set(prices["product"].unique())
        missing_in_prices = expected_products - price_products
        extra_in_prices = price_products - expected_products

        per_p_rows = prices.groupby("product").size()
        for p, n in per_p_rows.items():
            ts_min = int(prices.loc[prices["product"] == p, "timestamp"].min())
            ts_max = int(prices.loc[prices["product"] == p, "timestamp"].max())
            uniq_ts = int(prices.loc[prices["product"] == p, "timestamp"].nunique())
            rows_summary.append({
                "day": d, "product": p, "n_rows": int(n),
                "ts_min": ts_min, "ts_max": ts_max,
                "n_unique_ts": uniq_ts,
            })

        # NaN map per product (price columns only)
        price_cols = [c for c in prices.columns if c not in ("day", "timestamp", "product")]
        for p, df_p in prices.groupby("product"):
            for c in price_cols:
                n_nan = int(df_p[c].isna().sum())
                if n_nan:
                    nan_summary.append({"day": d, "product": p, "column": c, "n_nan": n_nan})

        # Trades counterparties
        for col in ("buyer", "seller"):
            vals = trades[col].dropna().astype(str)
            for v in vals.unique():
                if v == "" or v == "nan":
                    continue
                counterparties.add(v)
        for _, row in trades.iterrows():
            sym = str(row["symbol"])
            for col in ("buyer", "seller"):
                v = row[col]
                if pd.isna(v):
                    continue
                v = str(v)
                if v == "" or v == "nan":
                    continue
                if sym in cp_per_product:
                    cp_per_product[sym].add(v)
                trade_volume_per_cp[v] = trade_volume_per_cp.get(v, 0) + int(row["quantity"])

        append_log(
            f"Phase0 day={d} prices_rows={len(prices)} trades_rows={len(trades)} "
            f"missing_in_prices={sorted(missing_in_prices)} extras={sorted(extra_in_prices)}"
        )

    sanity = pd.DataFrame(rows_summary).sort_values(["day", "product"])
    sanity.to_csv(OUT / "sanity_checks.csv", index=False)

    nan_df = pd.DataFrame(nan_summary)
    nan_df.to_csv(OUT / "nan_map.csv", index=False)

    cp_rows = []
    for cp in sorted(counterparties):
        n_products = sum(1 for prods in cp_per_product.values() if cp in prods)
        cp_rows.append({
            "counterparty": cp,
            "total_quantity": int(trade_volume_per_cp.get(cp, 0)),
            "n_products_touched": n_products,
        })
    if cp_rows:
        cp_df = pd.DataFrame(cp_rows).sort_values("total_quantity", ascending=False)
    else:
        cp_df = pd.DataFrame(columns=["counterparty", "total_quantity", "n_products_touched"])
    cp_df.to_csv(OUT / "counterparties.csv", index=False)

    # Inventory.md
    lines = []
    lines.append("# Phase 0 — Data Inventory\n")
    lines.append(f"Days available: {days}\n\n")
    lines.append("## Per-day summary\n")
    for d in days:
        prices = load_prices(d)
        trades = load_trades(d)
        per_p = prices.groupby("product").size()
        lines.append(f"### Day {d}\n")
        lines.append(f"- prices rows: {len(prices):,}  trades rows: {len(trades):,}\n")
        lines.append(f"- distinct products in prices: {prices['product'].nunique()}\n")
        lines.append(f"- distinct symbols in trades: {trades['symbol'].nunique()}\n")
        lines.append(f"- timestamp range prices: {int(prices['timestamp'].min())}..{int(prices['timestamp'].max())}\n")
        lines.append(f"- per-product row counts min/max/median: {per_p.min()}/{per_p.max()}/{int(per_p.median())}\n")
        # Tick spacing
        ts0 = prices.loc[prices["product"] == ROUND5_PRODUCTS[0], "timestamp"].sort_values()
        diffs = ts0.diff().dropna().value_counts().head(3).to_dict()
        lines.append(f"- top tick spacings (product 0): {diffs}\n")
        lines.append("")
    lines.append("\n## Group taxonomy\n")
    for g, prods in ROUND5_GROUPS.items():
        lines.append(f"- **{g}**: {', '.join(prods)}\n")
    lines.append("\n## Counterparties\n")
    lines.append(f"Total distinct counterparties: {len(counterparties)}\n\n")
    if len(counterparties) == 0:
        lines.append(
            "**CRITICAL FINDING — buyer/seller fields are empty in every trade row across all 3 days.**\n"
            "Round 5 strips counterparty IDs (contradicting the assumption noted in the prompt).\n"
            "Phase 3 bot-detection cannot be done at the counterparty level. Lee-Ready signed-flow\n"
            "classification on aggregate trades is still feasible.\n\n"
        )
    else:
        lines.append("Top 20 by total trade quantity (across products & days):\n\n")
        lines.append(cp_df.head(20).to_markdown(index=False) + "\n")
    lines.append("\n## Notes\n")
    lines.append("- 50 expected products: {}\n".format(len(ROUND5_PRODUCTS)))
    lines.append("- Files: see sanity_checks.csv (per-day-product row coverage), counterparties.csv, nan_map.csv\n")

    (OUT / "inventory.md").write_text("".join(lines))

    append_log(
        f"Phase0 DONE — sanity rows={len(sanity)} cps={len(counterparties)} nan_entries={len(nan_df)}"
    )
    print("Phase 0 complete.")
    print(f"  sanity_checks.csv: {len(sanity)} rows")
    print(f"  counterparties.csv: {len(cp_df)} rows")
    print(f"  nan_map.csv: {len(nan_df)} rows")


if __name__ == "__main__":
    main()
