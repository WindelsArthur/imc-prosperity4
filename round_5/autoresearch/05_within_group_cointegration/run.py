"""Phase 5 — Within-group cross-product (10 groups × 5).

Per group:
- 5×5 return correlation + price correlation.
- Engle-Granger pairwise cointegration + Johansen on full 5-vector.
- For each cointegrated pair (and basket residual): OU on spread, half-life,
  z-score series, simple z-reversion strategy walk-forward Sharpe (day2->3, 2+3->4).
- Lead-lag CCF at lags ±1..±20.
- Group PCA.
- Identify any "basket residual" product.

Outputs
    05_cross_product/groups/{group}/corr.csv, ccf.csv, coint.csv,
                                    pca.csv, basket_residual.csv, summary.md
    05_cross_product/group_summary.csv  (one-row-per-group)
"""
from __future__ import annotations

import sys
import time
import warnings
from pathlib import Path
from itertools import combinations

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from utils.data_loader import load_prices, available_days
from utils.round5_products import ROUND5_GROUPS

warnings.filterwarnings("ignore")
OUT = Path(__file__).resolve().parent
GROUP_DIR = OUT / "groups"
GROUP_DIR.mkdir(parents=True, exist_ok=True)
LOG = ROOT / "logs" / "progress.md"


def append_log(msg: str) -> None:
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    with LOG.open("a") as f:
        f.write(f"- [{ts}] {msg}\n")


def stitch_group(prices_by_day, products):
    parts = []
    for d in sorted(prices_by_day.keys()):
        df = prices_by_day[d]
        sub = df.loc[df["product"].isin(products), ["day", "timestamp", "product", "mid_price"]].copy()
        sub["mid_price"] = sub["mid_price"].astype(float)
        parts.append(sub)
    out = pd.concat(parts, ignore_index=True)
    out = out.sort_values(["day", "timestamp", "product"]).reset_index(drop=True)
    pivot = out.pivot_table(index=["day", "timestamp"], columns="product", values="mid_price").reset_index()
    pivot.columns.name = None
    return pivot


def engle_granger_p(y: np.ndarray, x: np.ndarray) -> tuple[float, float, float]:
    """OLS y on x, ADF on residual. Return (slope, intercept, adf_pvalue)."""
    from statsmodels.tsa.stattools import adfuller
    mask = np.isfinite(y) & np.isfinite(x)
    if mask.sum() < 100:
        return float("nan"), float("nan"), float("nan")
    y, x = y[mask], x[mask]
    a = np.column_stack([np.ones_like(x), x])
    coef, *_ = np.linalg.lstsq(a, y, rcond=None)
    resid = y - (coef[0] + coef[1] * x)
    try:
        adf = adfuller(resid, autolag="AIC")
        pval = float(adf[1])
    except Exception:
        pval = float("nan")
    return float(coef[1]), float(coef[0]), pval


def ou_half_life(x: np.ndarray) -> float:
    if len(x) < 4:
        return float("inf")
    x_lag = x[:-1]; dx = np.diff(x)
    X = np.column_stack([np.ones_like(x_lag), x_lag])
    coef, *_ = np.linalg.lstsq(X, dx, rcond=None)
    beta = float(coef[1])
    if beta >= 0:
        return float("inf")
    return float(-np.log(2.0) / np.log(1.0 + beta))


def z_strategy_sharpe(spread: np.ndarray, day_marker: np.ndarray, train_days: list[int],
                      test_day: int, z_entry: float = 2.0, z_exit: float = 0.5) -> dict:
    """Simple z-score reversion strategy. Train on `train_days`, test on `test_day`.

    Strategy: short spread when z>+entry, long when z<-entry, exit at |z|<exit.
    PnL = position * Δspread.
    Sharpe is per-tick * sqrt(10000).
    """
    train_mask = np.isin(day_marker, train_days)
    test_mask = day_marker == test_day
    if train_mask.sum() < 100 or test_mask.sum() < 100:
        return {"sharpe": float("nan"), "n_trades": 0, "total_pnl": float("nan")}
    mu = float(np.nanmean(spread[train_mask]))
    sd = float(np.nanstd(spread[train_mask]))
    if sd <= 0:
        return {"sharpe": float("nan"), "n_trades": 0, "total_pnl": float("nan")}
    s_test = spread[test_mask]
    z = (s_test - mu) / sd
    pos = np.zeros_like(s_test, dtype=float)
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
    pnl = pos[:-1] * np.diff(s_test)
    if pnl.std() <= 0:
        return {"sharpe": float("nan"), "n_trades": int(n_trades), "total_pnl": float(pnl.sum())}
    sharpe = float(pnl.mean() / pnl.std() * np.sqrt(10000))
    return {"sharpe": sharpe, "n_trades": int(n_trades), "total_pnl": float(pnl.sum())}


def main() -> None:
    days = available_days()
    append_log("Phase5 START")
    prices_by_day = {d: load_prices(d) for d in days}

    group_summary = []
    all_pair_coint = []

    for gname, products in ROUND5_GROUPS.items():
        gdir = GROUP_DIR / gname
        gdir.mkdir(parents=True, exist_ok=True)
        pivot = stitch_group(prices_by_day, products)
        # Forward-fill any missing prices within the group
        for p in products:
            if p in pivot.columns:
                pivot[p] = pivot[p].ffill().bfill()

        # Day marker
        day_marker = pivot["day"].to_numpy()

        # Price + return correlations
        prices_df = pivot[products].copy()
        rets_df = prices_df.diff().dropna()
        price_corr = prices_df.corr()
        ret_corr = rets_df.corr()
        price_corr.to_csv(gdir / "price_corr.csv")
        ret_corr.to_csv(gdir / "ret_corr.csv")

        # PCA on returns and prices
        try:
            pca_r = PCA(n_components=5).fit(rets_df.fillna(0).to_numpy())
            pca_p = PCA(n_components=5).fit(prices_df.fillna(method="ffill").to_numpy())
            pca_var_r = pca_r.explained_variance_ratio_.tolist()
            pca_var_p = pca_p.explained_variance_ratio_.tolist()
            pca_loadings_r = pd.DataFrame(pca_r.components_, columns=products,
                                          index=[f"PC{i+1}" for i in range(5)])
            pca_loadings_r.to_csv(gdir / "pca_loadings_returns.csv")
        except Exception:
            pca_var_r = [float("nan")] * 5; pca_var_p = [float("nan")] * 5

        # Engle-Granger pairwise
        coint_rows = []
        for a, b in combinations(products, 2):
            slope, intercept, pval = engle_granger_p(prices_df[a].to_numpy(), prices_df[b].to_numpy())
            spread = prices_df[a].to_numpy() - slope * prices_df[b].to_numpy() - intercept
            hl = ou_half_life(spread)
            # Walk-forward: train day2 -> test day3
            wf1 = z_strategy_sharpe(spread, day_marker, [2], 3)
            wf2 = z_strategy_sharpe(spread, day_marker, [2, 3], 4)
            coint_rows.append({
                "a": a, "b": b, "slope": slope, "intercept": intercept,
                "adf_p": pval, "ou_hl": hl,
                "wf1_sharpe": wf1["sharpe"], "wf1_pnl": wf1["total_pnl"],
                "wf2_sharpe": wf2["sharpe"], "wf2_pnl": wf2["total_pnl"],
            })
            all_pair_coint.append({"group": gname, **coint_rows[-1]})
        coint_df = pd.DataFrame(coint_rows)
        coint_df.to_csv(gdir / "engle_granger.csv", index=False)

        # Johansen on the 5-vector
        try:
            from statsmodels.tsa.vector_ar.vecm import coint_johansen
            j = coint_johansen(prices_df.to_numpy(), det_order=0, k_ar_diff=1)
            johansen_rows = []
            for k, (tr, cv) in enumerate(zip(j.lr1, j.cvt)):
                johansen_rows.append({"r<=k": k, "trace_stat": float(tr), "cv_5pct": float(cv[1])})
            pd.DataFrame(johansen_rows).to_csv(gdir / "johansen.csv", index=False)
            n_coint = int(sum(t > c[1] for t, c in zip(j.lr1, j.cvt)))
            johansen_first_vec = j.evec[:, 0].tolist()
        except Exception as e:
            n_coint = -1
            johansen_first_vec = []

        # Lead-lag CCF — pick top spearman-corr pair for compactness
        ccf_rows = []
        for a, b in combinations(products, 2):
            ra = rets_df[a].to_numpy()
            rb = rets_df[b].to_numpy()
            n = len(ra)
            best_l = 0; best_c = 0.0
            for lag in range(-20, 21):
                if lag == 0:
                    continue
                if lag > 0:
                    x = ra[:-lag]; y = rb[lag:]
                else:
                    x = ra[-lag:]; y = rb[:lag if lag != 0 else None]
                if len(x) < 100:
                    continue
                c = float(np.corrcoef(x, y)[0, 1])
                if abs(c) > abs(best_c):
                    best_c = c; best_l = lag
            ccf_rows.append({"a": a, "b": b, "best_lag": best_l, "best_corr": best_c})
        pd.DataFrame(ccf_rows).to_csv(gdir / "ccf.csv", index=False)

        # Basket-residual: each product regressed on the other four
        basket_rows = []
        for tgt in products:
            others = [p for p in products if p != tgt]
            X = prices_df[others].to_numpy()
            y = prices_df[tgt].to_numpy()
            mask = np.all(np.isfinite(X), axis=1) & np.isfinite(y)
            X1 = np.column_stack([np.ones(mask.sum()), X[mask]])
            coef, *_ = np.linalg.lstsq(X1, y[mask], rcond=None)
            yhat = X1 @ coef
            resid = y[mask] - yhat
            ss_res = float(np.sum(resid ** 2))
            ss_tot = float(np.sum((y[mask] - y[mask].mean()) ** 2))
            r2 = float(1 - ss_res / ss_tot) if ss_tot > 0 else float("nan")
            basket_rows.append({
                "target": tgt, "r2": r2,
                "resid_std": float(np.std(resid)),
                "resid_hl": ou_half_life(resid),
                **{f"coef_{others[k]}": float(coef[k + 1]) for k in range(len(others))},
                "intercept": float(coef[0]),
            })
        pd.DataFrame(basket_rows).to_csv(gdir / "basket_residual.csv", index=False)

        # Group summary
        # mean off-diagonal correlation
        mask = ~np.eye(len(products), dtype=bool)
        mean_ret_corr = float(np.nanmean(ret_corr.values[mask]))
        mean_price_corr = float(np.nanmean(price_corr.values[mask]))
        # best EG pair by adf_p
        best_eg = coint_df.loc[coint_df["adf_p"].idxmin()] if not coint_df.empty else None
        # best basket residual
        best_basket = max(basket_rows, key=lambda r: r["r2"]) if basket_rows else None

        group_summary.append({
            "group": gname,
            "mean_ret_corr_offdiag": mean_ret_corr,
            "mean_price_corr_offdiag": mean_price_corr,
            "pca_PC1_var_returns": pca_var_r[0],
            "pca_PC2_var_returns": pca_var_r[1],
            "pca_PC1_var_prices": pca_var_p[0],
            "johansen_n_coint_5pct": n_coint,
            "best_eg_pair": f"{best_eg['a']}/{best_eg['b']}" if best_eg is not None else "",
            "best_eg_adf_p": float(best_eg["adf_p"]) if best_eg is not None else float("nan"),
            "best_eg_wf1_sharpe": float(best_eg["wf1_sharpe"]) if best_eg is not None else float("nan"),
            "best_eg_wf2_sharpe": float(best_eg["wf2_sharpe"]) if best_eg is not None else float("nan"),
            "best_basket_target": best_basket["target"] if best_basket else "",
            "best_basket_r2": best_basket["r2"] if best_basket else float("nan"),
            "best_basket_resid_hl": best_basket["resid_hl"] if best_basket else float("nan"),
        })
        print(f"[{gname}] mean_ret_corr={mean_ret_corr:.3f}  best_eg_pair={best_eg['a']}/{best_eg['b']}  "
              f"adf_p={best_eg['adf_p']:.4f}  basket r²={best_basket['r2']:.3f}")

    pd.DataFrame(group_summary).to_csv(OUT / "group_summary.csv", index=False)
    pd.DataFrame(all_pair_coint).to_csv(OUT / "all_pair_cointegration.csv", index=False)
    append_log("Phase5 DONE")
    print("Phase 5 done.")


if __name__ == "__main__":
    main()
