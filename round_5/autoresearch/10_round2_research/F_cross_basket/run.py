"""Phase F — Cross-group basket relations.

Round 1 found PEBBLES sum=50,000 and SNACKPACK sum=50,221. Hunt for similar
invariants:
1. Per-group min-variance basket (smallest-eigenvalue eigvec of cov matrix).
   Test residual stationarity (ADF).
2. 50-product PCA last-component baskets.
3. Targeted 2-3 group baskets via brute search of triplets.

Outputs:
    13_round2_research/F_cross_basket/min_var_baskets.csv
    13_round2_research/F_cross_basket/decision.md
"""
from __future__ import annotations

import sys
import time
import warnings
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from utils.data_loader import load_prices, available_days
from utils.round5_products import ROUND5_GROUPS, ROUND5_PRODUCTS

warnings.filterwarnings("ignore")
OUT = Path(__file__).resolve().parent
LOG = ROOT / "logs" / "progress.md"


def append_log(msg):
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    with LOG.open("a") as f:
        f.write(f"- [{ts}] {msg}\n")


def stitch_pivot():
    days = available_days()
    parts = []
    for d in days:
        df = load_prices(d)
        sub = df.loc[df["product"].isin(ROUND5_PRODUCTS),
                     ["day", "timestamp", "product", "mid_price"]].copy()
        sub["mid_price"] = sub["mid_price"].astype(float)
        parts.append(sub)
    full = pd.concat(parts, ignore_index=True).sort_values(["day", "timestamp"])
    pivot = full.pivot_table(index=["day", "timestamp"], columns="product", values="mid_price")
    pivot = pivot[ROUND5_PRODUCTS].ffill().bfill()
    return pivot


def adf_pvalue(x):
    from statsmodels.tsa.stattools import adfuller
    try:
        return float(adfuller(x, autolag="AIC")[1])
    except Exception:
        return float("nan")


def ou_half_life(x):
    if len(x) < 4:
        return float("inf")
    x_lag = x[:-1]; dx = np.diff(x)
    X = np.column_stack([np.ones_like(x_lag), x_lag])
    coef, *_ = np.linalg.lstsq(X, dx, rcond=None)
    beta = float(coef[1])
    if beta >= 0:
        return float("inf")
    return float(-np.log(2.0) / np.log(1.0 + beta))


def main():
    print("Phase F start.")
    pivot = stitch_pivot()
    days_marker = pivot.index.get_level_values("day").to_numpy()

    rows = []

    # 1. Per-group min-variance basket
    for gname, prods in ROUND5_GROUPS.items():
        X = pivot[prods].to_numpy()
        # Center
        Xc = X - X.mean(axis=0)
        cov = np.cov(Xc.T)
        eigvals, eigvecs = np.linalg.eigh(cov)
        # Smallest eigenvalue
        v = eigvecs[:, 0]
        # Normalise so largest |coef|=1 for readability
        v = v / np.max(np.abs(v))
        spread = X @ v
        adf_p = adf_pvalue(spread)
        rows.append({
            "set": f"group_{gname}_minvar",
            "members": ",".join(prods),
            "weights": ",".join(f"{c:.4f}" for c in v),
            "min_eigval": float(eigvals[0]),
            "spread_mean": float(spread.mean()),
            "spread_std": float(spread.std()),
            "adf_p": adf_p,
            "ou_half_life": ou_half_life(spread),
            "rel_std": float(spread.std() / abs(spread.mean())) if abs(spread.mean()) > 1 else float("nan"),
        })

    # 2. Global min-variance basket using 50-product PCA last component
    X = pivot[ROUND5_PRODUCTS].to_numpy()
    Xc = X - X.mean(axis=0)
    cov = np.cov(Xc.T)
    eigvals, eigvecs = np.linalg.eigh(cov)
    v = eigvecs[:, 0]
    v = v / np.max(np.abs(v))
    spread = X @ v
    adf_p = adf_pvalue(spread)
    rows.append({
        "set": "global_minvar",
        "members": "50",
        "weights": "(see weights csv)",
        "min_eigval": float(eigvals[0]),
        "spread_mean": float(spread.mean()),
        "spread_std": float(spread.std()),
        "adf_p": adf_p,
        "ou_half_life": ou_half_life(spread),
        "rel_std": float("nan"),
    })
    pd.DataFrame({"product": ROUND5_PRODUCTS, "weight": v}).to_csv(OUT / "global_minvar_weights.csv",
                                                                    index=False)

    # 3. Targeted cross-group triplet search: pairs with min-var-spread already low,
    # then try adding one cross-group product. Use a subsample for ADF for speed.
    try:
        pairs_df = pd.read_csv(ROOT / "06_global_cross_group" / "cross_group_pairs_high_corr.csv")
    except Exception:
        pairs_df = pd.DataFrame()
    pairs_df["abs_pc"] = pairs_df["price_corr"].abs()
    top_pairs = pairs_df.sort_values("abs_pc", ascending=False).head(8)

    # subsample every 30 ticks → 1000 obs across days for cheaper ADF
    SUB = 30
    sub_idx = np.arange(0, len(pivot), SUB)
    sub_X = pivot.iloc[sub_idx]

    triplet_rows = []
    for _, r in top_pairs.iterrows():
        a, b = r["a"], r["b"]
        for c in ROUND5_PRODUCTS:
            if c in (a, b):
                continue
            Xtri = sub_X[[a, b, c]].to_numpy()
            Xc = Xtri - Xtri.mean(axis=0)
            cov = np.cov(Xc.T)
            eigvals, eigvecs = np.linalg.eigh(cov)
            v = eigvecs[:, 0]
            if np.max(np.abs(v)) < 1e-9:
                continue
            v = v / np.max(np.abs(v))
            spread = Xtri @ v
            sd = float(spread.std())
            mu = float(spread.mean())
            rel = sd / max(abs(mu), 1.0)
            if rel > 0.02:  # only accept very stable spreads
                continue
            adf_p = adf_pvalue(spread)
            if adf_p > 0.05:
                continue
            triplet_rows.append({
                "members": f"{a},{b},{c}",
                "weights": ",".join(f"{x:.3f}" for x in v),
                "min_eigval": float(eigvals[0]),
                "spread_mean": mu, "spread_std": sd,
                "adf_p": adf_p, "ou_half_life": ou_half_life(spread),
                "rel_std": rel,
            })

    pd.DataFrame(rows).to_csv(OUT / "min_var_baskets.csv", index=False)
    pd.DataFrame(triplet_rows).to_csv(OUT / "triplet_baskets.csv", index=False)

    md = ["# Phase F — Cross-Basket Hunt\n\n",
          "## Per-group min-variance baskets\n\n",
          pd.DataFrame(rows).sort_values("rel_std").to_markdown(index=False) + "\n\n",
          "## Stationary cross-group triplets (ADF p<0.05, rel_std<0.05)\n\n",
          (pd.DataFrame(triplet_rows).sort_values("ou_half_life").head(20).to_markdown(index=False)
           if triplet_rows else "_None found_") + "\n",
    ]
    (OUT / "decision.md").write_text("".join(md))
    append_log(f"PhaseF DONE — found {len(triplet_rows)} cross-group triplets")
    print("Phase F done. triplets:", len(triplet_rows))


if __name__ == "__main__":
    main()
