# UV_VISOR_YELLOW

**Group:** `uv_visor` | **v3 3-day PnL:** +802 | **mr_v6 3-day PnL:** +524 | **Position cap (v3):** 10

## Microstructure

## Cointegration overlays where this product is a leg
- [CROSS] `UV_VISOR_YELLOW ~ GALAXY_SOUNDS_DARK_MATTER` slope=+1.5837 intercept=-5238.83 sd=200.0
- [CROSS] `GALAXY_SOUNDS_DARK_MATTER ~ UV_VISOR_YELLOW` slope=+0.3725 intercept=+6144.99 sd=200.0

## Mean-reversion (mr_study v6)
- mr_v6 mode: default MM (inside-spread bb+1/ba-1 with inv_skew=−pos·0.2)

## Reconciled findings (citations)
- ROUND_5/autoresearch/mr_study/07_findings/per_product/UV_VISOR_YELLOW.md
- ROUND_5/autoresearch/14_lag_research/E_ar_extended/sign_switching.csv
- ROUND_5/autoresearch/mr_study/02_threshold_search/per_product/UV_VISOR_YELLOW/top20.csv
- ROUND_5/autoresearch/data_views/prices_r5_d2.parquet
- ROUND_5/autoresearch/01_eda/per_product/UV_VISOR_YELLOW/summary.png
- ROUND_5/autoresearch/05_cross_product/groups/uv_visor/price_corr.csv
- ROUND_5/autoresearch/07_hidden_patterns/per_product/UV_VISOR_YELLOW.json
- ROUND_5/autoresearch/05_cross_product/groups/uv_visor/ret_corr.csv
- ROUND_5/autoresearch/mr_study/01_fair_value_zoo/per_product/UV_VISOR_YELLOW/ranking.csv
- ROUND_5/autoresearch/05_cross_product/groups/uv_visor/basket_residual.csv
- ROUND_5/autoresearch/07_hidden_patterns/per_product/OXYGEN_SHAKE_GARLIC.json
- ROUND_5/autoresearch/data_views/prices_r5_d3.parquet
- ROUND_5/autoresearch/04_statistical_patterns/intraday/UV_VISOR_YELLOW.csv
- ROUND_5/autoresearch/mr_study/01_fair_value_zoo/per_product/UV_VISOR_YELLOW/diagnostics.csv

## Recommendation (final algo)
- **Primary mechanism:** `inside_spread_mm`
- **Secondary signals:** inv_skew(-pos*0.2), coint_pairs(n=2)
- **Rationale:** v3 PnL +802 — moderate; baseline kept

## 2 ranked alternatives
2. Inside-spread MM only (drop overlays) — baseline before v3 layering
