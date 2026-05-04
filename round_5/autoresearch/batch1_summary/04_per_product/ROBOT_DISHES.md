# ROBOT_DISHES

**Group:** `robot` | **v3 3-day PnL:** -2,982 | **mr_v6 3-day PnL:** +11,219 | **Position cap (v3):** 10

## Microstructure
- **AR(1) on Δmid:** -0.2317 (re-verified on stitched 2+3+4 mids)
- **Lattice ratio:** 0.1016 (n_distinct_mids = 3,048 of 30,000 ticks)

## Mean-reversion (mr_study v6)
- mr_v6 mode: **TAKER** (rolling_mean w=50, z_in=2.5)

## Stability flag
- ⚠️ Days 2/3/4 distributions diverge (KS p < 1e-9) — directional drift between days. Strategy uses inv_skew=−pos·0.2 to absorb.

## Reconciled findings (citations)
- ROUND_5/autoresearch/mr_study/07_findings/per_product/PEBBLES_M.md
- ROUND_5/autoresearch/mr_study/07_findings/per_product/PEBBLES_L.md
- ROUND_5/autoresearch/10_backtesting/sweep_mr_d_3prods.py
- ROUND_5/autoresearch/07_hidden_patterns/per_product/SLEEP_POD_LAMB_WOOL.json
- ROUND_5/autoresearch/mr_study/07_findings/per_product/ROBOT_MOPPING.md
- ROUND_5/autoresearch/mr_study/07_findings/per_product/PEBBLES_XS.md
- ROUND_5/autoresearch/mr_study/07_findings/per_product/ROBOT_DISHES.md
- ROUND_5/autoresearch/07_hidden_patterns/per_product/ROBOT_DISHES.json
- ROUND_5/autoresearch/mr_study/05_robustness/stability_report.md
- ROUND_5/autoresearch/01_eda/per_product/ROBOT_DISHES/summary.png
- ROUND_5/autoresearch/05_cross_product/groups/robot/price_corr.csv
- ROUND_5/autoresearch/mr_study/01_fair_value_zoo/per_product/ROBOT_DISHES/diagnostics.csv
- ROUND_5/autoresearch/13_round2_research/M_submit/diff_v1_to_v2.md
- ROUND_5/autoresearch/mr_study/07_findings/per_product/SLEEP_POD_POLYESTER.md
- ROUND_5/autoresearch/04_statistical_patterns/intraday/ROBOT_DISHES.csv
- ROUND_5/autoresearch/05_cross_product/groups/robot/basket_residual.csv
- ROUND_5/autoresearch/mr_study/07_findings/per_product/OXYGEN_SHAKE_CHOCOLATE.md
- ROUND_5/autoresearch/mr_study/02_threshold_search/per_product/ROBOT_DISHES/top20.csv
- ROUND_5/autoresearch/mr_study/01_fair_value_zoo/per_product/ROBOT_DISHES/ranking.csv
- ROUND_5/autoresearch/05_cross_product/groups/robot/ret_corr.csv

## Recommendation (final algo)
- **Primary mechanism:** `inside_spread_mm`
- **Secondary signals:** inv_skew(-pos*0.2)
- **Rationale:** v3 PnL -2,982 — moderate; baseline kept; Day-of-day KS break flagged — conservative inventory skew; mr_v6 outperformed v3 here (+11,219 vs -2,982) — TAKER candidate for Phase H

## 2 ranked alternatives
1. mr_v6 TAKER (rolling_mean w=50, z_in=2.5) — would yield ~+11,219 per mr_study
2. Inside-spread MM only (drop overlays) — baseline before v3 layering
