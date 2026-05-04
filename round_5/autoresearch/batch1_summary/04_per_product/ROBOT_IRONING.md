# ROBOT_IRONING

**Group:** `robot` | **v3 3-day PnL:** +1,064 | **mr_v6 3-day PnL:** +0 | **Position cap (v3):** 10

## Microstructure
- **AR(1) on Δmid:** -0.1253 (re-verified on stitched 2+3+4 mids)
- **Lattice ratio:** 0.0210 (n_distinct_mids = 631 of 30,000 ticks)

## Cointegration overlays where this product is a leg
- [CROSS] `ROBOT_IRONING ~ PEBBLES_M` slope=-0.9154 intercept=+18096.05 sd=200.0
- [CROSS] `PEBBLES_M ~ ROBOT_IRONING` slope=-0.7284 intercept=+16601.80 sd=200.0

## Mean-reversion (mr_study v6)
- mr_v6 mode: **IDLE** — chronic MM loser; mr_study chose to skip

## Reconciled findings (citations)
- ROUND_5/autoresearch/mr_study/01_fair_value_zoo/per_product/ROBOT_IRONING/ranking.csv
- ROUND_5/autoresearch/14_lag_research/E_ar_extended/sign_switching.csv
- ROUND_5/autoresearch/10_backtesting/sweep_mr_d_3prods.py
- ROUND_5/autoresearch/mr_study/00_setup/data_sanity.md
- ROUND_5/autoresearch/04_statistical_patterns/intraday/ROBOT_IRONING.csv
- ROUND_5/autoresearch/mr_study/02_threshold_search/per_product/ROBOT_IRONING/top20.csv
- ROUND_5/autoresearch/05_cross_product/groups/robot/price_corr.csv
- ROUND_5/autoresearch/mr_study/07_findings/group_summary.md
- ROUND_5/autoresearch/07_hidden_patterns/per_product/PEBBLES_L.json
- ROUND_5/autoresearch/01_eda/per_product/ROBOT_IRONING/summary.png
- ROUND_5/autoresearch/10_backtesting/results/sweep_mr_d_3prods_results.json
- ROUND_5/autoresearch/07_hidden_patterns/per_product/MICROCHIP_CIRCLE.json
- ROUND_5/autoresearch/05_cross_product/groups/robot/basket_residual.csv
- ROUND_5/autoresearch/mr_study/01_fair_value_zoo/per_product/ROBOT_IRONING/diagnostics.csv
- ROUND_5/autoresearch/mr_study/07_findings/per_product/ROBOT_IRONING.md
- ROUND_5/autoresearch/data_views/prices_r5_d3.parquet
- ROUND_5/autoresearch/07_hidden_patterns/per_product/ROBOT_IRONING.json
- ROUND_5/autoresearch/05_cross_product/groups/robot/ret_corr.csv

## Recommendation (final algo)
- **Primary mechanism:** `inside_spread_mm`
- **Secondary signals:** inv_skew(-pos*0.2), coint_pairs(n=2)
- **Rationale:** v3 PnL +1,064 — moderate; baseline kept

## 2 ranked alternatives
1. IDLE — mr_v6 chose this (PnL=0); v3 yields +1,064
2. Inside-spread MM only (drop overlays) — baseline before v3 layering
