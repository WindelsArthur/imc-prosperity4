"""Phase A — per-product attribution decomposition.

For each of the 50 products, compute per-product PnL on baseline AND tuned
across all 5 folds. Build winners/losers/fragility tables and per-fold bar
charts for top-5 winners and top-5 losers.

Stateless trick: per-day per-product PnL is the same regardless of fold's
train days. So we run baseline once (3 days merged), tuned once, and parse
per-day per-product blocks. Then per-fold per-product PnL = the fold's
test-day per-product PnL.
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _audit_lib import run_algo, FOLDS, DAYS  # noqa: E402

OUT = Path(__file__).resolve().parent
PLOTS = OUT / "plots"
PLOTS.mkdir(parents=True, exist_ok=True)

PT_DIR = Path(__file__).resolve().parents[2]
BASELINE_ALGO = PT_DIR / "algo1.py"
TUNED_ALGO = PT_DIR / "07_assembly" / "algo1_tuned.py"


# ── pair touch counts ──────────────────────────────────────────────────────
def _read_tuned_pairs() -> list[tuple]:
    """Eval distilled_params_tuned.ALL_PAIRS to get the 166 pairs."""
    spec = PT_DIR / "07_assembly" / "distilled_params_tuned.py"
    ns: dict = {}
    exec(spec.read_text(), ns)
    return ns["ALL_PAIRS"]


def _read_baseline_pairs() -> list[tuple]:
    """Read COINT_PAIRS + CROSS_GROUP_PAIRS from baseline algo1.py."""
    src = (PT_DIR / "algo1.py").read_text()
    ns: dict = {}
    # Just exec the constants — but the file imports datamodel; instead, use
    # regex to extract the literals. Easier: import via a stripped exec.
    # The file's top section doesn't depend on datamodel for the constants we
    # need; but the file does import at line 5. Strip the imports for this exec.
    lines = src.splitlines()
    # We grab from "POSITION_LIMIT" through "ALL_PAIRS = COINT_PAIRS + CROSS_GROUP_PAIRS"
    capture: list[str] = []
    capturing = False
    for ln in lines:
        if ln.startswith("POSITION_LIMIT"):
            capturing = True
        if capturing:
            capture.append(ln)
            if ln.startswith("ALL_PAIRS"):
                break
    code = "\n".join(capture)
    exec(code, ns)
    return ns["ALL_PAIRS"]


def _pair_touch_counts(pairs: list[tuple]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for tup in pairs:
        a, b = tup[0], tup[1]
        counts[a] = counts.get(a, 0) + 1
        counts[b] = counts.get(b, 0) + 1
    return counts


# ── main ───────────────────────────────────────────────────────────────────
def main():
    print("[Phase A] running baseline merged backtest …")
    base_res = run_algo(BASELINE_ALGO)
    print(f"  baseline total_3day={base_res.total_3day:,} elapsed={base_res.elapsed_s:.1f}s")
    print(f"  per-day: {base_res.per_day_pnl}")

    print("[Phase A] running tuned merged backtest …")
    tuned_res = run_algo(TUNED_ALGO)
    print(f"  tuned total_3day={tuned_res.total_3day:,} elapsed={tuned_res.elapsed_s:.1f}s")
    print(f"  per-day: {tuned_res.per_day_pnl}")

    # collect product universe
    all_products = set()
    for d in DAYS:
        all_products.update(base_res.per_day_per_product.get(d, {}))
        all_products.update(tuned_res.per_day_per_product.get(d, {}))
    products = sorted(all_products)
    print(f"  product universe: {len(products)}")

    base_pairs = _read_baseline_pairs()
    tuned_pairs = _read_tuned_pairs()
    base_touch = _pair_touch_counts(base_pairs)
    tuned_touch = _pair_touch_counts(tuned_pairs)
    print(f"  baseline pairs={len(base_pairs)} | tuned pairs={len(tuned_pairs)}")

    # per-product per-fold PnL
    rows = []
    for p in products:
        b_folds = [base_res.per_day_per_product.get(fk["test"], {}).get(p, 0)
                   for fk in FOLDS]
        t_folds = [tuned_res.per_day_per_product.get(fk["test"], {}).get(p, 0)
                   for fk in FOLDS]
        b_med = sorted(b_folds)[len(b_folds) // 2]
        t_med = sorted(t_folds)[len(t_folds) // 2]
        b_min = min(b_folds)
        t_min = min(t_folds)
        rows.append({
            "product": p,
            "baseline_F1": b_folds[0], "tuned_F1": t_folds[0],
            "baseline_F2": b_folds[1], "tuned_F2": t_folds[1],
            "baseline_F3": b_folds[2], "tuned_F3": t_folds[2],
            "baseline_F4": b_folds[3], "tuned_F4": t_folds[3],
            "baseline_F5": b_folds[4], "tuned_F5": t_folds[4],
            "baseline_median": b_med,
            "tuned_median": t_med,
            "delta_median": t_med - b_med,
            "baseline_fold_min": b_min,
            "tuned_fold_min": t_min,
            "fold_min_delta": t_min - b_min,
            "baseline_3day": sum(base_res.per_day_per_product.get(d, {}).get(p, 0) for d in DAYS),
            "tuned_3day":    sum(tuned_res.per_day_per_product.get(d, {}).get(p, 0) for d in DAYS),
            "delta_3day":    sum(tuned_res.per_day_per_product.get(d, {}).get(p, 0) - base_res.per_day_per_product.get(d, {}).get(p, 0) for d in DAYS),
            "baseline_n_pairs": base_touch.get(p, 0),
            "tuned_n_pairs": tuned_touch.get(p, 0),
            "added_n_pairs": tuned_touch.get(p, 0) - base_touch.get(p, 0),
        })
    df = pd.DataFrame(rows).sort_values("delta_3day", ascending=False)
    df.to_csv(OUT / "per_product_attribution.csv", index=False)

    # ── winners/losers/fragility ───────────────────────────────────────────
    winners = df.nlargest(5, "delta_3day")
    losers = df.nsmallest(5, "delta_3day")

    fragility_mask = (df["delta_median"] > 0) & (df["fold_min_delta"] < 0)
    fragility = df[fragility_mask].sort_values("fold_min_delta")

    summary = {
        "baseline_total_3day": base_res.total_3day,
        "baseline_per_day": base_res.per_day_pnl,
        "baseline_sharpe": base_res.sharpe_3day,
        "baseline_max_dd": base_res.max_dd_3day,
        "baseline_fold_min": base_res.fold_min,
        "baseline_fold_median": base_res.fold_median,
        "tuned_total_3day": tuned_res.total_3day,
        "tuned_per_day": tuned_res.per_day_pnl,
        "tuned_sharpe": tuned_res.sharpe_3day,
        "tuned_max_dd": tuned_res.max_dd_3day,
        "tuned_fold_min": tuned_res.fold_min,
        "tuned_fold_median": tuned_res.fold_median,
        "delta_total_3day": tuned_res.total_3day - base_res.total_3day,
        "delta_fold_min": tuned_res.fold_min - base_res.fold_min,
        "delta_fold_median": tuned_res.fold_median - base_res.fold_median,
        "n_products": len(products),
        "n_winners_with_uplift": int((df["delta_3day"] > 0).sum()),
        "n_losers_with_drag": int((df["delta_3day"] < 0).sum()),
        "n_fragility_flagged": int(fragility_mask.sum()),
        "winners_top5": winners[["product", "baseline_3day", "tuned_3day", "delta_3day",
                                  "baseline_fold_min", "tuned_fold_min",
                                  "fold_min_delta", "added_n_pairs"]].to_dict("records"),
        "losers_top5":  losers[["product", "baseline_3day", "tuned_3day", "delta_3day",
                                 "baseline_fold_min", "tuned_fold_min",
                                 "fold_min_delta", "added_n_pairs"]].to_dict("records"),
        "fragility_flagged": fragility[["product", "delta_median", "fold_min_delta",
                                         "added_n_pairs"]].to_dict("records"),
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2, default=str))

    # ── plots ──────────────────────────────────────────────────────────────
    fold_names = [fk["name"] for fk in FOLDS]
    plot_set = list(winners["product"]) + list(losers["product"])
    for prod in plot_set:
        b_folds = [base_res.per_day_per_product.get(fk["test"], {}).get(prod, 0) for fk in FOLDS]
        t_folds = [tuned_res.per_day_per_product.get(fk["test"], {}).get(prod, 0) for fk in FOLDS]
        x = list(range(len(fold_names)))
        w = 0.35
        fig, ax = plt.subplots(figsize=(7, 4))
        ax.bar([xi - w / 2 for xi in x], b_folds, w, label="baseline")
        ax.bar([xi + w / 2 for xi in x], t_folds, w, label="tuned")
        ax.set_xticks(x); ax.set_xticklabels(fold_names)
        ax.set_ylabel("PnL")
        ax.axhline(0, color="grey", lw=0.5)
        ax.set_title(f"{prod}  Δ3day={t_folds and (sum(t_folds)-sum(b_folds))//5*5:,}")
        ax.legend()
        plt.tight_layout()
        fig.savefig(PLOTS / f"{prod}.png", dpi=120)
        plt.close(fig)

    # ── markdown summary ──────────────────────────────────────────────────
    md_lines = [
        "# Phase A — per-product attribution\n",
        f"- baseline 3-day total: **{base_res.total_3day:,}**, "
        f"fold_min={base_res.fold_min:,}, fold_median={base_res.fold_median:,.0f}, "
        f"sharpe={base_res.sharpe_3day:.2f}",
        f"- tuned 3-day total: **{tuned_res.total_3day:,}**, "
        f"fold_min={tuned_res.fold_min:,}, fold_median={tuned_res.fold_median:,.0f}, "
        f"sharpe={tuned_res.sharpe_3day:.2f}",
        f"- delta total = **{tuned_res.total_3day - base_res.total_3day:+,}** "
        f"(fold_min {tuned_res.fold_min - base_res.fold_min:+,}, "
        f"fold_median {tuned_res.fold_median - base_res.fold_median:+,.0f})",
        "",
        "## Top 5 winners (Δ3day desc)\n",
        winners[["product", "baseline_3day", "tuned_3day", "delta_3day",
                 "baseline_fold_min", "tuned_fold_min", "fold_min_delta",
                 "added_n_pairs"]].to_markdown(index=False),
        "",
        "## Top 5 losers (Δ3day asc)\n",
        losers[["product", "baseline_3day", "tuned_3day", "delta_3day",
                "baseline_fold_min", "tuned_fold_min", "fold_min_delta",
                "added_n_pairs"]].to_markdown(index=False),
        "",
        "## Fragility (median up, fold_min down)\n",
        fragility[["product", "delta_median", "fold_min_delta", "added_n_pairs"]].to_markdown(index=False) if len(fragility) else "_none_",
    ]
    (OUT / "summary.md").write_text("\n".join(md_lines))
    print(f"\n[Phase A] wrote per_product_attribution.csv, summary.json, summary.md, plots/*.png")


if __name__ == "__main__":
    main()
