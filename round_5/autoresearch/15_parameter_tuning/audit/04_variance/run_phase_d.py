"""Phase D — variance source decomposition.

Sharpe dropped 63→13 from baseline to tuned. Where is the variance coming from?

For each product, compute:
  - cross-day std of per-day PnL (does it swing wildly day to day?)
  - cross-fold std of per-fold PnL (since folds collapse to days under
    statelessness: F1=F3=F5 share day3, so the empirical fold-PnL series for
    each product is [day3, day4, day3, day2, day3] → 5 values with day3 weighted)
  - same metrics on baseline for comparison
  - delta_std (tuned - baseline)

Identify top contributors to variance. If concentrated in 5-10 products, those
are the levers for variance reduction. If spread, structural.

No backtests required — re-uses Phase A merged stdouts via run_algo.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _audit_lib import run_algo, FOLDS, DAYS  # noqa: E402

OUT = Path(__file__).resolve().parent
PT_DIR = Path(__file__).resolve().parents[2]
BASELINE_ALGO = PT_DIR / "algo1.py"
TUNED_ALGO = PT_DIR / "07_assembly" / "algo1_tuned.py"


def _per_product_per_day(res) -> pd.DataFrame:
    rows = []
    for d in DAYS:
        for p, v in res.per_day_per_product.get(d, {}).items():
            rows.append({"day": d, "product": p, "pnl": v})
    return pd.DataFrame(rows)


def main():
    print("[Phase D] re-running baseline + tuned …")
    base_res = run_algo(BASELINE_ALGO)
    tuned_res = run_algo(TUNED_ALGO)
    print(f"  baseline per-day: {base_res.per_day_pnl}")
    print(f"  tuned    per-day: {tuned_res.per_day_pnl}")

    bp = _per_product_per_day(base_res)
    tp = _per_product_per_day(tuned_res)

    products = sorted(set(bp["product"]) | set(tp["product"]))

    rows = []
    for prod in products:
        b = bp[bp["product"] == prod].set_index("day")["pnl"].reindex(DAYS).fillna(0).astype(float)
        t = tp[tp["product"] == prod].set_index("day")["pnl"].reindex(DAYS).fillna(0).astype(float)
        # cross-day std (population std over 3 days)
        b_xday_std = float(b.std(ddof=0))
        t_xday_std = float(t.std(ddof=0))
        # cross-fold std (PnL each fold = test_day's PnL → series of 5 values per fold)
        b_fold = np.array([b[fk["test"]] for fk in FOLDS])
        t_fold = np.array([t[fk["test"]] for fk in FOLDS])
        b_xfold_std = float(b_fold.std(ddof=0))
        t_xfold_std = float(t_fold.std(ddof=0))
        rows.append({
            "product": prod,
            "baseline_d2": b[2], "baseline_d3": b[3], "baseline_d4": b[4],
            "tuned_d2":    t[2], "tuned_d3":    t[3], "tuned_d4":    t[4],
            "baseline_xday_std":  b_xday_std,
            "tuned_xday_std":     t_xday_std,
            "delta_xday_std":     t_xday_std - b_xday_std,
            "baseline_xfold_std": b_xfold_std,
            "tuned_xfold_std":    t_xfold_std,
            "delta_xfold_std":    t_xfold_std - b_xfold_std,
            "baseline_3day":      float(b.sum()),
            "tuned_3day":         float(t.sum()),
        })
    df = pd.DataFrame(rows)

    # totals
    base_total_xday_std = float(np.sqrt((df["baseline_xday_std"] ** 2).sum()))
    tuned_total_xday_std = float(np.sqrt((df["tuned_xday_std"] ** 2).sum()))
    # actual total per-day std over 3 days
    base_pd = pd.Series(base_res.per_day_pnl).reindex(DAYS).astype(float)
    tuned_pd = pd.Series(tuned_res.per_day_pnl).reindex(DAYS).astype(float)
    base_pf_std = float(base_pd.std(ddof=0))
    tuned_pf_std = float(tuned_pd.std(ddof=0))

    df = df.sort_values("delta_xday_std", ascending=False)
    df.to_csv(OUT / "variance_per_product.csv", index=False)

    # top 10 contributors to delta_xday_std
    top10 = df.nlargest(10, "delta_xday_std")
    bot10 = df.nsmallest(10, "delta_xday_std")
    top_share_of_increase = float(top10["delta_xday_std"].sum() /
                                  max(df[df["delta_xday_std"] > 0]["delta_xday_std"].sum(), 1e-9))

    summary = {
        "baseline_per_day": base_res.per_day_pnl,
        "tuned_per_day": tuned_res.per_day_pnl,
        "baseline_total_per_day_std": base_pf_std,
        "tuned_total_per_day_std": tuned_pf_std,
        "delta_total_per_day_std": tuned_pf_std - base_pf_std,
        "baseline_sharpe": base_res.sharpe_3day,
        "tuned_sharpe": tuned_res.sharpe_3day,
        "n_products_with_higher_xday_std": int((df["delta_xday_std"] > 0).sum()),
        "n_products_with_lower_xday_std": int((df["delta_xday_std"] < 0).sum()),
        "top10_delta_xday_std_share_of_increase": top_share_of_increase,
        "top10_variance_contributors": top10[["product", "baseline_xday_std",
                                                "tuned_xday_std", "delta_xday_std",
                                                "tuned_d2", "tuned_d3", "tuned_d4"]].to_dict("records"),
        "bot10_variance_reducers": bot10[["product", "baseline_xday_std",
                                            "tuned_xday_std", "delta_xday_std"]].to_dict("records"),
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2, default=str))

    md = [
        "# Phase D — variance decomposition\n",
        f"- baseline per-day total std (3 days): **{base_pf_std:,.0f}** (sharpe={base_res.sharpe_3day:.2f})",
        f"- tuned    per-day total std (3 days): **{tuned_pf_std:,.0f}** (sharpe={tuned_res.sharpe_3day:.2f})",
        f"- Δ per-day std: **{tuned_pf_std - base_pf_std:+,.0f}**",
        f"- Top-10 products account for **{top_share_of_increase*100:.1f}%** of total per-product variance increase",
        f"- products with higher xday std (more volatile in tuned): {int((df['delta_xday_std']>0).sum())}",
        f"- products with lower xday std: {int((df['delta_xday_std']<0).sum())}",
        "",
        "## Top 10 cross-day variance contributors (tuned - baseline)",
        top10[["product", "baseline_d2", "baseline_d3", "baseline_d4",
               "tuned_d2", "tuned_d3", "tuned_d4",
               "baseline_xday_std", "tuned_xday_std", "delta_xday_std"]].to_markdown(index=False),
        "",
        "## Bottom 10 (variance REDUCERS)",
        bot10[["product", "baseline_xday_std", "tuned_xday_std", "delta_xday_std"]].to_markdown(index=False),
    ]
    (OUT / "summary.md").write_text("\n".join(md))

    # bar chart
    top15 = df.nlargest(15, "delta_xday_std")
    fig, ax = plt.subplots(figsize=(10, 5))
    x = np.arange(len(top15))
    w = 0.4
    ax.bar(x - w / 2, top15["baseline_xday_std"], w, label="baseline xday_std")
    ax.bar(x + w / 2, top15["tuned_xday_std"],    w, label="tuned xday_std")
    ax.set_xticks(x); ax.set_xticklabels(top15["product"], rotation=70, ha="right")
    ax.set_ylabel("cross-day std of per-product PnL")
    ax.set_title("Top 15 variance contributors (tuned - baseline)")
    ax.legend()
    plt.tight_layout()
    fig.savefig(OUT / "top_variance_contributors.png", dpi=120)
    plt.close(fig)

    print(f"[Phase D] top10 products account for {top_share_of_increase*100:.1f}% of variance increase")
    print(f"[Phase D] wrote variance_per_product.csv, summary.json, summary.md, top_variance_contributors.png")


if __name__ == "__main__":
    main()
