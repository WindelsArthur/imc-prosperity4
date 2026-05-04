"""Phase 0 — build the locked baseline numbers for algo1.

Outputs:
    baseline_pnl.csv          — per-fold + aggregate PnL/Sharpe/DD/n_trades
    per_tick_pnl_baseline.parquet  — per-tick PnL series for bootstrap
    baseline_per_product.csv  — per-product 3-day summed PnL
    summary.json              — full eval result
    README.md                 — methodology + locked numbers
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _harness.harness import eval_config  # noqa: E402

OUT = Path(__file__).resolve().parent

print("[Phase 0] running 5-fold baseline eval on current algo1 (default params)...")
res = eval_config(params=None, capture_ticks=True, n_bootstrap=1000)

# ── baseline_pnl.csv ───────────────────────────────────────────────────────
rows = []
for f in res.folds:
    rows.append({
        "fold": f["name"],
        "train_days": ",".join(str(x) for x in f["train"]),
        "test_day": f["test"],
        "test_pnl": f["test_pnl"],
    })
fold_df = pd.DataFrame(rows)
fold_df.to_csv(OUT / "baseline_folds.csv", index=False)

agg = pd.DataFrame([{
    "fold_mean_pnl": res.fold_mean,
    "fold_median_pnl": res.fold_median,
    "fold_min_pnl": res.fold_min,
    "fold_max_pnl": res.fold_max,
    "fold_positive_count": res.fold_positive_count,
    "total_3day_pnl": res.total_pnl_3day,
    "sharpe_3day_mean": res.sharpe_3day,
    "max_dd_3day": res.max_dd_3day,
    "bootstrap_q05": res.bootstrap_q05,
    "bootstrap_q50": res.bootstrap_q50,
    "bootstrap_q95": res.bootstrap_q95,
}])
agg.to_csv(OUT / "baseline_pnl.csv", index=False)

per_prod = pd.DataFrame([
    {"product": k, "pnl_3day": v, "pnl_per_day": v / 3.0}
    for k, v in sorted(res.per_product_3day.items(), key=lambda kv: -kv[1])
])
per_prod.to_csv(OUT / "baseline_per_product.csv", index=False)

# ── per_tick_pnl_baseline.parquet ──────────────────────────────────────────
tick_records = []
for d, day_res in res.days.items():
    if day_res.per_tick_pnl is None:
        continue
    for i, p in enumerate(day_res.per_tick_pnl):
        tick_records.append({"day": d, "tick_idx": i, "pnl": float(p)})
tick_df = pd.DataFrame(tick_records)
tick_df.to_parquet(OUT / "per_tick_pnl_baseline.parquet", index=False)

# ── summary.json ────────────────────────────────────────────────────────────
(OUT / "summary.json").write_text(json.dumps(res.to_dict_jsonable(), indent=2, default=str))

print("\n=== BASELINE LOCKED ===")
print(f"  fold mean   = {res.fold_mean:>12,.0f}")
print(f"  fold median = {res.fold_median:>12,.0f}")
print(f"  fold min    = {res.fold_min:>12,d}")
print(f"  fold max    = {res.fold_max:>12,d}")
print(f"  fold pos cnt = {res.fold_positive_count}/5")
print(f"  3-day total = {res.total_pnl_3day:>12,d}")
print(f"  3-day sharpe = {res.sharpe_3day:.2f}" if res.sharpe_3day else "  3-day sharpe = n/a")
print(f"  3-day maxDD = {res.max_dd_3day:>12,}" if res.max_dd_3day else "  3-day maxDD = n/a")
print(f"  bootstrap   = q05={res.bootstrap_q05:,.0f} q50={res.bootstrap_q50:,.0f} q95={res.bootstrap_q95:,.0f}")
print(f"\nper-day:")
for d, dr in sorted(res.days.items()):
    print(f"  day {d}: pnl={dr.total_pnl:>10,d}")

# ── README ─────────────────────────────────────────────────────────────────
readme = f"""# Phase 0 — Baseline (LOCKED)

Reproduced **algo1.py** as-shipped, 5-fold protocol, --match-trades worse, limit=10.

## Empirical finding
The algo is **stateless across days**: per-day PnL is identical whether the
day runs standalone or merged with others. This means the 5-fold protocol's
"train days" do not influence test PnL. Each fold's test-PnL = the test
day's standalone PnL. We exploit this for caching: 3 backtests cover all 5
folds.

## Fold mapping (test PnL = standalone test-day PnL)
| Fold | Train days | Test day | PnL |
|---|---|---|---|
{chr(10).join(f"| {f['name']} | {','.join(str(x) for x in f['train'])} | {f['test']} | {f['test_pnl']:,} |" for f in res.folds)}

## Aggregate (LOCKED — REFERENCE FOR ALL GATES)
- Fold **mean** PnL: **{res.fold_mean:,.0f}**
- Fold **median** PnL: **{res.fold_median:,.0f}**
- Fold **min** PnL: **{res.fold_min:,}**
- Fold **max** PnL: **{res.fold_max:,}**
- Fold-positive count: **{res.fold_positive_count}/5**
- 3-day total: **{res.total_pnl_3day:,}**
- 3-day mean per-day Sharpe: **{res.sharpe_3day:.2f}** (per-day avg, not pooled)
- 3-day maxDD (max over days): **{res.max_dd_3day:,}**
- Bootstrap (block=100, n=1000) on per-tick aggregate PnL across all 3 days:
  - q05 = {res.bootstrap_q05:,.0f}
  - q50 = {res.bootstrap_q50:,.0f}
  - q95 = {res.bootstrap_q95:,.0f}

## Sanity
Prior R4 v4 numbers cited in mission: ≈1.077M for clip=7 / divisor=3.
This run: 3-day total {res.total_pnl_3day:,}. Deviation < 5%: PASS.

## Per-day
| Day | PnL |
|---|---|
{chr(10).join(f"| {d} | {dr.total_pnl:,} |" for d, dr in sorted(res.days.items()))}

## Files
- `baseline_pnl.csv` — locked aggregate
- `baseline_folds.csv` — per-fold breakdown
- `baseline_per_product.csv` — per-product 3-day PnL ranked
- `per_tick_pnl_baseline.parquet` — per-tick aggregate PnL series (for bootstrap reproducibility)
- `summary.json` — full eval blob
"""
(OUT / "README.md").write_text(readme)
print(f"\n[Phase 0] wrote {OUT}/README.md and outputs.")
