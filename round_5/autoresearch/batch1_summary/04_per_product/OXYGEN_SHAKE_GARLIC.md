# OXYGEN_SHAKE_GARLIC

**Group:** `oxygen_shake` | **v3 3-day PnL:** +8,073 | **mr_v6 3-day PnL:** +7,743 | **Position cap (v3):** 10

## Microstructure

## Cointegration overlays where this product is a leg
- [WITHIN] `OXYGEN_SHAKE_CHOCOLATE ~ OXYGEN_SHAKE_GARLIC` slope=-0.1550 intercept=+11066.00 sd=237.0
- [CROSS] `OXYGEN_SHAKE_GARLIC ~ PEBBLES_S` slope=-1.0114 intercept=+20960.00 sd=200.0
- [CROSS] `PEBBLES_S ~ OXYGEN_SHAKE_GARLIC` slope=-0.7727 intercept=+18147.25 sd=200.0
- [CROSS] `PANEL_2X4 ~ OXYGEN_SHAKE_GARLIC` slope=+0.5545 intercept=+4653.12 sd=200.0
- [CROSS] `SNACKPACK_PISTACHIO ~ OXYGEN_SHAKE_GARLIC` slope=-0.1488 intercept=+11269.91 sd=200.0

## Mean-reversion (mr_study v6)
- mr_v6 mode: default MM (inside-spread bb+1/ba-1 with inv_skew=−pos·0.2)

## Reconciled findings (citations)
- ROUND_5/autoresearch/13_round2_research/A_sine/oos_mse.csv
- ROUND_5/autoresearch/mr_study/07_findings/per_product/OXYGEN_SHAKE_GARLIC.md
- ROUND_5/autoresearch/05_cross_product/groups/oxygen_shake/ret_corr.csv
- ROUND_5/autoresearch/11_findings/findings.md
- ROUND_5/autoresearch/mr_study/01_fair_value_zoo/per_product/OXYGEN_SHAKE_GARLIC/diagnostics.csv
- ROUND_5/autoresearch/14_lag_research/O_submit/diff_v2_to_v3.md
- ROUND_5/autoresearch/13_round2_research/A_sine/per_day_fits.csv
- ROUND_5/autoresearch/13_round2_research/G_intraday/decision.md
- ROUND_5/autoresearch/04_statistical_patterns/intraday/OXYGEN_SHAKE_GARLIC.csv
- ROUND_5/autoresearch/13_round2_research/A_sine/plots/OXYGEN_SHAKE_GARLIC.png
- ROUND_5/autoresearch/mr_study/01_fair_value_zoo/per_product/OXYGEN_SHAKE_GARLIC/ranking.csv
- ROUND_5/autoresearch/05_cross_product/groups/oxygen_shake/basket_residual.csv
- ROUND_5/autoresearch/07_hidden_patterns/per_product/OXYGEN_SHAKE_EVENING_BREATH.json
- ROUND_5/autoresearch/14_lag_research/C_lagged_coint/decision.md
- ROUND_5/autoresearch/05_cross_product/groups/oxygen_shake/price_corr.csv
- ROUND_5/autoresearch/mr_study/02_threshold_search/per_product/OXYGEN_SHAKE_GARLIC/top20.csv
- ROUND_5/autoresearch/13_round2_research/A_sine/run.py
- ROUND_5/autoresearch/07_hidden_patterns/per_product/OXYGEN_SHAKE_GARLIC.json
- ROUND_5/autoresearch/13_round2_research/A_sine/rolling_phase.csv
- ROUND_5/autoresearch/13_round2_research/A_sine/decision.md
- ROUND_5/autoresearch/01_eda/per_product/OXYGEN_SHAKE_GARLIC/summary.png

## Recommendation (final algo)
- **Primary mechanism:** `inside_spread_mm`
- **Secondary signals:** inv_skew(-pos*0.2), coint_pairs(n=5)
- **Rationale:** Strong v3 contributor (+8,073) — keep current setup

## 2 ranked alternatives
2. Inside-spread MM only (drop overlays) — baseline before v3 layering
