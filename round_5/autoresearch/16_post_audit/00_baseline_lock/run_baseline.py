"""Phase 0 — lock the baseline.

Runs the audit's chosen runner-up (algo1_drop_harmful_only.py) once with
match_mode='worse' and saves the resulting per-fold and per-product PnL to
audit_baseline.csv. Verifies reproduction within 5% of the audit's
candidates.csv numbers (489,823 / 456,258 / 446,200; fold_min 446,200).
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

_PA = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_PA))
from _pa_lib import run_algo, baseline_summary, progress_log

BASELINE = (
    _PA.parent / "parameter_tuning" / "audit" / "07_final" / "algo1_drop_harmful_only.py"
).resolve()
OUT_DIR = _PA / "00_baseline_lock"
OUT_DIR.mkdir(exist_ok=True)


def main() -> int:
    progress_log(f"Phase 0 START — locking baseline {BASELINE.name}")
    res = run_algo(BASELINE, match_mode="worse",
                   save_log_as="baseline_drop_harmful_only")

    print(f"per-day PnL: {res.per_day_pnl}")
    print(f"folds:       {res.fold_pnls}")
    print(f"fold_min={res.fold_min}  fold_median={res.fold_median}  "
          f"fold_mean={res.fold_mean:.1f}")
    print(f"3-day total={res.total_3day}  sharpe={res.sharpe_3day}  "
          f"max_dd={res.max_dd_3day}  elapsed={res.elapsed_s:.1f}s")

    # Reproduction check vs audit/07_final/candidates.csv row v_drop_harmful_only
    expected = {2: 489823, 3: 456258, 4: 446200}
    actual = res.per_day_pnl
    rep_rows = []
    max_pct_diff = 0.0
    for d, exp in expected.items():
        act = actual.get(d, 0)
        diff = act - exp
        pct = abs(diff) / max(abs(exp), 1) * 100
        max_pct_diff = max(max_pct_diff, pct)
        rep_rows.append({"day": d, "expected": exp, "actual": act,
                         "abs_diff": diff, "pct_diff": round(pct, 3)})
    if max_pct_diff > 5.0:
        progress_log(f"Phase 0 ERROR — reproduction off by {max_pct_diff:.1f}% (>5%)")
        print(f"REPRODUCTION FAILED: max_pct_diff={max_pct_diff:.2f}% > 5%",
              file=sys.stderr)
        return 1

    progress_log(f"Phase 0 — baseline locked. fold_min={res.fold_min}, "
                 f"max_pct_diff={max_pct_diff:.2f}%")

    # Save the full result
    pp_3day = res.per_product_total_3day()
    summary_csv = OUT_DIR / "audit_baseline.csv"
    with summary_csv.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["section", "key", "value"])
        for d, v in sorted(res.per_day_pnl.items()):
            w.writerow(["per_day_pnl", f"day_{d}", v])
        for fk, v in res.fold_pnls.items():
            w.writerow(["fold_pnls", fk, v])
        w.writerow(["aggregate", "fold_min", res.fold_min])
        w.writerow(["aggregate", "fold_median", res.fold_median])
        w.writerow(["aggregate", "fold_mean", round(res.fold_mean, 1)])
        w.writerow(["aggregate", "total_3day", res.total_3day])
        w.writerow(["aggregate", "sharpe_3day", res.sharpe_3day])
        w.writerow(["aggregate", "max_dd_3day", res.max_dd_3day])
        for p, v in sorted(pp_3day.items()):
            w.writerow(["per_product_3day", p, v])
        for d in sorted(res.per_day_per_product):
            for p, v in sorted(res.per_day_per_product[d].items()):
                w.writerow([f"per_product_day_{d}", p, v])

    rep_csv = OUT_DIR / "reproduction_check.csv"
    with rep_csv.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["day", "expected", "actual",
                                          "abs_diff", "pct_diff"])
        w.writeheader()
        for r in rep_rows:
            w.writerow(r)

    # JSON snapshot for downstream phases
    snap = {
        "algo": str(BASELINE),
        "per_day_pnl": res.per_day_pnl,
        "per_day_per_product": res.per_day_per_product,
        "fold_pnls": res.fold_pnls,
        "fold_min": res.fold_min,
        "fold_median": res.fold_median,
        "fold_mean": res.fold_mean,
        "total_3day": res.total_3day,
        "sharpe_3day": res.sharpe_3day,
        "max_dd_3day": res.max_dd_3day,
    }
    with (OUT_DIR / "baseline.json").open("w") as f:
        json.dump(snap, f, indent=2)

    print(f"\nWROTE: {summary_csv}")
    print(f"WROTE: {rep_csv}")
    print(f"WROTE: {OUT_DIR/'baseline.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
