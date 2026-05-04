"""Smoke test: assemble one cell, run, verify it parses correctly."""
import sys
from pathlib import Path

_PA = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_PA))
sys.path.insert(0, str(_PA / "01_robot_dishes_specialised"))

from importlib import import_module
import importlib.util

# Direct import, since 02_run_sweep.py starts with a digit
spec = importlib.util.spec_from_file_location(
    "sweep_mod", _PA / "01_robot_dishes_specialised" / "02_run_sweep.py"
)
sweep_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sweep_mod)


def main():
    # cell with all features enabled, mid params
    r = sweep_mod.run_one(
        "smoke_a1.0_c5_b0.20",
        ar1_alpha=1.0, log_clip=5, inv_beta=0.20,
        use_ar1=True, use_log=True
    )
    print("SMOKE CELL RESULT:")
    for k, v in r.items():
        print(f"  {k}: {v}")
    base_fold_min = 446200
    delta = r["fold_min"] - base_fold_min
    print(f"\nfold_min Δ vs baseline: {delta:+,}")


if __name__ == "__main__":
    main()
