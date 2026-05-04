"""Statistical primitives for ROUND_5 autoresearch.

All functions accept array-likes (np.ndarray / pd.Series / list) and return
plain Python floats or small typed dicts. Statsmodels and scipy are imported
lazily so this module is cheap to import.

Public API
    adf_test(x)                         -> dict
    kpss_test(x)                        -> dict
    hurst_dfa(x, scales=None)           -> float
    ou_half_life(x)                     -> float
    spearman_ic(x, y)                   -> dict
    lo_mackinlay_var_ratio(x, q=2)      -> dict
    jarque_bera(x)                      -> dict
    arch_lm(x, lags=10)                 -> dict
"""
from __future__ import annotations

from typing import Iterable, Optional, Sequence

import numpy as np
import pandas as pd


# ── helpers ────────────────────────────────────────────────────────────────

def _as_array(x: Iterable[float]) -> np.ndarray:
    a = np.asarray(x, dtype=float).ravel()
    a = a[np.isfinite(a)]
    return a


# ── stationarity ───────────────────────────────────────────────────────────

def adf_test(x: Iterable[float], *, regression: str = "c", autolag: str = "AIC") -> dict:
    """Augmented Dickey-Fuller test. Null = unit-root (non-stationary)."""
    from statsmodels.tsa.stattools import adfuller

    a = _as_array(x)
    stat, pval, used_lag, n_obs, crit, _icbest = adfuller(a, regression=regression, autolag=autolag)
    return {
        "stat": float(stat),
        "pvalue": float(pval),
        "lags": int(used_lag),
        "nobs": int(n_obs),
        "crit": {k: float(v) for k, v in crit.items()},
        "stationary_5pct": bool(pval < 0.05),
    }


def kpss_test(x: Iterable[float], *, regression: str = "c", nlags: str = "auto") -> dict:
    """KPSS. Null = stationary (opposite of ADF)."""
    from statsmodels.tsa.stattools import kpss

    a = _as_array(x)
    # statsmodels emits an InterpolationWarning when stat is outside the table;
    # we silence by reading the raw output and converting locally.
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        stat, pval, used_lag, crit = kpss(a, regression=regression, nlags=nlags)
    return {
        "stat": float(stat),
        "pvalue": float(pval),
        "lags": int(used_lag),
        "crit": {k: float(v) for k, v in crit.items()},
        "stationary_5pct": bool(pval >= 0.05),
    }


# ── long-memory / fractal ───────────────────────────────────────────────────

def hurst_dfa(x: Iterable[float], *, scales: Optional[Sequence[int]] = None) -> float:
    """Hurst exponent via Detrended Fluctuation Analysis (DFA-1).

    H ≈ 0.5 → random walk; H < 0.5 → mean-reverting; H > 0.5 → trending.
    """
    a = _as_array(x)
    n = len(a)
    if n < 32:
        raise ValueError("hurst_dfa needs at least 32 observations")

    y = np.cumsum(a - a.mean())
    if scales is None:
        max_scale = max(8, n // 4)
        scales = np.unique(np.logspace(np.log10(8), np.log10(max_scale), 16).astype(int))

    fluct = []
    valid_scales = []
    for s in scales:
        s = int(s)
        if s < 4 or s >= n:
            continue
        m = n // s
        if m < 2:
            continue
        segs = y[: m * s].reshape(m, s)
        # detrend each segment with a linear fit and accumulate RMS
        t = np.arange(s)
        rms = []
        for seg in segs:
            slope, intercept = np.polyfit(t, seg, 1)
            resid = seg - (slope * t + intercept)
            rms.append(np.sqrt(np.mean(resid ** 2)))
        fluct.append(np.mean(rms))
        valid_scales.append(s)

    if len(valid_scales) < 4:
        raise ValueError("hurst_dfa: not enough valid scales for a stable fit")

    log_s = np.log(valid_scales)
    log_f = np.log(fluct)
    slope, _intercept = np.polyfit(log_s, log_f, 1)
    return float(slope)


# ── mean-reversion speed ───────────────────────────────────────────────────

def ou_half_life(x: Iterable[float]) -> float:
    """Estimate Ornstein-Uhlenbeck half-life by AR(1) on the level.

    Δx_t = α + β·x_{t-1} + ε  →  half-life = -ln(2) / ln(1 + β)

    Returns +inf if the series is non-mean-reverting (β ≥ 0) or if regression
    cannot be estimated.
    """
    a = _as_array(x)
    if len(a) < 4:
        return float("inf")
    x_lag = a[:-1]
    dx = np.diff(a)
    # OLS: dx = alpha + beta * x_lag
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


# ── correlation / IC ───────────────────────────────────────────────────────

def spearman_ic(x: Iterable[float], y: Iterable[float]) -> dict:
    """Rank-correlation IC between a signal x and a forward-return y."""
    from scipy import stats

    xa = np.asarray(x, dtype=float).ravel()
    ya = np.asarray(y, dtype=float).ravel()
    n = min(len(xa), len(ya))
    xa, ya = xa[:n], ya[:n]
    mask = np.isfinite(xa) & np.isfinite(ya)
    if mask.sum() < 4:
        return {"ic": float("nan"), "pvalue": float("nan"), "n": int(mask.sum())}
    r, p = stats.spearmanr(xa[mask], ya[mask])
    return {"ic": float(r), "pvalue": float(p), "n": int(mask.sum())}


# ── variance-ratio ─────────────────────────────────────────────────────────

def lo_mackinlay_var_ratio(x: Iterable[float], q: int = 2) -> dict:
    """Lo–MacKinlay variance ratio test (homoskedastic).

    VR(q) = Var(r_q) / (q · Var(r_1))

    Under random walk with iid increments VR(q) = 1. The Z-stat is normalised
    so |Z| > 1.96 rejects iid at 5%.
    """
    a = _as_array(x)
    if q < 2 or len(a) < q + 2:
        raise ValueError("lo_mackinlay_var_ratio: need q≥2 and len(x) > q+1")
    r1 = np.diff(a)
    rq = a[q:] - a[:-q]
    n = len(r1)
    var1 = float(np.var(r1, ddof=1))
    varq = float(np.var(rq, ddof=1)) / q if q > 0 else float("nan")
    if var1 <= 0:
        return {"vr": float("nan"), "z": float("nan"), "pvalue": float("nan"), "n": n}
    vr = varq / var1
    # Asymptotic variance of (vr-1) under iid (Lo–MacKinlay 1988):
    # 2 * (2q-1)(q-1) / (3qN)
    asym_var = 2.0 * (2 * q - 1) * (q - 1) / (3.0 * q * n)
    z = (vr - 1.0) / np.sqrt(asym_var) if asym_var > 0 else float("nan")
    from scipy import stats
    pvalue = 2.0 * (1.0 - stats.norm.cdf(abs(z))) if np.isfinite(z) else float("nan")
    return {"vr": float(vr), "z": float(z), "pvalue": float(pvalue), "n": n, "q": q}


# ── normality ──────────────────────────────────────────────────────────────

def jarque_bera(x: Iterable[float]) -> dict:
    """Jarque-Bera normality test on a series."""
    from scipy import stats
    a = _as_array(x)
    if len(a) < 8:
        return {"stat": float("nan"), "pvalue": float("nan"), "skew": float("nan"),
                "kurtosis": float("nan"), "n": len(a)}
    stat, pval = stats.jarque_bera(a)
    return {
        "stat": float(stat),
        "pvalue": float(pval),
        "skew": float(stats.skew(a)),
        "kurtosis": float(stats.kurtosis(a, fisher=False)),
        "n": int(len(a)),
        "normal_5pct": bool(pval >= 0.05),
    }


# ── ARCH effects / vol clustering ──────────────────────────────────────────

def arch_lm(x: Iterable[float], lags: int = 10) -> dict:
    """Engle's ARCH-LM test for conditional heteroskedasticity.

    Null: no ARCH effects (homoskedastic).
    """
    from statsmodels.stats.diagnostic import het_arch

    a = _as_array(x)
    if len(a) < lags + 5:
        raise ValueError("arch_lm: not enough observations for chosen lag count")
    stat, pval, fstat, fpval = het_arch(a, nlags=lags)
    return {
        "lm_stat": float(stat),
        "lm_pvalue": float(pval),
        "f_stat": float(fstat),
        "f_pvalue": float(fpval),
        "lags": int(lags),
        "arch_5pct": bool(pval < 0.05),
    }