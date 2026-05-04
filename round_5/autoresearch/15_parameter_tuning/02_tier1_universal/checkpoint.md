# Phase 2 (Tier-1 Universal) Checkpoint

## LHS coarse sweep
- 51 configs evaluated
- baseline rank by fold_median: see lhs_results.csv
- top fold_median: 363,578
- median across all configs: 349,660

## TPE optimization
- 40 TPE trials
- best fold_median: 363,619

## Plateau analysis
| param               |   n_values |   n_pass_a_b_c |   max_contig_pass |   best_value |   best_fold_median |    anchor |
|:--------------------|-----------:|---------------:|------------------:|-------------:|-------------------:|----------:|
| PAIR_TILT_DIVISOR   |          6 |              1 |                 1 |         2    |             364290 |  1.69545  |
| PAIR_TILT_CLIP      |          6 |              0 |                 0 |        10    |             360391 | 11.5806   |
| INV_SKEW_BETA       |          5 |              0 |                 0 |         0.15 |             362905 |  0.119412 |
| QUOTE_BASE_SIZE_CAP |          4 |              4 |                 4 |         4    |             363944 |  6        |
| fair_quote_gate     |          5 |              1 |                 1 |         0.75 |             364273 |  0.591718 |

## Decision
- Decision: **revert_to_baseline**
- Reverted: no LHS/TPE config passed gates (a)+(b)+(c)+(e) vs locked baseline
- Params kept at: {'PAIR_TILT_DIVISOR': 3.0, 'PAIR_TILT_CLIP': 7.0, 'INV_SKEW_BETA': 0.2, 'QUOTE_BASE_SIZE_CAP': 8}