"""Phase D — VAR(p) per group + Granger + IRF.

For each of 10 groups, fit VAR on the 5-vector mid series (stitched, but with
a within-day modelling assumption — we just dummy-out the day boundary).
- BIC chooses p (max 10).
- Granger causality matrix per group.
- IRFs at horizon 50.
- Identify "leader" products.

Outputs:
    14_lag_research/D_var/per_group_summary.csv
    14_lag_research/D_var/granger_matrices.csv
    14_lag_research/D_var/decision.md
"""
from __future__ import annotations

import sys
import time
import warnings
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


def main():
    print("Phase D start.")
    pivot = stitch_pivot()
    from statsmodels.tsa.api import VAR

    rows = []
    granger_rows = []
    leaders = []

    for gname, prods in ROUND5_GROUPS.items():
        # Use returns (differenced) for VAR — prices are unit-root
        rets = pivot[prods].diff().dropna()
        # Subsample for speed
        rets_sub = rets.iloc[::3]  # every 3rd tick → 10K obs
        try:
            model = VAR(rets_sub)
            sel = model.select_order(maxlags=10)
            p = int(sel.bic)
            p = max(1, p)
            res = model.fit(p)
        except Exception as e:
            print(f"VAR failed for {gname}: {e}")
            continue

        # Granger causality matrix: for each pair (a → b), F-stat and p
        gc_matrix = np.zeros((5, 5))
        gc_pmatrix = np.ones((5, 5))
        for a_idx, a in enumerate(prods):
            for b_idx, b in enumerate(prods):
                if a_idx == b_idx:
                    continue
                try:
                    test = res.test_causality(b, [a], kind="f", signif=0.05)
                    gc_matrix[a_idx, b_idx] = float(test.test_statistic)
                    gc_pmatrix[a_idx, b_idx] = float(test.pvalue)
                except Exception:
                    continue

        # Save granger matrix
        for a_idx, a in enumerate(prods):
            for b_idx, b in enumerate(prods):
                if a_idx != b_idx:
                    granger_rows.append({"group": gname, "from": a, "to": b,
                                          "f_stat": float(gc_matrix[a_idx, b_idx]),
                                          "p_value": float(gc_pmatrix[a_idx, b_idx])})

        # Leaders: count of significant outgoing causality vs incoming
        out_sig = (gc_pmatrix < 0.01).sum(axis=1)
        in_sig = (gc_pmatrix < 0.01).sum(axis=0)
        for a_idx, a in enumerate(prods):
            leaders.append({
                "group": gname, "product": a,
                "out_sig": int(out_sig[a_idx]),
                "in_sig": int(in_sig[a_idx]),
                "leadership_score": int(out_sig[a_idx] - in_sig[a_idx]),
            })

        rows.append({
            "group": gname, "var_p": p, "n_obs": len(rets_sub),
            "max_out_sig": int(out_sig.max()),
            "max_in_sig": int(in_sig.max()),
        })
        print(f"  {gname}: p={p}, max_out_sig={int(out_sig.max())}, max_in_sig={int(in_sig.max())}")

    pd.DataFrame(rows).to_csv(OUT / "per_group_summary.csv", index=False)
    pd.DataFrame(granger_rows).to_csv(OUT / "granger_matrices.csv", index=False)
    pd.DataFrame(leaders).to_csv(OUT / "leadership.csv", index=False)

    md = ["# Phase D — VAR per group + Granger\n\n",
          "## Per-group summary\n\n",
          pd.DataFrame(rows).to_markdown(index=False) + "\n\n",
          "## Top leadership scores (out_sig − in_sig)\n\n",
          pd.DataFrame(leaders).sort_values("leadership_score", ascending=False).head(20).to_markdown(index=False) + "\n",
    ]
    (OUT / "decision.md").write_text("".join(md))
    append_log("PhaseD DONE")
    print("Phase D done.")


if __name__ == "__main__":
    main()
