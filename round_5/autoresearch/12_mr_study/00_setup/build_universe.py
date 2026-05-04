"""Phase 0 — build product_universe.csv with per-product MR-relevant stats.

Stats per product (combined across days 2/3/4):
  rows, n_distinct, mid mean/std/min/max, lattice_ratio, spread_p50,
  ADF p, KPSS p, Hurst (DFA), OU half-life, AR(1) coef + p,
  KS p (day2 vs day3 / 2 vs 4 / 3 vs 4),
  bucket (DETERMINISTIC / STRONG_MR / MILD_MR / WEAK_DRIFT).

Walk-forward: each stat is computed *per day* and on the concatenated series.
Use day-2 stats for bucketing (training window).
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats as sstats
from statsmodels.tsa.stattools import adfuller, kpss

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from utils.data_loader import load_prices  # noqa: E402
from utils.round5_products import ROUND5_PRODUCTS  # noqa: E402
from utils.stats import hurst_dfa, ou_half_life  # noqa: E402

OUT_DIR = Path(__file__).resolve().parent
DAYS = [2, 3, 4]


def safe_adf(x: np.ndarray) -> float:
    try:
        return float(adfuller(x, regression="c", autolag="AIC")[1])
    except Exception:
        return float("nan")


def safe_kpss(x: np.ndarray) -> float:
    try:
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            return float(kpss(x, regression="c", nlags="auto")[1])
    except Exception:
        return float("nan")


def safe_hurst(x: np.ndarray) -> float:
    try:
        return float(hurst_dfa(x))
    except Exception:
        return float("nan")


def safe_hl(x: np.ndarray) -> float:
    try:
        v = ou_half_life(x)
        return v if np.isfinite(v) else float("inf")
    except Exception:
        return float("inf")


def ar1(x: np.ndarray) -> tuple[float, float]:
    """AR(1) coefficient on first-differences: dx_t = a + b*dx_{t-1} + e."""
    if len(x) < 4:
        return float("nan"), float("nan")
    dx = np.diff(x)
    if len(dx) < 4:
        return float("nan"), float("nan")
    y = dx[1:]
    Xc = np.column_stack([np.ones(len(dx) - 1), dx[:-1]])
    coef, *_ = np.linalg.lstsq(Xc, y, rcond=None)
    yhat = Xc @ coef
    resid = y - yhat
    n = len(y)
    sse = float(np.sum(resid ** 2))
    sxx = float(np.sum((Xc[:, 1] - Xc[:, 1].mean()) ** 2))
    if sxx <= 0 or sse <= 0:
        return float(coef[1]), float("nan")
    se = np.sqrt(sse / (n - 2)) / np.sqrt(sxx)
    t = coef[1] / se if se > 0 else float("nan")
    p = 2.0 * (1 - sstats.norm.cdf(abs(t))) if np.isfinite(t) else float("nan")
    return float(coef[1]), float(p)


def bucket(half_life: float, adf_p: float, lattice_ratio: float, ar1_diff: float) -> str:
    """Priority hint only — every product still gets the full sweep.

    DETERMINISTIC: lattice (n_distinct/N small) or strongly stationary.
    STRONG_MR:     fast level reversion (small half-life) AND ADF p < 0.01.
    MILD_MR:       moderate half-life with ADF p < 0.05.
    INCREMENT_MR:  prices look unit-root but increments are anti-persistent
                   (|AR1_diff| > 0.05 with negative sign) — exploitable via
                   short-window MR on residuals.
    WEAK_DRIFT:    rest.
    """
    if (lattice_ratio < 0.05) or (np.isfinite(adf_p) and adf_p < 1e-6):
        return "DETERMINISTIC"
    if np.isfinite(half_life) and 1.0 <= half_life <= 50.0 and np.isfinite(adf_p) and adf_p < 0.01:
        return "STRONG_MR"
    if np.isfinite(half_life) and 50.0 < half_life <= 500.0 and np.isfinite(adf_p) and adf_p < 0.05:
        return "MILD_MR"
    if np.isfinite(ar1_diff) and ar1_diff < -0.05:
        return "INCREMENT_MR"
    return "WEAK_DRIFT"


def build() -> pd.DataFrame:
    # one big load, indexed by (day, product, timestamp)
    frames = []
    for d in DAYS:
        df = load_prices(d)[["day", "timestamp", "product", "bid_price_1", "ask_price_1", "mid_price"]].copy()
        df["spread"] = df["ask_price_1"] - df["bid_price_1"]
        frames.append(df)
    big = pd.concat(frames, ignore_index=True)
    big["mid_price"] = big["mid_price"].astype(float)

    rows = []
    by_prod = big.groupby("product", sort=False)
    for prod in ROUND5_PRODUCTS:
        if prod not in by_prod.groups:
            rows.append({"product": prod, "rows": 0, "bucket": "MISSING"})
            continue
        g = by_prod.get_group(prod).sort_values(["day", "timestamp"])
        mid = g["mid_price"].astype(float).to_numpy()
        sp = g["spread"].astype(float).to_numpy()
        n = len(mid)

        n_distinct = int(np.unique(mid).size)
        lattice_ratio = n_distinct / n if n > 0 else float("nan")

        # day-level snapshots
        day_mids = {d: g.loc[g["day"] == d, "mid_price"].astype(float).to_numpy() for d in DAYS}

        adf_p = safe_adf(day_mids[2]) if len(day_mids[2]) >= 32 else float("nan")
        kpss_p = safe_kpss(day_mids[2]) if len(day_mids[2]) >= 32 else float("nan")
        hurst_lv = safe_hurst(day_mids[2]) if len(day_mids[2]) >= 64 else float("nan")
        # Hurst on increments: H<0.5 => MR in returns, H≈0.5 => random walk
        d2_diff = np.diff(day_mids[2]) if len(day_mids[2]) >= 2 else np.array([])
        hurst_inc = safe_hurst(d2_diff) if len(d2_diff) >= 64 else float("nan")
        hl = safe_hl(day_mids[2]) if len(day_mids[2]) >= 16 else float("inf")

        ar1_b, ar1_p = ar1(day_mids[2])
        # Per-tick increment stdev (proxy for short-term vol)
        diff_std = float(np.nanstd(d2_diff)) if len(d2_diff) > 1 else float("nan")
        # Lag-1 autocorr of increments (negative -> MR in increments)
        if len(d2_diff) >= 8:
            r1 = float(np.corrcoef(d2_diff[:-1], d2_diff[1:])[0, 1])
        else:
            r1 = float("nan")

        # KS across day pairs (compare distributions of first-differences)
        def diffs(a):
            return np.diff(a) if len(a) >= 2 else np.array([])

        d23 = sstats.ks_2samp(diffs(day_mids[2]), diffs(day_mids[3])).pvalue if (
            len(day_mids[2]) > 4 and len(day_mids[3]) > 4
        ) else float("nan")
        d24 = sstats.ks_2samp(diffs(day_mids[2]), diffs(day_mids[4])).pvalue if (
            len(day_mids[2]) > 4 and len(day_mids[4]) > 4
        ) else float("nan")
        d34 = sstats.ks_2samp(diffs(day_mids[3]), diffs(day_mids[4])).pvalue if (
            len(day_mids[3]) > 4 and len(day_mids[4]) > 4
        ) else float("nan")

        rows.append({
            "product": prod,
            "rows": n,
            "n_distinct": n_distinct,
            "lattice_ratio": lattice_ratio,
            "mid_mean": float(np.nanmean(mid)),
            "mid_std": float(np.nanstd(mid)),
            "mid_min": float(np.nanmin(mid)),
            "mid_max": float(np.nanmax(mid)),
            "spread_p50": float(np.nanmedian(sp)),
            "spread_mean": float(np.nanmean(sp)),
            "adf_p_d2": adf_p,
            "kpss_p_d2": kpss_p,
            "hurst_level_d2": hurst_lv,
            "hurst_inc_d2": hurst_inc,
            "ou_half_life_d2": hl,
            "ar1_diff_coef_d2": ar1_b,
            "ar1_diff_p_d2": ar1_p,
            "diff_std_d2": diff_std,
            "diff_autocorr_lag1_d2": r1,
            "ks_p_d2_d3": d23,
            "ks_p_d2_d4": d24,
            "ks_p_d3_d4": d34,
            "bucket": bucket(hl, adf_p, lattice_ratio, ar1_b),
        })
    df = pd.DataFrame(rows)
    df.to_csv(OUT_DIR / "product_universe.csv", index=False)
    return df


if __name__ == "__main__":
    df = build()
    print(f"wrote {OUT_DIR/'product_universe.csv'}  ({len(df)} rows)")
    bucket_counts = df["bucket"].value_counts()
    print("\nbucket distribution:")
    print(bucket_counts.to_string())
