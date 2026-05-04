# SNACKPACK_RASPBERRY

**Group:** `snackpack` | **v3 3-day PnL:** -10,238 | **mr_v6 3-day PnL:** +5,330 | **Position cap (v3):** 5

## Microstructure
- **SNACKPACK basket member:** Σ_snack = 50,221 ± 190 (re-verified, std=189.6)

## Cointegration overlays where this product is a leg
- [WITHIN] `SNACKPACK_RASPBERRY ~ SNACKPACK_VANILLA` slope=+0.0130 intercept=+9962.00 sd=161.0

## Mean-reversion (mr_study v6)
- mr_v6 mode: default MM (inside-spread bb+1/ba-1 with inv_skew=−pos·0.2)

## Reconciled findings (citations)
- ROUND_5/autoresearch/01_eda/per_product/SNACKPACK_RASPBERRY/summary.png
- ROUND_5/autoresearch/05_cross_product/groups/snackpack/price_corr.csv
- ROUND_5/autoresearch/mr_study/00_setup/data_sanity.md
- ROUND_5/autoresearch/07_hidden_patterns/per_product/SNACKPACK_RASPBERRY.json
- ROUND_5/autoresearch/data_views/prices_r5_d2.parquet
- ROUND_5/autoresearch/04_statistical_patterns/intraday/SNACKPACK_RASPBERRY.csv
- ROUND_5/autoresearch/13_round2_research/C_johansen/decision.md
- ROUND_5/autoresearch/mr_study/02_threshold_search/per_product/SNACKPACK_RASPBERRY/top20.csv
- ROUND_5/autoresearch/05_cross_product/groups/snackpack/ret_corr.csv
- ROUND_5/autoresearch/mr_study/07_findings/per_product/SNACKPACK_RASPBERRY.md
- ROUND_5/autoresearch/13_round2_research/B_bleeders/forensics.csv
- ROUND_5/autoresearch/13_round2_research/K_strategy_v2/ablation.py
- ROUND_5/autoresearch/05_cross_product/groups/snackpack/basket_residual.csv
- ROUND_5/autoresearch/mr_study/01_fair_value_zoo/per_product/SNACKPACK_RASPBERRY/diagnostics.csv
- ROUND_5/autoresearch/mr_study/01_fair_value_zoo/per_product/SNACKPACK_RASPBERRY/ranking.csv

## Recommendation (final algo)
- **Primary mechanism:** `basket_invariant_SNACKPACK`
- **Secondary signals:** snack_skew, inside_spread_mm, inv_skew, coint_pairs(n=1), prod_cap=5
- **Rationale:** Chronic loser in v3 — Phase H ablation will test tighter cap or IDLE

## 2 ranked alternatives
2. Inside-spread MM only (drop overlays) — baseline before v3 layering
