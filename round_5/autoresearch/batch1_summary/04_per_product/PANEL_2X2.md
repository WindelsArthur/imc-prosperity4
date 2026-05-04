# PANEL_2X2

**Group:** `panel` | **v3 3-day PnL:** -87 | **mr_v6 3-day PnL:** +2,530 | **Position cap (v3):** 10

## Microstructure

## Mean-reversion (mr_study v6)
- mr_v6 mode: default MM (inside-spread bb+1/ba-1 with inv_skew=−pos·0.2)

## Reconciled findings (citations)
- ROUND_5/autoresearch/07_hidden_patterns/per_product/PANEL_2X2.json
- ROUND_5/autoresearch/05_cross_product/groups/panel/ret_corr.csv
- ROUND_5/autoresearch/data_views/prices_r5_d4.parquet
- ROUND_5/autoresearch/mr_study/01_fair_value_zoo/per_product/PANEL_2X2/diagnostics.csv
- ROUND_5/autoresearch/mr_study/07_findings/per_product/PANEL_2X2.md
- ROUND_5/autoresearch/mr_study/02_threshold_search/per_product/PANEL_2X2/top20.csv
- ROUND_5/autoresearch/05_cross_product/groups/panel/price_corr.csv
- ROUND_5/autoresearch/14_lag_research/D_var/decision.md
- ROUND_5/autoresearch/01_eda/per_product/PANEL_2X2/summary.png
- ROUND_5/autoresearch/05_cross_product/groups/panel/basket_residual.csv
- ROUND_5/autoresearch/mr_study/01_fair_value_zoo/per_product/PANEL_2X2/ranking.csv
- ROUND_5/autoresearch/04_statistical_patterns/intraday/PANEL_2X2.csv

## Recommendation (final algo)
- **Primary mechanism:** `inside_spread_mm`
- **Secondary signals:** inv_skew(-pos*0.2)
- **Rationale:** v3 PnL -87 — moderate; baseline kept

## 2 ranked alternatives
2. Inside-spread MM only (drop overlays) — baseline before v3 layering
