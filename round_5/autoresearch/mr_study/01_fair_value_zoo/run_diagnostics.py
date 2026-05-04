"""Phase 1 — run all FV diagnostics for every product, walk-forward.

For each product we evaluate every FV on day-3 (test fold A) and day-4
(test fold B). Calibration-only data is restricted to indices < train_end:

  Fold A  :  train = day2,        test = day3
  Fold B  :  train = day2 + day3, test = day4

Per (product, FV, fold) we record:
  ic_spearman      Spearman IC of residual = (price - FV) vs forward-return -dmid(t+1)
  ic_pvalue        Spearman p-value
  half_life        OU half-life of residual on test fold (smaller = stronger MR)
  adf_p            ADF p of residual
  mean_abs_res     mean |residual| on test fold
  std_res          residual stdev
  spread_p50       median BBO spread on test fold
  res_to_spread    mean_abs_res / spread_p50 (smaller = tighter)

A composite score for pre-screening:
    score = z(|ic|) + z(-log10(half_life+1)) - z(res_to_spread)
Top-8 per product are kept; saved to fv_shortlist.csv.

Outputs
  fv_catalog.csv
  per_product/{product}/diagnostics.csv
  fv_shortlist.csv
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from statsmodels.tsa.stattools import adfuller

HERE = Path(__file__).resolve().parent
AUTORES = HERE.parents[1]
sys.path.insert(0, str(AUTORES))
sys.path.insert(0, str(HERE))

from utils.data_loader import load_prices  # noqa: E402
from utils.round5_products import ROUND5_PRODUCTS  # noqa: E402
from fair_values import catalog, compute_fv  # noqa: E402

DAYS = [2, 3, 4]
TRAIN_END_FOLD_A = 10_000  # day2 only
TRAIN_END_FOLD_B = 20_000  # day2 + day3
TEST_RANGES = {"A": (10_000, 20_000), "B": (20_000, 30_000)}


def safe_ou_half_life(x: np.ndarray) -> float:
    """Half-life of x via AR(1) on x: dx = a + b·x_lag → hl = -ln2/ln(1+b)."""
    a = x[np.isfinite(x)]
    if len(a) < 16:
        return float("inf")
    x_lag = a[:-1]
    dx = np.diff(a)
    X = np.column_stack([np.ones_like(x_lag), x_lag])
    try:
        coef, *_ = np.linalg.lstsq(X, dx, rcond=None)
    except np.linalg.LinAlgError:
        return float("inf")
    beta = float(coef[1])
    rho = 1.0 + beta
    if not (0.0 < rho < 1.0):
        return float("inf")
    return float(-np.log(2.0) / np.log(rho))


def safe_adf(x: np.ndarray) -> float:
    a = x[np.isfinite(x)]
    if len(a) < 32:
        return float("nan")
    try:
        return float(adfuller(a, regression="c", autolag="AIC")[1])
    except Exception:
        return float("nan")


def diagnose_one(mid: np.ndarray, fv: np.ndarray, lo: int, hi: int, spread_p50: float) -> Dict:
    """Compute residual diagnostics on slice [lo, hi)."""
    res_full = mid - fv
    res = res_full[lo:hi]
    fwd = -np.diff(mid[lo : hi + 1])  # forward 1-step price change negated for IC
    if len(fwd) != len(res):
        # boundary case — clip to common length
        n_ok = min(len(fwd), len(res))
        res, fwd = res[:n_ok], fwd[:n_ok]
    mask = np.isfinite(res) & np.isfinite(fwd)
    if mask.sum() < 32:
        return {"ic_spearman": np.nan, "ic_pvalue": np.nan, "half_life": np.inf,
                "adf_p": np.nan, "mean_abs_res": np.nan, "std_res": np.nan,
                "n_ok": int(mask.sum()), "res_to_spread": np.nan}
    ic, ic_p = spearmanr(res[mask], fwd[mask])
    hl = safe_ou_half_life(res[mask])
    adfp = safe_adf(res[mask])
    mar = float(np.mean(np.abs(res[mask])))
    sr = float(np.std(res[mask]))
    return {
        "ic_spearman": float(ic) if np.isfinite(ic) else np.nan,
        "ic_pvalue": float(ic_p) if np.isfinite(ic_p) else np.nan,
        "half_life": hl,
        "adf_p": adfp,
        "mean_abs_res": mar,
        "std_res": sr,
        "n_ok": int(mask.sum()),
        "res_to_spread": mar / spread_p50 if spread_p50 > 0 else np.nan,
    }


def load_product_arrays(prod: str):
    """Concat day 2/3/4 mid + bid/ask/bv/av arrays for a product."""
    frames = []
    for d in DAYS:
        df = load_prices(d)
        sub = df[df["product"] == prod].sort_values(["day", "timestamp"])
        frames.append(sub)
    big = pd.concat(frames, ignore_index=True)
    mid = big["mid_price"].astype(float).to_numpy()
    mid_filler = pd.Series(mid)
    bid = big["bid_price_1"].astype(float).fillna(mid_filler).to_numpy()
    ask = big["ask_price_1"].astype(float).fillna(mid_filler).to_numpy()
    bv = big["bid_volume_1"].astype(float).fillna(0).to_numpy()
    av = big["ask_volume_1"].astype(float).fillna(0).to_numpy()
    spread = (ask - bid)
    spread_p50_d3 = float(np.nanmedian(spread[10_000:20_000]))
    spread_p50_d4 = float(np.nanmedian(spread[20_000:30_000]))
    return mid, bid, ask, bv, av, spread_p50_d3, spread_p50_d4


def run() -> None:
    cat_items = catalog()
    # write catalog once
    cat_df = pd.DataFrame([
        {"fv_id": it["fv_id"], "family": it["family"], "params": json.dumps(it["params"])}
        for it in cat_items
    ])
    cat_df.to_csv(HERE / "fv_catalog.csv", index=False)
    print(f"wrote fv_catalog.csv ({len(cat_df)} rows)")

    all_diag_rows: List[Dict] = []
    shortlist_rows: List[Dict] = []
    t_total = time.time()
    for i_prod, prod in enumerate(ROUND5_PRODUCTS):
        t0 = time.time()
        try:
            mid, bid, ask, bv, av, sp_d3, sp_d4 = load_product_arrays(prod)
        except Exception as e:
            print(f"[{i_prod+1}/50] {prod}: SKIP ({e})")
            continue
        # compute every FV once with each fold's calibration cutoff
        # Some FVs (Kalman, OFI, Markov) depend on train_end — recompute for each fold
        fold_train_end = {"A": TRAIN_END_FOLD_A, "B": TRAIN_END_FOLD_B}
        per_fold_fvs: Dict[str, Dict[str, np.ndarray]] = {"A": {}, "B": {}}
        for it in cat_items:
            for fold, te in fold_train_end.items():
                # Recompute only for FVs whose calibration depends on train_end
                if fold == "B" and it["family"] not in ("kalman", "ofi_corrected", "markov"):
                    per_fold_fvs[fold][it["fv_id"]] = per_fold_fvs["A"][it["fv_id"]]
                    continue
                try:
                    fv = compute_fv(it["fv_id"], it["family"], it["params"],
                                    mid=mid, bid=bid, ask=ask, bv=bv, av=av,
                                    train_end=te)
                except Exception as e:
                    fv = np.full_like(mid, np.nan)
                per_fold_fvs[fold][it["fv_id"]] = fv

        # diagnostics per fold
        prod_dir = HERE / "per_product" / prod
        prod_dir.mkdir(parents=True, exist_ok=True)
        rows = []
        for it in cat_items:
            for fold in ("A", "B"):
                lo, hi = TEST_RANGES[fold]
                spread_p50 = sp_d3 if fold == "A" else sp_d4
                diag = diagnose_one(mid, per_fold_fvs[fold][it["fv_id"]], lo, hi, spread_p50)
                row = {
                    "product": prod,
                    "fv_id": it["fv_id"],
                    "family": it["family"],
                    "fold": fold,
                    "spread_p50": spread_p50,
                    **diag,
                }
                rows.append(row)
                all_diag_rows.append(row)
        diag_df = pd.DataFrame(rows)
        diag_df.to_csv(prod_dir / "diagnostics.csv", index=False)

        # composite score per FV (avg over folds)
        agg = diag_df.groupby("fv_id").agg(
            ic_abs=("ic_spearman", lambda s: float(np.nanmean(np.abs(s)))),
            half_life=("half_life", lambda s: float(np.nanmean(np.where(np.isfinite(s), s, np.nan)))),
            mean_abs_res=("mean_abs_res", "mean"),
            res_to_spread=("res_to_spread", "mean"),
            adf_p=("adf_p", "mean"),
        ).reset_index()
        # z-scores within product
        def zscore(s: pd.Series) -> pd.Series:
            mu = s.mean(skipna=True)
            sd = s.std(skipna=True, ddof=0)
            if sd == 0 or np.isnan(sd):
                return pd.Series([0.0] * len(s))
            return (s - mu) / sd
        agg["z_ic"] = zscore(agg["ic_abs"])
        agg["z_hl"] = zscore(-np.log10(agg["half_life"].replace([np.inf, -np.inf], np.nan).fillna(1e9) + 1))
        agg["z_res"] = zscore(-agg["res_to_spread"].fillna(agg["res_to_spread"].max() if agg["res_to_spread"].notna().any() else 0))
        agg["score"] = agg["z_ic"].fillna(0) + agg["z_hl"].fillna(0) + agg["z_res"].fillna(0)
        agg["product"] = prod
        agg = agg.sort_values("score", ascending=False)
        agg.to_csv(prod_dir / "ranking.csv", index=False)
        # shortlist top 8
        top8 = agg.head(8).copy()
        top8["rank"] = range(1, len(top8) + 1)
        for _, r in top8.iterrows():
            shortlist_rows.append({
                "product": prod,
                "rank": int(r["rank"]),
                "fv_id": r["fv_id"],
                "score": float(r["score"]),
                "ic_abs": float(r["ic_abs"]),
                "half_life": float(r["half_life"]) if np.isfinite(r["half_life"]) else np.inf,
                "mean_abs_res": float(r["mean_abs_res"]),
                "res_to_spread": float(r["res_to_spread"]) if np.isfinite(r["res_to_spread"]) else np.nan,
            })
        elapsed = time.time() - t0
        print(f"[{i_prod+1}/50] {prod}: done ({elapsed:.1f}s)  top FV={top8.iloc[0]['fv_id']}  ic={top8.iloc[0]['ic_abs']:.3f}")

    # save full diagnostics (long format)
    pd.DataFrame(all_diag_rows).to_csv(HERE / "all_diagnostics.csv", index=False)
    pd.DataFrame(shortlist_rows).to_csv(HERE / "fv_shortlist.csv", index=False)
    print(f"\nTOTAL elapsed: {time.time() - t_total:.1f}s")
    print(f"wrote all_diagnostics.csv  ({len(all_diag_rows)} rows)")
    print(f"wrote fv_shortlist.csv     ({len(shortlist_rows)} rows)")


if __name__ == "__main__":
    run()
