"""Phase H stress tests for strategy_final."""
import sys, csv
from pathlib import Path
sys.path.insert(0, "ROUND_5/autoresearch")
from utils.backtester import run_backtest

ALGO = "ROUND_5/batch1_summary/08_final_algo/strategy_final.py"
DATA = "ROUND_5/autoresearch/10_backtesting/data"
OUT = Path("ROUND_5/batch1_summary/08_final_algo/stress_tests.csv")
WF_OUT = Path("ROUND_5/batch1_summary/08_final_algo/walk_forward_results.csv")

def call(days, name, extra=None):
    extra = list(extra or [])
    res = run_backtest(ALGO, days, data_dir=DATA, run_name=name, extra_flags=extra)
    return {"name":name, "days":",".join(days), "extra":" ".join(extra),
            "total_pnl":res.total_pnl, "sharpe":res.sharpe_ratio,
            "max_dd":res.max_drawdown_abs, "calmar":res.calmar_ratio}

stress = []
# 1. baseline (--match-trades worse): already verified at 733,058
stress.append(call(["5-2","5-3","5-4"], "baseline_worse", ["--match-trades","worse"]))
# 2. --match-trades all (upper band)
stress.append(call(["5-2","5-3","5-4"], "match_all", ["--match-trades","all"]))
# 3. day removal: train d2 only, test d3+d4
stress.append(call(["5-3","5-4"], "drop_d2", ["--match-trades","worse"]))
# 4. day removal: keep d2+d4 only (drop d3)
stress.append(call(["5-2","5-4"], "drop_d3", ["--match-trades","worse"]))
# 5. day removal: keep d2+d3 only (drop d4)
stress.append(call(["5-2","5-3"], "drop_d4", ["--match-trades","worse"]))

# walk-forward folds (per-day standalone)
wf = []
wf.append(call(["5-2"], "wf_d2", ["--match-trades","worse"]))
wf.append(call(["5-3"], "wf_d3", ["--match-trades","worse"]))
wf.append(call(["5-4"], "wf_d4", ["--match-trades","worse"]))

with OUT.open("w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(stress[0].keys()))
    w.writeheader()
    [w.writerow(r) for r in stress]

with WF_OUT.open("w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(wf[0].keys()))
    w.writeheader()
    [w.writerow(r) for r in wf]

for r in stress:
    print(f"STRESS {r['name']}: pnl={r['total_pnl']} sharpe={r['sharpe']} dd={r['max_dd']}")
for r in wf:
    print(f"WF {r['name']}: pnl={r['total_pnl']} sharpe={r['sharpe']} dd={r['max_dd']}")

print("DONE")
