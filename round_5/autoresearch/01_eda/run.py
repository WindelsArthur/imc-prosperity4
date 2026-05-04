"""Phase 1 — Per-product univariate EDA.

For each of 50 R5 products: load days 2-4 stitched, run a battery of stats
(returns dist, ADF/KPSS, ACF/PACF, Hurst, VR, OU half-life, FFT, spread,
tick-grid mod-K) and dump a 6-panel PNG + a single per-product row in a
master CSV.

Output
    01_eda/per_product/{product}/summary.png
    01_eda/per_product_summary.csv
"""
from __future__ import annotations

import os
import sys
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from utils.data_loader import load_prices, available_days
from utils.round5_products import ROUND5_PRODUCTS, group_of
from utils.stats import (
    adf_test, kpss_test, hurst_dfa, ou_half_life,
    lo_mackinlay_var_ratio, jarque_bera, arch_lm,
)

OUT = Path(__file__).resolve().parent
PER_DIR = OUT / "per_product"
PER_DIR.mkdir(parents=True, exist_ok=True)

LOG = ROOT / "logs" / "progress.md"
warnings.filterwarnings("ignore")


def append_log(msg: str) -> None:
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    with LOG.open("a") as f:
        f.write(f"- [{ts}] {msg}\n")


def stitch_product(prices_by_day: dict[int, pd.DataFrame], product: str) -> pd.DataFrame:
    """Concatenate days for one product, sort, reset_index. Adds 'global_t' tick index."""
    parts = []
    days = sorted(prices_by_day.keys())
    for d in days:
        df = prices_by_day[d]
        sub = df.loc[df["product"] == product, [
            "day", "timestamp", "bid_price_1", "bid_volume_1",
            "bid_price_2", "bid_volume_2", "bid_price_3", "bid_volume_3",
            "ask_price_1", "ask_volume_1", "ask_price_2", "ask_volume_2",
            "ask_price_3", "ask_volume_3", "mid_price", "profit_and_loss",
        ]].copy()
        parts.append(sub)
    out = pd.concat(parts, ignore_index=True)
    out = out.sort_values(["day", "timestamp"]).reset_index(drop=True)
    out["global_t"] = np.arange(len(out))
    return out


def weighted_mid(row) -> float:
    bp1, bv1 = row["bid_price_1"], row["bid_volume_1"]
    ap1, av1 = row["ask_price_1"], row["ask_volume_1"]
    if pd.isna(bp1) or pd.isna(ap1) or pd.isna(bv1) or pd.isna(av1):
        return row["mid_price"]
    if (bv1 + av1) <= 0:
        return (bp1 + ap1) / 2.0
    return (bp1 * av1 + ap1 * bv1) / (bv1 + av1)


def acf(x: np.ndarray, n_lags: int = 50) -> np.ndarray:
    n = len(x)
    x = x - x.mean()
    var = x.var()
    if var == 0:
        return np.zeros(n_lags + 1)
    out = np.zeros(n_lags + 1)
    for k in range(n_lags + 1):
        if k == 0:
            out[k] = 1.0
        else:
            out[k] = float(np.dot(x[:n - k], x[k:]) / ((n - k) * var))
    return out


def fft_top_freqs(x: np.ndarray, top: int = 3) -> list[tuple[float, float]]:
    """Return top-`top` (period, power) — period in ticks, power normalized."""
    n = len(x)
    if n < 16:
        return []
    x_d = x - np.mean(x)
    F = np.fft.rfft(x_d * np.hanning(n))
    p = np.abs(F) ** 2
    freqs = np.fft.rfftfreq(n, d=1.0)
    # skip DC
    idx = np.argsort(p[1:])[::-1][:top] + 1
    out = []
    total = float(p[1:].sum()) or 1.0
    for i in idx:
        if freqs[i] <= 0:
            continue
        period = 1.0 / freqs[i]
        out.append((float(period), float(p[i] / total)))
    return out


def mod_k_r2(price: np.ndarray, t: np.ndarray, K: int) -> float:
    """R² of price ~ (t mod K) using bin-mean predictor."""
    if K < 2 or K >= len(price):
        return 0.0
    bins = (t.astype(np.int64) % K)
    means = pd.Series(price).groupby(bins).mean()
    pred = means.reindex(bins).to_numpy()
    ss_res = float(np.nansum((price - pred) ** 2))
    ss_tot = float(np.nansum((price - np.nanmean(price)) ** 2))
    if ss_tot == 0:
        return 0.0
    return float(1.0 - ss_res / ss_tot)


def analyse_product(product: str, df: pd.DataFrame) -> dict:
    mid = df["mid_price"].astype(float).to_numpy()
    wmid = df.apply(weighted_mid, axis=1).astype(float).to_numpy()
    if np.all(np.isnan(mid)):
        return {"product": product, "skip_reason": "all nan mid"}
    # Fill rare nans in mid forward
    mid = pd.Series(mid).ffill().bfill().to_numpy()
    wmid = pd.Series(wmid).ffill().bfill().to_numpy()
    rets = np.diff(mid)
    log_rets = np.diff(np.log(np.where(mid > 0, mid, np.nan)))
    log_rets = log_rets[np.isfinite(log_rets)]

    spread = (df["ask_price_1"] - df["bid_price_1"]).astype(float).dropna().to_numpy()
    bid_depth = df[["bid_volume_1", "bid_volume_2", "bid_volume_3"]].fillna(0).sum(axis=1).to_numpy()
    ask_depth = df[["ask_volume_1", "ask_volume_2", "ask_volume_3"]].fillna(0).sum(axis=1).to_numpy()

    # Tick-grid analysis
    distinct_prices = int(pd.unique(mid).shape[0])
    # Mod-K test for K in some range
    Ks = [10, 50, 100, 200, 500, 1000, 2000, 5000, 10000]
    t = df["global_t"].to_numpy()
    mod_r2 = {K: mod_k_r2(mid, t, K) for K in Ks}
    best_K = max(mod_r2, key=mod_r2.get)
    best_K_R2 = mod_r2[best_K]

    out = {
        "product": product,
        "group": group_of(product),
        "n_obs": int(len(mid)),
        "mid_mean": float(np.nanmean(mid)),
        "mid_std": float(np.nanstd(mid)),
        "mid_min": float(np.nanmin(mid)),
        "mid_max": float(np.nanmax(mid)),
        "ret_mean": float(np.nanmean(rets)) if rets.size else float("nan"),
        "ret_std": float(np.nanstd(rets)) if rets.size else float("nan"),
        "n_distinct_mids": distinct_prices,
        "spread_mean": float(np.nanmean(spread)) if spread.size else float("nan"),
        "spread_median": float(np.nanmedian(spread)) if spread.size else float("nan"),
        "bid_depth_mean": float(np.nanmean(bid_depth)),
        "ask_depth_mean": float(np.nanmean(ask_depth)),
    }

    # Stationarity
    try:
        adf_p = adf_test(mid)
        out["adf_p_mid"] = adf_p["pvalue"]; out["adf_stationary_mid"] = adf_p["stationary_5pct"]
    except Exception:
        out["adf_p_mid"] = float("nan"); out["adf_stationary_mid"] = False
    try:
        adf_r = adf_test(rets)
        out["adf_p_ret"] = adf_r["pvalue"]
    except Exception:
        out["adf_p_ret"] = float("nan")
    try:
        kpss_p = kpss_test(mid)
        out["kpss_p_mid"] = kpss_p["pvalue"]; out["kpss_stationary_mid"] = kpss_p["stationary_5pct"]
    except Exception:
        out["kpss_p_mid"] = float("nan"); out["kpss_stationary_mid"] = False

    # Hurst
    try:
        out["hurst"] = hurst_dfa(mid)
    except Exception:
        out["hurst"] = float("nan")

    # OU half-life
    try:
        hl = ou_half_life(mid)
        out["ou_half_life"] = hl if np.isfinite(hl) else float("inf")
    except Exception:
        out["ou_half_life"] = float("inf")

    # Variance ratio
    for q in (2, 4, 8, 16, 32):
        try:
            vr = lo_mackinlay_var_ratio(mid, q=q)
            out[f"vr_{q}"] = vr["vr"]; out[f"vr_z_{q}"] = vr["z"]
        except Exception:
            out[f"vr_{q}"] = float("nan"); out[f"vr_z_{q}"] = float("nan")

    # Normality / ARCH
    try:
        jb = jarque_bera(rets)
        out["jb_p"] = jb["pvalue"]; out["skew"] = jb["skew"]; out["kurt"] = jb["kurtosis"]
    except Exception:
        out["jb_p"] = float("nan"); out["skew"] = float("nan"); out["kurt"] = float("nan")
    try:
        arch = arch_lm(rets, lags=10)
        out["arch_p"] = arch["lm_pvalue"]; out["arch_5pct"] = arch["arch_5pct"]
    except Exception:
        out["arch_p"] = float("nan"); out["arch_5pct"] = False

    # ACF on returns and squared returns at lag 1, 5, 20
    try:
        ac = acf(rets, n_lags=200)
        out["acf_ret_1"] = float(ac[1]); out["acf_ret_5"] = float(ac[5]); out["acf_ret_20"] = float(ac[20])
        ac2 = acf(rets ** 2, n_lags=200)
        out["acf_sqret_1"] = float(ac2[1]); out["acf_sqret_5"] = float(ac2[5])
    except Exception:
        out["acf_ret_1"] = float("nan")

    # FFT top freqs
    tops = fft_top_freqs(mid, top=3)
    if tops:
        out["fft_top_period"] = tops[0][0]; out["fft_top_power"] = tops[0][1]
    else:
        out["fft_top_period"] = float("nan"); out["fft_top_power"] = float("nan")

    # Mod-K
    out["mod_K_best"] = int(best_K)
    out["mod_K_best_R2"] = float(best_K_R2)
    for K, r2 in mod_r2.items():
        out[f"mod_K_R2_{K}"] = float(r2)

    # 6-panel PNG
    plot_dir = PER_DIR / product
    plot_dir.mkdir(parents=True, exist_ok=True)
    try:
        fig, axes = plt.subplots(2, 3, figsize=(15, 8))
        axes[0, 0].plot(mid, lw=0.4)
        axes[0, 0].set_title(f"{product}: mid (stitched 2-4)")
        axes[0, 0].axvline(len(mid) // 3, color="r", lw=0.4)
        axes[0, 0].axvline(2 * len(mid) // 3, color="r", lw=0.4)

        axes[0, 1].hist(rets, bins=60, alpha=0.8)
        axes[0, 1].set_title(f"returns hist (skew={out['skew']:.2f} kurt={out['kurt']:.2f})")

        axes[0, 2].plot(np.arange(0, 51), acf(rets, 50), marker=".", lw=0.5)
        axes[0, 2].axhline(0, color="k", lw=0.3)
        axes[0, 2].set_title("ACF(returns) lags 0..50")

        axes[1, 0].plot(np.arange(0, 51), acf(rets ** 2, 50), marker=".", lw=0.5)
        axes[1, 0].axhline(0, color="k", lw=0.3)
        axes[1, 0].set_title("ACF(squared returns)")

        # FFT
        n = len(mid)
        F = np.abs(np.fft.rfft((mid - mid.mean()) * np.hanning(n)))
        freqs = np.fft.rfftfreq(n, d=1.0)
        axes[1, 1].loglog(freqs[1:], F[1:] + 1e-12, lw=0.5)
        axes[1, 1].set_title("FFT |F| (log-log)")

        # mod-K R2
        ks = list(mod_r2.keys())
        r2s = [mod_r2[k] for k in ks]
        axes[1, 2].bar([str(k) for k in ks], r2s)
        axes[1, 2].set_title(f"mod-K R² (best K={best_K} R²={best_K_R2:.3f})")
        axes[1, 2].tick_params(axis="x", labelrotation=45)

        fig.suptitle(
            f"{product} | n={len(mid)} | adf_p={out['adf_p_mid']:.3f} | hurst={out['hurst']:.3f} | "
            f"OU_HL={out['ou_half_life']:.0f}",
        )
        fig.tight_layout()
        fig.savefig(plot_dir / "summary.png", dpi=80)
        plt.close(fig)
    except Exception as e:
        out["plot_error"] = str(e)

    return out


def main() -> None:
    days = available_days()
    append_log(f"Phase1 START — products={len(ROUND5_PRODUCTS)} days={days}")
    prices_by_day = {d: load_prices(d) for d in days}

    rows = []
    for i, product in enumerate(ROUND5_PRODUCTS, start=1):
        t0 = time.time()
        df = stitch_product(prices_by_day, product)
        try:
            stats = analyse_product(product, df)
        except Exception as e:
            stats = {"product": product, "error": str(e)}
        rows.append(stats)
        if i % 10 == 0 or i == len(ROUND5_PRODUCTS):
            append_log(f"Phase1 progress {i}/{len(ROUND5_PRODUCTS)} last={product} t={time.time()-t0:.1f}s")
            print(f"[{i}/{len(ROUND5_PRODUCTS)}] {product} ok ({time.time()-t0:.1f}s)")

    df_out = pd.DataFrame(rows)
    df_out.to_csv(OUT / "per_product_summary.csv", index=False)
    append_log(f"Phase1 DONE — wrote per_product_summary.csv rows={len(df_out)}")
    print(f"Phase 1 complete. {len(df_out)} rows -> per_product_summary.csv")


if __name__ == "__main__":
    main()
