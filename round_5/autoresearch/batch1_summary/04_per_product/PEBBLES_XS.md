# PEBBLES_XS

**Group:** `pebbles` | **v3 3-day PnL:** +12,928 | **mr_v6 3-day PnL:** +15,016 | **Position cap (v3):** 10

## Microstructure
- **PEBBLES basket member:** Σ_pebbles = 50,000 ± 2.8 (re-verified, std=2.80, half-life 0.16 ticks)

## Cointegration overlays where this product is a leg
- [CROSS] `SNACKPACK_PISTACHIO ~ PEBBLES_XS` slope=+0.0992 intercept=+8761.10 sd=200.0

## Mean-reversion (mr_study v6)
- mr_v6 mode: **TAKER** (rolling_quadratic w=500, z_in=1.25)

## Reconciled findings (citations)
- ROUND_5/autoresearch/mr_study/01_fair_value_zoo/per_product/PEBBLES_XS/ranking.csv
- ROUND_5/autoresearch/04_statistical_patterns/intraday/PEBBLES_XS.csv
- ROUND_5/autoresearch/13_round2_research/A_sine/oos_mse.csv
- ROUND_5/autoresearch/mr_study/02_threshold_search/per_product/PEBBLES_XS/top20.csv
- ROUND_5/autoresearch/mr_study/07_findings/per_product/PEBBLES_XS.md
- ROUND_5/autoresearch/13_round2_research/A_sine/plots/PEBBLES_XS.png
- ROUND_5/autoresearch/13_round2_research/A_sine/per_day_fits.csv
- ROUND_5/autoresearch/01_eda/per_product/PEBBLES_XS/summary.png
- ROUND_5/autoresearch/mr_study/05_robustness/stability_report.md
- ROUND_5/autoresearch/mr_study/07_findings/group_summary.md
- ROUND_5/autoresearch/14_lag_research/O_submit/findings_v3.md
- ROUND_5/autoresearch/14_lag_research/B_leadlag/decision.md
- ROUND_5/autoresearch/mr_study/06_strategy_mr/distilled_params.py
- ROUND_5/autoresearch/05_cross_product/groups/pebbles/ret_corr.csv
- ROUND_5/autoresearch/05_cross_product/groups/pebbles/basket_residual.csv
- ROUND_5/autoresearch/mr_study/01_fair_value_zoo/per_product/PEBBLES_XS/diagnostics.csv
- ROUND_5/autoresearch/07_hidden_patterns/per_product/SLEEP_POD_SUEDE.json
- ROUND_5/autoresearch/13_round2_research/A_sine/run.py
- ROUND_5/autoresearch/05_cross_product/groups/pebbles/price_corr.csv
- ROUND_5/autoresearch/07_hidden_patterns/per_product/ROBOT_VACUUMING.json
- ROUND_5/autoresearch/07_hidden_patterns/per_product/PEBBLES_XS.json
- ROUND_5/autoresearch/13_round2_research/A_sine/rolling_phase.csv
- ROUND_5/autoresearch/13_round2_research/A_sine/decision.md

## Recommendation (final algo)
- **Primary mechanism:** `basket_invariant_PEBBLES`
- **Secondary signals:** pebble_skew, inside_spread_mm, inv_skew, coint_pairs(n=1)
- **Rationale:** Strong v3 contributor (+12,928) — keep current setup; mr_v6 outperformed v3 here (+15,016 vs +12,928) — TAKER candidate for Phase H

## 2 ranked alternatives
1. mr_v6 TAKER (rolling_quadratic w=500, z_in=1.25) — would yield ~+15,016 per mr_study
2. Inside-spread MM only (drop overlays) — baseline before v3 layering
