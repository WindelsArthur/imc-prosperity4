"""Variant 1c — log-pair-only ROBOT_DISHES overlay (USE_AR1=False).

This is the **winning variant** of Phase 1. Because the winner happens to be
the log-pair-only sub-variant, the assembled algorithm is identical to
`04_combined_handler.py`. This file simply emits the same source through the
sweep template with USE_AR1=False, USE_LOG=True, log_clip=10, β_dishes=0.6.

Run: writes `03_log_pair_overlay.algo.py` (assembled), then runs the 5-fold
backtest and prints summary.
"""
import importlib.util
import json
import sys
from pathlib import Path

_PA = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_PA))
from _pa_lib import run_algo

OUT = _PA / "01_robot_dishes_specialised"
spec = importlib.util.spec_from_file_location("sweep_mod", OUT / "02_run_sweep.py")
sm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sm)

# Phase 1 winner cell: 1c_c10_b0.6
src = sm.assemble(ar1_alpha=0.0, log_clip=10, inv_beta=0.6,
                   use_ar1=False, use_log=True)
ALGO = OUT / "03_log_pair_overlay_algo.py"
ALGO.write_text(src)

if __name__ == "__main__":
    res = run_algo(ALGO, match_mode="worse",
                   save_log_as="phase1_log_overlay_eval")
    print(f"03_log_pair_overlay (=1c_c10_b0.6, log-pair-only):")
    print(f"  fold_min={res.fold_min:,}  fold_median={res.fold_median:,}  "
          f"fold_mean={res.fold_mean:,.1f}")
    print(f"  total_3day={res.total_3day:,}  sharpe={res.sharpe_3day}  "
          f"max_dd={res.max_dd_3day}")
    dishes_3d = sum(res.per_day_per_product.get(d, {}).get("ROBOT_DISHES", 0)
                    for d in (2, 3, 4))
    print(f"  ROBOT_DISHES 3-day = {dishes_3d:,}")
    print(f"\nNote: identical algo to 04_combined_handler.py (the winner).")
