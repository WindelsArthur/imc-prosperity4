"""Phase 4 — Statistical patterns.

Per product:
- OU mean-reversion fit (mu, theta, sigma, half-life).
- AR(p) BIC selection p∈{1..10}.
- HMM 2-state on returns (regime persistence + transition matrix).
- CUSUM change-point on returns.
- Time-of-day binning (timestamp mod 10000 in 100-tick bins) — mean return + vol.
- Day-of-day stability (KS test day2 vs day3 vs day4 returns).
- Cross-day autocorrelation: end-of-N predicts start-of-N+1.

Outputs
    04_statistical_patterns/stat_summary.csv
    04_statistical_patterns/intraday/{product}.csv  (time-of-day curve)
"""
from __future__ import annotations

import sys
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats as sstats

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from utils.data_loader import load_prices, available_days
from utils.round5_products import ROUND5_PRODUCTS, group_of

warnings.filterwarnings("ignore")
OUT = Path(__file__).resolve().parent
INTRA = OUT / "intraday"
INTRA.mkdir(parents=True, exist_ok=True)
LOG = ROOT / "logs" / "progress.md"


def append_log(msg: str) -> None:
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    with LOG.open("a") as f:
        f.write(f"- [{ts}] {msg}\n")


def stitch(prices_by_day, product):
    parts = []
    for d in sorted(prices_by_day.keys()):
        df = prices_by_day[d]
        sub = df.loc[df["product"] == product, ["day", "timestamp", "mid_price"]].copy()
        sub["mid_price"] = sub["mid_price"].astype(float).ffill().bfill()
        parts.append(sub)
    out = pd.concat(parts, ignore_index=True).sort_values(["day", "timestamp"]).reset_index(drop=True)
    return out


def ou_fit(x: np.ndarray) -> tuple[float, float, float, float]:
    """OLS AR(1) → mu, theta, sigma, half-life."""
    if len(x) < 4:
        return float("nan"), float("nan"), float("nan"), float("inf")
    x_lag = x[:-1]; dx = np.diff(x)
    X = np.column_stack([np.ones_like(x_lag), x_lag])
    coef, *_ = np.linalg.lstsq(X, dx, rcond=None)
    alpha, beta = float(coef[0]), float(coef[1])
    if beta >= 0:
        return float("nan"), beta, float("nan"), float("inf")
    theta = -beta
    mu = -alpha / beta
    resid = dx - (alpha + beta * x_lag)
    sigma = float(np.std(resid))
    hl = float(-np.log(2.0) / np.log(1.0 + beta))
    return mu, theta, sigma, hl


def ar_bic(x: np.ndarray, max_p: int = 10):
    from statsmodels.tsa.ar_model import AutoReg
    best_p = 0; best_bic = np.inf; best_ar1 = float("nan")
    for p in range(1, max_p + 1):
        try:
            m = AutoReg(x, lags=p, old_names=False).fit()
            if m.bic < best_bic:
                best_bic = m.bic; best_p = p
                best_ar1 = float(m.params[1]) if len(m.params) > 1 else float("nan")
        except Exception:
            continue
    return best_p, float(best_bic), best_ar1


def hmm_2state(rets: np.ndarray):
    try:
        from hmmlearn.hmm import GaussianHMM
        x = rets.reshape(-1, 1)
        m = GaussianHMM(n_components=2, covariance_type="full", n_iter=50, random_state=0)
        m.fit(x)
        # persistence = diag of transition matrix
        p_persist = float(np.mean(np.diag(m.transmat_)))
        means = sorted(m.means_.flatten().tolist())
        vols = sorted(np.sqrt(m.covars_.flatten()).tolist())
        return p_persist, means, vols
    except Exception:
        return float("nan"), [float("nan"), float("nan")], [float("nan"), float("nan")]


def cusum_count(x: np.ndarray, threshold: float = 4.0) -> int:
    """Count CUSUM threshold crossings of |s_t|."""
    if len(x) < 8:
        return 0
    z = (x - np.mean(x)) / (np.std(x) + 1e-12)
    s_pos = 0.0; s_neg = 0.0; n = 0
    for v in z:
        s_pos = max(0.0, s_pos + v - 0.5)
        s_neg = min(0.0, s_neg + v + 0.5)
        if s_pos > threshold or s_neg < -threshold:
            n += 1
            s_pos = 0.0; s_neg = 0.0
    return n


def main() -> None:
    days = available_days()
    append_log(f"Phase4 START")
    prices_by_day = {d: load_prices(d) for d in days}

    rows = []
    for i, product in enumerate(ROUND5_PRODUCTS, start=1):
        df = stitch(prices_by_day, product)
        mid = df["mid_price"].to_numpy()
        rets = np.diff(mid)

        # OU
        mu, theta, sigma, hl = ou_fit(mid)

        # AR BIC
        try:
            best_p, best_bic, ar1 = ar_bic(rets, max_p=10)
        except Exception:
            best_p, best_bic, ar1 = -1, float("nan"), float("nan")

        # HMM
        p_persist, means, vols = hmm_2state(rets[: min(len(rets), 30000)])

        # CUSUM count
        n_change = cusum_count(rets, 4.0)

        # Day-of-day KS
        rets_by_day = {d: np.diff(df.loc[df["day"] == d, "mid_price"].to_numpy()) for d in sorted(days)}
        ks_pvals = []
        ds = sorted(rets_by_day.keys())
        for a in range(len(ds)):
            for b in range(a + 1, len(ds)):
                if len(rets_by_day[ds[a]]) > 10 and len(rets_by_day[ds[b]]) > 10:
                    s, p = sstats.ks_2samp(rets_by_day[ds[a]], rets_by_day[ds[b]])
                    ks_pvals.append(p)
        ks_min_p = float(min(ks_pvals)) if ks_pvals else float("nan")
        ks_mean_p = float(np.mean(ks_pvals)) if ks_pvals else float("nan")

        # Time-of-day: 100-tick bins
        ts = df["timestamp"].to_numpy()
        # 100 bins over 0..999900
        bins = (ts // 10000).astype(int)  # 100 bins
        df_tmp = pd.DataFrame({"bin": bins, "mid": mid})
        df_tmp["ret"] = df_tmp["mid"].diff()
        intraday = df_tmp.groupby("bin").agg(mean_ret=("ret", "mean"),
                                              vol=("ret", "std"),
                                              mean_mid=("mid", "mean")).reset_index()
        intraday.to_csv(INTRA / f"{product}.csv", index=False)
        intraday_mean_ret_std = float(intraday["mean_ret"].std())
        intraday_mean_ret_max = float(intraday["mean_ret"].abs().max())

        # Cross-day autocorr: corr(end_d, start_d+1)
        cross = []
        for a in range(len(ds) - 1):
            mid_a = df.loc[df["day"] == ds[a], "mid_price"].to_numpy()
            mid_b = df.loc[df["day"] == ds[a + 1], "mid_price"].to_numpy()
            if len(mid_a) > 100 and len(mid_b) > 100:
                end_drift = mid_a[-100:].mean() - mid_a[-200:-100].mean()
                start_drift = mid_b[100:200].mean() - mid_b[:100].mean()
                cross.append((end_drift, start_drift))
        if cross:
            arr = np.array(cross)
            if arr.shape[0] > 1:
                cross_corr = float(np.corrcoef(arr[:, 0], arr[:, 1])[0, 1])
            else:
                cross_corr = float(arr[0, 0] * arr[0, 1])
        else:
            cross_corr = float("nan")

        rows.append({
            "product": product,
            "group": group_of(product),
            "ou_mu": mu, "ou_theta": theta, "ou_sigma": sigma, "ou_half_life": hl,
            "ar_best_p": best_p, "ar1_coef": ar1, "ar_best_bic": best_bic,
            "hmm_persistence": p_persist,
            "hmm_mean0": means[0], "hmm_mean1": means[1],
            "hmm_vol0": vols[0], "hmm_vol1": vols[1],
            "cusum_n_changes": n_change,
            "ks_min_p": ks_min_p, "ks_mean_p": ks_mean_p,
            "intraday_meanret_std": intraday_mean_ret_std,
            "intraday_meanret_absmax": intraday_mean_ret_max,
            "cross_day_drift_corr": cross_corr,
        })
        if i % 10 == 0 or i == len(ROUND5_PRODUCTS):
            print(f"[{i}/{len(ROUND5_PRODUCTS)}] {product}  ar_p={best_p}  hl={hl:.0f}")

    pd.DataFrame(rows).to_csv(OUT / "stat_summary.csv", index=False)
    append_log(f"Phase4 DONE")
    print("Phase 4 done.")


if __name__ == "__main__":
    main()
