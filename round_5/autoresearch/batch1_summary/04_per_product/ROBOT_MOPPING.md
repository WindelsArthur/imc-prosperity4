# ROBOT_MOPPING

**Group:** `robot` | **v3 3-day PnL:** +994 | **mr_v6 3-day PnL:** +10,225 | **Position cap (v3):** 4

## Microstructure

## Mean-reversion (mr_study v6)
- mr_v6 mode: **TAKER** (rolling_quadratic w=500, z_in=1.25)

## Reconciled findings (citations)
- ROUND_5/autoresearch/13_round2_research/B_bleeders/forensics_summary.csv
- ROUND_5/autoresearch/13_round2_research/B_bleeders/decision.md
- ROUND_5/autoresearch/mr_study/02_threshold_search/per_product/ROBOT_MOPPING/top20.csv
- ROUND_5/autoresearch/mr_study/07_findings/per_product/ROBOT_MOPPING.md
- ROUND_5/autoresearch/13_round2_research/M_submit/findings_v2.md
- ROUND_5/autoresearch/mr_study/05_robustness/stability_report.md
- ROUND_5/autoresearch/mr_study/01_fair_value_zoo/per_product/ROBOT_MOPPING/diagnostics.csv
- ROUND_5/autoresearch/05_cross_product/groups/robot/price_corr.csv
- ROUND_5/autoresearch/07_hidden_patterns/per_product/OXYGEN_SHAKE_MORNING_BREATH.json
- ROUND_5/autoresearch/13_round2_research/M_submit/diff_v1_to_v2.md
- ROUND_5/autoresearch/01_eda/per_product/ROBOT_MOPPING/summary.png
- ROUND_5/autoresearch/07_hidden_patterns/per_product/ROBOT_MOPPING.json
- ROUND_5/autoresearch/13_round2_research/B_bleeders/run.py
- ROUND_5/autoresearch/05_cross_product/groups/robot/basket_residual.csv
- ROUND_5/autoresearch/mr_study/01_fair_value_zoo/per_product/ROBOT_MOPPING/ranking.csv
- ROUND_5/autoresearch/13_round2_research/B_bleeders/recipes.csv
- ROUND_5/autoresearch/04_statistical_patterns/intraday/ROBOT_MOPPING.csv
- ROUND_5/autoresearch/07_hidden_patterns/per_product/GALAXY_SOUNDS_DARK_MATTER.json
- ROUND_5/autoresearch/05_cross_product/groups/robot/ret_corr.csv

## Recommendation (final algo)
- **Primary mechanism:** `inside_spread_mm`
- **Secondary signals:** inv_skew(-pos*0.2), prod_cap=4
- **Rationale:** v3 PnL +994 — moderate; baseline kept; mr_v6 outperformed v3 here (+10,225 vs +994) — TAKER candidate for Phase H

## 2 ranked alternatives
1. mr_v6 TAKER (rolling_quadratic w=500, z_in=1.25) — would yield ~+10,225 per mr_study
2. Inside-spread MM only (drop overlays) — baseline before v3 layering
