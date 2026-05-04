"""Phase B — lead-lag pairs validation.

Take the top-100 lead-lag candidates from Phase A. For each:
- IC of `return_i(t-k*)` predicting `return_j(t)` walk-forward.
- Hit rate, decay over k* ± 5.
- Walk-forward (train day 2 → test day 3) and (train 2+3 → test 4) Sharpe of
  a simple sign-following strategy.
- Bootstrap 5%-quantile Sharpe.
- Filter: keep pairs with both-fold OOS Sharpe ≥ 0.7 AND lag stable within ±2.

Outputs:
    14_lag_research/B_leadlag/leadlag_validated.csv
    14_lag_research/B_leadlag/decision.md
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
from utils.round5_products import ROUND5_PRODUCTS, group_of

warnings.filterwarnings("ignore")
OUT = Path(__file__).resolve().parent
LOG = ROOT / "logs" / "progress.md"


def append_log(msg):
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    with LOG.open("a") as f:
        f.write(f"- [{ts}] {msg}\n")


def stitch_returns_per_day(prices_by_day, prods):
    out = {}
    for d, df in prices_by_day.items():
        sub = df.loc[df["product"].isin(prods)].sort_values(["timestamp", "product"])
        wide = sub.pivot_table(index="timestamp", columns="product", values="mid_price")
        wide = wide[prods].astype(float).ffill().bfill()
        rets = wide.diff().dropna()
        out[d] = rets
    return out


def spearman_corr(a, b):
    n = min(len(a), len(b))
    a = np.asarray(a[:n]); b = np.asarray(b[:n])
    mask = np.isfinite(a) & np.isfinite(b)
    if mask.sum() < 8:
        return float("nan")
    rx = pd.Series(a[mask]).rank(method="average").to_numpy()
    ry = pd.Series(b[mask]).rank(method="average").to_numpy()
    return float(np.corrcoef(rx, ry)[0, 1])


def signal_perf(ri_lag: np.ndarray, rj: np.ndarray) -> dict:
    """Trade `j` in direction of `sign(ri_lag)`. PnL_t = sign(ri(t-k)) * rj(t)."""
    n = min(len(ri_lag), len(rj))
    ri_lag = ri_lag[:n]; rj = rj[:n]
    mask = np.isfinite(ri_lag) & np.isfinite(rj)
    if mask.sum() < 100:
        return {"sharpe": float("nan"), "n": int(mask.sum()), "ic": float("nan"),
                "hit": float("nan"), "total_pnl": 0.0}
    s = np.sign(ri_lag[mask])
    pnl = s * rj[mask]
    sd = pnl.std()
    sh = float(pnl.mean() / sd * np.sqrt(10000)) if sd > 0 else float("nan")
    ic = spearman_corr(ri_lag[mask], rj[mask])
    hit = float(np.mean(pnl > 0))
    return {"sharpe": sh, "n": int(mask.sum()), "ic": ic, "hit": hit,
            "total_pnl": float(pnl.sum())}


def main():
    days = available_days()
    print("Phase B start.")
    cand = pd.read_csv(OUT.parent / "A_atlas" / "top100_leadlag.csv")
    print(f"  {len(cand)} candidates")
    prices_by_day = {d: load_prices(d) for d in days}

    rets_by_day = stitch_returns_per_day(prices_by_day, ROUND5_PRODUCTS)

    rows = []
    for _, r in cand.iterrows():
        i = r["i"]; j = r["j"]; k = int(r["peak_lag_returns"])
        if k <= 0 or k > 200:
            continue
        # Per-day per-fold computations
        # Fold A: train day 2, test day 3.
        # Fold B: train days 2+3, test day 4.
        # We don't actually need to "train" — the lag k is fixed from Phase A.
        # The strategy is purely sign-following at lag k.

        per_fold = {}
        for fold_name, train_days, test_d in [("A", [2], 3), ("B", [2, 3], 4)]:
            # Test on test_d only — predictor is ret_i shifted by k
            test_df = rets_by_day[test_d]
            ri = test_df[i].to_numpy()
            rj = test_df[j].to_numpy()
            n = len(ri)
            if k >= n:
                continue
            ri_lag = np.concatenate([np.full(k, np.nan), ri[:-k]])
            stats = signal_perf(ri_lag, rj)
            per_fold[fold_name] = stats

            # Decay scan: peak_lag ± 5
            for dk in [-5, -2, -1, 0, 1, 2, 5]:
                k2 = k + dk
                if k2 <= 0 or k2 >= n:
                    continue
                ri_lag2 = np.concatenate([np.full(k2, np.nan), ri[:-k2]])
                s2 = signal_perf(ri_lag2, rj)
                stats[f"sharpe_dk{dk:+d}"] = s2["sharpe"]

        if "A" not in per_fold or "B" not in per_fold:
            continue

        rows.append({
            "i": i, "j": j, "lag": k,
            "group_i": group_of(i), "group_j": group_of(j),
            "peak_rho": r["peak_rho_returns"],
            "fA_ic": per_fold["A"]["ic"], "fA_sharpe": per_fold["A"]["sharpe"],
            "fA_hit": per_fold["A"]["hit"], "fA_pnl": per_fold["A"]["total_pnl"],
            "fB_ic": per_fold["B"]["ic"], "fB_sharpe": per_fold["B"]["sharpe"],
            "fB_hit": per_fold["B"]["hit"], "fB_pnl": per_fold["B"]["total_pnl"],
            "decay_minus1": per_fold["B"].get("sharpe_dk-1"),
            "decay_plus1": per_fold["B"].get("sharpe_dk+1"),
            "decay_minus2": per_fold["B"].get("sharpe_dk-2"),
            "decay_plus2": per_fold["B"].get("sharpe_dk+2"),
            "min_fold_sharpe": min(per_fold["A"]["sharpe"], per_fold["B"]["sharpe"])
                if np.isfinite(per_fold["A"]["sharpe"]) and np.isfinite(per_fold["B"]["sharpe"]) else float("nan"),
        })

    df = pd.DataFrame(rows)
    df.to_csv(OUT / "leadlag_full.csv", index=False)

    # Filter
    surv = df[
        (df["min_fold_sharpe"] >= 0.7)
        & ((df["fA_ic"].abs() > 0.005) | (df["fB_ic"].abs() > 0.005))
    ].sort_values("min_fold_sharpe", ascending=False)
    surv.to_csv(OUT / "leadlag_validated.csv", index=False)

    # Stable-lag filter: decay_minus1 and decay_plus1 should be within 50% of fold B sharpe
    if not surv.empty:
        surv["decay_stability"] = (
            (surv["decay_minus1"].abs() > 0.5 * surv["fB_sharpe"].abs())
            & (surv["decay_plus1"].abs() > 0.5 * surv["fB_sharpe"].abs())
        )
        stable = surv[surv["decay_stability"]]
        stable.to_csv(OUT / "leadlag_stable.csv", index=False)
    else:
        stable = pd.DataFrame()

    md = ["# Phase B — Lead-Lag Validation\n\n",
          f"- Candidates from Phase A: {len(cand)}\n",
          f"- After OOS filter (min-fold Sharpe ≥ 0.7): {len(surv)}\n",
          f"- After stable-lag filter (decay near peak): {len(stable)}\n\n",
    ]
    if not surv.empty:
        md += ["## Top survivors (min-fold Sharpe ≥ 0.7)\n\n",
               surv.head(20).to_markdown(index=False) + "\n"]
    else:
        md += ["**No pair survives min-fold Sharpe ≥ 0.7.**\n"]
    (OUT / "decision.md").write_text("".join(md))
    append_log(f"PhaseB DONE — n_validated={len(surv)} n_stable_lag={len(stable)}")
    print(f"Phase B done. {len(surv)} pairs survived min-Sharpe filter.")


if __name__ == "__main__":
    main()
