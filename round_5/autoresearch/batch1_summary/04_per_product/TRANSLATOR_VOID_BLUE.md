# TRANSLATOR_VOID_BLUE

**Group:** `translator` | **v3 3-day PnL:** +10,529 | **mr_v6 3-day PnL:** +10,199 | **Position cap (v3):** 10

## Microstructure

## Cointegration overlays where this product is a leg
- [WITHIN] `TRANSLATOR_ECLIPSE_CHARCOAL ~ TRANSLATOR_VOID_BLUE` slope=+0.4560 intercept=+4954.00 sd=308.0

## Mean-reversion (mr_study v6)
- mr_v6 mode: default MM (inside-spread bb+1/ba-1 with inv_skew=−pos·0.2)

## Reconciled findings (citations)
- ROUND_5/autoresearch/mr_study/02_threshold_search/per_product/TRANSLATOR_VOID_BLUE/top20.csv
- ROUND_5/autoresearch/mr_study/01_fair_value_zoo/per_product/TRANSLATOR_VOID_BLUE/ranking.csv
- ROUND_5/autoresearch/05_cross_product/groups/translator/basket_residual.csv
- ROUND_5/autoresearch/mr_study/01_fair_value_zoo/per_product/TRANSLATOR_VOID_BLUE/diagnostics.csv
- ROUND_5/autoresearch/07_hidden_patterns/per_product/TRANSLATOR_VOID_BLUE.json
- ROUND_5/autoresearch/01_eda/per_product/TRANSLATOR_VOID_BLUE/summary.png
- ROUND_5/autoresearch/05_cross_product/groups/translator/price_corr.csv
- ROUND_5/autoresearch/04_statistical_patterns/intraday/TRANSLATOR_VOID_BLUE.csv
- ROUND_5/autoresearch/05_cross_product/groups/translator/ret_corr.csv
- ROUND_5/autoresearch/07_hidden_patterns/per_product/PEBBLES_S.json
- ROUND_5/autoresearch/mr_study/07_findings/per_product/TRANSLATOR_VOID_BLUE.md

## Recommendation (final algo)
- **Primary mechanism:** `inside_spread_mm`
- **Secondary signals:** inv_skew(-pos*0.2), coint_pairs(n=1)
- **Rationale:** Strong v3 contributor (+10,529) — keep current setup

## 2 ranked alternatives
2. Inside-spread MM only (drop overlays) — baseline before v3 layering
