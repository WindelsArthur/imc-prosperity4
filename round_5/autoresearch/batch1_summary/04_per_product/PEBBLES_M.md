# PEBBLES_M

**Group:** `pebbles` | **v3 3-day PnL:** +943 | **mr_v6 3-day PnL:** +9,103 | **Position cap (v3):** 10

## Microstructure
- **PEBBLES basket member:** Σ_pebbles = 50,000 ± 2.8 (re-verified, std=2.80, half-life 0.16 ticks)

## Cointegration overlays where this product is a leg
- [CROSS] `PEBBLES_M ~ OXYGEN_SHAKE_MORNING_BREATH` slope=-0.9037 intercept=+19300.55 sd=200.0
- [CROSS] `ROBOT_IRONING ~ PEBBLES_M` slope=-0.9154 intercept=+18096.05 sd=200.0
- [CROSS] `PEBBLES_M ~ ROBOT_IRONING` slope=-0.7284 intercept=+16601.80 sd=200.0

## Mean-reversion (mr_study v6)
- mr_v6 mode: **TAKER** (rolling_quadratic w=2000, z_in=1.0)

## Reconciled findings (citations)
- ROUND_5/autoresearch/13_round2_research/B_bleeders/forensics_summary.csv
- ROUND_5/autoresearch/13_round2_research/B_bleeders/decision.md
- ROUND_5/autoresearch/mr_study/07_findings/per_product/PEBBLES_M.md
- ROUND_5/autoresearch/mr_study/07_findings/headline.md
- ROUND_5/autoresearch/mr_study/01_fair_value_zoo/per_product/PEBBLES_M/ranking.csv
- ROUND_5/autoresearch/data_views/prices_r5_d2.parquet
- ROUND_5/autoresearch/01_eda/per_product/PEBBLES_M/summary.png
- ROUND_5/autoresearch/mr_study/05_robustness/stability_report.md
- ROUND_5/autoresearch/mr_study/07_findings/group_summary.md
- ROUND_5/autoresearch/07_hidden_patterns/per_product/PEBBLES_M.json
- ROUND_5/autoresearch/14_lag_research/B_leadlag/decision.md
- ROUND_5/autoresearch/mr_study/06_strategy_mr/distilled_params.py
- ROUND_5/autoresearch/05_cross_product/groups/pebbles/ret_corr.csv
- ROUND_5/autoresearch/05_cross_product/groups/pebbles/basket_residual.csv
- ROUND_5/autoresearch/13_round2_research/B_bleeders/run.py
- ROUND_5/autoresearch/14_lag_research/C_lagged_coint/decision.md
- ROUND_5/autoresearch/mr_study/01_fair_value_zoo/per_product/PEBBLES_M/diagnostics.csv
- ROUND_5/autoresearch/mr_study/02_threshold_search/per_product/PEBBLES_M/top20.csv
- ROUND_5/autoresearch/13_round2_research/B_bleeders/forensics.csv
- ROUND_5/autoresearch/05_cross_product/groups/pebbles/price_corr.csv
- ROUND_5/autoresearch/13_round2_research/B_bleeders/recipes.csv
- ROUND_5/autoresearch/04_statistical_patterns/intraday/PEBBLES_M.csv

## Recommendation (final algo)
- **Primary mechanism:** `basket_invariant_PEBBLES`
- **Secondary signals:** pebble_skew, inside_spread_mm, inv_skew, coint_pairs(n=3)
- **Rationale:** v3 PnL +943 — moderate; baseline kept; mr_v6 outperformed v3 here (+9,103 vs +943) — TAKER candidate for Phase H

## 2 ranked alternatives
1. mr_v6 TAKER (rolling_quadratic w=2000, z_in=1.0) — would yield ~+9,103 per mr_study
2. Inside-spread MM only (drop overlays) — baseline before v3 layering
