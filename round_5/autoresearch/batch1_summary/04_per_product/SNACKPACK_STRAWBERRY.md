# SNACKPACK_STRAWBERRY

**Group:** `snackpack` | **v3 3-day PnL:** +13,860 | **mr_v6 3-day PnL:** +2,614 | **Position cap (v3):** 10

## Microstructure
- **SNACKPACK basket member:** Σ_snack = 50,221 ± 190 (re-verified, std=189.6)

## Cointegration overlays where this product is a leg
- [WITHIN] `SNACKPACK_CHOCOLATE ~ SNACKPACK_STRAWBERRY` slope=-0.1060 intercept=+11051.00 sd=145.0
- [CROSS] `UV_VISOR_AMBER ~ SNACKPACK_STRAWBERRY` slope=-2.4501 intercept=+34143.94 sd=200.0
- [CROSS] `SNACKPACK_STRAWBERRY ~ SLEEP_POD_POLYESTER` slope=+0.3255 intercept=+6852.82 sd=200.0
- [CROSS] `SNACKPACK_STRAWBERRY ~ UV_VISOR_AMBER` slope=-0.3259 intercept=+13284.98 sd=200.0

## Mean-reversion (mr_study v6)
- mr_v6 mode: default MM (inside-spread bb+1/ba-1 with inv_skew=−pos·0.2)

## Reconciled findings (citations)
- ROUND_5/autoresearch/04_statistical_patterns/intraday/SNACKPACK_STRAWBERRY.csv
- ROUND_5/autoresearch/05_cross_product/groups/snackpack/price_corr.csv
- ROUND_5/autoresearch/mr_study/00_setup/data_sanity.md
- ROUND_5/autoresearch/mr_study/07_findings/per_product/SNACKPACK_STRAWBERRY.md
- ROUND_5/autoresearch/13_round2_research/C_johansen/decision.md
- ROUND_5/autoresearch/01_eda/per_product/SNACKPACK_STRAWBERRY/summary.png
- ROUND_5/autoresearch/05_cross_product/groups/snackpack/ret_corr.csv
- ROUND_5/autoresearch/mr_study/01_fair_value_zoo/per_product/SNACKPACK_STRAWBERRY/ranking.csv
- ROUND_5/autoresearch/07_hidden_patterns/per_product/SNACKPACK_STRAWBERRY.json
- ROUND_5/autoresearch/13_round2_research/K_strategy_v2/ablation.py
- ROUND_5/autoresearch/05_cross_product/groups/snackpack/basket_residual.csv
- ROUND_5/autoresearch/mr_study/01_fair_value_zoo/per_product/SNACKPACK_STRAWBERRY/diagnostics.csv
- ROUND_5/autoresearch/mr_study/02_threshold_search/per_product/SNACKPACK_STRAWBERRY/top20.csv

## Recommendation (final algo)
- **Primary mechanism:** `basket_invariant_SNACKPACK`
- **Secondary signals:** snack_skew, inside_spread_mm, inv_skew, coint_pairs(n=4)
- **Rationale:** Strong v3 contributor (+13,860) — keep current setup

## 2 ranked alternatives
2. Inside-spread MM only (drop overlays) — baseline before v3 layering
