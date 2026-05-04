"""Phase 2 Step 2a — fit AR(1) on Δmid per product per day, save coefs.

Cross-day-stability filter: a product survives if the AR(1) coef has the
SAME SIGN across days 2/3/4 AND the per-day mean coef magnitude > 0.05.

This is a coarse robustness gate — fitting AR(1) on tick-level data with
~10K observations per day, even small coefs are statistically significant
but may not be tradeable. We require sign consistency to filter regime
shifters (e.g., ROBOT_DISHES had φ=-0.0009/-0.0041/-0.2904 across days 2/3/4
— that 'pooled' -0.232 is entirely Day 4 and is regime-shifted).
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

import numpy as np
import pandas as pd

_PA = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_PA))
from _pa_lib import progress_log

OUT = _PA / "02_mr_skew_overlay"
OUT.mkdir(exist_ok=True)
DATA = _PA.parent.parent / "Data"

PRIORITY = [
    "OXYGEN_SHAKE_EVENING_BREATH",
    "ROBOT_IRONING",
    "PEBBLES_L",
    "PEBBLES_M",
    "PEBBLES_XS",
    "ROBOT_MOPPING",
    "OXYGEN_SHAKE_CHOCOLATE",
]
DAYS = (2, 3, 4)


def fit_ar1(diffs: np.ndarray):
    x = diffs[:-1]
    y = diffs[1:]
    mask = ~(np.isnan(x) | np.isnan(y))
    x, y = x[mask], y[mask]
    n = len(x)
    if n < 30:
        return None, None, n, None, None
    phi, c = np.polyfit(x, y, 1)
    yhat = phi * x + c
    ss_res = np.sum((y - yhat) ** 2)
    ss_tot = np.sum((y - np.mean(y)) ** 2)
    r2 = 1 - ss_res / max(ss_tot, 1e-12)
    var_d = float(np.var(diffs[~np.isnan(diffs)]))
    return float(phi), float(c), int(n), float(r2), var_d


def main() -> int:
    progress_log("Phase 2 Step 2a — AR(1) per priority product per day")
    rows = []
    for prod in PRIORITY:
        coefs, vars_d = {}, {}
        for d in DAYS:
            df = pd.read_csv(DATA / f"prices_round_5_day_{d}.csv", sep=";")
            df = df[df["product"] == prod]
            if df.empty:
                rows.append({"product": prod, "day": d, "n": 0,
                             "phi": None, "intercept": None, "r2": None,
                             "var_dmid": None})
                continue
            df = df.sort_values("timestamp")
            mid = ((df["bid_price_1"] + df["ask_price_1"]) / 2.0).to_numpy()
            diffs = np.diff(mid, prepend=np.nan)
            phi, c, n, r2, vd = fit_ar1(diffs)
            coefs[d] = phi
            vars_d[d] = vd
            rows.append({"product": prod, "day": d, "n": n, "phi": phi,
                         "intercept": c, "r2": r2, "var_dmid": vd})
        # cross-day summary
        valid = [v for v in coefs.values() if v is not None]
        if valid:
            mean_phi = float(np.mean(valid))
            std_phi = float(np.std(valid))
            same_sign = all(v > 0 for v in valid) or all(v < 0 for v in valid)
            survives = same_sign and abs(mean_phi) > 0.05
        else:
            mean_phi = std_phi = None
            same_sign = False
            survives = False
        rows.append({"product": prod, "day": "summary", "n": None,
                     "phi": mean_phi, "intercept": None, "r2": None,
                     "var_dmid": None,
                     "std_phi_xday": std_phi, "same_sign": same_sign,
                     "survives_filter": survives})

    keys = ["product", "day", "n", "phi", "intercept", "r2", "var_dmid",
            "std_phi_xday", "same_sign", "survives_filter"]
    with (OUT / "ar1_coefs_per_product.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        for r in rows:
            for k in keys:
                r.setdefault(k, None)
            w.writerow(r)

    surv = [r for r in rows if r.get("day") == "summary" and r.get("survives_filter")]
    progress_log(f"Phase 2 Step 2a — {len(surv)}/7 priority products survive cross-day stability")

    # Print summary
    print("AR(1) summary across days 2/3/4:")
    for prod in PRIORITY:
        per_day = {r["day"]: r["phi"] for r in rows if r["product"] == prod and r["day"] != "summary"}
        summ = next(r for r in rows if r["product"] == prod and r["day"] == "summary")
        d2, d3, d4 = per_day.get(2), per_day.get(3), per_day.get(4)
        d2s = f"{d2:+.4f}" if d2 is not None else "  --  "
        d3s = f"{d3:+.4f}" if d3 is not None else "  --  "
        d4s = f"{d4:+.4f}" if d4 is not None else "  --  "
        mean = f"{summ['phi']:+.4f}" if summ['phi'] is not None else "  --  "
        std = f"{summ['std_phi_xday']:.4f}" if summ['std_phi_xday'] is not None else "  --  "
        flag = "✓ survives" if summ.get("survives_filter") else "✗ DROPPED"
        print(f"  {prod:32s}  d2={d2s} d3={d3s} d4={d4s}  mean={mean}  std={std}  {flag}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
