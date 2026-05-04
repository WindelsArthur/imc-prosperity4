# TRANSLATOR_ASTRO_BLACK

**Group:** `translator` | **v3 3-day PnL:** +8,030 | **mr_v6 3-day PnL:** +2,694 | **Position cap (v3):** 10

## Microstructure

## Mean-reversion (mr_study v6)
- mr_v6 mode: default MM (inside-spread bb+1/ba-1 with inv_skew=−pos·0.2)

## Reconciled findings (citations)
- ROUND_5/autoresearch/07_hidden_patterns/per_product/TRANSLATOR_ASTRO_BLACK.json
- ROUND_5/autoresearch/05_cross_product/groups/translator/basket_residual.csv
- ROUND_5/autoresearch/mr_study/01_fair_value_zoo/per_product/TRANSLATOR_ASTRO_BLACK/ranking.csv
- ROUND_5/autoresearch/mr_study/07_findings/per_product/TRANSLATOR_ASTRO_BLACK.md
- ROUND_5/autoresearch/05_cross_product/groups/translator/price_corr.csv
- ROUND_5/autoresearch/mr_study/01_fair_value_zoo/per_product/TRANSLATOR_ASTRO_BLACK/diagnostics.csv
- ROUND_5/autoresearch/01_eda/per_product/TRANSLATOR_ASTRO_BLACK/summary.png
- ROUND_5/autoresearch/05_cross_product/groups/translator/ret_corr.csv
- ROUND_5/autoresearch/04_statistical_patterns/intraday/TRANSLATOR_ASTRO_BLACK.csv
- ROUND_5/autoresearch/mr_study/02_threshold_search/per_product/TRANSLATOR_ASTRO_BLACK/top20.csv

## Recommendation (final algo)
- **Primary mechanism:** `inside_spread_mm`
- **Secondary signals:** inv_skew(-pos*0.2)
- **Rationale:** Strong v3 contributor (+8,030) — keep current setup

## 2 ranked alternatives
2. Inside-spread MM only (drop overlays) — baseline before v3 layering
