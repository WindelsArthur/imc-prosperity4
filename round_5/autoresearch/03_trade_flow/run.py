"""Phase 3 — Trade flow. Counterparties were stripped (see Phase 0), so this
phase concentrates on aggregate flow:
- Volume profile per product (count, total qty, mean size, time clustering).
- Lee-Ready / quote-based trade-side classification, signed-flow IC vs forward
  mid moves at horizons 1, 5, 20.
- Trade clustering (autocorr of inter-arrival times).
- Trade-vs-book diagnostics: trade-at-bid vs trade-at-ask vs in-between fraction.

Outputs
    03_trade_flow/trade_summary.csv
    03_trade_flow/bot_candidates.md  (cannot identify per-counterparty bots —
                                       documents the data limitation and
                                       reports per-product anomalies instead)
"""
from __future__ import annotations

import sys
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from utils.data_loader import load_prices, load_trades, available_days
from utils.round5_products import ROUND5_PRODUCTS, group_of

warnings.filterwarnings("ignore")
OUT = Path(__file__).resolve().parent
LOG = ROOT / "logs" / "progress.md"


def append_log(msg: str) -> None:
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    with LOG.open("a") as f:
        f.write(f"- [{ts}] {msg}\n")


def lee_ready_classify(trade_price: float, mid: float, prev_mid: float, bid: float, ask: float) -> int:
    """Returns +1 (buy), -1 (sell), 0 (unclassified)."""
    if pd.isna(trade_price) or pd.isna(mid):
        return 0
    if not pd.isna(bid) and trade_price >= ask:
        return 1
    if not pd.isna(ask) and trade_price <= bid:
        return -1
    if trade_price > mid:
        return 1
    if trade_price < mid:
        return -1
    # Tick rule fallback
    if not pd.isna(prev_mid):
        if mid > prev_mid:
            return 1
        if mid < prev_mid:
            return -1
    return 0


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
    append_log(f"Phase3 START — days={days}")
    prices_by_day = {d: load_prices(d) for d in days}
    trades_by_day = {d: load_trades(d) for d in days}

    rows = []
    for i, product in enumerate(ROUND5_PRODUCTS, start=1):
        # Trades for this product across days
        tr_parts = []
        pr_parts = []
        for d in sorted(days):
            tr = trades_by_day[d]
            tr_p = tr.loc[tr["symbol"] == product, ["timestamp", "price", "quantity"]].copy()
            tr_p["day"] = d
            tr_parts.append(tr_p)
            pr_p = prices_by_day[d].loc[prices_by_day[d]["product"] == product,
                                        ["day", "timestamp", "bid_price_1", "ask_price_1", "mid_price"]].copy()
            pr_parts.append(pr_p)
        trades = pd.concat(tr_parts, ignore_index=True).sort_values(["day", "timestamp"]).reset_index(drop=True)
        prices = pd.concat(pr_parts, ignore_index=True).sort_values(["day", "timestamp"]).reset_index(drop=True)

        n_trades = len(trades)
        if n_trades == 0:
            rows.append({"product": product, "group": group_of(product), "n_trades": 0})
            continue

        # Merge each trade with the latest book snapshot at or before its timestamp
        # We use a merge_asof per day to keep day boundaries clean.
        merged_parts = []
        for d in sorted(days):
            tr_d = trades[trades["day"] == d].copy()
            pr_d = prices[prices["day"] == d].copy()
            if tr_d.empty or pr_d.empty:
                continue
            tr_d = tr_d.sort_values("timestamp")
            pr_d = pr_d.sort_values("timestamp")
            merged = pd.merge_asof(tr_d, pr_d, on="timestamp", direction="backward")
            merged_parts.append(merged)
        if not merged_parts:
            continue
        merged = pd.concat(merged_parts, ignore_index=True)
        merged["prev_mid"] = merged.groupby("day_x")["mid_price"].shift(1)

        # Classify
        signs = []
        for tup in merged.itertuples(index=False):
            sgn = lee_ready_classify(tup.price, tup.mid_price, tup.prev_mid, tup.bid_price_1, tup.ask_price_1)
            signs.append(sgn)
        merged["sign"] = signs
        signed_qty = merged["sign"] * merged["quantity"].astype(float)

        # Trade location
        at_ask = ((merged["price"] >= merged["ask_price_1"]) & merged["ask_price_1"].notna()).mean()
        at_bid = ((merged["price"] <= merged["bid_price_1"]) & merged["bid_price_1"].notna()).mean()
        between = 1.0 - at_ask - at_bid

        # Aggregate signed flow into 100-tick bins (one bin = one snapshot timestamp)
        # Compute IC vs forward mid moves
        # Build per-snapshot signed flow over the stitched price series
        # Use day+timestamp key
        flow = merged.groupby(["day_x", "timestamp"], as_index=False).agg(
            signed_qty=("sign", lambda s: float((s.values * merged.loc[s.index, "quantity"]).sum())),
            n_trades=("sign", "size"),
        )

        # For IC, build aligned arrays: for each price snapshot row in `prices`, attach signed_qty
        # then compute forward mid changes.
        prices_full = prices.copy()
        prices_full["mid_price"] = prices_full["mid_price"].astype(float).ffill().bfill()
        prices_full["signed_qty"] = 0.0
        prices_full["n_trades_bin"] = 0
        idx = pd.MultiIndex.from_frame(prices_full[["day", "timestamp"]])
        flow.columns = ["day", "timestamp", "signed_qty", "n_trades"]
        flow_idx = pd.MultiIndex.from_frame(flow[["day", "timestamp"]])
        prices_full = prices_full.set_index(["day", "timestamp"])
        flow = flow.set_index(["day", "timestamp"])
        prices_full.loc[prices_full.index.intersection(flow.index), "signed_qty"] = flow["signed_qty"].reindex(
            prices_full.index.intersection(flow.index)
        )
        prices_full.loc[prices_full.index.intersection(flow.index), "n_trades_bin"] = flow["n_trades"].reindex(
            prices_full.index.intersection(flow.index)
        )
        prices_full = prices_full.reset_index().sort_values(["day", "timestamp"]).reset_index(drop=True)

        mid = prices_full["mid_price"].to_numpy()
        sq = prices_full["signed_qty"].to_numpy()

        fr1 = np.concatenate([np.diff(mid), [np.nan]])
        fr5 = np.concatenate([mid[5:] - mid[:-5], [np.nan] * 5])
        fr20 = np.concatenate([mid[20:] - mid[:-20], [np.nan] * 20])

        ic_sq_h1 = spearman(sq, fr1)
        ic_sq_h5 = spearman(sq, fr5)
        ic_sq_h20 = spearman(sq, fr20)

        # Inter-arrival diagnostics
        ts = trades["timestamp"].astype(float).to_numpy()
        if len(ts) > 1:
            # Per-day inter-arrival
            inter = []
            for d in sorted(days):
                tts = trades.loc[trades["day"] == d, "timestamp"].to_numpy().astype(float)
                if len(tts) > 1:
                    inter.append(np.diff(tts))
            inter = np.concatenate(inter) if inter else np.array([])
            mean_iat = float(np.mean(inter)) if inter.size else float("nan")
            cv_iat = float(np.std(inter) / np.mean(inter)) if inter.size and np.mean(inter) > 0 else float("nan")
        else:
            mean_iat = float("nan"); cv_iat = float("nan")

        rows.append({
            "product": product,
            "group": group_of(product),
            "n_trades": n_trades,
            "tot_qty": int(trades["quantity"].sum()),
            "mean_qty": float(trades["quantity"].mean()),
            "median_qty": float(trades["quantity"].median()),
            "frac_at_ask": float(at_ask),
            "frac_at_bid": float(at_bid),
            "frac_between": float(between),
            "ic_signed_flow_h1": ic_sq_h1,
            "ic_signed_flow_h5": ic_sq_h5,
            "ic_signed_flow_h20": ic_sq_h20,
            "mean_iat_ticks": mean_iat,
            "cv_iat": cv_iat,
        })

        if i % 10 == 0 or i == len(ROUND5_PRODUCTS):
            print(f"[{i}/{len(ROUND5_PRODUCTS)}] {product}  n_trades={n_trades}")

    df = pd.DataFrame(rows)
    df.to_csv(OUT / "trade_summary.csv", index=False)

    md = []
    md.append("# Phase 3 — Trade Flow & Bot Candidates\n\n")
    md.append("## Data limitation\n\n")
    md.append("Round-5 trade rows have **empty buyer/seller fields for all 3 days**, so per-counterparty\n")
    md.append("profiling and bot-fingerprinting are impossible. Phase 3 instead focuses on aggregate\n")
    md.append("signed flow (Lee-Ready), trade location, and inter-arrival statistics.\n\n")
    md.append("## Top |IC(signed_flow, forward mid)| at h=5\n\n")
    df["abs_ic"] = df["ic_signed_flow_h5"].abs()
    md.append(df.sort_values("abs_ic", ascending=False)[
        ["product", "group", "n_trades", "ic_signed_flow_h1", "ic_signed_flow_h5", "ic_signed_flow_h20", "frac_at_ask", "frac_at_bid"]
    ].head(15).to_markdown(index=False) + "\n")
    md.append("\n## Trade location asymmetry — products where flow is one-sided\n\n")
    df["asym"] = (df["frac_at_ask"] - df["frac_at_bid"]).abs()
    md.append(df.sort_values("asym", ascending=False)[
        ["product", "group", "n_trades", "frac_at_ask", "frac_at_bid", "frac_between", "asym"]
    ].head(15).to_markdown(index=False) + "\n")
    md.append("\n## Bursty trading (low CV inter-arrival → regular)\n\n")
    md.append(df.sort_values("cv_iat")[
        ["product", "group", "n_trades", "mean_iat_ticks", "cv_iat"]
    ].head(15).to_markdown(index=False) + "\n")

    (OUT / "bot_candidates.md").write_text("".join(md))
    append_log(f"Phase3 DONE — n products with trades={int((df['n_trades']>0).sum())}")
    print("Phase 3 done.")


if __name__ == "__main__":
    main()
