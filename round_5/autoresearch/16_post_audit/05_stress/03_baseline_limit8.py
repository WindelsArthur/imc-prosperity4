"""Phase 5 follow-up — does the limit=8 stress also break the baseline?

If the baseline drops the same %, then this is not a v04 weakness — it's a
property of the underlying make/take strategy at lim=10. If the baseline
holds up better, then v04's added components must rely on lim=10 more than
the baseline does (worth flagging in findings).
"""
import json
import sys
from pathlib import Path

_PA = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_PA))
from _pa_lib import run_algo, write_csv

OUT = _PA / "05_stress"
BASELINE_PATH = (_PA.parent / "parameter_tuning" / "audit" / "07_final"
                 / "algo1_drop_harmful_only.py")
BASELINE_JSON = json.loads((_PA / "00_baseline_lock" / "baseline.json").read_text())

products = [line.split(":")[0].split("=", 1)[1]
            for line in (_PA.parent / "utils" / "limit_flags.txt").read_text().split()]
extra = [f"--limit={p}:8" for p in products]

res = run_algo(BASELINE_PATH, match_mode="worse",
                extra_flags=extra, save_log_as="phase5_baseline_lim8")

base_fm = BASELINE_JSON["fold_min"]
out = {
    "F1_pnl": res.fold_pnls["F1"], "F2_pnl": res.fold_pnls["F2"],
    "F3_pnl": res.fold_pnls["F3"], "F4_pnl": res.fold_pnls["F4"],
    "F5_pnl": res.fold_pnls["F5"],
    "fold_min": res.fold_min, "fold_median": res.fold_median,
    "fold_mean": round(res.fold_mean, 1),
    "total_3day": res.total_3day,
    "sharpe_3day": res.sharpe_3day,
    "max_dd_3day": res.max_dd_3day,
    "fraction_of_full_lim_baseline": res.fold_min / base_fm,
}
write_csv([out], OUT / "limit_8_baseline.csv")

print(f"Baseline lim=8 fold_min: {res.fold_min:,}")
print(f"Baseline lim=10 fold_min: {base_fm:,}")
print(f"Baseline lim=8 / lim=10 ratio: {res.fold_min/base_fm*100:.1f}%")
print(f"v04 winner lim=8 fold_min: 86,295 (18.8% of v04 headline 459,226)")
