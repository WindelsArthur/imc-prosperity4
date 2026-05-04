# SNACKPACK_CHOCOLATE

**Group:** `snackpack` | **v3 3-day PnL:** -4,689 | **mr_v6 3-day PnL:** +5,017 | **Position cap (v3):** 5

## Microstructure
- **AR(1) on Δmid:** -0.0311 (re-verified on stitched 2+3+4 mids)
- **SNACKPACK basket member:** Σ_snack = 50,221 ± 190 (re-verified, std=189.6)

## Cointegration overlays where this product is a leg
- [WITHIN] `SNACKPACK_CHOCOLATE ~ SNACKPACK_STRAWBERRY` slope=-0.1060 intercept=+11051.00 sd=145.0
- [CROSS] `SNACKPACK_CHOCOLATE ~ PANEL_2X4` slope=-0.2171 intercept=+12289.62 sd=200.0

## Mean-reversion (mr_study v6)
- mr_v6 mode: **MM with signal skew** (AR(1) on Δmid)

## Reconciled findings (citations)
- ROUND_5/autoresearch/13_round2_research/B_bleeders/forensics_summary.csv
- ROUND_5/autoresearch/13_round2_research/B_bleeders/decision.md
- ROUND_5/autoresearch/01_eda/per_product/SNACKPACK_CHOCOLATE/summary.png
- ROUND_5/autoresearch/05_cross_product/groups/snackpack/price_corr.csv
- ROUND_5/autoresearch/mr_study/01_fair_value_zoo/per_product/SNACKPACK_CHOCOLATE/ranking.csv
- ROUND_5/autoresearch/mr_study/07_findings/group_summary.md
- ROUND_5/autoresearch/07_hidden_patterns/per_product/SNACKPACK_CHOCOLATE.json
- ROUND_5/autoresearch/13_round2_research/C_johansen/decision.md
- ROUND_5/autoresearch/13_round2_research/M_submit/diff_v1_to_v2.md
- ROUND_5/autoresearch/04_statistical_patterns/intraday/SNACKPACK_CHOCOLATE.csv
- ROUND_5/autoresearch/07_hidden_patterns/per_product/SNACKPACK_VANILLA.json
- ROUND_5/autoresearch/05_cross_product/groups/snackpack/ret_corr.csv
- ROUND_5/autoresearch/13_round2_research/B_bleeders/run.py
- ROUND_5/autoresearch/13_round2_research/B_bleeders/forensics.csv
- ROUND_5/autoresearch/13_round2_research/K_strategy_v2/ablation.py
- ROUND_5/autoresearch/mr_study/02_threshold_search/per_product/SNACKPACK_CHOCOLATE/top20.csv
- ROUND_5/autoresearch/05_cross_product/groups/snackpack/basket_residual.csv
- ROUND_5/autoresearch/mr_study/01_fair_value_zoo/per_product/SNACKPACK_CHOCOLATE/diagnostics.csv
- ROUND_5/autoresearch/data_views/prices_r5_d3.parquet
- ROUND_5/autoresearch/mr_study/07_findings/per_product/SNACKPACK_CHOCOLATE.md
- ROUND_5/autoresearch/13_round2_research/B_bleeders/recipes.csv

## Recommendation (final algo)
- **Primary mechanism:** `basket_invariant_SNACKPACK`
- **Secondary signals:** snack_skew, inside_spread_mm, inv_skew, coint_pairs(n=2), prod_cap=5
- **Rationale:** v3 PnL -4,689 — moderate; baseline kept

## 2 ranked alternatives
2. Inside-spread MM only (drop overlays) — baseline before v3 layering
