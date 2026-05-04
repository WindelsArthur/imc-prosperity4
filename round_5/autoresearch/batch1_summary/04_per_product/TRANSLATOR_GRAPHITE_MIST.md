# TRANSLATOR_GRAPHITE_MIST

**Group:** `translator` | **v3 3-day PnL:** +4,278 | **mr_v6 3-day PnL:** +3,874 | **Position cap (v3):** 10

## Microstructure

## Mean-reversion (mr_study v6)
- mr_v6 mode: default MM (inside-spread bb+1/ba-1 with inv_skew=−pos·0.2)

## Reconciled findings (citations)
- ROUND_5/autoresearch/05_cross_product/groups/translator/basket_residual.csv
- ROUND_5/autoresearch/07_hidden_patterns/per_product/TRANSLATOR_GRAPHITE_MIST.json
- ROUND_5/autoresearch/mr_study/02_threshold_search/per_product/TRANSLATOR_GRAPHITE_MIST/top20.csv
- ROUND_5/autoresearch/mr_study/07_findings/per_product/TRANSLATOR_GRAPHITE_MIST.md
- ROUND_5/autoresearch/05_cross_product/groups/translator/price_corr.csv
- ROUND_5/autoresearch/01_eda/per_product/TRANSLATOR_GRAPHITE_MIST/summary.png
- ROUND_5/autoresearch/mr_study/01_fair_value_zoo/per_product/TRANSLATOR_GRAPHITE_MIST/ranking.csv
- ROUND_5/autoresearch/05_cross_product/groups/translator/ret_corr.csv
- ROUND_5/autoresearch/07_hidden_patterns/per_product/MICROCHIP_TRIANGLE.json
- ROUND_5/autoresearch/04_statistical_patterns/intraday/TRANSLATOR_GRAPHITE_MIST.csv
- ROUND_5/autoresearch/mr_study/01_fair_value_zoo/per_product/TRANSLATOR_GRAPHITE_MIST/diagnostics.csv

## Recommendation (final algo)
- **Primary mechanism:** `inside_spread_mm`
- **Secondary signals:** inv_skew(-pos*0.2)
- **Rationale:** v3 PnL +4,278 — moderate; baseline kept

## 2 ranked alternatives
2. Inside-spread MM only (drop overlays) — baseline before v3 layering
