# Phase 1 Step 1a — ROBOT_DISHES diagnostic

Baseline: `algo1_drop_harmful_only.py` (audit's runner-up). All numbers below are from the locked baseline run.


## Per-day ROBOT_DISHES PnL on baseline

| day | dishes_pnl |
|---|---|
| 2 | 16,701 |
| 3 | 3,121 |
| 4 | 6,379 |

3-day total: **26,201**

## Per-fold ROBOT_DISHES contribution (test-day)

| fold | dishes_pnl |
|---|---|
| F1 | 3,121 |
| F2 | 6,379 |
| F3 | 3,121 |
| F4 | 16,701 |
| F5 | 3,121 |

fold_min(dishes) = **3,121**

## AR(1) on Δmid per day

| day | n | φ | intercept | R² | var(Δmid) |
|---|---|---|---|---|---|
| 2 | 9998 | -0.0009 | -0.0059 | 0.0000 | 93.1771 |
| 3 | 9998 | -0.0041 | 0.0214 | 0.0000 | 100.1938 |
| 4 | 9998 | -0.2904 | 0.1386 | 0.0844 | 754.9274 |
| all_pooled | 29996 | -0.2317 | 0.0506 | 0.0537 | 316.1018 |

## Spread distribution per day

| day | n | mean | median | p25 | p75 | p90 | max | %=1 | %≤2 |
|---|---|---|---|---|---|---|---|---|---|
| 2 | 10000 | 6.954 | 7.0 | 7.0 | 7.0 | 8.0 | 8.0 | 0.0% | 0.1% |
| 3 | 10000 | 7.283 | 7.0 | 7.0 | 8.0 | 8.0 | 8.0 | 0.0% | 0.0% |
| 4 | 10000 | 7.814 | 8.0 | 8.0 | 8.0 | 8.0 | 8.0 | 0.0% | 0.0% |

## Existing pairs touching ROBOT_DISHES (in baseline ALL_PAIRS)

| a | b | slope | intercept |
|---|---|---|---|
| PEBBLES_XL | ROBOT_DISHES | 2.5644 | -12461.15 |
| PEBBLES_XL | ROBOT_DISHES | 2.5803 | -12603.17 |
| PEBBLES_XL | ROBOT_DISHES | 2.5607 | -12428.07 |
| PEBBLES_XL | ROBOT_DISHES | 2.5615 | -12434.87 |

All four are PEBBLES_XL→ROBOT_DISHES with very similar parameters (close to one calibration). They contribute additively to global `pair_skew` for ROBOT_DISHES via the chained `-slope*tilt/max(|slope|,1)` term.

## Phase-6 log-study novel ROBOT_DISHES pairs

Source: `log_study/06_oos_validation/ship_list_dedup.csv`. Isolated 5-fold sum PnL.

| pair | β | α | isolated_5fold_pnl |
|---|---|---|---|
| PEBBLES_S – ROBOT_DISHES | -1.4245 | 22.2138 | 18,992 |
| ROBOT_DISHES – PANEL_2X4 | 0.7853 | 1.8855 | 17,304 |
| GALAXY_SOUNDS_BLACK_HOLES – ROBOT_DISHES | 1.2349 | -2.0304 | 13,530 |
| ROBOT_DISHES – SNACKPACK_STRAWBERRY | 1.2191 | -2.1006 | 12,158 |

Sum of 4 isolated: **61,983**.
