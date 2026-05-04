# MICROCHIP_SQUARE

**Group:** `microchip` | **v3 3-day PnL:** +6,182 | **mr_v6 3-day PnL:** +7,985 | **Position cap (v3):** 10

## Microstructure

## Cointegration overlays where this product is a leg
- [WITHIN] `MICROCHIP_RECTANGLE ~ MICROCHIP_SQUARE` slope=-0.4010 intercept=+14119.00 sd=304.0
- [CROSS] `MICROCHIP_SQUARE ~ SLEEP_POD_SUEDE` slope=+1.8678 intercept=-7692.97 sd=200.0
- [CROSS] `SLEEP_POD_SUEDE ~ MICROCHIP_SQUARE` slope=+0.4516 intercept=+5257.75 sd=200.0

## Mean-reversion (mr_study v6)
- mr_v6 mode: default MM (inside-spread bb+1/ba-1 with inv_skew=−pos·0.2)

## Stability flag
- ⚠️ Days 2/3/4 distributions diverge (KS p < 1e-9) — directional drift between days. Strategy uses inv_skew=−pos·0.2 to absorb.

## Reconciled findings (citations)
- ROUND_5/autoresearch/07_hidden_patterns/per_product/TRANSLATOR_ASTRO_BLACK.json
- ROUND_5/autoresearch/07_hidden_patterns/per_product/UV_VISOR_ORANGE.json
- ROUND_5/autoresearch/07_hidden_patterns/per_product/MICROCHIP_SQUARE.json
- ROUND_5/autoresearch/13_round2_research/D_micro/decision.md
- ROUND_5/autoresearch/mr_study/00_setup/data_sanity.md
- ROUND_5/autoresearch/11_findings/findings.md
- ROUND_5/autoresearch/07_hidden_patterns/per_product/MICROCHIP_OVAL.json
- ROUND_5/autoresearch/01_eda/per_product/MICROCHIP_SQUARE/summary.png
- ROUND_5/autoresearch/14_lag_research/O_submit/diff_v2_to_v3.md
- ROUND_5/autoresearch/07_hidden_patterns/per_product/UV_VISOR_AMBER.json
- ROUND_5/autoresearch/14_lag_research/F_flow_lag/decision.md
- ROUND_5/autoresearch/mr_study/02_threshold_search/per_product/MICROCHIP_SQUARE/top20.csv
- ROUND_5/autoresearch/04_statistical_patterns/intraday/MICROCHIP_SQUARE.csv
- ROUND_5/autoresearch/07_hidden_patterns/per_product/OXYGEN_SHAKE_CHOCOLATE.json
- ROUND_5/autoresearch/14_lag_research/O_submit/findings_v3.md
- ROUND_5/autoresearch/11_findings/exploitable_patterns.md
- ROUND_5/autoresearch/07_hidden_patterns/per_product/SLEEP_POD_COTTON.json
- ROUND_5/autoresearch/05_cross_product/groups/microchip/basket_residual.csv
- ROUND_5/autoresearch/07_hidden_patterns/findings.md
- ROUND_5/autoresearch/14_lag_research/C_lagged_coint/decision.md
- ROUND_5/autoresearch/05_cross_product/groups/microchip/ret_corr.csv
- ROUND_5/autoresearch/08_signals/run.py
- ROUND_5/autoresearch/mr_study/01_fair_value_zoo/per_product/MICROCHIP_SQUARE/diagnostics.csv
- ROUND_5/autoresearch/mr_study/01_fair_value_zoo/per_product/MICROCHIP_SQUARE/ranking.csv
- ROUND_5/autoresearch/data_views/prices_r5_d3.parquet

## Recommendation (final algo)
- **Primary mechanism:** `inside_spread_mm`
- **Secondary signals:** inv_skew(-pos*0.2), coint_pairs(n=3)
- **Rationale:** v3 PnL +6,182 — moderate; baseline kept; Day-of-day KS break flagged — conservative inventory skew

## 2 ranked alternatives
2. Inside-spread MM only (drop overlays) — baseline before v3 layering
