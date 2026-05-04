# SLEEP_POD_POLYESTER

**Group:** `sleep_pod` | **v3 3-day PnL:** +4,040 | **mr_v6 3-day PnL:** +8,049 | **Position cap (v3):** 10

## Microstructure

## Cointegration overlays where this product is a leg
- [WITHIN] `SLEEP_POD_COTTON ~ SLEEP_POD_POLYESTER` slope=+0.5190 intercept=+5144.00 sd=328.0
- [WITHIN] `SLEEP_POD_POLYESTER ~ SLEEP_POD_SUEDE` slope=+0.7560 intercept=+2977.00 sd=426.0
- [CROSS] `SLEEP_POD_POLYESTER ~ UV_VISOR_AMBER` slope=-0.9226 intercept=+19139.77 sd=200.0
- [CROSS] `UV_VISOR_AMBER ~ SLEEP_POD_POLYESTER` slope=-0.9595 intercept=+19272.87 sd=200.0
- [CROSS] `SNACKPACK_STRAWBERRY ~ SLEEP_POD_POLYESTER` slope=+0.3255 intercept=+6852.82 sd=200.0

## Mean-reversion (mr_study v6)
- mr_v6 mode: **TAKER** (range_mid w=500, z_in=1.75)

## Stability flag
- ⚠️ Days 2/3/4 distributions diverge (KS p < 1e-9) — directional drift between days. Strategy uses inv_skew=−pos·0.2 to absorb.

## Reconciled findings (citations)
- ROUND_5/autoresearch/07_hidden_patterns/per_product/SLEEP_POD_POLYESTER.json
- ROUND_5/autoresearch/13_round2_research/A_sine/oos_mse.csv
- ROUND_5/autoresearch/05_cross_product/groups/sleep_pod/price_corr.csv
- ROUND_5/autoresearch/01_eda/per_product/SLEEP_POD_POLYESTER/summary.png
- ROUND_5/autoresearch/07_hidden_patterns/per_product/TRANSLATOR_GRAPHITE_MIST.json
- ROUND_5/autoresearch/mr_study/01_fair_value_zoo/per_product/SLEEP_POD_POLYESTER/diagnostics.csv
- ROUND_5/autoresearch/05_cross_product/groups/sleep_pod/ret_corr.csv
- ROUND_5/autoresearch/13_round2_research/A_sine/per_day_fits.csv
- ROUND_5/autoresearch/mr_study/05_robustness/stability_report.md
- ROUND_5/autoresearch/13_round2_research/A_sine/plots/SLEEP_POD_POLYESTER.png
- ROUND_5/autoresearch/05_cross_product/groups/sleep_pod/basket_residual.csv
- ROUND_5/autoresearch/mr_study/07_findings/per_product/SLEEP_POD_POLYESTER.md
- ROUND_5/autoresearch/14_lag_research/D_var/decision.md
- ROUND_5/autoresearch/04_statistical_patterns/intraday/SLEEP_POD_POLYESTER.csv
- ROUND_5/autoresearch/mr_study/01_fair_value_zoo/per_product/SLEEP_POD_POLYESTER/ranking.csv
- ROUND_5/autoresearch/13_round2_research/A_sine/run.py
- ROUND_5/autoresearch/07_hidden_patterns/per_product/ROBOT_LAUNDRY.json
- ROUND_5/autoresearch/mr_study/02_threshold_search/per_product/SLEEP_POD_POLYESTER/top20.csv
- ROUND_5/autoresearch/13_round2_research/A_sine/rolling_phase.csv
- ROUND_5/autoresearch/13_round2_research/A_sine/decision.md

## Recommendation (final algo)
- **Primary mechanism:** `inside_spread_mm`
- **Secondary signals:** inv_skew(-pos*0.2), coint_pairs(n=5)
- **Rationale:** v3 PnL +4,040 — moderate; baseline kept; Day-of-day KS break flagged — conservative inventory skew; mr_v6 outperformed v3 here (+8,049 vs +4,040) — TAKER candidate for Phase H

## 2 ranked alternatives
1. mr_v6 TAKER (range_mid w=500, z_in=1.75) — would yield ~+8,049 per mr_study
2. Inside-spread MM only (drop overlays) — baseline before v3 layering
