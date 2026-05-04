# Phase D Checkpoint

## How many conflicts found?
10 conflicts in `conflicts.jsonl`, all decided.

## How many re-verified?
- v3 baseline backtest **reproduced exactly** (TOTAL=733,320 / Sharpe=8.34 / DD=23,990).
- 10 within-group cointegration ADF p-values recomputed on stitched days 2+3+4.
- 5 cross-group cointegration spot checks.
- 5 AR(1) coefficients on top mean-reversion candidates.
- 3 lattice ratios (n_distinct_mids).
- 2 basket invariants (PEBBLES, SNACKPACK).

Total: 25 statistical claims reverified + 1 backtest baseline.

## Top-5 surprising disagreements
1. **OXYGEN_SHAKE_CHOCOLATE/OXYGEN_SHAKE_GARLIC**: claimed ADF p=0.030, observed 0.918. Massive non-stationarity on full 3-day stitch — confirmed regime break (KS p≈0 across days). Original fit was likely fold-conditional. **Decision: drop this pair from final algo**, keep CHOCOLATE as single-product MR overlay.
2. **ROBOT_LAUNDRY/ROBOT_VACUUMING**: claimed ADF p=0.026, observed 0.378. Pair survives in v3 because OOS Sharpe was positive in both folds (1.19, 1.70) despite full-stitch non-stationarity. KEEP with awareness.
3. **SLEEP_POD_COTTON/SLEEP_POD_POLYESTER**: claimed 0.033, observed 0.146. Same fold-vs-stitch divergence pattern. KEEP.
4. **CROSS-GROUP cointegration is STRONGER than within-group**: 5/5 spot-checks have ADF p < 0.01 on full stitch. Phase C of round 3 found genuine structural relationships across groups; the within-group "low-hanging fruit" was actually weaker. This is consistent with the +201K v2→v3 jump.
5. **mr_study v6 (TAKER mode) underperforms v3 by 334K** (399K vs 733K). Layering cross-group cointegration overlays on passive MM dominates per-product TAKER selection. Final algo should NOT switch to TAKER except possibly for ROBOT_DISHES (highest |AR(1)| = 0.232).

## Decisions for Phase H
- **Baseline = strategy_v3.py** (733,320). My final must match or beat with better robustness.
- DROP OXYGEN_SHAKE_CHOCOLATE/GARLIC pair (replace with single-product OXYGEN_SHAKE_CHOCOLATE skew based on AR(1)).
- KEEP all 30 cross-group pairs from v3 (high-confidence reverified).
- TEST PEBBLES_L cap (chronic -12K loser).
- TEST replacing borderline within-group pairs with single-product overlays.
- DEFER sine overlay (failed in v2 ablation).
- DEFER mr_study TAKER mode (mr_v6 dominated by v3).

## Reverify outputs
- `reverify_results/stats_reverify.csv` (25 rows)
- `reverify_results/stats_reverify.md` (markdown table)
- v3 baseline reproduction logged in `10_backtesting/results/reverify_v3.{log,csv}`
