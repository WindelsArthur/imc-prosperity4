# SNACKPACK_PISTACHIO

**Group:** `snackpack` | **v3 3-day PnL:** +8,711 | **mr_v6 3-day PnL:** +1,692 | **Position cap (v3):** 10

## Microstructure
- **SNACKPACK basket member:** Σ_snack = 50,221 ± 190 (re-verified, std=189.6)

## Cointegration overlays where this product is a leg
- [CROSS] `SNACKPACK_PISTACHIO ~ OXYGEN_SHAKE_GARLIC` slope=-0.1488 intercept=+11269.91 sd=200.0
- [CROSS] `SNACKPACK_PISTACHIO ~ PEBBLES_XS` slope=+0.0992 intercept=+8761.10 sd=200.0
- [CROSS] `SNACKPACK_PISTACHIO ~ MICROCHIP_OVAL` slope=+0.0907 intercept=+8753.81 sd=200.0

## Mean-reversion (mr_study v6)
- mr_v6 mode: default MM (inside-spread bb+1/ba-1 with inv_skew=−pos·0.2)

## Reconciled findings (citations)
- ROUND_5/autoresearch/mr_study/07_findings/per_product/SNACKPACK_PISTACHIO.md
- ROUND_5/autoresearch/mr_study/01_fair_value_zoo/per_product/SNACKPACK_PISTACHIO/diagnostics.csv
- ROUND_5/autoresearch/05_cross_product/groups/snackpack/price_corr.csv
- ROUND_5/autoresearch/07_hidden_patterns/per_product/SNACKPACK_RASPBERRY.json
- ROUND_5/autoresearch/data_views/prices_r5_d4.parquet
- ROUND_5/autoresearch/mr_study/02_threshold_search/per_product/SNACKPACK_PISTACHIO/top20.csv
- ROUND_5/autoresearch/13_round2_research/C_johansen/decision.md
- ROUND_5/autoresearch/01_eda/per_product/SNACKPACK_PISTACHIO/summary.png
- ROUND_5/autoresearch/04_statistical_patterns/intraday/SNACKPACK_PISTACHIO.csv
- ROUND_5/autoresearch/05_cross_product/groups/snackpack/ret_corr.csv
- ROUND_5/autoresearch/13_round2_research/K_strategy_v2/ablation.py
- ROUND_5/autoresearch/mr_study/01_fair_value_zoo/per_product/SNACKPACK_PISTACHIO/ranking.csv
- ROUND_5/autoresearch/05_cross_product/groups/snackpack/basket_residual.csv
- ROUND_5/autoresearch/07_hidden_patterns/per_product/SNACKPACK_PISTACHIO.json

## Recommendation (final algo)
- **Primary mechanism:** `basket_invariant_SNACKPACK`
- **Secondary signals:** snack_skew, inside_spread_mm, inv_skew, coint_pairs(n=3)
- **Rationale:** Strong v3 contributor (+8,711) — keep current setup

## 2 ranked alternatives
2. Inside-spread MM only (drop overlays) — baseline before v3 layering
