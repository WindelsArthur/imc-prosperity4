# PANEL_2X4

**Group:** `panel` | **v3 3-day PnL:** +6,762 | **mr_v6 3-day PnL:** +6,130 | **Position cap (v3):** 10

## Microstructure

## Cointegration overlays where this product is a leg
- [CROSS] `PEBBLES_XL ~ PANEL_2X4` slope=+2.4821 intercept=-14735.73 sd=200.0
- [CROSS] `PANEL_2X4 ~ PEBBLES_XL` slope=+0.3093 intercept=+7174.37 sd=200.0
- [CROSS] `PEBBLES_S ~ PANEL_2X4` slope=-1.1018 intercept=+21344.63 sd=200.0
- [CROSS] `PANEL_2X4 ~ OXYGEN_SHAKE_GARLIC` slope=+0.5545 intercept=+4653.12 sd=200.0
- [CROSS] `PANEL_2X4 ~ PEBBLES_S` slope=-0.6242 intercept=+16840.75 sd=200.0
- [CROSS] `SNACKPACK_CHOCOLATE ~ PANEL_2X4` slope=-0.2171 intercept=+12289.62 sd=200.0
- [CROSS] `SNACKPACK_VANILLA ~ PANEL_2X4` slope=+0.1490 intercept=+8418.80 sd=200.0

## Mean-reversion (mr_study v6)
- mr_v6 mode: default MM (inside-spread bb+1/ba-1 with inv_skew=−pos·0.2)

## Reconciled findings (citations)
- ROUND_5/autoresearch/05_cross_product/groups/panel/ret_corr.csv
- ROUND_5/autoresearch/mr_study/01_fair_value_zoo/per_product/PANEL_2X4/ranking.csv
- ROUND_5/autoresearch/mr_study/02_threshold_search/per_product/PANEL_2X4/top20.csv
- ROUND_5/autoresearch/mr_study/01_fair_value_zoo/per_product/PANEL_2X4/diagnostics.csv
- ROUND_5/autoresearch/data_views/prices_r5_d4.parquet
- ROUND_5/autoresearch/01_eda/per_product/PANEL_2X4/summary.png
- ROUND_5/autoresearch/14_lag_research/O_submit/findings_v3.md
- ROUND_5/autoresearch/07_hidden_patterns/per_product/PANEL_2X4.json
- ROUND_5/autoresearch/05_cross_product/groups/panel/price_corr.csv
- ROUND_5/autoresearch/mr_study/07_findings/per_product/PANEL_2X4.md
- ROUND_5/autoresearch/14_lag_research/C_lagged_coint/decision.md
- ROUND_5/autoresearch/05_cross_product/groups/panel/basket_residual.csv
- ROUND_5/autoresearch/data_views/prices_r5_d3.parquet
- ROUND_5/autoresearch/04_statistical_patterns/intraday/PANEL_2X4.csv

## Recommendation (final algo)
- **Primary mechanism:** `inside_spread_mm`
- **Secondary signals:** inv_skew(-pos*0.2), coint_pairs(n=7)
- **Rationale:** v3 PnL +6,762 — moderate; baseline kept

## 2 ranked alternatives
2. Inside-spread MM only (drop overlays) — baseline before v3 layering
