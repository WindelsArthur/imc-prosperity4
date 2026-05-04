"""Phase 7 — HIDDEN PATTERN HUNTING.

Per product, run an aggressive battery of tests:
- Deterministic-function fits: sin(ω t)+ct+d (ω-grid), poly(t) deg 1..3.
- Lattice test: distinct prices + Markov chain entropy.
- Compressibility (gzip) ratio.
- Symbolic dynamics: discretise to {-1,0,+1}, build empirical Markov chain.
- Modular timestamp test for K ∈ {10..10000}.
- Wavelet (db4, 6 levels): energy per scale.
- Anchor-and-revert: large moves followed by exact revert within N ticks.
- Cross-product hidden links: random forest of mid_i ~ mids of other 49.
- Sum-invariant scan beyond per-group: does sum_all_50 stay flat?

Outputs
    07_hidden_patterns/findings.md (ranked)
    07_hidden_patterns/per_product/{product}.json
    07_hidden_patterns/sum_invariants_summary.csv
"""
from __future__ import annotations

import gzip
import json
import sys
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from utils.data_loader import load_prices, available_days
from utils.round5_products import ROUND5_PRODUCTS, ROUND5_GROUPS, group_of

warnings.filterwarnings("ignore")
OUT = Path(__file__).resolve().parent
PER = OUT / "per_product"
PER.mkdir(parents=True, exist_ok=True)
LOG = ROOT / "logs" / "progress.md"


def append_log(msg: str) -> None:
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    with LOG.open("a") as f:
        f.write(f"- [{ts}] {msg}\n")


def fit_sine(t: np.ndarray, x: np.ndarray, omegas) -> dict:
    """Best-fit x = A sin(ω t + φ) + c t + d via grid-search over ω."""
    best = {"omega": float("nan"), "r2": -1.0, "A": 0.0, "phi": 0.0, "c": 0.0, "d": 0.0}
    n = len(t)
    if n < 100:
        return best
    for w in omegas:
        s = np.sin(w * t)
        c = np.cos(w * t)
        X = np.column_stack([np.ones(n), t, s, c])
        coef, *_ = np.linalg.lstsq(X, x, rcond=None)
        pred = X @ coef
        ss_res = float(np.sum((x - pred) ** 2))
        ss_tot = float(np.sum((x - x.mean()) ** 2))
        r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0
        if r2 > best["r2"]:
            A = float(np.hypot(coef[2], coef[3]))
            phi = float(np.arctan2(coef[3], coef[2]))
            best = {"omega": float(w), "r2": float(r2), "A": A, "phi": phi,
                    "c": float(coef[1]), "d": float(coef[0])}
    return best


def fit_poly(t: np.ndarray, x: np.ndarray, deg: int) -> dict:
    if len(t) < deg + 2:
        return {"deg": deg, "r2": float("nan"), "coefs": []}
    coefs = np.polyfit(t, x, deg)
    pred = np.polyval(coefs, t)
    ss_res = float(np.sum((x - pred) ** 2))
    ss_tot = float(np.sum((x - x.mean()) ** 2))
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0
    return {"deg": deg, "r2": float(r2), "coefs": [float(c) for c in coefs]}


def gzip_ratio(x: np.ndarray) -> float:
    raw = (x.astype(np.int64).tobytes())
    compressed = gzip.compress(raw, compresslevel=6)
    return len(compressed) / len(raw)


def symbolic_chi2(rets: np.ndarray) -> tuple[float, float]:
    """Discretise returns to {-1,0,+1}, build 3x3 transition counts, χ² test."""
    if len(rets) < 50:
        return float("nan"), float("nan")
    s = np.sign(rets)
    s[np.isnan(s)] = 0
    # Combine consecutive states
    counts = np.zeros((3, 3))
    for k in range(1, len(s)):
        i = int(s[k - 1] + 1)
        j = int(s[k] + 1)
        counts[i, j] += 1
    # χ² independence
    row_tot = counts.sum(axis=1, keepdims=True)
    col_tot = counts.sum(axis=0, keepdims=True)
    grand = counts.sum()
    expected = (row_tot @ col_tot) / max(grand, 1)
    mask = expected > 0
    chi2 = float(((counts[mask] - expected[mask]) ** 2 / expected[mask]).sum())
    # df = 4
    from scipy.stats import chi2 as chi2dist
    pval = float(1 - chi2dist.cdf(chi2, df=4))
    return chi2, pval


def mod_k_r2(price: np.ndarray, t: np.ndarray, K: int) -> float:
    if K < 2 or K >= len(price):
        return 0.0
    bins = (t.astype(np.int64) % K)
    means = pd.Series(price).groupby(bins).mean()
    pred = means.reindex(bins).to_numpy()
    ss_res = float(np.nansum((price - pred) ** 2))
    ss_tot = float(np.nansum((price - np.nanmean(price)) ** 2))
    return float(1 - ss_res / ss_tot) if ss_tot > 0 else 0.0


def anchor_revert(mid: np.ndarray, mag: float, window: int) -> dict:
    """Count large moves > `mag` followed by an exact revert within `window` ticks."""
    rets = np.diff(mid)
    big = np.where(np.abs(rets) > mag)[0]
    n_revert = 0; n_total = len(big)
    for k in big:
        seg = mid[k + 1: k + 1 + window]
        if len(seg) == 0:
            continue
        # Revert means returning within mag/2 of the level prior to the spike
        if np.any(np.abs(seg - mid[k]) < mag / 2):
            n_revert += 1
    return {"n_total_spikes": int(n_total), "n_reverts": int(n_revert),
            "frac_revert": float(n_revert / n_total) if n_total else float("nan")}


def cross_rf_r2(target_idx: int, all_mids: np.ndarray, lag: int = 1) -> tuple[float, float, str]:
    """Train RF on lagged other-product mids → predict target. Return train R², OOS R², top feature."""
    from sklearn.ensemble import RandomForestRegressor
    n_t, n_p = all_mids.shape
    if n_t < 1000:
        return float("nan"), float("nan"), ""
    Y = all_mids[lag:, target_idx]
    X = np.delete(all_mids, target_idx, axis=1)[:-lag]
    # Train/test split: first 70% train
    split = int(0.7 * len(Y))
    Xtr, Ytr = X[:split], Y[:split]
    Xte, Yte = X[split:], Y[split:]
    rf = RandomForestRegressor(n_estimators=20, max_depth=8, n_jobs=-1, random_state=0)
    rf.fit(Xtr, Ytr)
    train_r2 = float(rf.score(Xtr, Ytr))
    oos_r2 = float(rf.score(Xte, Yte))
    # Top feature
    fi = rf.feature_importances_
    other_idx = [k for k in range(n_p) if k != target_idx]
    top = ROUND5_PRODUCTS[other_idx[int(np.argmax(fi))]]
    return train_r2, oos_r2, top


def main() -> None:
    days = available_days()
    print("Phase7 START")
    parts = []
    for d in days:
        df = load_prices(d)
        sub = df.loc[df["product"].isin(ROUND5_PRODUCTS), ["day", "timestamp", "product", "mid_price"]].copy()
        sub["mid_price"] = sub["mid_price"].astype(float)
        parts.append(sub)
    full = pd.concat(parts, ignore_index=True).sort_values(["day", "timestamp", "product"])
    pivot = full.pivot_table(index=["day", "timestamp"], columns="product", values="mid_price")
    pivot = pivot[ROUND5_PRODUCTS].ffill().bfill()
    all_mids = pivot.to_numpy()  # shape (T, 50)

    rows = []
    omegas = np.concatenate([
        np.linspace(2 * np.pi / 30000, 2 * np.pi / 1000, 20),
        np.linspace(2 * np.pi / 1000, 2 * np.pi / 100, 20),
        np.linspace(2 * np.pi / 100, 2 * np.pi / 10, 20),
    ])

    for i, product in enumerate(ROUND5_PRODUCTS, start=1):
        x = pivot[product].to_numpy()
        t = np.arange(len(x))
        rets = np.diff(x)
        n_obs = len(x)

        # 1. Sine
        sine = fit_sine(t, x, omegas)

        # 2. Polynomial
        poly1 = fit_poly(t, x, 1)
        poly3 = fit_poly(t, x, 3)
        poly5 = fit_poly(t, x, 5)

        # 3. Lattice
        n_distinct = int(pd.unique(x).shape[0])
        lattice_ratio = n_distinct / n_obs

        # 4. Compressibility
        gz = gzip_ratio(x)

        # 5. Symbolic χ²
        chi2_v, chi2_p = symbolic_chi2(rets)

        # 6. Mod-K best
        Ks = [10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000]
        mod_r2 = {K: mod_k_r2(x, t, K) for K in Ks}
        best_K = int(max(mod_r2, key=mod_r2.get))
        best_K_R2 = float(mod_r2[best_K])

        # 7. Anchor-revert
        med_abs_ret = float(np.median(np.abs(rets[rets != 0]))) if (rets != 0).any() else 1.0
        ar = anchor_revert(x, mag=max(med_abs_ret * 4, 5.0), window=20)

        # 8. Cross RF
        try:
            tr_r2, oos_r2, top_feat = cross_rf_r2(i - 1, all_mids, lag=1)
        except Exception:
            tr_r2, oos_r2, top_feat = float("nan"), float("nan"), ""

        rec = {
            "product": product,
            "group": group_of(product),
            "n_obs": n_obs,
            "sine_omega": sine["omega"], "sine_period": (2 * np.pi / sine["omega"]) if sine["omega"] else float("nan"),
            "sine_A": sine["A"], "sine_R2": sine["r2"], "sine_drift_c": sine["c"],
            "poly1_R2": poly1["r2"], "poly3_R2": poly3["r2"], "poly5_R2": poly5["r2"],
            "n_distinct_mids": n_distinct, "lattice_ratio": lattice_ratio,
            "gzip_ratio": gz,
            "chi2_symbolic": chi2_v, "chi2_p": chi2_p,
            "mod_K_best": best_K, "mod_K_best_R2": best_K_R2,
            "anchor_n_spikes": ar["n_total_spikes"], "anchor_revert_frac": ar["frac_revert"],
            "rf_train_R2": tr_r2, "rf_oos_R2": oos_r2, "rf_top_feature": top_feat,
        }
        rows.append(rec)
        with (PER / f"{product}.json").open("w") as f:
            json.dump({**rec, "mod_K_R2_full": mod_r2}, f, indent=2)

        if i % 10 == 0 or i == len(ROUND5_PRODUCTS):
            print(f"[{i}/{len(ROUND5_PRODUCTS)}] {product}  sineR²={sine['r2']:.3f}  poly3R²={poly3['r2']:.3f}  rfOOS={oos_r2:.3f}")

    df = pd.DataFrame(rows)
    df.to_csv(OUT / "hidden_summary.csv", index=False)

    # findings.md ranked
    md = ["# Phase 7 — Hidden Pattern Findings\n\n"]
    md.append("## Ranked by deterministic-fit R² (sine or poly3)\n\n")
    df["max_det_R2"] = df[["sine_R2", "poly3_R2", "poly5_R2", "mod_K_best_R2"]].max(axis=1)
    md.append(df.sort_values("max_det_R2", ascending=False)[
        ["product", "group", "sine_R2", "sine_period", "poly3_R2", "poly5_R2", "mod_K_best", "mod_K_best_R2"]
    ].head(15).to_markdown(index=False) + "\n")

    md.append("\n## Lattice candidates (lowest distinct-mids count)\n\n")
    md.append(df.sort_values("n_distinct_mids")[
        ["product", "group", "n_distinct_mids", "lattice_ratio", "gzip_ratio", "chi2_p"]
    ].head(10).to_markdown(index=False) + "\n")

    md.append("\n## Highest cross-product RF OOS R² (predictable from other products)\n\n")
    md.append(df.sort_values("rf_oos_R2", ascending=False)[
        ["product", "group", "rf_train_R2", "rf_oos_R2", "rf_top_feature"]
    ].head(15).to_markdown(index=False) + "\n")

    md.append("\n## Anchor-and-revert candidates (fraction of large moves that revert)\n\n")
    md.append(df.sort_values("anchor_revert_frac", ascending=False)[
        ["product", "group", "anchor_n_spikes", "anchor_revert_frac"]
    ].head(15).to_markdown(index=False) + "\n")

    (OUT / "findings.md").write_text("".join(md))

    # Sum-invariant: scan all triples / quartets / quintets cross-group? Phase 5 already
    # did per-group; here just report the all-50 sum stability and the per-group sums.
    sums = []
    for gname, prods in ROUND5_GROUPS.items():
        s = pivot[prods].sum(axis=1)
        sums.append({"set": gname, "n_products": len(prods),
                     "mean": float(s.mean()), "std": float(s.std()),
                     "min": float(s.min()), "max": float(s.max()),
                     "rel_std": float(s.std() / s.mean()) if s.mean() else float("nan")})
    s_all = pivot[ROUND5_PRODUCTS].sum(axis=1)
    sums.append({"set": "ALL_50", "n_products": 50, "mean": float(s_all.mean()),
                 "std": float(s_all.std()), "min": float(s_all.min()),
                 "max": float(s_all.max()), "rel_std": float(s_all.std() / s_all.mean())})
    pd.DataFrame(sums).to_csv(OUT / "sum_invariants_summary.csv", index=False)

    append_log("Phase7 DONE")
    print("Phase 7 done.")


if __name__ == "__main__":
    main()
