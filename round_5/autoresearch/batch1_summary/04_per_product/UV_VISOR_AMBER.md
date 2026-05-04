# UV_VISOR_AMBER

**Group:** `uv_visor` | **v3 3-day PnL:** +8,853 | **mr_v6 3-day PnL:** +10,718 | **Position cap (v3):** 10

## Microstructure

## Cointegration overlays where this product is a leg
- [WITHIN] `UV_VISOR_AMBER ~ UV_VISOR_MAGENTA` slope=-1.2380 intercept=+21897.00 sd=371.0
- [CROSS] `UV_VISOR_AMBER ~ SNACKPACK_STRAWBERRY` slope=-2.4501 intercept=+34143.94 sd=200.0
- [CROSS] `SLEEP_POD_POLYESTER ~ UV_VISOR_AMBER` slope=-0.9226 intercept=+19139.77 sd=200.0
- [CROSS] `UV_VISOR_AMBER ~ SLEEP_POD_POLYESTER` slope=-0.9595 intercept=+19272.87 sd=200.0
- [CROSS] `SNACKPACK_STRAWBERRY ~ UV_VISOR_AMBER` slope=-0.3259 intercept=+13284.98 sd=200.0

## Mean-reversion (mr_study v6)
- mr_v6 mode: default MM (inside-spread bb+1/ba-1 with inv_skew=−pos·0.2)

## Stability flag
- ⚠️ Days 2/3/4 distributions diverge (KS p < 1e-9) — directional drift between days. Strategy uses inv_skew=−pos·0.2 to absorb.

## Reconciled findings (citations)
- ROUND_5/autoresearch/07_hidden_patterns/per_product/MICROCHIP_SQUARE.json
- ROUND_5/autoresearch/13_round2_research/A_sine/oos_mse.csv
- ROUND_5/autoresearch/13_round2_research/A_sine/plots/UV_VISOR_AMBER.png
- ROUND_5/autoresearch/04_statistical_patterns/intraday/UV_VISOR_AMBER.csv
- ROUND_5/autoresearch/05_cross_product/groups/uv_visor/price_corr.csv
- ROUND_5/autoresearch/13_round2_research/A_sine/per_day_fits.csv
- ROUND_5/autoresearch/07_hidden_patterns/per_product/UV_VISOR_AMBER.json
- ROUND_5/autoresearch/13_round2_research/M_submit/findings_v2.md
- ROUND_5/autoresearch/mr_study/01_fair_value_zoo/per_product/UV_VISOR_AMBER/diagnostics.csv
- ROUND_5/autoresearch/05_cross_product/groups/uv_visor/ret_corr.csv
- ROUND_5/autoresearch/mr_study/07_findings/per_product/UV_VISOR_AMBER.md
- ROUND_5/autoresearch/07_hidden_patterns/per_product/SNACKPACK_STRAWBERRY.json
- ROUND_5/autoresearch/mr_study/01_fair_value_zoo/per_product/UV_VISOR_AMBER/ranking.csv
- ROUND_5/autoresearch/mr_study/02_threshold_search/per_product/UV_VISOR_AMBER/top20.csv
- ROUND_5/autoresearch/13_round2_research/K_strategy_v2/ablation.py
- ROUND_5/autoresearch/05_cross_product/groups/uv_visor/basket_residual.csv
- ROUND_5/autoresearch/13_round2_research/A_sine/run.py
- ROUND_5/autoresearch/07_hidden_patterns/per_product/GALAXY_SOUNDS_PLANETARY_RINGS.json
- ROUND_5/autoresearch/01_eda/per_product/UV_VISOR_AMBER/summary.png
- ROUND_5/autoresearch/13_round2_research/A_sine/rolling_phase.csv
- ROUND_5/autoresearch/13_round2_research/A_sine/decision.md

## Recommendation (final algo)
- **Primary mechanism:** `inside_spread_mm`
- **Secondary signals:** inv_skew(-pos*0.2), coint_pairs(n=5)
- **Rationale:** Strong v3 contributor (+8,853) — keep current setup; Day-of-day KS break flagged — conservative inventory skew

## 2 ranked alternatives
2. Inside-spread MM only (drop overlays) — baseline before v3 layering
