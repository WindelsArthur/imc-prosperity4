"""Phase K — Ablation table for v2 components.

Builds 4 strategy variants by toggling features in strategy_v2:
    v1_baseline           : v1 from 12_final_strategy.
    v2_no_caps            : v2 without PROD_CAP (set all caps to 10).
    v2_no_snack_weights   : v2 with old equal-weight SNACKPACK basket signal.
    v2_no_sine_amber      : v2 without UV_VISOR_AMBER sine overlay.
    v2_full               : full v2.

Runs each with `--match-trades worse` over days 5-2/5-3/5-4 and
records per-product PnL, total, Sharpe, max DD.
"""
from __future__ import annotations

import csv
import shutil
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from utils.backtester import run_backtest
from utils.round5_products import ROUND5_PRODUCTS

OUT = Path(__file__).resolve().parent
ABL_DIR = OUT / "ablation_strategies"
ABL_DIR.mkdir(exist_ok=True)


# Patch helpers — we generate variants of strategy_v2 by string replacement.

def _read(path):
    return Path(path).read_text()


def _make_variants():
    base = (OUT / "strategy_v2.py").read_text()
    variants = {}

    # No caps
    no_caps = base.replace(
        "PROD_CAP = {\n",
        "PROD_CAP_DISABLED = {\n",
    ).replace(
        "def _cap(prod):\n    return PROD_CAP.get(prod, POSITION_LIMIT)",
        "def _cap(prod):\n    return POSITION_LIMIT"
    )
    variants["v2_no_caps"] = no_caps

    # No SNACK weighted basket — revert to equal-weight sum-50221
    no_sw = base.replace(
        "SNACK_WEIGHTS = {\n"
        "    \"SNACKPACK_CHOCOLATE\": -1.0,\n"
        "    \"SNACKPACK_PISTACHIO\":  0.1106,\n"
        "    \"SNACKPACK_RASPBERRY\":  0.0158,\n"
        "    \"SNACKPACK_STRAWBERRY\": -0.1379,\n"
        "    \"SNACKPACK_VANILLA\":   -0.9579,\n"
        "}",
        "SNACK_WEIGHTS = {\n"
        "    \"SNACKPACK_CHOCOLATE\": 1.0,\n"
        "    \"SNACKPACK_PISTACHIO\": 1.0,\n"
        "    \"SNACKPACK_RASPBERRY\": 1.0,\n"
        "    \"SNACKPACK_STRAWBERRY\": 1.0,\n"
        "    \"SNACKPACK_VANILLA\": 1.0,\n"
        "}"
    ).replace(
        "SNACK_SPREAD_TARGET = -19782.3",
        "SNACK_SPREAD_TARGET = 50221.0"
    ).replace(
        "SNACK_SPREAD_SD = 46.0",
        "SNACK_SPREAD_SD = 190.0"
    )
    variants["v2_no_snack_weights"] = no_sw

    # No sine
    no_sine = base.replace(
        "        if \"UV_VISOR_AMBER\" in mids:",
        "        if False and \"UV_VISOR_AMBER\" in mids:",
    )
    variants["v2_no_sine_amber"] = no_sine

    return variants


def main() -> None:
    variants = _make_variants()
    rows = []

    runs = [("v1_baseline", ROOT / "12_final_strategy" / "strategy.py"),
            ("v2_full", OUT / "strategy_v2.py")]
    for name, src in variants.items():
        path = ABL_DIR / f"{name}.py"
        path.write_text(src)
        runs.append((name, path))

    for name, path in runs:
        print(f"\n=== Running {name} ===")
        res = run_backtest(
            str(path), ["5-2", "5-3", "5-4"],
            data_dir=str(ROOT / "10_backtesting" / "data"),
            run_name=f"abl_{name}",
            extra_flags=["--match-trades", "worse"],
        )
        row = {
            "variant": name,
            "total_pnl": res.total_pnl,
            "sharpe": res.sharpe_ratio,
            "max_drawdown_abs": res.max_drawdown_abs,
            **{f"pnl_{p}": res.per_product.get(p, 0) for p in ROUND5_PRODUCTS},
        }
        rows.append(row)
        print(f"  total={res.total_pnl} sharpe={res.sharpe_ratio} dd={res.max_drawdown_abs}")

    fieldnames = ["variant", "total_pnl", "sharpe", "max_drawdown_abs"] \
                 + [f"pnl_{p}" for p in ROUND5_PRODUCTS]
    with (OUT / "ablation_table.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow(r)

    # Summary
    print("\n=== Summary ===")
    for r in rows:
        print(f"  {r['variant']:<25} total={r['total_pnl']:>10}  sharpe={r['sharpe']}")


if __name__ == "__main__":
    main()
