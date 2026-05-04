"""Phase 6 — Global cross-group.

- 50×50 return correlation, hierarchical cluster (linkage tree).
- 50×50 sum-stability sweep across cross-group pairs.
- Global PCA top 5 components, loadings.
- |corr| > 0.5 cross-group pairs (return space).

Outputs
    06_global_cross_group/global_ret_corr.csv
    06_global_cross_group/global_price_corr.csv
    06_global_cross_group/cross_group_pairs_high_corr.csv
    06_global_cross_group/global_pca.csv
    06_global_cross_group/dendrogram.png
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
from scipy.cluster import hierarchy
from sklearn.decomposition import PCA

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from utils.data_loader import load_prices, available_days
from utils.round5_products import ROUND5_PRODUCTS, group_of

warnings.filterwarnings("ignore")
OUT = Path(__file__).resolve().parent
LOG = ROOT / "logs" / "progress.md"


def main():
    days = available_days()
    print("Phase6 START")
    parts = []
    for d in days:
        df = load_prices(d)
        sub = df.loc[df["product"].isin(ROUND5_PRODUCTS), ["day", "timestamp", "product", "mid_price"]].copy()
        sub["mid_price"] = sub["mid_price"].astype(float)
        parts.append(sub)
    full = pd.concat(parts, ignore_index=True).sort_values(["day", "timestamp", "product"])
    pivot = full.pivot_table(index=["day", "timestamp"], columns="product", values="mid_price")
    pivot = pivot[ROUND5_PRODUCTS].ffill().bfill()

    # Returns
    rets = pivot.diff().dropna()
    ret_corr = rets.corr()
    price_corr = pivot.corr()
    ret_corr.to_csv(OUT / "global_ret_corr.csv")
    price_corr.to_csv(OUT / "global_price_corr.csv")

    # Cross-group pairs with |corr|>0.4
    pairs = []
    for i in range(len(ROUND5_PRODUCTS)):
        for j in range(i + 1, len(ROUND5_PRODUCTS)):
            a = ROUND5_PRODUCTS[i]; b = ROUND5_PRODUCTS[j]
            if group_of(a) == group_of(b):
                continue
            rc = float(ret_corr.iloc[i, j])
            pc = float(price_corr.iloc[i, j])
            if abs(rc) > 0.1 or abs(pc) > 0.7:
                pairs.append({"a": a, "b": b, "ret_corr": rc, "price_corr": pc})
    pd.DataFrame(pairs).sort_values("ret_corr", key=lambda s: -s.abs()).to_csv(
        OUT / "cross_group_pairs_high_corr.csv", index=False
    )

    # Hierarchical clustering on returns
    dist = (1 - ret_corr.abs()).to_numpy().copy()
    np.fill_diagonal(dist, 0.0)
    condensed = dist[np.triu_indices_from(dist, k=1)]
    try:
        Z = hierarchy.linkage(condensed, method="average")
        fig, ax = plt.subplots(figsize=(14, 8))
        hierarchy.dendrogram(Z, labels=ROUND5_PRODUCTS, leaf_rotation=90, ax=ax)
        fig.tight_layout()
        fig.savefig(OUT / "dendrogram.png", dpi=80)
        plt.close(fig)
    except Exception as e:
        print("dendrogram failed", e)

    # PCA
    try:
        pca = PCA(n_components=5).fit(rets.fillna(0).to_numpy())
        var = pd.Series(pca.explained_variance_ratio_, index=[f"PC{k+1}" for k in range(5)])
        loadings = pd.DataFrame(pca.components_, columns=ROUND5_PRODUCTS,
                                index=[f"PC{k+1}" for k in range(5)])
        loadings.to_csv(OUT / "global_pca_loadings.csv")
        var.to_csv(OUT / "global_pca_var.csv")
    except Exception as e:
        print("pca failed", e)

    # Cross-group sum-invariant scan: try all pairs (i,j) with sum stability
    sums_summary = []
    for i in range(len(ROUND5_PRODUCTS)):
        for j in range(i + 1, len(ROUND5_PRODUCTS)):
            if group_of(ROUND5_PRODUCTS[i]) == group_of(ROUND5_PRODUCTS[j]):
                continue
            a = pivot[ROUND5_PRODUCTS[i]].to_numpy()
            b = pivot[ROUND5_PRODUCTS[j]].to_numpy()
            s = a + b
            d = a - b
            cv_sum = float(np.std(s) / abs(np.mean(s))) if np.mean(s) != 0 else float("nan")
            cv_diff = float(np.std(d) / abs(np.mean(d))) if abs(np.mean(d)) > 1 else float("nan")
            if cv_sum < 0.005 or (np.isfinite(cv_diff) and cv_diff < 0.01):
                sums_summary.append({"a": ROUND5_PRODUCTS[i], "b": ROUND5_PRODUCTS[j],
                                     "sum_mean": float(np.mean(s)), "sum_std": float(np.std(s)),
                                     "diff_mean": float(np.mean(d)), "diff_std": float(np.std(d))})
    pd.DataFrame(sums_summary).to_csv(OUT / "cross_group_sum_invariants.csv", index=False)
    print(f"Phase 6 done. cross-group high-corr pairs: {len(pairs)}, sum-invariants: {len(sums_summary)}")


if __name__ == "__main__":
    main()
