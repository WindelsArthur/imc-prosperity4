"""Phase 1 — Step 1a diagnostic for ROBOT_DISHES.

Outputs:
  - 01_diagnostic.md (human-readable summary)
  - ar1_coefs_dishes.csv (per-day AR(1) on Δmid)
  - dishes_spread_dist.csv (spread distribution per day)
"""
from __future__ import annotations

import csv
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

_PA = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_PA))
from _pa_lib import progress_log

OUT = _PA / "01_robot_dishes_specialised"
OUT.mkdir(exist_ok=True)
DATA = _PA.parent.parent / "Data"

PRODUCT = "ROBOT_DISHES"
DAYS = (2, 3, 4)


def load_prices_day(day: int) -> pd.DataFrame:
    fp = DATA / f"prices_round_5_day_{day}.csv"
    df = pd.read_csv(fp, sep=";")
    df = df[df["product"] == PRODUCT].copy()
    if df.empty:
        raise RuntimeError(f"No {PRODUCT} rows in {fp}")
    df["mid"] = (df["bid_price_1"] + df["ask_price_1"]) / 2.0
    df["spread"] = df["ask_price_1"] - df["bid_price_1"]
    df = df.sort_values("timestamp").reset_index(drop=True)
    return df


def fit_ar1(diffs: np.ndarray) -> dict:
    """φ from Δmid_t = c + φ Δmid_{t-1} + ε, plus residual stats."""
    x = diffs[:-1]
    y = diffs[1:]
    mask = ~(np.isnan(x) | np.isnan(y))
    x, y = x[mask], y[mask]
    n = len(x)
    if n < 30:
        return {"phi": None, "intercept": None, "n": n, "r2": None}
    phi, c = np.polyfit(x, y, 1)
    yhat = phi * x + c
    ss_res = np.sum((y - yhat) ** 2)
    ss_tot = np.sum((y - np.mean(y)) ** 2)
    r2 = 1 - ss_res / max(ss_tot, 1e-12)
    return {"phi": float(phi), "intercept": float(c), "n": int(n),
            "r2": float(r2), "var_dmid": float(np.var(diffs[~np.isnan(diffs)]))}


def main() -> int:
    progress_log("Phase 1 Step 1a — ROBOT_DISHES diagnostic")
    rows_ar1, rows_spread = [], []
    diffs_all = []

    for d in DAYS:
        df = load_prices_day(d)
        diffs = df["mid"].diff().to_numpy()
        ar1 = fit_ar1(diffs)
        rows_ar1.append({"day": d, **ar1})
        diffs_all.append(diffs[~np.isnan(diffs)])

        s = df["spread"].to_numpy()
        rows_spread.append({
            "day": d,
            "n": len(s),
            "mean": float(np.mean(s)),
            "median": float(np.median(s)),
            "p25": float(np.percentile(s, 25)),
            "p75": float(np.percentile(s, 75)),
            "p90": float(np.percentile(s, 90)),
            "max": float(np.max(s)),
            "frac_spread_1": float(np.mean(s == 1)),
            "frac_spread_le_2": float(np.mean(s <= 2)),
        })

    # Cross-day pooled AR(1) (3-day stitched, with NaN at boundaries)
    pooled_diffs = np.concatenate(diffs_all)
    ar1_pool = fit_ar1(pooled_diffs)
    rows_ar1.append({"day": "all_pooled", **ar1_pool})

    # Save CSVs
    with (OUT / "ar1_coefs_dishes.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows_ar1[0].keys()))
        w.writeheader()
        for r in rows_ar1:
            w.writerow(r)

    with (OUT / "dishes_spread_dist.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows_spread[0].keys()))
        w.writeheader()
        for r in rows_spread:
            w.writerow(r)

    # Pull baseline ROBOT_DISHES per-day PnL from Phase 0
    base = json.loads((_PA / "00_baseline_lock" / "baseline.json").read_text())
    dishes_per_day = {d: base["per_day_per_product"][str(d)].get(PRODUCT, 0)
                      for d in DAYS}
    folds = base["fold_pnls"]  # totals — for per-fold dishes contribution we need test-day dishes pnl

    fold_dishes = {
        "F1": dishes_per_day[3],
        "F2": dishes_per_day[4],
        "F3": dishes_per_day[3],
        "F4": dishes_per_day[2],
        "F5": dishes_per_day[3],
    }

    # Existing pairs touching ROBOT_DISHES (from algo1_drop_harmful_only.py)
    # We grep'd: all 4 PEBBLES_XL→ROBOT_DISHES with slope ~2.56-2.58, intercept ~-12,400 to -12,600
    existing_pairs_dishes = [
        ("PEBBLES_XL", "ROBOT_DISHES", 2.564397695004785, -12461.145043672),
        ("PEBBLES_XL", "ROBOT_DISHES", 2.580310373321849, -12603.173905101849),
        ("PEBBLES_XL", "ROBOT_DISHES", 2.56069672636587,  -12428.06846030326),
        ("PEBBLES_XL", "ROBOT_DISHES", 2.5614599343393354, -12434.873479647302),
    ]

    # Phase-6 log-study novel ROBOT_DISHES pairs (from ship_list_dedup.csv)
    log_pairs_dishes = [
        ("PEBBLES_S",                "ROBOT_DISHES",    -1.424539615179072,  22.21380995919832),
        ("ROBOT_DISHES",             "PANEL_2X4",        0.7852940330682344,  1.885458055632914),
        ("GALAXY_SOUNDS_BLACK_HOLES","ROBOT_DISHES",     1.234892829761178,  -2.0303511860381143),
        ("ROBOT_DISHES",             "SNACKPACK_STRAWBERRY", 1.2191408531743275, -2.100596770515793),
    ]
    # Phase 6 isolated PnL of these 4 pairs (5-fold sum, from ship_list_dedup.csv)
    log_pairs_isolated_pnl = {
        ("PEBBLES_S","ROBOT_DISHES"): 18991.5,
        ("ROBOT_DISHES","PANEL_2X4"): 17304.0,
        ("GALAXY_SOUNDS_BLACK_HOLES","ROBOT_DISHES"): 13529.5,
        ("ROBOT_DISHES","SNACKPACK_STRAWBERRY"): 12158.0,
    }

    # Save log-pairs and existing-pairs as JSON for downstream phases
    with (OUT / "dishes_pairs_meta.json").open("w") as f:
        json.dump({
            "existing_global_pairs_touching_dishes": existing_pairs_dishes,
            "log_pairs_for_dedicated_handler": log_pairs_dishes,
            "log_pairs_isolated_pnl_5fold": {f"{a}|{b}": v
                for (a, b), v in log_pairs_isolated_pnl.items()},
            "baseline_dishes_per_day": dishes_per_day,
            "baseline_dishes_per_fold": fold_dishes,
        }, f, indent=2)

    # Markdown summary
    md = []
    md.append("# Phase 1 Step 1a — ROBOT_DISHES diagnostic\n")
    md.append("Baseline: `algo1_drop_harmful_only.py` (audit's runner-up). "
              "All numbers below are from the locked baseline run.\n")
    md.append("\n## Per-day ROBOT_DISHES PnL on baseline\n")
    md.append("| day | dishes_pnl |\n|---|---|")
    for d in DAYS:
        md.append(f"| {d} | {dishes_per_day[d]:,} |")
    md.append(f"\n3-day total: **{sum(dishes_per_day.values()):,}**\n")

    md.append("## Per-fold ROBOT_DISHES contribution (test-day)\n")
    md.append("| fold | dishes_pnl |\n|---|---|")
    for f, v in fold_dishes.items():
        md.append(f"| {f} | {v:,} |")
    md.append(f"\nfold_min(dishes) = **{min(fold_dishes.values()):,}**\n")

    md.append("## AR(1) on Δmid per day\n")
    md.append("| day | n | φ | intercept | R² | var(Δmid) |\n|---|---|---|---|---|---|")
    for r in rows_ar1:
        phi = f"{r['phi']:.4f}" if r['phi'] is not None else "–"
        ic  = f"{r['intercept']:.4f}" if r['intercept'] is not None else "–"
        r2  = f"{r['r2']:.4f}" if r['r2'] is not None else "–"
        v   = f"{r['var_dmid']:.4f}" if r.get('var_dmid') is not None else "–"
        md.append(f"| {r['day']} | {r['n']} | {phi} | {ic} | {r2} | {v} |")

    md.append("\n## Spread distribution per day\n")
    md.append("| day | n | mean | median | p25 | p75 | p90 | max | %=1 | %≤2 |\n"
              "|---|---|---|---|---|---|---|---|---|---|")
    for r in rows_spread:
        md.append(f"| {r['day']} | {r['n']} | {r['mean']:.3f} | "
                  f"{r['median']:.1f} | {r['p25']:.1f} | {r['p75']:.1f} | "
                  f"{r['p90']:.1f} | {r['max']:.1f} | "
                  f"{r['frac_spread_1']*100:.1f}% | {r['frac_spread_le_2']*100:.1f}% |")

    md.append("\n## Existing pairs touching ROBOT_DISHES (in baseline ALL_PAIRS)\n")
    md.append("| a | b | slope | intercept |\n|---|---|---|---|")
    for a, b, s, ic in existing_pairs_dishes:
        md.append(f"| {a} | {b} | {s:.4f} | {ic:.2f} |")
    md.append("\nAll four are PEBBLES_XL→ROBOT_DISHES with very similar parameters "
              "(close to one calibration). They contribute additively to global "
              "`pair_skew` for ROBOT_DISHES via the chained `-slope*tilt/max(|slope|,1)` term.\n")

    md.append("## Phase-6 log-study novel ROBOT_DISHES pairs\n")
    md.append("Source: `log_study/06_oos_validation/ship_list_dedup.csv`. Isolated 5-fold sum PnL.\n")
    md.append("| pair | β | α | isolated_5fold_pnl |\n|---|---|---|---|")
    for (a, b, beta, alpha), pnl in zip(log_pairs_dishes, log_pairs_isolated_pnl.values()):
        md.append(f"| {a} – {b} | {beta:.4f} | {alpha:.4f} | {pnl:,.0f} |")
    md.append(f"\nSum of 4 isolated: **{sum(log_pairs_isolated_pnl.values()):,.0f}**.\n")

    (OUT / "01_diagnostic.md").write_text("\n".join(md))
    progress_log(f"Phase 1 Step 1a — diagnostic written: dishes baseline 3d={sum(dishes_per_day.values()):,}, "
                 f"AR1 pooled φ={ar1_pool['phi']:.4f}, log-pair isolated sum={sum(log_pairs_isolated_pnl.values()):,.0f}")
    print(open(OUT / "01_diagnostic.md").read())
    return 0


if __name__ == "__main__":
    sys.exit(main())
