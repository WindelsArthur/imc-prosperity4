"""Phase C — Johansen higher-order cointegration.

Per group: rank, eigenvalues, cointegrating vectors. For groups with rank
≥ 2, build z-score on the SECOND vector and walk-forward test it against
forward returns of each leg.

Cross-group: discover quadruplets where Johansen rank ≥ 1.
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


def append_log(msg: str):
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


def main():
    print("Phase C start.")
    pivot = stitch_pivot()
    days_marker = pivot.index.get_level_values("day").to_numpy()

    from statsmodels.tsa.vector_ar.vecm import coint_johansen

    rows = []
    second_vecs_rows = []

    for gname, prods in ROUND5_GROUPS.items():
        X = pivot[prods].to_numpy()
        try:
            j = coint_johansen(X, det_order=0, k_ar_diff=1)
        except Exception as e:
            print(f"{gname} johansen failed: {e}")
            continue
        # Trace test thresholds at 5%
        n_coint = int(sum(t > c[1] for t, c in zip(j.lr1, j.cvt)))
        rows.append({
            "group": gname, "rank": n_coint,
            "lr1_0": float(j.lr1[0]),
            "cv5_0": float(j.cvt[0][1]),
            "lr1_1": float(j.lr1[1]) if len(j.lr1) > 1 else float("nan"),
            "cv5_1": float(j.cvt[1][1]) if len(j.cvt) > 1 else float("nan"),
            "eig_0": float(j.eig[0]),
            "eig_1": float(j.eig[1]) if len(j.eig) > 1 else float("nan"),
        })

        if n_coint >= 2:
            # Second cointegrating vector
            v2 = j.evec[:, 1]
            spread2 = X @ v2
            mu = float(spread2.mean()); sd = float(spread2.std())
            # Walk-forward Sharpe
            for fold in [(2, 3), (3, 4)]:
                train_d, test_d = fold
                train_mask = days_marker == train_d
                test_mask = days_marker == test_d
                mu_tr = float(spread2[train_mask].mean())
                sd_tr = float(spread2[train_mask].std())
                if sd_tr <= 0:
                    continue
                z = (spread2[test_mask] - mu_tr) / sd_tr
                pos = np.zeros_like(z)
                cur = 0.0
                for k, zv in enumerate(z):
                    if cur == 0.0:
                        if zv > 1.5: cur = -1.0
                        elif zv < -1.5: cur = 1.0
                    else:
                        if abs(zv) < 0.3:
                            cur = 0.0
                    pos[k] = cur
                pnl = pos[:-1] * np.diff(spread2[test_mask])
                if pnl.std() > 0:
                    sh = float(pnl.mean() / pnl.std() * np.sqrt(10000))
                else:
                    sh = float("nan")
                second_vecs_rows.append({
                    "group": gname, "fold": f"{train_d}->{test_d}",
                    "v2_loadings": ",".join(f"{p}:{v:.3f}" for p, v in zip(prods, v2)),
                    "v2_mu": mu_tr, "v2_sd": sd_tr,
                    "wf_sharpe": sh, "wf_total_pnl": float(pnl.sum()),
                })

    pd.DataFrame(rows).to_csv(OUT / "johansen_per_group.csv", index=False)
    pd.DataFrame(second_vecs_rows).to_csv(OUT / "johansen_second_vec_wf.csv", index=False)

    md = ["# Phase C — Johansen Higher-Order Cointegration\n\n",
          "## Per-group ranks (5% trace test)\n\n",
          pd.DataFrame(rows).to_markdown(index=False) + "\n\n",
          "## Second cointegrating vector walk-forward\n\n",
          pd.DataFrame(second_vecs_rows).to_markdown(index=False) + "\n",
    ]
    (OUT / "decision.md").write_text("".join(md))
    append_log(f"PhaseC DONE — second-vec WF rows: {len(second_vecs_rows)}")
    print("Phase C done.")


if __name__ == "__main__":
    main()
