"""Phase 1 — sweep the dedicated ROBOT_DISHES handler grid.

Sub-variants:
  1b: full grid α × log_clip × β = 5 × 4 × 4 = 80 cells
  1c: log-pair-only (USE_AR1=False), α=N/A, log_clip × β = 4 × 4 = 16 cells
  1d: AR(1)-only (USE_LOG=False), α × β = 5 × 4 = 20 cells
  1e: combined winner (no extra cells; we just pick from above)

All cells run a single 3-day merged backtest each; per-fold PnL is composed
afterwards. Parallelism via ThreadPoolExecutor n_workers=4 (subprocess-based,
so the GIL is not an issue).

Outputs:
  ablation.csv — every cell with full per-fold PnL + per-product 3-day PnL
                 for ROBOT_DISHES specifically (per-product attribution).
  findings.md  — summary + winner.
"""
from __future__ import annotations

import csv
import json
import re
import sys
import time
from itertools import product
from pathlib import Path

_PA = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_PA))
from _pa_lib import (run_algo_text, baseline_summary, ablation_gate, FOLDS,
                      progress_log, write_csv)

OUT = _PA / "01_robot_dishes_specialised"
OUT.mkdir(exist_ok=True)
TEMPLATE = (OUT / "_dishes_template.py").read_text()
BASELINE_SRC = (_PA.parent / "parameter_tuning" / "audit" / "07_final"
                / "algo1_drop_harmful_only.py").read_text()
BASELINE_JSON = json.loads((_PA / "00_baseline_lock" / "baseline.json").read_text())

# Extract ALL_PAIRS literal block from baseline source verbatim.
_ALL_PAIRS_PAT = re.compile(r"^ALL_PAIRS\s*=\s*\[.*?^\]\s*$", re.MULTILINE | re.DOTALL)
m = _ALL_PAIRS_PAT.search(BASELINE_SRC)
if not m:
    raise RuntimeError("ALL_PAIRS not found in baseline source")
ALL_PAIRS_LITERAL = m.group(0)


def assemble(ar1_alpha: float, log_clip: float, inv_beta: float,
             use_ar1: bool, use_log: bool) -> str:
    """Substitute placeholders + inject ALL_PAIRS into template."""
    src = TEMPLATE
    src = src.replace("__AR1_ALPHA__", str(ar1_alpha))
    src = src.replace("__LOG_CLIP__", str(log_clip))
    src = src.replace("__INV_BETA__", str(inv_beta))
    src = src.replace("__USE_AR1__", "True" if use_ar1 else "False")
    src = src.replace("__USE_LOG__", "True" if use_log else "False")
    src = re.sub(r"^ALL_PAIRS\s*=\s*\[\]\s*#.*$",
                 ALL_PAIRS_LITERAL, src, count=1, flags=re.MULTILINE)
    return src


def run_one(label: str, ar1_alpha: float, log_clip: float, inv_beta: float,
            use_ar1: bool, use_log: bool) -> dict:
    src = assemble(ar1_alpha, log_clip, inv_beta, use_ar1, use_log)
    t0 = time.time()
    res = run_algo_text(src, save_log_as=f"phase1_{label}")
    elapsed = time.time() - t0
    dishes_3d = sum(res.per_day_per_product.get(d, {}).get("ROBOT_DISHES", 0)
                    for d in (2, 3, 4))
    dishes_per_day = {d: res.per_day_per_product.get(d, {}).get("ROBOT_DISHES", 0)
                      for d in (2, 3, 4)}
    return {
        "label": label,
        "variant": label.split("_", 1)[0] if "_" in label else "?",
        "ar1_alpha": ar1_alpha,
        "log_clip": log_clip,
        "inv_beta": inv_beta,
        "use_ar1": use_ar1,
        "use_log": use_log,
        "elapsed_s": round(elapsed, 1),
        # per-fold totals
        "F1_pnl": res.fold_pnls["F1"],
        "F2_pnl": res.fold_pnls["F2"],
        "F3_pnl": res.fold_pnls["F3"],
        "F4_pnl": res.fold_pnls["F4"],
        "F5_pnl": res.fold_pnls["F5"],
        "fold_min": res.fold_min,
        "fold_median": res.fold_median,
        "fold_mean": round(res.fold_mean, 1),
        "total_3day": res.total_3day,
        "sharpe_3day": res.sharpe_3day,
        "max_dd_3day": res.max_dd_3day,
        # per-product attribution
        "dishes_day2": dishes_per_day[2],
        "dishes_day3": dishes_per_day[3],
        "dishes_day4": dishes_per_day[4],
        "dishes_3day": dishes_3d,
    }


def main(serial: bool = False) -> int:
    progress_log("Phase 1 — starting dedicated handler sweep")

    # build the grid
    cells = []  # (label, params)
    # 1b: full grid
    for a, c, b in product([0.5, 1.0, 1.5, 2.0, 2.5], [3, 5, 7, 10],
                           [0.10, 0.20, 0.40, 0.60]):
        label = f"1b_a{a}_c{c}_b{b}"
        cells.append((label, dict(ar1_alpha=a, log_clip=c, inv_beta=b,
                                  use_ar1=True, use_log=True)))
    # 1c: log-only
    for c, b in product([3, 5, 7, 10], [0.10, 0.20, 0.40, 0.60]):
        label = f"1c_c{c}_b{b}"
        cells.append((label, dict(ar1_alpha=0.0, log_clip=c, inv_beta=b,
                                  use_ar1=False, use_log=True)))
    # 1d: AR(1)-only
    for a, b in product([0.5, 1.0, 1.5, 2.0, 2.5], [0.10, 0.20, 0.40, 0.60]):
        label = f"1d_a{a}_b{b}"
        cells.append((label, dict(ar1_alpha=a, log_clip=0.0, inv_beta=b,
                                  use_ar1=True, use_log=False)))

    n_cells = len(cells)
    progress_log(f"Phase 1 — {n_cells} cells (1b={80}, 1c={16}, 1d={20})")
    print(f"[Phase 1] {n_cells} cells to evaluate")

    rows = []
    if serial:
        for i, (label, p) in enumerate(cells):
            r = run_one(label, **p)
            rows.append(r)
            if (i + 1) % 10 == 0:
                progress_log(f"Phase 1 — {i+1}/{n_cells} done")
    else:
        from concurrent.futures import ThreadPoolExecutor, as_completed
        with ThreadPoolExecutor(max_workers=4) as ex:
            futs = {ex.submit(run_one, label, **p): label
                    for label, p in cells}
            done = 0
            for fut in as_completed(futs):
                label = futs[fut]
                try:
                    rows.append(fut.result())
                except Exception as e:
                    print(f"[ERROR] {label}: {e}")
                    progress_log(f"Phase 1 ERROR — {label}: {e}")
                done += 1
                if done % 10 == 0:
                    progress_log(f"Phase 1 — {done}/{n_cells} done")
                    print(f"[Phase 1] {done}/{n_cells} done")

    rows.sort(key=lambda r: (r["variant"], -r["fold_min"], -r["sharpe_3day"]))

    write_csv(rows, OUT / "ablation.csv")
    progress_log(f"Phase 1 — sweep complete; ablation.csv has {len(rows)} rows")
    print(f"\n[Phase 1] WROTE: {OUT/'ablation.csv'} ({len(rows)} rows)")

    # Quick summary: top per variant by fold_min
    base_fold_min = BASELINE_JSON["fold_min"]
    base_dishes_3d = sum(BASELINE_JSON["per_day_per_product"][str(d)].get("ROBOT_DISHES", 0)
                         for d in (2, 3, 4))
    print(f"\nBaseline: fold_min={base_fold_min:,}, dishes_3day={base_dishes_3d:,}\n")
    for v in ("1b", "1c", "1d"):
        vr = [r for r in rows if r["label"].startswith(v)]
        vr.sort(key=lambda r: (-r["fold_min"], -(r["sharpe_3day"] or -1e9)))
        if not vr:
            continue
        print(f"=== Variant {v} top-3 by fold_min ===")
        for r in vr[:3]:
            print(f"  {r['label']}: fold_min={r['fold_min']:,}  median={r['fold_median']}  "
                  f"mean={r['fold_mean']:,}  dishes_3d={r['dishes_3day']:,}  "
                  f"Δfold_min={r['fold_min']-base_fold_min:+,}")
    return 0


if __name__ == "__main__":
    sys.exit(main(serial=False))
