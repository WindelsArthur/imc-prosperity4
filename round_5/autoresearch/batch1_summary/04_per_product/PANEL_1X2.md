# PANEL_1X2

**Group:** `panel` | **v3 3-day PnL:** +509 | **mr_v6 3-day PnL:** -456 | **Position cap (v3):** 3

## Microstructure

## Cointegration overlays where this product is a leg
- [CROSS] `SNACKPACK_VANILLA ~ PANEL_1X2` slope=+0.1461 intercept=+8793.78 sd=200.0

## Mean-reversion (mr_study v6)
- mr_v6 mode: default MM (inside-spread bb+1/ba-1 with inv_skew=−pos·0.2)

## Reconciled findings (citations)
- ROUND_5/autoresearch/07_hidden_patterns/per_product/PANEL_1X2.json
- ROUND_5/autoresearch/13_round2_research/B_bleeders/forensics_summary.csv
- ROUND_5/autoresearch/logs/progress.md
- ROUND_5/autoresearch/13_round2_research/B_bleeders/decision.md
- ROUND_5/autoresearch/05_cross_product/groups/panel/ret_corr.csv
- ROUND_5/autoresearch/14_lag_research/O_submit/diff_v2_to_v3.md
- ROUND_5/autoresearch/13_round2_research/M_submit/findings_v2.md
- ROUND_5/autoresearch/07_hidden_patterns/per_product/OXYGEN_SHAKE_MINT.json
- ROUND_5/autoresearch/04_statistical_patterns/intraday/PANEL_1X2.csv
- ROUND_5/autoresearch/mr_study/02_threshold_search/per_product/PANEL_1X2/top20.csv
- ROUND_5/autoresearch/13_round2_research/M_submit/diff_v1_to_v2.md
- ROUND_5/autoresearch/14_lag_research/O_submit/findings_v3.md
- ROUND_5/autoresearch/14_lag_research/B_leadlag/decision.md
- ROUND_5/autoresearch/05_cross_product/groups/panel/price_corr.csv
- ROUND_5/autoresearch/12_final_strategy/pnl_estimates.md
- ROUND_5/autoresearch/mr_study/07_findings/per_product/PANEL_1X2.md
- ROUND_5/autoresearch/07_hidden_patterns/per_product/PANEL_4X4.json
- ROUND_5/autoresearch/13_round2_research/B_bleeders/run.py
- ROUND_5/autoresearch/13_round2_research/B_bleeders/forensics.csv
- ROUND_5/autoresearch/01_eda/per_product/PANEL_1X2/summary.png
- ROUND_5/autoresearch/mr_study/01_fair_value_zoo/per_product/PANEL_1X2/ranking.csv
- ROUND_5/autoresearch/mr_study/01_fair_value_zoo/per_product/PANEL_1X2/diagnostics.csv
- ROUND_5/autoresearch/05_cross_product/groups/panel/basket_residual.csv
- ROUND_5/autoresearch/13_round2_research/B_bleeders/recipes.csv
- ROUND_5/autoresearch/14_lag_research/E_ar_extended/decision.md

## Recommendation (final algo)
- **Primary mechanism:** `inside_spread_mm`
- **Secondary signals:** inv_skew(-pos*0.2), coint_pairs(n=1), prod_cap=3
- **Rationale:** v3 PnL +509 — moderate; baseline kept

## 2 ranked alternatives
2. Inside-spread MM only (drop overlays) — baseline before v3 layering
