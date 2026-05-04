"""Phase A — exhaustive CCF atlas.

Vectorised FFT-based cross-correlation on returns, prices, and OFI for every
ordered pair of the 50 R5 products at lags k ∈ [-200, 200].

Key design points
- We compute *standardised* cross-correlation: ρ_xy(k) = Cov(x_t, y_{t+k}) / (σ_x σ_y).
  Convention used here: a positive k means y leads x by k ticks (i.e. y(t-k)
  predicts x(t)). We will therefore treat positive k as "the second product
  lags the first" → first product leads.
- We work *within day*: stitching across the 5-2 / 5-3 / 5-4 boundary would
  produce spurious correlations from carry-overs. CCFs are computed per day
  and AVERAGED (weighted by len-2k).
- Bonferroni-corrected significance threshold for ~50·49·401 = 982,450 tests:
  α = 0.05 / N → critical |z| ≈ 5.8 → for N≈10,000 obs, |ρ_crit| ≈ 0.058.

Outputs
    A_atlas/ccf_returns.parquet   long-form (i, j, lag, rho)
    A_atlas/ccf_prices.parquet
    A_atlas/ccf_ofi.parquet
    A_atlas/peak_summary.csv      (i, j, peak_rho_returns, peak_lag_returns, ...)
    A_atlas/heatmap_returns.png
    A_atlas/top100_leadlag.csv    candidates for Phase B (k* > 0, |ρ| highest)
"""
from __future__ import annotations

import sys
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from utils.data_loader import load_prices, available_days
from utils.round5_products import ROUND5_PRODUCTS, group_of

warnings.filterwarnings("ignore")
OUT = Path(__file__).resolve().parent
LOG = ROOT / "logs" / "progress.md"

MAX_LAG = 200
LAGS_FINE = list(range(-50, 51))               # 1-tick spacing |k|≤50
LAGS_COARSE = [k for k in range(-MAX_LAG, MAX_LAG + 1, 5)
               if abs(k) > 50]                 # 5-tick spacing 50<|k|≤200
LAGS_ALL = sorted(set(LAGS_FINE) | set(LAGS_COARSE))
N_LAGS = len(LAGS_ALL)


def append_log(msg: str) -> None:
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    with LOG.open("a") as f:
        f.write(f"- [{ts}] {msg}\n")


def fft_xcorr_full(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    """Full cross-correlation ρ_xy(k) for k ∈ [-(n-1), n-1]. Standardised
    (so ρ ∈ [-1,1] only at k=0; for |k|>0 the divisor uses σ from the
    overlapped subsamples for unbiased magnitude).

    We use the *biased* estimator scaled by σ_xσ_y of the full series, which
    is fast and consistent. Slight underestimate at large |k|. Adequate for
    ranking lead-lag candidates.
    """
    n = len(x)
    x = x - x.mean()
    y = y - y.mean()
    sx = x.std(ddof=0)
    sy = y.std(ddof=0)
    if sx == 0 or sy == 0:
        return np.zeros(2 * n - 1)
    # numpy correlate "full" returns Σ_t x[t+k] y[t]; result length 2n-1.
    # Index 0 corresponds to lag = -(n-1); index n-1 is lag 0; index 2n-2 is lag n-1.
    raw = np.correlate(x, y, mode="full")  # not FFT yet
    # Use FFT: faster
    n_fft = 1 << int(np.ceil(np.log2(2 * n)))
    fx = np.fft.rfft(x, n_fft)
    fy = np.fft.rfft(y, n_fft)
    raw = np.fft.irfft(fx * np.conjugate(fy), n_fft)[: 2 * n - 1]
    raw = np.concatenate([raw[-(n - 1):], raw[:n]])  # rearrange to [-(n-1), 0, ..., n-1]
    return raw / (n * sx * sy)


def fft_xcorr_at_lags(x: np.ndarray, y: np.ndarray, lags: list[int]) -> np.ndarray:
    """Return ρ_xy at the requested integer lags only, computed via FFT once."""
    n = len(x)
    full = fft_xcorr_full(x, y)
    # Map lag k → index = n - 1 + k
    idx = np.array([n - 1 + k for k in lags], dtype=int)
    idx = np.clip(idx, 0, len(full) - 1)
    return full[idx]


def stitch_per_day(prices_by_day: dict, product: str) -> dict:
    """Return {day: mid array} ffilled."""
    out = {}
    for d, df in prices_by_day.items():
        sub = df.loc[df["product"] == product].sort_values("timestamp")
        out[d] = sub["mid_price"].astype(float).ffill().bfill().to_numpy()
    return out


def stitch_ofi_per_day(prices_by_day: dict, product: str) -> dict:
    """Build per-day L1 OFI from the price table."""
    out = {}
    for d, df in prices_by_day.items():
        sub = df.loc[df["product"] == product].sort_values("timestamp").reset_index(drop=True)
        bp = sub["bid_price_1"].ffill().to_numpy()
        bv = sub["bid_volume_1"].fillna(0).to_numpy().astype(float)
        ap = sub["ask_price_1"].ffill().to_numpy()
        av = sub["ask_volume_1"].fillna(0).to_numpy().astype(float)
        n = len(bp)
        e_bid = np.zeros(n)
        e_ask = np.zeros(n)
        for k in range(1, n):
            if bp[k] > bp[k - 1]:
                e_bid[k] = bv[k]
            elif bp[k] == bp[k - 1]:
                e_bid[k] = bv[k] - bv[k - 1]
            else:
                e_bid[k] = -bv[k - 1]
            if ap[k] < ap[k - 1]:
                e_ask[k] = av[k]
            elif ap[k] == ap[k - 1]:
                e_ask[k] = av[k] - av[k - 1]
            else:
                e_ask[k] = -av[k - 1]
        out[d] = e_bid - e_ask
    return out


def main() -> None:
    days = available_days()
    print("Phase A start. Days:", days)
    t0 = time.time()
    prices_by_day = {d: load_prices(d) for d in days}

    # Build per-day matrices: (n, P) for prices, returns, ofi.
    print("Stitching per-day arrays...")
    mid_by_day = {d: {} for d in days}
    ret_by_day = {d: {} for d in days}
    ofi_by_day = {d: {} for d in days}
    for prod in ROUND5_PRODUCTS:
        midmap = stitch_per_day(prices_by_day, prod)
        for d in days:
            mid_by_day[d][prod] = midmap[d]
            ret_by_day[d][prod] = np.diff(midmap[d])
        ofimap = stitch_ofi_per_day(prices_by_day, prod)
        for d in days:
            ofi_by_day[d][prod] = ofimap[d]

    # For each ordered pair (i, j), compute CCF on returns, prices, OFI per day, then average
    n_prods = len(ROUND5_PRODUCTS)
    rows_ret = []
    rows_pr = []
    rows_ofi = []
    peaks = []

    print(f"Computing CCFs for {n_prods*(n_prods-1)} ordered pairs × {N_LAGS} lags × 3 series ...")
    for i, pi in enumerate(ROUND5_PRODUCTS):
        for j, pj in enumerate(ROUND5_PRODUCTS):
            if i == j:
                continue
            # Compute per-day rho(lag) on each of (returns, prices, ofi), avg
            ret_rhos = np.zeros(N_LAGS)
            pr_rhos = np.zeros(N_LAGS)
            ofi_rhos = np.zeros(N_LAGS)
            n_days = 0
            for d in days:
                xr = ret_by_day[d][pi]; yr = ret_by_day[d][pj]
                xp = mid_by_day[d][pi][1:]; yp = mid_by_day[d][pj][1:]
                xo = ofi_by_day[d][pi]; yo = ofi_by_day[d][pj]
                if len(xr) < 4 * MAX_LAG:
                    continue
                # Returns
                ret_rhos += fft_xcorr_at_lags(xr, yr, LAGS_ALL)
                pr_rhos += fft_xcorr_at_lags(xp, yp, LAGS_ALL)
                ofi_rhos += fft_xcorr_at_lags(xo, yo, LAGS_ALL)
                n_days += 1
            if n_days == 0:
                continue
            ret_rhos /= n_days
            pr_rhos /= n_days
            ofi_rhos /= n_days

            # Append rows in long form for parquet
            for k_idx, k in enumerate(LAGS_ALL):
                rows_ret.append((pi, pj, k, float(ret_rhos[k_idx])))
                rows_pr.append((pi, pj, k, float(pr_rhos[k_idx])))
                rows_ofi.append((pi, pj, k, float(ofi_rhos[k_idx])))

            # Peak summary
            kr_idx = int(np.argmax(np.abs(ret_rhos)))
            kp_idx = int(np.argmax(np.abs(pr_rhos)))
            ko_idx = int(np.argmax(np.abs(ofi_rhos)))
            peaks.append({
                "i": pi, "j": pj,
                "group_i": group_of(pi), "group_j": group_of(pj),
                "peak_lag_returns": int(LAGS_ALL[kr_idx]),
                "peak_rho_returns": float(ret_rhos[kr_idx]),
                "peak_lag_prices": int(LAGS_ALL[kp_idx]),
                "peak_rho_prices": float(pr_rhos[kp_idx]),
                "peak_lag_ofi": int(LAGS_ALL[ko_idx]),
                "peak_rho_ofi": float(ofi_rhos[ko_idx]),
            })
        if i % 5 == 0:
            elapsed = time.time() - t0
            print(f"  {i+1}/{n_prods} products done. {elapsed:.1f}s elapsed")

    # Save long parquets
    print("Saving parquets...")
    pd.DataFrame(rows_ret, columns=["i", "j", "lag", "rho"]).to_parquet(OUT / "ccf_returns.parquet", index=False)
    pd.DataFrame(rows_pr, columns=["i", "j", "lag", "rho"]).to_parquet(OUT / "ccf_prices.parquet", index=False)
    pd.DataFrame(rows_ofi, columns=["i", "j", "lag", "rho"]).to_parquet(OUT / "ccf_ofi.parquet", index=False)
    peaks_df = pd.DataFrame(peaks)
    peaks_df.to_csv(OUT / "peak_summary.csv", index=False)

    # Bonferroni threshold (returns, n ~ 10000):
    n_obs = 9999
    n_tests = len(peaks) * N_LAGS
    z_crit = float(np.abs(np.sqrt(2) * np.sqrt(np.log(n_tests / 0.05)) / np.sqrt(2)))
    rho_crit = z_crit / np.sqrt(n_obs)

    # Top-100 lead-lag pairs (k* > 0 → i leads j by k*)
    # Note our convention: ρ_xy(k) = E[x_t y_{t+k}], so k > 0 means y(t+k) regressed on x(t).
    # Therefore "i leads j" if peak lag > 0 → x(t) (= return_i(t)) predicts y(t+k) (= return_j).
    leadlag = peaks_df.copy()
    leadlag["abs_rho_returns"] = leadlag["peak_rho_returns"].abs()
    # Filter both lags > 0 (proper lead-lag) and large |rho|
    cand = leadlag[leadlag["peak_lag_returns"] > 0].sort_values("abs_rho_returns", ascending=False).head(100)
    cand.to_csv(OUT / "top100_leadlag.csv", index=False)

    # Heatmap of |peak_rho_returns|
    matrix = np.zeros((n_prods, n_prods))
    lag_matrix = np.zeros((n_prods, n_prods), dtype=int)
    name_to_idx = {p: k for k, p in enumerate(ROUND5_PRODUCTS)}
    for r in peaks:
        matrix[name_to_idx[r["i"]], name_to_idx[r["j"]]] = abs(r["peak_rho_returns"])
        lag_matrix[name_to_idx[r["i"]], name_to_idx[r["j"]]] = r["peak_lag_returns"]
    fig, ax = plt.subplots(figsize=(14, 12))
    im = ax.imshow(matrix, cmap="hot", vmin=0, vmax=min(0.5, matrix.max()))
    ax.set_xticks(range(n_prods)); ax.set_yticks(range(n_prods))
    ax.set_xticklabels(ROUND5_PRODUCTS, rotation=90, fontsize=5)
    ax.set_yticklabels(ROUND5_PRODUCTS, fontsize=5)
    fig.colorbar(im, ax=ax, label="|peak ρ| on returns")
    ax.set_title(f"|peak ρ| on returns (Bonferroni ρ_crit ≈ {rho_crit:.3f})")
    fig.tight_layout()
    fig.savefig(OUT / "heatmap_returns.png", dpi=80)
    plt.close(fig)

    md = ["# Phase A — CCF Atlas\n\n",
          f"- N pairs (ordered): {len(peaks)}\n",
          f"- Lags tested: {N_LAGS} (range -{MAX_LAG}..+{MAX_LAG}; fine ±50, coarse 5-step beyond)\n",
          f"- Bonferroni-corrected critical |ρ|: {rho_crit:.4f}\n\n",
          "## Top 30 lead-lag candidates (k* > 0, ranked by |ρ| on returns)\n\n",
          cand.head(30)[["i", "j", "group_i", "group_j", "peak_lag_returns", "peak_rho_returns",
                          "peak_rho_prices"]].to_markdown(index=False) + "\n",
    ]
    (OUT / "decision.md").write_text("".join(md))
    elapsed = time.time() - t0
    append_log(f"PhaseA DONE — {len(peaks)} pairs, {elapsed:.0f}s elapsed; "
               f"top peak |ρ|={leadlag['abs_rho_returns'].max():.3f}; "
               f"Bonferroni ρ_crit={rho_crit:.4f}")
    print(f"Phase A done in {elapsed:.0f}s")


if __name__ == "__main__":
    main()
