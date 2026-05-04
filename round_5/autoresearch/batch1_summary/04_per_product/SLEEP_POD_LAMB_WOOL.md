# SLEEP_POD_LAMB_WOOL

**Group:** `sleep_pod` | **v3 3-day PnL:** -2,310 | **mr_v6 3-day PnL:** +0 | **Position cap (v3):** 3

## Microstructure

## Cointegration overlays where this product is a leg
- [CROSS] `TRANSLATOR_ECLIPSE_CHARCOAL ~ SLEEP_POD_LAMB_WOOL` slope=-0.5308 intercept=+15493.89 sd=200.0
- [CROSS] `SLEEP_POD_LAMB_WOOL ~ TRANSLATOR_ECLIPSE_CHARCOAL` slope=-0.7159 intercept=+17727.49 sd=200.0

## Mean-reversion (mr_study v6)
- mr_v6 mode: **IDLE** — chronic MM loser; mr_study chose to skip

## Reconciled findings (citations)
- ROUND_5/autoresearch/13_round2_research/B_bleeders/forensics_summary.csv
- ROUND_5/autoresearch/04_statistical_patterns/intraday/SLEEP_POD_LAMB_WOOL.csv
- ROUND_5/autoresearch/13_round2_research/B_bleeders/decision.md
- ROUND_5/autoresearch/05_cross_product/groups/sleep_pod/price_corr.csv
- ROUND_5/autoresearch/07_hidden_patterns/per_product/SLEEP_POD_LAMB_WOOL.json
- ROUND_5/autoresearch/data_views/prices_r5_d4.parquet
- ROUND_5/autoresearch/05_cross_product/groups/sleep_pod/ret_corr.csv
- ROUND_5/autoresearch/mr_study/01_fair_value_zoo/per_product/SLEEP_POD_LAMB_WOOL/diagnostics.csv
- ROUND_5/autoresearch/13_round2_research/M_submit/diff_v1_to_v2.md
- ROUND_5/autoresearch/05_cross_product/groups/sleep_pod/basket_residual.csv
- ROUND_5/autoresearch/mr_study/02_threshold_search/per_product/SLEEP_POD_LAMB_WOOL/top20.csv
- ROUND_5/autoresearch/14_lag_research/D_var/decision.md
- ROUND_5/autoresearch/mr_study/07_findings/per_product/SLEEP_POD_LAMB_WOOL.md
- ROUND_5/autoresearch/13_round2_research/B_bleeders/run.py
- ROUND_5/autoresearch/mr_study/01_fair_value_zoo/per_product/SLEEP_POD_LAMB_WOOL/ranking.csv
- ROUND_5/autoresearch/13_round2_research/B_bleeders/forensics.csv
- ROUND_5/autoresearch/01_eda/per_product/SLEEP_POD_LAMB_WOOL/summary.png
- ROUND_5/autoresearch/13_round2_research/B_bleeders/recipes.csv

## Recommendation (final algo)
- **Primary mechanism:** `inside_spread_mm`
- **Secondary signals:** inv_skew(-pos*0.2), coint_pairs(n=2), prod_cap=3
- **Rationale:** v3 PnL -2,310 — moderate; baseline kept

## 2 ranked alternatives
1. IDLE — mr_v6 chose this (PnL=0); v3 yields -2,310
2. Inside-spread MM only (drop overlays) — baseline before v3 layering
