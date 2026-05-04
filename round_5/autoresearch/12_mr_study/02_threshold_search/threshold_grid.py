"""Phase 2 — threshold/rule grid search via fast in-process simulator.

For each (product, FV in top-K, rule, params):
  Walk-forward fold A: sigma fit on day-2, signal on day-3
  Walk-forward fold B: sigma fit on day-2+3, signal on day-4
  Record total_pnl day3, day4, avg daily, sharpe, n_trades, drawdown.

Grid: rule A (symmetric z) ∪ rule D (with stop) ∪ rule E (with time-stop) over
       sizings ∈ {fixed, linear@2, linear@3, step}.

Pre-screen: top-K FVs per product (default K=4). Output:
  grid_results.parquet (one row per (prod, fv, rule, params, fold))
  per_product/{p}/top20.csv
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
AUTORES = HERE.parents[1]
FV_DIR = HERE.parent / "01_fair_value_zoo"
sys.path.insert(0, str(AUTORES))
sys.path.insert(0, str(FV_DIR))
sys.path.insert(0, str(HERE))

from utils.data_loader import load_prices  # noqa: E402
from utils.round5_products import ROUND5_PRODUCTS  # noqa: E402
from fair_values import catalog, compute_fv  # noqa: E402
from simulator import Cfg, run_grid  # noqa: E402

DAYS = [2, 3, 4]
TRAIN_END_FOLD_A = 10_000   # day2
TRAIN_END_FOLD_B = 20_000   # day2 + day3
TEST_RANGES = {"A": (10_000, 20_000), "B": (20_000, 30_000)}
N_TOP_FV = 4

Z_IN_GRID = [0.5, 0.8, 1.0, 1.25, 1.5, 1.75, 2.0, 2.5]
Z_OUT_GRID = [0.0, 0.1, 0.25, 0.5]
Z_STOP_GRID = [None]            # refined in Phase 4
TIME_STOP_GRID = [None]          # refined in Phase 4
SIZING_GRID = [
    ("fixed", {}),
    ("linear", {"sizing_gamma": 3.0}),
    ("step", {}),
]


def load_arrays(prod: str):
    frames = []
    for d in DAYS:
        df = load_prices(d)
        sub = df[df["product"] == prod].sort_values(["day", "timestamp"])
        frames.append(sub)
    big = pd.concat(frames, ignore_index=True)
    mid = big["mid_price"].astype(float).to_numpy()
    mid_filler = pd.Series(mid)
    arrs = {
        "mid": mid,
        "bid": big["bid_price_1"].astype(float).fillna(mid_filler).to_numpy(),
        "ask": big["ask_price_1"].astype(float).fillna(mid_filler).to_numpy(),
        "bv": big["bid_volume_1"].astype(float).fillna(0).to_numpy(),
        "av": big["ask_volume_1"].astype(float).fillna(0).to_numpy(),
        "bid2": big["bid_price_2"].astype(float).fillna(np.nan).to_numpy(),
        "ask2": big["ask_price_2"].astype(float).fillna(np.nan).to_numpy(),
        "bv2": big["bid_volume_2"].astype(float).fillna(0).to_numpy(),
        "av2": big["ask_volume_2"].astype(float).fillna(0).to_numpy(),
        "bid3": big["bid_price_3"].astype(float).fillna(np.nan).to_numpy(),
        "ask3": big["ask_price_3"].astype(float).fillna(np.nan).to_numpy(),
        "bv3": big["bid_volume_3"].astype(float).fillna(0).to_numpy(),
        "av3": big["ask_volume_3"].astype(float).fillna(0).to_numpy(),
    }
    return arrs


def grid_for_product(prod: str, top_fv_ids: List[str], cat_index: Dict[str, dict]) -> List[Dict]:
    arrs = load_arrays(prod)
    mid = arrs["mid"]
    rows: List[Dict] = []
    # compute FVs once for fold A and fold B (since some recalibrate)
    for fv_id in top_fv_ids:
        item = cat_index[fv_id]
        fv_per_fold = {}
        for fold, te in (("A", TRAIN_END_FOLD_A), ("B", TRAIN_END_FOLD_B)):
            try:
                fv_per_fold[fold] = compute_fv(
                    fv_id, item["family"], item["params"],
                    mid=mid, bid=arrs["bid"], ask=arrs["ask"],
                    bv=arrs["bv"], av=arrs["av"], train_end=te,
                )
            except Exception as e:
                fv_per_fold[fold] = np.full_like(mid, np.nan)
        # sigma per fold = std of residual on train slice
        sigma_per_fold = {}
        for fold, te in (("A", TRAIN_END_FOLD_A), ("B", TRAIN_END_FOLD_B)):
            res_train = (mid - fv_per_fold[fold])[:te]
            res_train = res_train[np.isfinite(res_train)]
            if len(res_train) >= 100:
                s = float(np.std(res_train))
                if s <= 0:
                    s = 1.0
            else:
                s = 1.0
            sigma_per_fold[fold] = s
        # build the cfg grid (Rule A only — D/E/B refined in later phases)
        cfgs: List[Cfg] = []
        cfg_meta: List[dict] = []
        for zi in Z_IN_GRID:
            for zo in Z_OUT_GRID:
                if zo >= zi:
                    continue
                for sname, sk in SIZING_GRID:
                    sg = float(sk.get("sizing_gamma", 0.0))
                    cfgs.append(Cfg(
                        z_in=float(zi), z_out=float(zo), sizing=sname,
                        sizing_gamma=sg,
                    ))
                    cfg_meta.append({"z_in": zi, "z_out": zo,
                                     "sizing": sname, "sizing_gamma": sg})

        for fold in ("A", "B"):
            lo, hi = TEST_RANGES[fold]
            fv = fv_per_fold[fold]
            s = sigma_per_fold[fold]
            slc = slice(lo, hi)
            if not np.any(np.isfinite(fv[slc])):
                continue
            sigma_arr = np.full(hi - lo, s)
            results = run_grid(
                mid=mid[slc], fv=fv[slc], sigma=sigma_arr,
                bp1=arrs["bid"][slc], ap1=arrs["ask"][slc],
                bv1=arrs["bv"][slc], av1=arrs["av"][slc],
                bp2=arrs["bid2"][slc], ap2=arrs["ask2"][slc],
                bv2=arrs["bv2"][slc], av2=arrs["av2"][slc],
                bp3=arrs["bid3"][slc], ap3=arrs["ask3"][slc],
                bv3=arrs["bv3"][slc], av3=arrs["av3"][slc],
                cfgs=cfgs,
            )
            for cm, rec in zip(cfg_meta, results):
                rows.append({
                    "product": prod, "fv_id": fv_id, "rule": "A",
                    "z_in": cm["z_in"], "z_out": cm["z_out"],
                    "z_stop": -1.0, "time_stop": -1,
                    "sizing": cm["sizing"], "sizing_gamma": cm["sizing_gamma"],
                    "fold": fold, "sigma": s,
                    "total_pnl": float(rec["total_pnl"]),
                    "n_trades": int(rec["n_trades"]),
                    "gross_volume": int(rec["gross"]),
                    "max_dd": float(rec["max_dd"]),
                    "sharpe": float(rec["sharpe"]),
                    "final_pos": int(rec["final_pos"]),
                })
    return rows


def run() -> None:
    cat_items = catalog()
    cat_index = {it["fv_id"]: it for it in cat_items}
    shortlist = pd.read_csv(FV_DIR / "fv_shortlist.csv")
    rows_all: List[Dict] = []
    t_start = time.time()
    for i_prod, prod in enumerate(ROUND5_PRODUCTS):
        sub = shortlist[shortlist["product"] == prod].sort_values("rank")
        top_fv_ids = sub.head(N_TOP_FV)["fv_id"].tolist()
        if not top_fv_ids:
            continue
        t0 = time.time()
        rows = grid_for_product(prod, top_fv_ids, cat_index)
        elapsed = time.time() - t0
        print(f"[{i_prod+1}/50] {prod}: {len(rows)} rows in {elapsed:.1f}s "
              f"(top FVs={top_fv_ids})")
        rows_all.extend(rows)

    df = pd.DataFrame(rows_all)
    df.to_parquet(HERE / "grid_results.parquet", index=False)
    # per-product top-20 by walk-forward avg daily PnL
    pivot = (df.groupby(["product", "fv_id", "rule", "z_in", "z_out", "z_stop",
                         "time_stop", "sizing", "sizing_gamma"])
               .agg(pnl_A=("total_pnl", lambda s: s[df.loc[s.index, "fold"] == "A"].sum() if (df.loc[s.index, "fold"] == "A").any() else np.nan),
                    pnl_B=("total_pnl", lambda s: s[df.loc[s.index, "fold"] == "B"].sum() if (df.loc[s.index, "fold"] == "B").any() else np.nan),
                    sharpe_A=("sharpe", lambda s: s[df.loc[s.index, "fold"] == "A"].mean()),
                    sharpe_B=("sharpe", lambda s: s[df.loc[s.index, "fold"] == "B"].mean()),
                    nt_A=("n_trades", lambda s: s[df.loc[s.index, "fold"] == "A"].sum()),
                    nt_B=("n_trades", lambda s: s[df.loc[s.index, "fold"] == "B"].sum()),
                    dd_A=("max_dd", lambda s: s[df.loc[s.index, "fold"] == "A"].max()),
                    dd_B=("max_dd", lambda s: s[df.loc[s.index, "fold"] == "B"].max()),
                    )
               .reset_index())
    pivot["avg_daily_pnl"] = (pivot["pnl_A"] + pivot["pnl_B"]) / 2.0
    pivot["min_pnl"] = pivot[["pnl_A", "pnl_B"]].min(axis=1)
    pivot["min_sharpe"] = pivot[["sharpe_A", "sharpe_B"]].min(axis=1)
    pivot.to_parquet(HERE / "grid_pivot.parquet", index=False)
    # per-product top-20 by avg_daily_pnl, with min_pnl > -2000 sanity floor
    for prod in ROUND5_PRODUCTS:
        sub = pivot[pivot["product"] == prod].copy()
        if sub.empty:
            continue
        sub = sub.sort_values("avg_daily_pnl", ascending=False).head(20)
        prod_dir = HERE / "per_product" / prod
        prod_dir.mkdir(parents=True, exist_ok=True)
        sub.to_csv(prod_dir / "top20.csv", index=False)
    print(f"\nTOTAL: {len(df)} rows across all configs in {time.time() - t_start:.1f}s")
    # leaderboard preview
    best_per_prod = (pivot.sort_values(["product", "avg_daily_pnl"], ascending=[True, False])
                          .groupby("product").head(1).sort_values("avg_daily_pnl", ascending=False))
    print("\nTop 15 products by best avg_daily_pnl (in-process sim):")
    print(best_per_prod[["product", "fv_id", "z_in", "z_out", "sizing",
                         "pnl_A", "pnl_B", "avg_daily_pnl", "min_sharpe"]].head(15).to_string(index=False))


if __name__ == "__main__":
    run()
