# SLEEP_POD_SUEDE

**Group:** `sleep_pod` | **v3 3-day PnL:** +3,027 | **mr_v6 3-day PnL:** +0 | **Position cap (v3):** 10

## Microstructure

## Cointegration overlays where this product is a leg
- [WITHIN] `SLEEP_POD_POLYESTER ~ SLEEP_POD_SUEDE` slope=+0.7560 intercept=+2977.00 sd=426.0
- [CROSS] `MICROCHIP_SQUARE ~ SLEEP_POD_SUEDE` slope=+1.8678 intercept=-7692.97 sd=200.0
- [CROSS] `SLEEP_POD_SUEDE ~ MICROCHIP_SQUARE` slope=+0.4516 intercept=+5257.75 sd=200.0

## Mean-reversion (mr_study v6)
- mr_v6 mode: **IDLE** — chronic MM loser; mr_study chose to skip

## Reconciled findings (citations)
- ROUND_5/autoresearch/07_hidden_patterns/per_product/SLEEP_POD_POLYESTER.json
- ROUND_5/autoresearch/13_round2_research/A_sine/plots/SLEEP_POD_SUEDE.png
- ROUND_5/autoresearch/13_round2_research/A_sine/oos_mse.csv
- ROUND_5/autoresearch/05_cross_product/groups/sleep_pod/price_corr.csv
- ROUND_5/autoresearch/07_hidden_patterns/per_product/ROBOT_DISHES.json
- ROUND_5/autoresearch/05_cross_product/groups/sleep_pod/ret_corr.csv
- ROUND_5/autoresearch/13_round2_research/A_sine/per_day_fits.csv
- ROUND_5/autoresearch/01_eda/per_product/SLEEP_POD_SUEDE/summary.png
- ROUND_5/autoresearch/07_hidden_patterns/per_product/TRANSLATOR_VOID_BLUE.json
- ROUND_5/autoresearch/14_lag_research/O_submit/findings_v3.md
- ROUND_5/autoresearch/05_cross_product/groups/sleep_pod/basket_residual.csv
- ROUND_5/autoresearch/mr_study/01_fair_value_zoo/per_product/SLEEP_POD_SUEDE/ranking.csv
- ROUND_5/autoresearch/mr_study/07_findings/per_product/SLEEP_POD_SUEDE.md
- ROUND_5/autoresearch/mr_study/01_fair_value_zoo/per_product/SLEEP_POD_SUEDE/diagnostics.csv
- ROUND_5/autoresearch/04_statistical_patterns/intraday/SLEEP_POD_SUEDE.csv
- ROUND_5/autoresearch/07_hidden_patterns/per_product/SLEEP_POD_SUEDE.json
- ROUND_5/autoresearch/13_round2_research/A_sine/run.py
- ROUND_5/autoresearch/07_hidden_patterns/per_product/MICROCHIP_RECTANGLE.json
- ROUND_5/autoresearch/13_round2_research/A_sine/rolling_phase.csv
- ROUND_5/autoresearch/13_round2_research/A_sine/decision.md
- ROUND_5/autoresearch/mr_study/02_threshold_search/per_product/SLEEP_POD_SUEDE/top20.csv

## Recommendation (final algo)
- **Primary mechanism:** `inside_spread_mm`
- **Secondary signals:** inv_skew(-pos*0.2), coint_pairs(n=3)
- **Rationale:** v3 PnL +3,027 — moderate; baseline kept

## 2 ranked alternatives
1. IDLE — mr_v6 chose this (PnL=0); v3 yields +3,027
2. Inside-spread MM only (drop overlays) — baseline before v3 layering
