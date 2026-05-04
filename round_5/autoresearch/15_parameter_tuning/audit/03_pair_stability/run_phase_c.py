"""Phase C — pair stability across days.

For each tuned pair (a, b, slope_full, intercept_full):
  - Fit OLS regression a = β·b + α on DAY 2 ONLY (5-2)
  - Compute |β_day2 - slope_full| / |slope_full|
  - With (β_day2, α_day2) compute residual on day 3 and day 4
  - Run ADF on each held-out day's residual

Flag pairs as PARAMETER-UNSTABLE if:
  - |β shift| > 30% of |slope_full|, OR
  - max(ADF p-value on day 3, day 4) > 0.05

Pure analytics (no backtests). Uses statsmodels OLS + adfuller.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from statsmodels.tsa.stattools import adfuller

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
# noqa: E402
PT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = Path(__file__).resolve().parents[4] / "Data"   # ROUND_5/Data/

OUT = Path(__file__).resolve().parent


def _load_tuned_pairs() -> list[list]:
    spec = PT_DIR / "07_assembly" / "distilled_params_tuned.py"
    ns: dict = {}
    exec(spec.read_text(), ns)
    return ns["ALL_PAIRS"]


def _load_day_mids(day: int) -> pd.DataFrame:
    path = DATA_DIR / f"prices_round_5_day_{day}.csv"
    df = pd.read_csv(path, sep=";")
    # pivot to wide: timestamp x product → mid_price
    wide = df.pivot_table(index="timestamp", columns="product",
                          values="mid_price", aggfunc="last")
    wide = wide.sort_index().ffill()
    return wide


def _ols_simple(x: np.ndarray, y: np.ndarray) -> tuple[float, float]:
    """OLS y = β·x + α. Returns (β, α)."""
    n = len(x)
    if n == 0:
        return float("nan"), float("nan")
    xm, ym = x.mean(), y.mean()
    cov = ((x - xm) * (y - ym)).sum()
    var = ((x - xm) ** 2).sum()
    if var == 0:
        return float("nan"), float("nan")
    beta = cov / var
    alpha = ym - beta * xm
    return float(beta), float(alpha)


def _adf_p(arr: np.ndarray) -> float:
    if arr is None or len(arr) < 30:
        return float("nan")
    try:
        # autolag='AIC', maxlag default
        result = adfuller(arr, autolag="AIC")
        return float(result[1])
    except Exception:
        return float("nan")


def main():
    tuned_pairs = _load_tuned_pairs()
    print(f"[Phase C] tuned pairs: {len(tuned_pairs)}")

    print("[Phase C] loading prices for days 2/3/4 ...")
    mids_by_day = {d: _load_day_mids(d) for d in (2, 3, 4)}
    for d, w in mids_by_day.items():
        print(f"  day {d}: ticks={len(w)}, products={w.shape[1]}")

    rows = []
    for idx, (a, b, slope_full, intercept_full) in enumerate(
        ((p[0], p[1], p[2], p[3]) for p in tuned_pairs)
    ):
        # Series for day 2 (fit), day 3, day 4 (held-out)
        try:
            d2 = mids_by_day[2][[a, b]].dropna()
            d3 = mids_by_day[3][[a, b]].dropna()
            d4 = mids_by_day[4][[a, b]].dropna()
        except KeyError:
            rows.append({
                "pair_idx": idx, "a": a, "b": b,
                "slope_full": slope_full, "intercept_full": intercept_full,
                "missing_in_data": True,
            })
            continue

        # Convention: in algo, spread = mids[a] - slope*mids[b] - intercept,
        # tilt = -spread/PAIR_TILT_DIVISOR (clipped). So we regress a on b:
        #   a ≈ β·b + α  → spread = a - β·b - α  (β = slope, α = intercept)
        beta_d2, alpha_d2 = _ols_simple(d2[b].values, d2[a].values)

        # residuals using day-2-fit on each day
        if not (np.isnan(beta_d2) or np.isnan(alpha_d2)):
            resid_d2 = d2[a].values - beta_d2 * d2[b].values - alpha_d2
            resid_d3 = d3[a].values - beta_d2 * d3[b].values - alpha_d2
            resid_d4 = d4[a].values - beta_d2 * d4[b].values - alpha_d2
            adf_d3 = _adf_p(resid_d3)
            adf_d4 = _adf_p(resid_d4)
            adf_d2_self = _adf_p(resid_d2)
            resid_d3_mean = float(resid_d3.mean()); resid_d3_std = float(resid_d3.std())
            resid_d4_mean = float(resid_d4.mean()); resid_d4_std = float(resid_d4.std())
        else:
            adf_d3 = adf_d4 = adf_d2_self = float("nan")
            resid_d3_mean = resid_d3_std = resid_d4_mean = resid_d4_std = float("nan")

        beta_shift = (
            abs(beta_d2 - slope_full) / abs(slope_full)
            if slope_full != 0 and not np.isnan(beta_d2) else float("nan")
        )
        alpha_shift = (
            abs(alpha_d2 - intercept_full) / max(abs(intercept_full), 1.0)
            if not np.isnan(alpha_d2) else float("nan")
        )

        unstable_beta = (beta_shift > 0.30) if not np.isnan(beta_shift) else False
        unstable_adf = bool(
            (not np.isnan(adf_d3) and adf_d3 > 0.05) or
            (not np.isnan(adf_d4) and adf_d4 > 0.05)
        )
        unstable_any = unstable_beta or unstable_adf

        rows.append({
            "pair_idx": idx,
            "rank_in_ranking": idx - 8 if idx >= 9 else None,
            "is_added_pair": idx >= 39,
            "a": a, "b": b,
            "slope_full": slope_full, "intercept_full": intercept_full,
            "beta_day2": beta_d2, "intercept_day2": alpha_d2,
            "beta_shift_pct": beta_shift,
            "alpha_shift_rel": alpha_shift,
            "adf_p_d2_self_fit": adf_d2_self,
            "adf_p_d3_held_out": adf_d3,
            "adf_p_d4_held_out": adf_d4,
            "resid_d3_mean": resid_d3_mean, "resid_d3_std": resid_d3_std,
            "resid_d4_mean": resid_d4_mean, "resid_d4_std": resid_d4_std,
            "unstable_beta_30pct": unstable_beta,
            "unstable_adf_holdout": unstable_adf,
            "unstable_any": unstable_any,
        })

    df = pd.DataFrame(rows).sort_values(["unstable_any", "beta_shift_pct"],
                                        ascending=[False, False])
    df.to_csv(OUT / "pair_stability.csv", index=False)

    n_total = len(df)
    n_added = int(df["is_added_pair"].sum())
    n_unstable_total = int(df["unstable_any"].sum())
    n_unstable_added = int((df["is_added_pair"] & df["unstable_any"]).sum())
    n_beta_unstable = int(df["unstable_beta_30pct"].sum())
    n_adf_unstable = int(df["unstable_adf_holdout"].sum())
    n_beta_unstable_added = int((df["is_added_pair"] & df["unstable_beta_30pct"]).sum())

    # Refined "highly unstable": β shift >50% OR ADF >0.20 on BOTH held-out days
    highly = df[
        (df["beta_shift_pct"] > 0.50) |
        ((df["adf_p_d3_held_out"] > 0.20) & (df["adf_p_d4_held_out"] > 0.20))
    ]
    n_highly_unstable = len(highly)
    n_highly_unstable_added = int(highly["is_added_pair"].sum())

    summary = {
        "n_total_pairs": n_total,
        "n_added_pairs": n_added,
        "n_beta_shift_gt_30pct": n_beta_unstable,
        "n_beta_shift_gt_30pct_added": n_beta_unstable_added,
        "n_adf_holdout_gt_005": n_adf_unstable,
        "n_unstable_any": n_unstable_total,
        "n_unstable_among_added": n_unstable_added,
        "n_highly_unstable": n_highly_unstable,
        "n_highly_unstable_added": n_highly_unstable_added,
        "note": ("ADF holdout >0.05 fires on 166/166 pairs — the bar is too "
                 "loose for intraday Prosperity series. β-shift >30% (82 pairs) "
                 "is the discriminating signal; combined β>50% OR ADF>0.20 on "
                 "both days gives the 'highly unstable' set."),
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2, default=str))

    md = [
        "# Phase C — pair stability\n",
        f"- pairs analysed: {n_total} (of which {n_added} are added pairs at index ≥39)",
        f"- β shifts >30% (loose flag): **{n_beta_unstable}** "
        f"({n_beta_unstable_added} added)",
        f"- ADF holdout (d3 OR d4) p>0.05: {n_adf_unstable} — _bar too loose for intraday data_",
        f"- HIGHLY UNSTABLE (β>50% OR ADF>0.20 on both d3+d4): **{n_highly_unstable}** "
        f"({n_highly_unstable_added} added)",
        "",
        "**Note:** ADF >0.05 fires on every pair, indicating the residuals are "
        "broadly non-stationary on a daily basis even when fit globally. This "
        "suggests the strategy depends on **short-window mean-reversion** rather "
        "than true cointegration — interesting in itself. The discriminating "
        "criterion for overfit is **β-shift >30%**, with **β>50%** as the strict cut.",
        "",
        "## Top 20 most-unstable added pairs (β shift)",
        df[df["is_added_pair"]].nlargest(20, "beta_shift_pct")[
            ["pair_idx", "a", "b", "slope_full", "beta_day2", "beta_shift_pct",
             "adf_p_d3_held_out", "adf_p_d4_held_out"]
        ].to_markdown(index=False),
        "",
        "## Top 20 worst ADF holdout (max of d3,d4)",
        df.assign(max_adf=df[["adf_p_d3_held_out", "adf_p_d4_held_out"]].max(axis=1))
          .nlargest(20, "max_adf")[
            ["pair_idx", "a", "b", "is_added_pair", "max_adf",
             "adf_p_d3_held_out", "adf_p_d4_held_out", "beta_shift_pct"]
        ].to_markdown(index=False),
    ]
    (OUT / "summary.md").write_text("\n".join(md))
    print(f"[Phase C] {n_unstable_total}/{n_total} pairs unstable; {n_unstable_added} of those are added pairs")
    print(f"[Phase C] wrote pair_stability.csv, summary.json, summary.md")


if __name__ == "__main__":
    main()
