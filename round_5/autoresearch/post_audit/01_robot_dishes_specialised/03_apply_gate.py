"""Phase 1 — apply the strict 5-gate to every sweep cell, pick the winner.

Gates (mission-strict):
  (a) Mean fold PnL ≥ baseline + 2K
  (b) Median fold PnL ≥ baseline median
  (c) ALL 5 folds positive Δ vs baseline
  (d) fold_min ≥ baseline fold_min (proxy for bootstrap 5%-quantile)
  (e) MaxDD ≤ 1.20× baseline maxDD

Among gate-passing cells, decision = highest fold_min, tie-break by Sharpe.
Then mandatory per-product attribution: target ROBOT_DISHES 3-day must rise.
"""
import csv
import json
import sys
from pathlib import Path

_PA = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_PA))

OUT = _PA / "01_robot_dishes_specialised"
ABLATION = OUT / "ablation.csv"
BASELINE = json.loads((_PA / "00_baseline_lock" / "baseline.json").read_text())

base_folds = BASELINE["fold_pnls"]
base_fm = BASELINE["fold_min"]
base_fmed = BASELINE["fold_median"]
base_fmean = BASELINE["fold_mean"]
base_dd = BASELINE["max_dd_3day"]
base_dishes_3d = sum(BASELINE["per_day_per_product"][str(d)].get("ROBOT_DISHES", 0)
                     for d in (2, 3, 4))


def evaluate(row):
    deltas = [int(row[f"F{i}_pnl"]) - base_folds[f"F{i}"] for i in range(1, 6)]
    fm = int(row["fold_min"])
    fmed = float(row["fold_median"])
    fmean = float(row["fold_mean"])
    dd = int(row["max_dd_3day"]) if row["max_dd_3day"] else None
    dishes_3d = int(row["dishes_3day"])
    sharpe = float(row["sharpe_3day"]) if row["sharpe_3day"] else 0.0

    gate_a = fmean >= base_fmean + 2000
    gate_b = fmed >= base_fmed
    gate_c = all(d > 0 for d in deltas)
    gate_d = fm >= base_fm
    gate_e = dd is None or base_dd is None or dd <= 1.20 * base_dd
    target = dishes_3d > base_dishes_3d
    passed = gate_a and gate_b and gate_c and gate_d and gate_e and target
    return {
        "gate_a": gate_a, "gate_b": gate_b, "gate_c": gate_c,
        "gate_d": gate_d, "gate_e": gate_e, "target": target,
        "passed_strict": passed,
        "delta_fold_min": fm - base_fm,
        "delta_fold_median": fmed - base_fmed,
        "delta_mean": fmean - base_fmean,
        "delta_dishes_3d": dishes_3d - base_dishes_3d,
        "min_fold_delta": min(deltas),
        "max_dd_ratio": (dd / base_dd) if (dd and base_dd) else None,
        "sharpe": sharpe,
    }


with ABLATION.open() as f:
    rows = list(csv.DictReader(f))

evaluated = []
for r in rows:
    ev = evaluate(r)
    rec = {**r, **ev}
    evaluated.append(rec)

# Save evaluated CSV
out_csv = OUT / "ablation_with_gate.csv"
keys = list(evaluated[0].keys())
with out_csv.open("w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=keys)
    w.writeheader()
    for r in evaluated:
        w.writerow(r)

# Top-passing cells by variant
passed = [r for r in evaluated if r["passed_strict"]]
print(f"Total cells: {len(evaluated)}")
print(f"Passing strict gate: {len(passed)}")
print(f"  - 1b: {sum(1 for r in passed if r['label'].startswith('1b'))}")
print(f"  - 1c: {sum(1 for r in passed if r['label'].startswith('1c'))}")
print(f"  - 1d: {sum(1 for r in passed if r['label'].startswith('1d'))}")

if not passed:
    print("\nNO CELLS PASSED THE STRICT GATE. Listing top-5 by fold_min:")
    nearpass = sorted(evaluated, key=lambda r: -int(r["fold_min"]))[:5]
    for r in nearpass:
        print(f"  {r['label']}: fold_min={r['fold_min']}, "
              f"gates a={r['gate_a']} b={r['gate_b']} c={r['gate_c']} "
              f"d={r['gate_d']} e={r['gate_e']} target={r['target']}")
else:
    passed.sort(key=lambda r: (-int(r["fold_min"]), -r["sharpe"]))
    print("\nTop-10 PASSING cells (sorted by fold_min, then Sharpe):")
    for r in passed[:10]:
        print(f"  {r['label']:30s} fold_min={r['fold_min']:>6}  "
              f"median={r['fold_median']:>7}  mean={r['fold_mean']:>10}  "
              f"sharpe={r['sharpe']:.2f}  Δfm={r['delta_fold_min']:+,}  "
              f"Δdish={r['delta_dishes_3d']:+,}")

    winner = passed[0]
    print(f"\n=== WINNER ===")
    print(f"  label: {winner['label']}")
    print(f"  fold_min: {winner['fold_min']} (Δ={winner['delta_fold_min']:+,})")
    print(f"  fold_median: {winner['fold_median']} (Δ={winner['delta_fold_median']:+,.0f})")
    print(f"  fold_mean: {winner['fold_mean']} (Δ={winner['delta_mean']:+,.0f})")
    print(f"  sharpe: {winner['sharpe']}")
    print(f"  ROBOT_DISHES 3-day: {winner['dishes_3day']} (Δ={winner['delta_dishes_3d']:+,})")
    print(f"  max_dd_ratio: {winner['max_dd_ratio']:.3f}")
    # save winner JSON
    with (OUT / "winner.json").open("w") as f:
        json.dump(winner, f, indent=2, default=str)
