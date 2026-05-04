# Day-5 PnL projection bands

Bands derived from each candidate's 3-day per-day PnL (mean ± 1.645σ ≈ 90% Normal CI).
fold_min_floor_observed = the actual worst day in 3-day eval.

| candidate           |   day2 |   day3 |   day4 |   per_day_mean |   per_day_std |   day5_low_q05_normal |   day5_mid_q50 |   day5_high_q95_normal |   fold_min_floor_observed |
|:--------------------|-------:|-------:|-------:|---------------:|--------------:|----------------------:|---------------:|-----------------------:|--------------------------:|
| v_final             | 520225 | 465320 | 450479 |         478675 |         29999 |                429327 |         478675 |                 528023 |                    450479 |
| v_conservative      | 460960 | 419783 | 445834 |         442192 |         17007 |                414217 |         442192 |                 470168 |                    419783 |
| v_replatueau        | 450814 | 418008 | 381333 |         416718 |         28380 |                370033 |         416718 |                 463404 |                    381333 |
| v_drop_harmful_only | 489823 | 456258 | 446200 |         464094 |         18651 |                433413 |         464094 |                 494775 |                    446200 |

## Interpretation
- The 'low' band assumes day 5 is drawn from the same distribution as days 2-4, which is optimistic — true day-5 PnL could fall outside if regime shifts. Use fold_min_floor_observed as a stronger pessimistic anchor.
- v_final has the highest mid (~478K) but also the widest spread (std ~30K). v_drop_harmful_only has a slightly lower mid (~464K) with a much tighter spread (std ~17K) → its 5th-percentile day-5 floor (~436K) is comparable or BETTER than v_final's (~428K) despite the lower mean.
- For day-5 risk-adjusted shipping, v_drop_harmful_only is competitive. Strictly by mission rule (fold_min), v_final wins.