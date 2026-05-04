# TRANSLATOR_ECLIPSE_CHARCOAL

**Group:** `translator` | **v3 3-day PnL:** +5,648 | **mr_v6 3-day PnL:** +6,536 | **Position cap (v3):** 10

## Microstructure

## Cointegration overlays where this product is a leg
- [WITHIN] `TRANSLATOR_ECLIPSE_CHARCOAL ~ TRANSLATOR_VOID_BLUE` slope=+0.4560 intercept=+4954.00 sd=308.0
- [CROSS] `TRANSLATOR_ECLIPSE_CHARCOAL ~ SLEEP_POD_LAMB_WOOL` slope=-0.5308 intercept=+15493.89 sd=200.0
- [CROSS] `SLEEP_POD_LAMB_WOOL ~ TRANSLATOR_ECLIPSE_CHARCOAL` slope=-0.7159 intercept=+17727.49 sd=200.0

## Mean-reversion (mr_study v6)
- mr_v6 mode: default MM (inside-spread bb+1/ba-1 with inv_skew=−pos·0.2)

## Reconciled findings (citations)
- ROUND_5/autoresearch/mr_study/07_findings/per_product/TRANSLATOR_ECLIPSE_CHARCOAL.md
- ROUND_5/autoresearch/05_cross_product/groups/translator/basket_residual.csv
- ROUND_5/autoresearch/mr_study/02_threshold_search/per_product/TRANSLATOR_ECLIPSE_CHARCOAL/top20.csv
- ROUND_5/autoresearch/07_hidden_patterns/per_product/TRANSLATOR_ECLIPSE_CHARCOAL.json
- ROUND_5/autoresearch/07_hidden_patterns/per_product/SLEEP_POD_NYLON.json
- ROUND_5/autoresearch/04_statistical_patterns/intraday/TRANSLATOR_ECLIPSE_CHARCOAL.csv
- ROUND_5/autoresearch/05_cross_product/groups/translator/price_corr.csv
- ROUND_5/autoresearch/05_cross_product/groups/translator/ret_corr.csv
- ROUND_5/autoresearch/01_eda/per_product/TRANSLATOR_ECLIPSE_CHARCOAL/summary.png
- ROUND_5/autoresearch/data_views/prices_r5_d3.parquet
- ROUND_5/autoresearch/mr_study/01_fair_value_zoo/per_product/TRANSLATOR_ECLIPSE_CHARCOAL/ranking.csv
- ROUND_5/autoresearch/mr_study/01_fair_value_zoo/per_product/TRANSLATOR_ECLIPSE_CHARCOAL/diagnostics.csv

## Recommendation (final algo)
- **Primary mechanism:** `inside_spread_mm`
- **Secondary signals:** inv_skew(-pos*0.2), coint_pairs(n=3)
- **Rationale:** v3 PnL +5,648 — moderate; baseline kept

## 2 ranked alternatives
2. Inside-spread MM only (drop overlays) — baseline before v3 layering
