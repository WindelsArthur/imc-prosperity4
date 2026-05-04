# UV_VISOR_RED

**Group:** `uv_visor` | **v3 3-day PnL:** +110 | **mr_v6 3-day PnL:** -220 | **Position cap (v3):** 10

## Microstructure

## Mean-reversion (mr_study v6)
- mr_v6 mode: default MM (inside-spread bb+1/ba-1 with inv_skew=−pos·0.2)

## Reconciled findings (citations)
- ROUND_5/autoresearch/mr_study/00_setup/data_sanity.md
- ROUND_5/autoresearch/data_views/prices_r5_d2.parquet
- ROUND_5/autoresearch/04_statistical_patterns/intraday/UV_VISOR_RED.csv
- ROUND_5/autoresearch/05_cross_product/groups/uv_visor/price_corr.csv
- ROUND_5/autoresearch/mr_study/01_fair_value_zoo/per_product/UV_VISOR_RED/diagnostics.csv
- ROUND_5/autoresearch/mr_study/07_findings/per_product/UV_VISOR_RED.md
- ROUND_5/autoresearch/05_cross_product/groups/uv_visor/ret_corr.csv
- ROUND_5/autoresearch/mr_study/01_fair_value_zoo/per_product/UV_VISOR_RED/ranking.csv
- ROUND_5/autoresearch/05_cross_product/groups/uv_visor/basket_residual.csv
- ROUND_5/autoresearch/07_hidden_patterns/per_product/UV_VISOR_RED.json
- ROUND_5/autoresearch/mr_study/02_threshold_search/per_product/UV_VISOR_RED/top20.csv
- ROUND_5/autoresearch/01_eda/per_product/UV_VISOR_RED/summary.png

## Recommendation (final algo)
- **Primary mechanism:** `inside_spread_mm`
- **Secondary signals:** inv_skew(-pos*0.2)
- **Rationale:** v3 PnL +110 — moderate; baseline kept

## 2 ranked alternatives
2. Inside-spread MM only (drop overlays) — baseline before v3 layering
