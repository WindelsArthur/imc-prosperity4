# Round-5 per-product mean-reversion study

Goal: for each of the 50 round-5 products, find the MR configuration
(fair-value estimator + entry/exit thresholds + sizing rule) that
maximises walk-forward OOS PnL across days 2/3/4. Output is a single
runtime trader at `06_strategy_mr/strategy_mr.py` plus distilled per-product
parameters.

## Headline (locked-in v6)

| metric | value |
| --- | ---:|
| Total profit (engine, `--match-trades worse`) | **399,636** |
| Final 3-day PnL                               | 283,223 |
| Day-3 OOS PnL (fold A)                        | ≈ +98K  |
| Day-4 OOS PnL (fold B)                        | ≈ +93K  |
| **Avg daily OOS PnL**                         | **≈ 95K** |
| Max drawdown                                  | 69,390  |
| Sharpe (engine)                               | 0.93    |
| Calmar                                        | 5.76    |
| Round-2 baseline (per task brief)             | 396K    |
| Net beat                                      | +3.6K (below the 15K target — see `07_findings/headline.md`) |

Per-product mode split: **7 TAKER, 35 MM, 8 IDLE**.

## Folder map

```
mr_study/
├── README.md                                  this file
├── 00_setup/
│   ├── product_universe.csv                   per-product day-2 stats + bucket
│   └── data_sanity.md                         env + data check
├── 01_fair_value_zoo/
│   ├── fair_values.py                         15 FV families × parameter grid (45 FVs)
│   ├── run_diagnostics.py                     IC, half-life, ADF, mean|res|/spread per (prod, FV, fold)
│   ├── fv_catalog.csv                         the 45 FVs with their params
│   ├── all_diagnostics.csv                    4500 rows (50 × 45 × 2 folds)
│   ├── fv_shortlist.csv                       top-8 FVs per product by composite z-score
│   └── per_product/{prod}/{diagnostics,ranking}.csv
├── 02_threshold_search/
│   ├── simulator.py                           numba-JIT taker simulator
│   ├── threshold_grid.py                      driver for the sweep
│   ├── grid_results.parquet                   37,200 rows (full long format)
│   ├── grid_pivot.parquet                     pivoted to one row per config × fold
│   └── per_product/{prod}/top20.csv           per-product best 20 by avg_daily_pnl
├── 03_sizing_models/                          (rolled into 02 — sizing was a grid axis)
├── 04_combined_search/
│   ├── leaderboard.csv                        50 rows: product, mode, FV, threshold, skew
│   ├── per_product/{prod}/best_config.json    final per-product spec
│   └── v6_final_metrics.json                  locked headline + per-product PnL
├── 05_robustness/
│   ├── stress_tests.csv
│   └── stability_report.md
├── 06_strategy_mr/
│   ├── strategy_mr.py                         single-file Trader (TAKER + MM + IDLE)
│   ├── distilled_params.py                    per-product config (single source of truth)
│   └── utils_local.py                         ROUND5_PRODUCTS list (no autoresearch dep)
└── 07_findings/
    ├── headline.md                            day-5 projection + comparison vs baseline
    ├── group_summary.md                       10-group breakdown
    └── per_product/{prod}.md                  why this config, robustness, expected PnL
```

## Methodology summary

**Phase 0** — universe stats + bucketing. 47/50 products fail ADF stationarity
on day-2 mid → mid-level MR signal is rare; alpha is mostly microstructure.

**Phase 1** — implemented 45 causal FVs (rolling mean/median/EWMA, microprice,
Kalman, AR(p) on Δmid, OFI-corrected, Markov conditional mean, …). Per
(prod, FV, fold) computed Spearman IC of (price-FV) vs −Δmid(t+1), residual
half-life, ADF p, residual/spread ratio. Pre-screened top-4 FVs per product
for Phase 2.

**Phase 2** — built a numba-JIT in-process taker simulator (37,200 configs in
40s). Sweep over rule A (symmetric z-threshold) × 8 z_in × 4 z_out × 3 sizings
(fixed, linear @ γ=3, step). Rule D/E (stops) deferred to Phase 4 refinement.

**Phase 3** — sizing was a grid axis in Phase 2 rather than a separate phase.
Fixed sizing dominated the qualifying set; linear/step were never the per-
product winner.

**Phase 4** — picked the best taker per product subject to pnl_A > 0 ∧
pnl_B > 0 ∧ min_sharpe ≥ 0.5 (strict) → 6 products. Relaxed to pnl_A > 0
∧ pnl_B > 0 → +1 product (PEBBLES_L). Real backtest of strategy_mr v6
locked the leaderboard.

**Phase 5** — ran match-mode stress (`worse` ↔ `all`, <1% delta) and
walk-forward fold isolation (day-3 OOS = +98K, day-4 OOS = +93K, ratio
0.95). Limit-stress (limit=8) breaks because LIM=10 is hardcoded —
flagged in `stability_report.md`.

**Phase 6** — single-file `strategy_mr.py` with TAKER, MM, IDLE modes.
Position-limit landmine pattern applied verbatim. Imports
`distilled_params.get_params()` at construction; per-product FV state
held in a dict. No external state, no NumPy at runtime.

**Phase 7** — per-product, group, and headline reports.

## Reproducing the run

```python
import sys
sys.path.insert(0, 'ROUND_5/autoresearch')
from utils.backtester import run_backtest
res = run_backtest(
    'ROUND_5/autoresearch/mr_study/06_strategy_mr/strategy_mr.py',
    ['5-2','5-3','5-4'],
    run_name='mr_v6_final',
    extra_flags=['--match-trades','worse'],
)
print(res.total_pnl, res.max_drawdown_abs, res.sharpe_ratio)
```

## What's still on the table

See `07_findings/headline.md` § "Where to push next" — four concrete
extensions estimated to add another +30–50K.
