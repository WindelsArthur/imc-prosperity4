"""Phase 8 — Signal engineering & walk-forward validation.

We focus on the strongest signals surfaced in Phases 1–7:
1. Pebbles basket residual:   resid_i = mid_i - (50000 - sum_others)  ≡  sum_all - 50000
2. Snackpack basket residual: resid_i = mid_i - (50221 - sum_others)
3. Pairwise cointegration spread reversion (best WF Sharpe pairs from Phase 5):
    - SNACKPACK_RASPBERRY/SNACKPACK_VANILLA
    - MICROCHIP_RECTANGLE/MICROCHIP_SQUARE
    - SLEEP_POD_COTTON/SLEEP_POD_POLYESTER
    - ROBOT_LAUNDRY/ROBOT_VACUUMING
    - GALAXY_DARK_MATTER/PLANETARY_RINGS
4. AR(1) reversion on ROBOT_DISHES, ROBOT_IRONING, OXYGEN_SHAKE_EVENING_BREATH,
   OXYGEN_SHAKE_CHOCOLATE.
5. Per-product L1-imbalance signal — IC was tiny (~0.05) — kept as MM tilt only.

Walk-forward protocol:
    Fold A: train day 2,         test day 3
    Fold B: train day 2 + 3,     test day 4

For each strategy we compute on the test fold:
    - per-tick PnL series
    - hit rate
    - Sharpe (× sqrt(10000))
    - total PnL

Outputs
    08_signals/walk_forward_results.csv
    08_signals/signals_surviving.csv
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

from utils.data_loader import load_prices, available_days
from utils.round5_products import ROUND5_PRODUCTS, ROUND5_GROUPS

warnings.filterwarnings("ignore")
OUT = Path(__file__).resolve().parent
LOG = ROOT / "logs" / "progress.md"


def stitch_pivot():
    days = available_days()
    parts = []
    for d in days:
        df = load_prices(d)
        sub = df.loc[df["product"].isin(ROUND5_PRODUCTS),
                     ["day", "timestamp", "product", "mid_price",
                      "bid_price_1", "ask_price_1"]].copy()
        sub["mid_price"] = sub["mid_price"].astype(float)
        parts.append(sub)
    full = pd.concat(parts, ignore_index=True).sort_values(["day", "timestamp", "product"])
    pivot = full.pivot_table(index=["day", "timestamp"], columns="product", values="mid_price")
    pivot = pivot[ROUND5_PRODUCTS].ffill().bfill()
    return pivot


def z_strategy_sim(spread: np.ndarray, mu: float, sd: float,
                   z_entry: float = 1.5, z_exit: float = 0.5) -> dict:
    """Simulate a z-score reversion on `spread` given calibrated mu, sd."""
    if sd <= 0:
        return {"sharpe": float("nan"), "n_trades": 0, "total_pnl": 0.0, "hit_rate": float("nan")}
    z = (spread - mu) / sd
    pos = np.zeros_like(spread, dtype=float)
    cur = 0.0
    n_trades = 0
    for k, zv in enumerate(z):
        if cur == 0.0:
            if zv > z_entry:
                cur = -1.0; n_trades += 1
            elif zv < -z_entry:
                cur = 1.0; n_trades += 1
        else:
            if abs(zv) < z_exit:
                cur = 0.0
            elif cur > 0 and zv > z_entry:
                cur = -1.0; n_trades += 1
            elif cur < 0 and zv < -z_entry:
                cur = 1.0; n_trades += 1
        pos[k] = cur
    pnl = pos[:-1] * np.diff(spread)
    if pnl.std() <= 0:
        return {"sharpe": float("nan"), "n_trades": int(n_trades), "total_pnl": float(pnl.sum()),
                "hit_rate": float("nan")}
    sharpe = float(pnl.mean() / pnl.std() * np.sqrt(10000))
    hit = float(np.mean(pnl > 0))
    return {"sharpe": sharpe, "n_trades": int(n_trades), "total_pnl": float(pnl.sum()), "hit_rate": hit}


def main() -> None:
    pivot = stitch_pivot()
    days_marker = pivot.index.get_level_values("day").to_numpy()
    print("days in pivot:", np.unique(days_marker))

    folds = [
        {"name": "fold_A", "train_days": [2], "test_day": 3},
        {"name": "fold_B", "train_days": [2, 3], "test_day": 4},
    ]

    rows = []

    # -------- 1. Pebbles basket residual: sum_all - 50000 ---------
    pebbles_prods = ROUND5_GROUPS["pebbles"]
    pebbles_sum = pivot[pebbles_prods].sum(axis=1).to_numpy()

    for fold in folds:
        train_mask = np.isin(days_marker, fold["train_days"])
        test_mask = days_marker == fold["test_day"]
        target = float(pebbles_sum[train_mask].mean())  # ≈ 50000
        sd = float(pebbles_sum[train_mask].std())
        s_test = pebbles_sum[test_mask]
        # Strategy: when residual > +entry*sd, short the basket (= -1 each pebble); else +1.
        # Trade per-pebble: PnL ~ -position * Δsum / 5
        z = (s_test - target) / max(sd, 1e-6)
        pos = np.zeros_like(s_test)
        cur = 0.0
        z_entry = 2.0; z_exit = 0.0
        n_trades = 0
        for k, zv in enumerate(z):
            if cur == 0.0:
                if zv > z_entry:
                    cur = -1.0; n_trades += 1
                elif zv < -z_entry:
                    cur = 1.0; n_trades += 1
            else:
                # exit when z crosses zero
                if cur > 0 and zv >= z_exit:
                    cur = 0.0
                elif cur < 0 and zv <= -z_exit:
                    cur = 0.0
            pos[k] = cur
        # pos=+1 long basket; long-basket profit = +Δsum. pos=-1 short basket; profit = -Δsum.
        # Generic: pnl = pos * Δsum.
        pnl = pos[:-1] * np.diff(s_test)
        sharpe = float(pnl.mean() / pnl.std() * np.sqrt(10000)) if pnl.std() > 0 else float("nan")
        rows.append({
            "signal": "pebbles_basket_residual", "fold": fold["name"],
            "n_trades": int(n_trades), "total_pnl": float(pnl.sum()),
            "sharpe": sharpe, "hit_rate": float(np.mean(pnl > 0)),
            "calib_mu": target, "calib_sd": sd,
        })

    # -------- 2. Snackpack basket residual ---------
    snack_prods = ROUND5_GROUPS["snackpack"]
    snack_sum = pivot[snack_prods].sum(axis=1).to_numpy()
    for fold in folds:
        train_mask = np.isin(days_marker, fold["train_days"])
        test_mask = days_marker == fold["test_day"]
        target = float(snack_sum[train_mask].mean())
        sd = float(snack_sum[train_mask].std())
        res = z_strategy_sim(snack_sum[test_mask] - target, mu=0.0, sd=sd, z_entry=1.5, z_exit=0.3)
        rows.append({"signal": "snackpack_basket_residual", "fold": fold["name"],
                     **res, "calib_mu": target, "calib_sd": sd})

    # -------- 3. Pair cointegration mean-reversion ---------
    pair_specs = [
        ("SNACKPACK_RASPBERRY", "SNACKPACK_VANILLA"),
        ("MICROCHIP_RECTANGLE", "MICROCHIP_SQUARE"),
        ("SLEEP_POD_COTTON", "SLEEP_POD_POLYESTER"),
        ("ROBOT_LAUNDRY", "ROBOT_VACUUMING"),
        ("GALAXY_SOUNDS_DARK_MATTER", "GALAXY_SOUNDS_PLANETARY_RINGS"),
        ("SNACKPACK_CHOCOLATE", "SNACKPACK_STRAWBERRY"),
        ("UV_VISOR_AMBER", "UV_VISOR_MAGENTA"),
        ("TRANSLATOR_ECLIPSE_CHARCOAL", "TRANSLATOR_VOID_BLUE"),
        ("SLEEP_POD_LAMB_WOOL", "SLEEP_POD_NYLON"),
        ("OXYGEN_SHAKE_CHOCOLATE", "OXYGEN_SHAKE_GARLIC"),
        ("MICROCHIP_OVAL", "MICROCHIP_TRIANGLE"),
        ("SLEEP_POD_POLYESTER", "SLEEP_POD_SUEDE"),
        ("PEBBLES_M", "PEBBLES_XS"),
        ("PEBBLES_S", "PEBBLES_XL"),
    ]
    for a, b in pair_specs:
        for fold in folds:
            train_mask = np.isin(days_marker, fold["train_days"])
            test_mask = days_marker == fold["test_day"]
            ya = pivot[a].to_numpy()
            yb = pivot[b].to_numpy()
            # OLS slope+intercept on training
            X = np.column_stack([np.ones(train_mask.sum()), yb[train_mask]])
            coef, *_ = np.linalg.lstsq(X, ya[train_mask], rcond=None)
            slope = float(coef[1]); intercept = float(coef[0])
            spread_train = ya[train_mask] - slope * yb[train_mask] - intercept
            mu_tr = float(np.mean(spread_train))
            sd_tr = float(np.std(spread_train))
            spread_test = ya[test_mask] - slope * yb[test_mask] - intercept
            res = z_strategy_sim(spread_test, mu=mu_tr, sd=sd_tr, z_entry=1.5, z_exit=0.3)
            rows.append({"signal": f"pair_{a}/{b}", "fold": fold["name"], **res,
                         "calib_mu": mu_tr, "calib_sd": sd_tr,
                         "slope": slope, "intercept": intercept})

    # -------- 4. AR(1) reversion at lag 1 on selected products ---------
    ar1_targets = ["ROBOT_DISHES", "ROBOT_IRONING",
                   "OXYGEN_SHAKE_EVENING_BREATH", "OXYGEN_SHAKE_CHOCOLATE"]
    for prod in ar1_targets:
        for fold in folds:
            train_mask = np.isin(days_marker, fold["train_days"])
            test_mask = days_marker == fold["test_day"]
            x_tr = pivot[prod].to_numpy()[train_mask]
            x_te = pivot[prod].to_numpy()[test_mask]
            r_tr = np.diff(x_tr)
            # AR(1): r_t = phi * r_{t-1} + eps
            r_lag = r_tr[:-1]; r_now = r_tr[1:]
            X = np.column_stack([np.ones_like(r_lag), r_lag])
            coef, *_ = np.linalg.lstsq(X, r_now, rcond=None)
            phi = float(coef[1])
            r_te = np.diff(x_te)
            # Predict r_te[t] = phi * r_te[t-1]; trade in opposite sign of prediction (mean-revert)
            pred = phi * r_te[:-1]
            # Bet in direction of the AR(1) prediction (already mean-reverting if phi<0):
            #   pred_t = phi * r_{t-1}; if pred>0 we expect price up next tick, so go long.
            pos = np.sign(pred)
            pnl = pos * r_te[1:]
            sharpe = float(pnl.mean() / pnl.std() * np.sqrt(10000)) if pnl.std() > 0 else float("nan")
            n_trades = int((np.diff(np.sign(pos)) != 0).sum())
            rows.append({"signal": f"ar1_{prod}", "fold": fold["name"],
                         "phi": phi, "n_trades": n_trades,
                         "total_pnl": float(pnl.sum()),
                         "sharpe": sharpe,
                         "hit_rate": float(np.mean(pnl > 0))})

    df = pd.DataFrame(rows)
    df.to_csv(OUT / "walk_forward_results.csv", index=False)

    # Aggregate per signal across folds — keep ones where MIN sharpe ≥ 0.5 across folds
    agg = df.groupby("signal").agg(
        min_sharpe=("sharpe", "min"),
        max_sharpe=("sharpe", "max"),
        mean_sharpe=("sharpe", "mean"),
        sum_pnl=("total_pnl", "sum"),
    ).reset_index().sort_values("min_sharpe", ascending=False)
    surv = agg[agg["min_sharpe"] >= 0.5]
    surv.to_csv(OUT / "signals_surviving.csv", index=False)
    agg.to_csv(OUT / "signals_aggregate.csv", index=False)

    print(df.to_string(index=False))
    print("\n=== Survivors (min Sharpe >= 0.5) ===")
    print(surv.to_string(index=False))


if __name__ == "__main__":
    main()
