"""Save the Phase-1 winner as a real .py file (assembled from template)."""
import sys
from pathlib import Path

_PA = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_PA))
sys.path.insert(0, str(_PA / "01_robot_dishes_specialised"))

import importlib.util
spec = importlib.util.spec_from_file_location(
    "sweep_mod", _PA / "01_robot_dishes_specialised" / "02_run_sweep.py"
)
sm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sm)

# Winner: 1c_c10_b0.6 → log-only (no AR1), clip=10, inv_beta=0.6
src = sm.assemble(ar1_alpha=0.0, log_clip=10, inv_beta=0.6,
                   use_ar1=False, use_log=True)
out = _PA / "01_robot_dishes_specialised" / "04_combined_handler.py"
out.write_text(src)
print(f"WROTE: {out}")
