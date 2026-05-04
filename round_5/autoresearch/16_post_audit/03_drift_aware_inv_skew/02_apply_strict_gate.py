"""Phase 3 — re-evaluate per-product β cells with the strict 5-gate.

The mission requires:
  (a) Mean fold PnL ≥ baseline + 2K
  (b) Median fold PnL ≥ baseline median
  (c) ALL 5 folds positive Δ vs baseline
  (d) fold_min ≥ baseline fold_min
  (e) MaxDD ≤ 1.20× baseline maxDD

Plus: per-product attribution — TARGET product 3-day must rise.

The earlier `decisions.csv` used a relaxed rule (slack on mean) and
mis-marked many no-op β changes as "retained". This script applies the
strict gate, picks the best β per product (or β=0.20 if none pass), and
emits `decisions_strict.csv`.
"""
import csv
import json
import sys
from pathlib import Path

_PA = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_PA))
from _pa_lib import write_csv

OUT = _PA / "03_drift_aware_inv_skew"
BASELINE = json.loads((_PA / "00_baseline_lock" / "baseline.json").read_text())

base_folds = BASELINE["fold_pnls"]
base_fm = BASELINE["fold_min"]
base_fmed = BASELINE["fold_median"]
base_fmean = BASELINE["fold_mean"]
base_dd = BASELINE["max_dd_3day"]


def baseline_target_3day(prod):
    return sum(BASELINE["per_day_per_product"][str(d)].get(prod, 0)
               for d in (2, 3, 4))


def baseline_target_per_fold(prod):
    pp = {d: BASELINE["per_day_per_product"][str(d)].get(prod, 0) for d in (2, 3, 4)}
    return {"F1": pp[3], "F2": pp[4], "F3": pp[3], "F4": pp[2], "F5": pp[3]}


def evaluate(row):
    deltas = [int(row[f"F{i}_pnl"]) - base_folds[f"F{i}"] for i in range(1, 6)]
    fm = int(row["fold_min"])
    fmed = float(row["fold_median"])
    fmean = float(row["fold_mean"])
    dd = int(row["max_dd_3day"]) if row["max_dd_3day"] else None
    a = fmean >= base_fmean + 2000
    b = fmed >= base_fmed
    c = all(d > 0 for d in deltas)
    d = fm >= base_fm
    e = dd is None or base_dd is None or dd <= 1.20 * base_dd
    return {"gate_a": a, "gate_b": b, "gate_c": c, "gate_d": d, "gate_e": e,
            "all_pass": bool(a and b and c and d and e),
            "delta_fold_min": fm - base_fm,
            "delta_mean": fmean - base_fmean,
            "delta_median": fmed - base_fmed}


with (OUT / "per_product_beta_sweep.csv").open() as f:
    rows = list(csv.DictReader(f))

KS_FLAGGED = [
    "ROBOT_DISHES", "OXYGEN_SHAKE_CHOCOLATE", "MICROCHIP_OVAL",
    "MICROCHIP_SQUARE", "UV_VISOR_AMBER", "SLEEP_POD_POLYESTER",
    "MICROCHIP_TRIANGLE", "OXYGEN_SHAKE_EVENING_BREATH", "PANEL_1X4",
    "GALAXY_SOUNDS_BLACK_HOLES",
]

decisions = []
strict_retained = {}
for prod in KS_FLAGGED:
    base_target_3d = baseline_target_3day(prod)
    base_target_pf = baseline_target_per_fold(prod)
    base_target_fm = min(base_target_pf.values())
    prod_rows = [r for r in rows if r["label"].startswith(f"3b_{prod}_")]
    cands = []
    for r in prod_rows:
        beta = float(r["label"].rsplit("_b", 1)[-1])
        ev = evaluate(r)
        target_3d = int(r.get(f"{prod}_3day", 0)) if r.get(f"{prod}_3day") else 0
        target_pf = {
            "F1": int(r.get(f"{prod}_d3", 0) or 0),
            "F2": int(r.get(f"{prod}_d4", 0) or 0),
            "F3": int(r.get(f"{prod}_d3", 0) or 0),
            "F4": int(r.get(f"{prod}_d2", 0) or 0),
            "F5": int(r.get(f"{prod}_d3", 0) or 0),
        }
        target_fm = min(target_pf.values())
        target_3d_delta = target_3d - base_target_3d
        target_fm_delta = target_fm - base_target_fm
        passed_strict = ev["all_pass"] and target_3d_delta > 0 and target_fm_delta >= 0
        cands.append({
            "product": prod, "beta": beta, "passed_strict": passed_strict,
            "delta_fold_min": ev["delta_fold_min"],
            "delta_mean": ev["delta_mean"],
            "delta_median": ev["delta_median"],
            "all_pass_total": ev["all_pass"],
            "target_3d_delta": target_3d_delta,
            "target_fold_min_delta": target_fm_delta,
            "sharpe": float(r["sharpe_3day"]) if r["sharpe_3day"] else 0.0,
        })
    if any(c["passed_strict"] for c in cands):
        best = max(
            (c for c in cands if c["passed_strict"]),
            key=lambda c: (c["delta_fold_min"], c["sharpe"]),
        )
        chosen = best["beta"]
        retained = chosen != 0.20
    else:
        retained = False
        # report the candidate with highest fold_min for reference
        best = max(cands, key=lambda c: (c["delta_fold_min"], c["sharpe"]))
        chosen = 0.20
    if retained:
        strict_retained[prod] = chosen
    decisions.append({
        "product": prod, "chosen_beta": chosen, "retained_strict": retained,
        "any_passed_strict": any(c["passed_strict"] for c in cands),
        "best_delta_fold_min": best["delta_fold_min"],
        "best_delta_mean": best["delta_mean"],
        "best_delta_median": best["delta_median"],
        "best_target_3d_delta": best["target_3d_delta"],
        "best_target_fold_min_delta": best["target_fold_min_delta"],
        "best_passed_strict": best["passed_strict"],
        "best_beta": best["beta"],
    })

write_csv(decisions, OUT / "decisions_strict.csv")

print(f"Baseline: fold_min={base_fm}, fold_mean={base_fmean}, fold_median={base_fmed}\n")
print("Per-product strict-gate β decisions:")
for d in decisions:
    flag = "✓" if d["retained_strict"] else "✗"
    print(f"  {flag} {d['product']:32s} β={d['chosen_beta']}  "
          f"Δfm={d['best_delta_fold_min']:+,}  "
          f"Δmean={d['best_delta_mean']:+,.0f}  "
          f"Δmedian={d['best_delta_median']:+,.0f}  "
          f"target3d_Δ={d['best_target_3d_delta']:+,}  "
          f"strict={d['best_passed_strict']}")

print(f"\nRetained (strict): {strict_retained}")

with (OUT / "retained_betas_strict.json").open("w") as f:
    json.dump(strict_retained, f, indent=2)
