# UV_VISOR_ORANGE

**Group:** `uv_visor` | **v3 3-day PnL:** +9,194 | **mr_v6 3-day PnL:** +8,864 | **Position cap (v3):** 10

## Microstructure

## Mean-reversion (mr_study v6)
- mr_v6 mode: default MM (inside-spread bb+1/ba-1 with inv_skew=−pos·0.2)

## Reconciled findings (citations)
- ROUND_5/autoresearch/07_hidden_patterns/per_product/UV_VISOR_ORANGE.json
- ROUND_5/autoresearch/mr_study/01_fair_value_zoo/per_product/UV_VISOR_ORANGE/diagnostics.csv
- ROUND_5/autoresearch/mr_study/01_fair_value_zoo/per_product/UV_VISOR_ORANGE/ranking.csv
- ROUND_5/autoresearch/data_views/prices_r5_d2.parquet
- ROUND_5/autoresearch/05_cross_product/groups/uv_visor/price_corr.csv
- ROUND_5/autoresearch/05_cross_product/groups/uv_visor/ret_corr.csv
- ROUND_5/autoresearch/mr_study/07_findings/per_product/UV_VISOR_ORANGE.md
- ROUND_5/autoresearch/05_cross_product/groups/uv_visor/basket_residual.csv
- ROUND_5/autoresearch/04_statistical_patterns/intraday/UV_VISOR_ORANGE.csv
- ROUND_5/autoresearch/mr_study/02_threshold_search/per_product/UV_VISOR_ORANGE/top20.csv
- ROUND_5/autoresearch/01_eda/per_product/UV_VISOR_ORANGE/summary.png

## Recommendation (final algo)
- **Primary mechanism:** `inside_spread_mm`
- **Secondary signals:** inv_skew(-pos*0.2)
- **Rationale:** Strong v3 contributor (+9,194) — keep current setup

## 2 ranked alternatives
2. Inside-spread MM only (drop overlays) — baseline before v3 layering
