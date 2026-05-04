# PEBBLES_L

**Group:** `pebbles` | **v3 3-day PnL:** -12,237 | **mr_v6 3-day PnL:** +9,434 | **Position cap (v3):** 10

## Microstructure
- **PEBBLES basket member:** Σ_pebbles = 50,000 ± 2.8 (re-verified, std=2.80, half-life 0.16 ticks)

## Mean-reversion (mr_study v6)
- mr_v6 mode: **TAKER** (rolling_median w=100, z_in=1.5)

## Reconciled findings (citations)
- ROUND_5/autoresearch/13_round2_research/B_bleeders/forensics_summary.csv
- ROUND_5/autoresearch/13_round2_research/B_bleeders/decision.md
- ROUND_5/autoresearch/mr_study/07_findings/per_product/PEBBLES_M.md
- ROUND_5/autoresearch/mr_study/07_findings/per_product/PEBBLES_L.md
- ROUND_5/autoresearch/mr_study/README.md
- ROUND_5/autoresearch/mr_study/07_findings/per_product/ROBOT_MOPPING.md
- ROUND_5/autoresearch/mr_study/07_findings/per_product/PEBBLES_XS.md
- ROUND_5/autoresearch/data_views/prices_r5_d2.parquet
- ROUND_5/autoresearch/mr_study/07_findings/per_product/ROBOT_DISHES.md
- ROUND_5/autoresearch/01_eda/per_product/PEBBLES_L/summary.png
- ROUND_5/autoresearch/utils/backtester.py
- ROUND_5/autoresearch/07_hidden_patterns/per_product/PEBBLES_L.json
- ROUND_5/autoresearch/13_round2_research/M_submit/diff_v1_to_v2.md
- ROUND_5/autoresearch/14_lag_research/O_submit/findings_v3.md
- ROUND_5/autoresearch/mr_study/01_fair_value_zoo/per_product/PEBBLES_L/diagnostics.csv
- ROUND_5/autoresearch/mr_study/06_strategy_mr/distilled_params.py
- ROUND_5/autoresearch/mr_study/07_findings/per_product/SLEEP_POD_POLYESTER.md
- ROUND_5/autoresearch/04_statistical_patterns/intraday/PEBBLES_L.csv
- ROUND_5/autoresearch/05_cross_product/groups/pebbles/ret_corr.csv
- ROUND_5/autoresearch/mr_study/02_threshold_search/per_product/PEBBLES_L/top20.csv
- ROUND_5/autoresearch/05_cross_product/groups/pebbles/basket_residual.csv
- ROUND_5/autoresearch/13_round2_research/B_bleeders/run.py
- ROUND_5/autoresearch/13_round2_research/B_bleeders/forensics.csv
- ROUND_5/autoresearch/05_cross_product/groups/pebbles/price_corr.csv
- ROUND_5/autoresearch/mr_study/07_findings/per_product/OXYGEN_SHAKE_CHOCOLATE.md

## Recommendation (final algo)
- **Primary mechanism:** `basket_invariant_PEBBLES`
- **Secondary signals:** pebble_skew, inside_spread_mm, inv_skew
- **Rationale:** Chronic loser in v3 — Phase H ablation will test tighter cap or IDLE; mr_v6 outperformed v3 here (+9,434 vs -12,237) — TAKER candidate for Phase H

## 2 ranked alternatives
1. mr_v6 TAKER (rolling_median w=100, z_in=1.5) — would yield ~+9,434 per mr_study
2. Inside-spread MM only (drop overlays) — baseline before v3 layering
