# PEBBLES_XL

**Group:** `pebbles` | **v3 3-day PnL:** +9,942 | **mr_v6 3-day PnL:** +10,865 | **Position cap (v3):** 10

## Microstructure
- **PEBBLES basket member:** Σ_pebbles = 50,000 ± 2.8 (re-verified, std=2.80, half-life 0.16 ticks)

## Cointegration overlays where this product is a leg
- [CROSS] `PEBBLES_XL ~ PANEL_2X4` slope=+2.4821 intercept=-14735.73 sd=200.0
- [CROSS] `PANEL_2X4 ~ PEBBLES_XL` slope=+0.3093 intercept=+7174.37 sd=200.0

## Mean-reversion (mr_study v6)
- mr_v6 mode: default MM (inside-spread bb+1/ba-1 with inv_skew=−pos·0.2)

## Reconciled findings (citations)
- ROUND_5/autoresearch/07_hidden_patterns/per_product/UV_VISOR_MAGENTA.json
- ROUND_5/autoresearch/13_round2_research/A_sine/oos_mse.csv
- ROUND_5/autoresearch/mr_study/02_threshold_search/per_product/PEBBLES_XL/top20.csv
- ROUND_5/autoresearch/mr_study/07_findings/per_product/PEBBLES_XL.md
- ROUND_5/autoresearch/13_round2_research/A_sine/per_day_fits.csv
- ROUND_5/autoresearch/07_hidden_patterns/per_product/PEBBLES_XL.json
- ROUND_5/autoresearch/01_eda/per_product/PEBBLES_XL/summary.png
- ROUND_5/autoresearch/14_lag_research/O_submit/findings_v3.md
- ROUND_5/autoresearch/14_lag_research/B_leadlag/decision.md
- ROUND_5/autoresearch/05_cross_product/groups/pebbles/ret_corr.csv
- ROUND_5/autoresearch/mr_study/01_fair_value_zoo/per_product/PEBBLES_XL/ranking.csv
- ROUND_5/autoresearch/05_cross_product/groups/pebbles/basket_residual.csv
- ROUND_5/autoresearch/13_round2_research/A_sine/plots/PEBBLES_XL.png
- ROUND_5/autoresearch/04_statistical_patterns/intraday/PEBBLES_XL.csv
- ROUND_5/autoresearch/13_round2_research/A_sine/run.py
- ROUND_5/autoresearch/05_cross_product/groups/pebbles/price_corr.csv
- ROUND_5/autoresearch/mr_study/01_fair_value_zoo/per_product/PEBBLES_XL/diagnostics.csv
- ROUND_5/autoresearch/13_round2_research/A_sine/rolling_phase.csv
- ROUND_5/autoresearch/13_round2_research/A_sine/decision.md

## Recommendation (final algo)
- **Primary mechanism:** `basket_invariant_PEBBLES`
- **Secondary signals:** pebble_skew, inside_spread_mm, inv_skew, coint_pairs(n=2)
- **Rationale:** Strong v3 contributor (+9,942) — keep current setup

## 2 ranked alternatives
2. Inside-spread MM only (drop overlays) — baseline before v3 layering
