"""Phase 1 — fair-value estimator zoo.

Every FV is a CAUSAL function of the price/depth series: FV(t) depends only on
information up to and including t-1 (or t for "anchored" variants like
microprice computed from the *current* book).  Each function returns an array
the same length as input mid, with NaN in the warm-up region.

Catalog item shape (see fv_catalog.csv):
    fv_id, family, params (json string), description

These FV producers operate on raw arrays for speed; calibration is done
separately on a TRAIN slice and the output is then evaluated on the TEST slice
to enforce walk-forward.

Public:
    compute_all_fvs(prices_df, *, calib_slice) -> Dict[fv_id, np.ndarray]
    catalog() -> List[Dict]
    NO_LOOK_AHEAD_ASSERTION applied via shift in every causal FV.
"""
from __future__ import annotations

import json
from typing import Dict, List, Optional

import numpy as np
import pandas as pd


# ── primitives ─────────────────────────────────────────────────────────────


def _rolling_mean_causal(x: np.ndarray, w: int) -> np.ndarray:
    """FV(t) = mean(x[t-w:t]). t-th value uses indices < t."""
    n = len(x)
    out = np.full(n, np.nan)
    if w <= 0 or w >= n:
        return out
    cs = np.cumsum(np.concatenate([[0.0], x]))
    # mean over [t-w, t-1] inclusive -> use cs[t] - cs[t-w]
    idx = np.arange(w, n)
    out[idx] = (cs[idx] - cs[idx - w]) / w
    return out


def _rolling_median_causal(x: np.ndarray, w: int) -> np.ndarray:
    """Median of x[t-w:t]."""
    n = len(x)
    out = np.full(n, np.nan)
    if w <= 0 or w >= n:
        return out
    s = pd.Series(x)
    # rolling().median() includes current, so shift by 1
    r = s.rolling(w).median().shift(1).to_numpy()
    return r


def _ewma_causal(x: np.ndarray, half_life: float) -> np.ndarray:
    """EWMA with given half-life. FV(t) = ewma over x[..t-1] (shifted)."""
    n = len(x)
    if half_life <= 0:
        return np.full(n, np.nan)
    alpha = 1.0 - 0.5 ** (1.0 / half_life)
    out = np.full(n, np.nan)
    if n == 0:
        return out
    state = x[0]
    for t in range(1, n):
        out[t] = state  # uses info up to t-1
        state = alpha * x[t] + (1 - alpha) * state
    return out


def _rolling_min_max_mid(x: np.ndarray, w: int) -> np.ndarray:
    """FV(t) = (max(x[t-w:t]) + min(x[t-w:t])) / 2."""
    n = len(x)
    out = np.full(n, np.nan)
    if w <= 0 or w >= n:
        return out
    s = pd.Series(x)
    rmax = s.rolling(w).max().shift(1).to_numpy()
    rmin = s.rolling(w).min().shift(1).to_numpy()
    return (rmax + rmin) / 2.0


def _rolling_linreg_causal(x: np.ndarray, w: int) -> np.ndarray:
    """Rolling OLS of x ~ a + b*t over the past w points; FV(t) = predicted x at t.

    Uses only x[t-w..t-1].
    """
    n = len(x)
    out = np.full(n, np.nan)
    if w < 4 or w >= n:
        return out
    t_arr = np.arange(w, dtype=float)
    t_mean = t_arr.mean()
    t_var = ((t_arr - t_mean) ** 2).sum()
    if t_var <= 0:
        return out
    for t in range(w, n):
        seg = x[t - w : t]
        b = ((t_arr - t_mean) * (seg - seg.mean())).sum() / t_var
        a = seg.mean() - b * t_mean
        out[t] = a + b * w  # extrapolate one step ahead
    return out


def _rolling_quadratic_causal(x: np.ndarray, w: int) -> np.ndarray:
    """Rolling 2nd-degree polynomial fit over past w; FV(t) = poly extrap at t."""
    n = len(x)
    out = np.full(n, np.nan)
    if w < 6 or w >= n:
        return out
    t_arr = np.arange(w, dtype=float)
    A = np.column_stack([np.ones(w), t_arr, t_arr ** 2])
    AtA_inv = np.linalg.pinv(A.T @ A)
    for t in range(w, n):
        seg = x[t - w : t]
        coef = AtA_inv @ (A.T @ seg)
        out[t] = coef[0] + coef[1] * w + coef[2] * w * w
    return out


def _kalman_level_causal(x: np.ndarray, q: float, r: float) -> np.ndarray:
    """Random-walk + noise Kalman filter: x_t = mu_t + eps; mu_t = mu_{t-1} + eta.

    FV(t) = E[mu_t | x_{0..t-1}] (predicted, before seeing x_t).
    Q = process variance, R = obs variance.
    """
    n = len(x)
    out = np.full(n, np.nan)
    if n == 0 or r <= 0 or q < 0:
        return out
    mu = float(x[0])
    p = r  # initial variance
    out[1] = mu  # one-step predict before x[1]
    for t in range(1, n):
        # update with x[t] (after recording prediction for t)
        out[t] = mu  # FV at t is predicted level using x[..t-1]
        # innovation
        s = p + r
        k = p / s
        mu = mu + k * (x[t] - mu)
        p = (1 - k) * p + q  # propagate
    return out


def _calibrate_kalman_qr(x: np.ndarray) -> tuple[float, float]:
    """Quick MLE estimate of Q/R for random-walk + noise.

    Use innovation-form: dx_t = (mu_t - mu_{t-1}) + (eps_t - eps_{t-1}). The
    autocovariance of dx gives gamma0 = Q + 2R, gamma1 = -R, so:
        R = -gamma1, Q = gamma0 + 2*gamma1.
    Clipped to small positive minima.
    """
    dx = np.diff(x)
    if len(dx) < 4:
        return 1.0, 1.0
    gamma0 = float(np.var(dx, ddof=1))
    gamma1 = float(np.cov(dx[:-1], dx[1:], ddof=1)[0, 1]) if len(dx) >= 2 else 0.0
    R = max(-gamma1, 1e-3)
    Q = max(gamma0 + 2 * gamma1, 1e-6)
    return Q, R


def _ar_one_step(x: np.ndarray, p: int, *, refit_every: int = 5000, train_w: int = 5000) -> np.ndarray:
    """AR(p) on first-differences (mid is unit-root); FV(t) = mid(t-1) + AR(p)·dx[..t-1].

    Refit OLS coefficients every `refit_every` ticks using the last `train_w` diffs.
    """
    n = len(x)
    out = np.full(n, np.nan)
    if p < 1 or n < p + 4:
        return out
    dx = np.diff(x)
    coef: Optional[np.ndarray] = None
    last_fit = -1
    for t in range(p + 1, n):
        # fit if needed
        end = t - 1  # we have dx[0..end-1] available (dx index runs 0..n-2)
        # but dx index e at time t corresponds to x[e+1]-x[e]; the most recent
        # diff usable is dx[t-2] (uses x[t-2], x[t-1]) — strictly < t.
        avail_end = t - 1  # exclusive
        # refit at first valid step + every refit_every
        if coef is None or (t - last_fit) >= refit_every:
            train_start = max(0, avail_end - train_w)
            d_segment = dx[train_start:avail_end]
            if len(d_segment) >= p + 5:
                Xm = np.column_stack([d_segment[p - 1 - k : len(d_segment) - 1 - k] for k in range(p)])
                yv = d_segment[p:]
                if Xm.shape[0] >= p + 4:
                    try:
                        coef, *_ = np.linalg.lstsq(Xm, yv, rcond=None)
                        last_fit = t
                    except np.linalg.LinAlgError:
                        coef = np.zeros(p)
                        last_fit = t
        if coef is None:
            continue
        # forecast next dx using lag-vector dx[avail_end-1, avail_end-2, ...]
        if avail_end - p < 0:
            continue
        lags = dx[avail_end - p : avail_end][::-1]
        dx_hat = float(coef @ lags)
        out[t] = float(x[t - 1]) + dx_hat
    return out


def _arma11_one_step(x: np.ndarray, *, refit_every: int = 5000) -> np.ndarray:
    """ARMA(1,1) one-step on diffs, refit periodically via statsmodels."""
    from statsmodels.tsa.arima.model import ARIMA
    n = len(x)
    out = np.full(n, np.nan)
    dx = np.diff(x)
    if len(dx) < 100:
        return out
    fit_res = None
    last_fit = -1
    for t in range(50, n):
        avail = t - 1
        if fit_res is None or (t - last_fit) >= refit_every:
            try:
                model = ARIMA(dx[: avail], order=(1, 0, 1))
                fit_res = model.fit(method_kwargs={"warn_convergence": False})
                last_fit = t
            except Exception:
                fit_res = None
        if fit_res is None:
            continue
        try:
            forecast = fit_res.forecast(steps=1)
            dx_hat = float(forecast[0])
            out[t] = float(x[t - 1]) + dx_hat
        except Exception:
            continue
    return out


def _holt_winters_causal(x: np.ndarray, alpha: float, beta: float) -> np.ndarray:
    """Causal Holt's linear (double-exp) smoothing. FV(t) = level + slope (predicted)."""
    n = len(x)
    out = np.full(n, np.nan)
    if n < 3:
        return out
    level = x[0]
    slope = 0.0
    out[1] = level + slope
    for t in range(1, n):
        out[t] = level + slope
        new_level = alpha * x[t] + (1 - alpha) * (level + slope)
        new_slope = beta * (new_level - level) + (1 - beta) * slope
        level, slope = new_level, new_slope
    return out


def _microprice(bid: np.ndarray, ask: np.ndarray, bv: np.ndarray, av: np.ndarray) -> np.ndarray:
    """Volume-weighted mid: (bid·av + ask·bv) / (av + bv)."""
    denom = bv + av
    out = np.full(len(bid), np.nan)
    mask = denom > 0
    out[mask] = (bid[mask] * av[mask] + ask[mask] * bv[mask]) / denom[mask]
    return out


def _lattice_snap(x: np.ndarray, step: float) -> np.ndarray:
    """Round to nearest multiple of `step`. Lattice products only."""
    if step <= 0:
        return np.full_like(x, np.nan)
    return np.round(x / step) * step


def _ofi_corrected(mid: np.ndarray, bid: np.ndarray, ask: np.ndarray,
                   bv: np.ndarray, av: np.ndarray, *,
                   alpha: float, lag: int = 1) -> np.ndarray:
    """FV(t) = mid(t-1) + alpha·OFI(t-1).

    OFI ≈ Δbid·bv + Δask·(-av) (sign convention: positive => buying pressure).
    """
    n = len(mid)
    out = np.full(n, np.nan)
    db = np.diff(bid, prepend=bid[0])
    da = np.diff(ask, prepend=ask[0])
    ofi = db * bv - da * av
    if lag < 1:
        lag = 1
    for t in range(lag + 1, n):
        out[t] = float(mid[t - 1]) + alpha * float(ofi[t - lag])
    return out


def _calibrate_ofi_alpha(mid: np.ndarray, bid: np.ndarray, ask: np.ndarray,
                          bv: np.ndarray, av: np.ndarray) -> float:
    """Regress next-tick mid change on lag-1 OFI: dmid_t = alpha·OFI_{t-1}."""
    db = np.diff(bid, prepend=bid[0])
    da = np.diff(ask, prepend=ask[0])
    ofi = db * bv - da * av
    dmid = np.diff(mid)
    if len(dmid) < 10:
        return 0.0
    x_ofi = ofi[:-1]
    y = dmid
    denom = (x_ofi ** 2).sum()
    if denom <= 0:
        return 0.0
    return float((x_ofi * y).sum() / denom)


# ── markov conditional mean ────────────────────────────────────────────────


def _markov_state_mean(x: np.ndarray, *, k: int, train_end: int) -> np.ndarray:
    """Discretise (mid - rolling_med) into K bins on day-2; FV(t) = mid(t-1) + E[Δmid|state_{t-1}].

    `train_end`: index up to which the empirical transition distribution is built.
    """
    n = len(x)
    out = np.full(n, np.nan)
    if n < 200 or k < 2:
        return out
    # use causal residual: residual = x - rolling_mean(x, 200) (shifted)
    w_ref = 200
    base = _rolling_mean_causal(x, w_ref)
    res = x - base
    # bin edges from train slice only (no look-ahead beyond train_end)
    train_res = res[:train_end]
    train_res = train_res[np.isfinite(train_res)]
    if len(train_res) < 100:
        return out
    qs = np.linspace(0, 1, k + 1)[1:-1]
    edges = np.quantile(train_res, qs)
    # state of element at time t computed from residual[t]
    state = np.full(n, -1, dtype=int)
    fin = np.isfinite(res)
    state[fin] = np.searchsorted(edges, res[fin])
    # build empirical state -> next dmid map on train slice
    dmid = np.diff(x, prepend=x[0])
    # use pairs (state[t-1], dmid[t]) for t in [w_ref+1 .. train_end]
    means = np.zeros(k)
    counts = np.zeros(k, dtype=int)
    for t in range(w_ref + 1, train_end):
        s = state[t - 1]
        if s < 0 or s >= k:
            continue
        means[s] += dmid[t]
        counts[s] += 1
    safe = counts > 0
    means[safe] /= counts[safe]
    means[~safe] = 0.0
    # apply: FV(t) = x[t-1] + means[state[t-1]]
    for t in range(w_ref + 1, n):
        s = state[t - 1]
        if s < 0 or s >= k:
            continue
        out[t] = x[t - 1] + means[s]
    return out


# ── catalog driver ─────────────────────────────────────────────────────────


def catalog() -> List[Dict]:
    """List of all (fv_id, family, params) tuples we evaluate."""
    items: List[Dict] = []
    # 1. Rolling mean
    for w in (50, 100, 200, 500, 1000, 2000, 5000):
        items.append({"fv_id": f"mean_{w}", "family": "rolling_mean", "params": {"w": w}})
    # 2. Rolling median
    for w in (50, 100, 200, 500, 1000, 2000):
        items.append({"fv_id": f"median_{w}", "family": "rolling_median", "params": {"w": w}})
    # 3. EWMA
    for h in (10, 25, 50, 100, 200, 500, 1000):
        items.append({"fv_id": f"ewma_{h}", "family": "ewma", "params": {"half_life": h}})
    # 4. Microprice (raw + smoothed)
    items.append({"fv_id": "microprice_raw", "family": "microprice", "params": {}})
    for h in (25, 100):
        items.append({"fv_id": f"microprice_ewma{h}", "family": "microprice_ewma", "params": {"half_life": h}})
    # 5. Range midpoint (substitute for VWAP given lack of trade volume)
    for w in (200, 500, 1000):
        items.append({"fv_id": f"rangemid_{w}", "family": "range_mid", "params": {"w": w}})
    # 6. Kalman
    items.append({"fv_id": "kalman_mle", "family": "kalman", "params": {"calib": "innovations"}})
    # 7. Rolling linear regression
    for w in (200, 500, 2000):
        items.append({"fv_id": f"linreg_{w}", "family": "rolling_linreg", "params": {"w": w}})
    # 8. Rolling quadratic
    for w in (500, 2000):
        items.append({"fv_id": f"quad_{w}", "family": "rolling_quadratic", "params": {"w": w}})
    # 9. AR(p) on diffs
    for p in (1, 2, 3, 5):
        items.append({"fv_id": f"ar{p}_dx", "family": "ar_diff", "params": {"p": p}})
    # 10. Holt-Winters
    items.append({"fv_id": "holt", "family": "holt", "params": {"alpha": 0.05, "beta": 0.01}})
    # 12. Lattice snap (only useful for deterministic products; we still test)
    for step in (1, 2, 5):
        items.append({"fv_id": f"lattice_{step}", "family": "lattice", "params": {"step": step}})
    # 13. Markov conditional mean
    for k in (10, 20, 50):
        items.append({"fv_id": f"markov_{k}", "family": "markov", "params": {"k": k}})
    # 14. OFI-corrected mid
    items.append({"fv_id": "ofi_lag1", "family": "ofi_corrected", "params": {"lag": 1}})
    # 15. Anchored mid (the trivial 'no FV') - useful to include as null baseline
    items.append({"fv_id": "mid_anchor", "family": "anchor", "params": {}})
    return items


def compute_fv(fv_id: str, family: str, params: Dict, *,
               mid: np.ndarray, bid: np.ndarray, ask: np.ndarray,
               bv: np.ndarray, av: np.ndarray, train_end: int) -> np.ndarray:
    """Compute one FV. `train_end` defines the calibration cutoff."""
    if family == "rolling_mean":
        return _rolling_mean_causal(mid, params["w"])
    if family == "rolling_median":
        return _rolling_median_causal(mid, params["w"])
    if family == "ewma":
        return _ewma_causal(mid, params["half_life"])
    if family == "microprice":
        mp = _microprice(bid, ask, bv, av)
        # shift to enforce causality (use t-1 microprice for FV at t)
        out = np.full_like(mp, np.nan)
        out[1:] = mp[:-1]
        return out
    if family == "microprice_ewma":
        mp = _microprice(bid, ask, bv, av)
        smooth = _ewma_causal(mp, params["half_life"])
        return smooth
    if family == "range_mid":
        return _rolling_min_max_mid(mid, params["w"])
    if family == "kalman":
        Q, R = _calibrate_kalman_qr(mid[:train_end])
        return _kalman_level_causal(mid, Q, R)
    if family == "rolling_linreg":
        return _rolling_linreg_causal(mid, params["w"])
    if family == "rolling_quadratic":
        return _rolling_quadratic_causal(mid, params["w"])
    if family == "ar_diff":
        return _ar_one_step(mid, params["p"])
    if family == "arma11_diff":
        return _arma11_one_step(mid)
    if family == "holt":
        return _holt_winters_causal(mid, params["alpha"], params["beta"])
    if family == "lattice":
        # snap to nearest grid step using mid(t-1) value
        snapped = _lattice_snap(mid, params["step"])
        out = np.full_like(snapped, np.nan)
        out[1:] = snapped[:-1]
        return out
    if family == "markov":
        return _markov_state_mean(mid, k=params["k"], train_end=train_end)
    if family == "ofi_corrected":
        alpha = _calibrate_ofi_alpha(mid[:train_end], bid[:train_end], ask[:train_end],
                                     bv[:train_end], av[:train_end])
        return _ofi_corrected(mid, bid, ask, bv, av, alpha=alpha, lag=params.get("lag", 1))
    if family == "anchor":
        # FV(t) = mid(t-1) -> trivial: signal r = mid(t) - mid(t-1) = dmid
        out = np.full_like(mid, np.nan)
        out[1:] = mid[:-1]
        return out
    raise ValueError(f"unknown family: {family}")


def assert_no_lookahead(fv: np.ndarray, mid: np.ndarray) -> None:
    """Sanity check: FV[0] must be NaN and replacing mid[k:] with garbage should
    not change FV[:k]. We check the nan-on-first and raise if violated.
    """
    if len(fv) == 0:
        return
    if not np.isnan(fv[0]):
        raise AssertionError("FV[0] must be NaN to enforce no-look-ahead at boundary")
