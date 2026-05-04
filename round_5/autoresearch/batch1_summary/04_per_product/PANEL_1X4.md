# PANEL_1X4

**Group:** `panel` | **v3 3-day PnL:** +8,268 | **mr_v6 3-day PnL:** +4,542 | **Position cap (v3):** 10

## Microstructure

## Cointegration overlays where this product is a leg
- [CROSS] `GALAXY_SOUNDS_SOLAR_WINDS ~ PANEL_1X4` slope=-0.5377 intercept=+15490.30 sd=200.0

## Mean-reversion (mr_study v6)
- mr_v6 mode: default MM (inside-spread bb+1/ba-1 with inv_skew=−pos·0.2)

## Stability flag
- ⚠️ Days 2/3/4 distributions diverge (KS p < 1e-9) — directional drift between days. Strategy uses inv_skew=−pos·0.2 to absorb.

## Reconciled findings (citations)
- ROUND_5/autoresearch/logs/progress.md
- ROUND_5/autoresearch/05_cross_product/groups/panel/ret_corr.csv
- ROUND_5/autoresearch/mr_study/07_findings/per_product/PANEL_1X4.md
- ROUND_5/autoresearch/14_lag_research/O_submit/diff_v2_to_v3.md
- ROUND_5/autoresearch/04_statistical_patterns/intraday/PANEL_1X4.csv
- ROUND_5/autoresearch/07_hidden_patterns/per_product/TRANSLATOR_ECLIPSE_CHARCOAL.json
- ROUND_5/autoresearch/13_round2_research/G_intraday/decision.md
- ROUND_5/autoresearch/14_lag_research/O_submit/findings_v3.md
- ROUND_5/autoresearch/14_lag_research/B_leadlag/decision.md
- ROUND_5/autoresearch/01_eda/per_product/PANEL_1X4/summary.png
- ROUND_5/autoresearch/05_cross_product/groups/panel/price_corr.csv
- ROUND_5/autoresearch/mr_study/02_threshold_search/per_product/PANEL_1X4/top20.csv
- ROUND_5/autoresearch/mr_study/01_fair_value_zoo/per_product/PANEL_1X4/ranking.csv
- ROUND_5/autoresearch/14_lag_research/C_lagged_coint/decision.md
- ROUND_5/autoresearch/07_hidden_patterns/per_product/GALAXY_SOUNDS_SOLAR_WINDS.json
- ROUND_5/autoresearch/07_hidden_patterns/per_product/PANEL_1X4.json
- ROUND_5/autoresearch/mr_study/01_fair_value_zoo/per_product/PANEL_1X4/diagnostics.csv
- ROUND_5/autoresearch/05_cross_product/groups/panel/basket_residual.csv

## Recommendation (final algo)
- **Primary mechanism:** `inside_spread_mm`
- **Secondary signals:** inv_skew(-pos*0.2), coint_pairs(n=1)
- **Rationale:** Strong v3 contributor (+8,268) — keep current setup; Day-of-day KS break flagged — conservative inventory skew

## 2 ranked alternatives
2. Inside-spread MM only (drop overlays) — baseline before v3 layering
