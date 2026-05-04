# Phase 0 — Baseline (LOCKED)

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
| F1 | 2 | 3 | 363,578 |
| F2 | 2,3 | 4 | 354,448 |
| F3 | 4 | 3 | 363,578 |
| F4 | 3,4 | 2 | 364,990 |
| F5 | 2,4 | 3 | 363,578 |

## Aggregate (LOCKED — REFERENCE FOR ALL GATES)
- Fold **mean** PnL: **362,034**
- Fold **median** PnL: **363,578**
- Fold **min** PnL: **354,448**
- Fold **max** PnL: **364,990**
- Fold-positive count: **5/5**
- 3-day total: **1,083,016**
- 3-day mean per-day Sharpe: **63.08** (per-day avg, not pooled)
- 3-day maxDD (max over days): **24,692**
- Bootstrap (block=100, n=1000) on per-tick aggregate PnL across all 3 days:
  - q05 = 943,838
  - q50 = 1,085,215
  - q95 = 1,262,435

## Sanity
Prior R4 v4 numbers cited in mission: ≈1.077M for clip=7 / divisor=3.
This run: 3-day total 1,083,016. Deviation < 5%: PASS.

## Per-day
| Day | PnL |
|---|---|
| 2 | 364,990 |
| 3 | 363,578 |
| 4 | 354,448 |

## Files
- `baseline_pnl.csv` — locked aggregate
- `baseline_folds.csv` — per-fold breakdown
- `baseline_per_product.csv` — per-product 3-day PnL ranked
- `per_tick_pnl_baseline.parquet` — per-tick aggregate PnL series (for bootstrap reproducibility)
- `summary.json` — full eval blob
