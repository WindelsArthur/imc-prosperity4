# ROBOT_LAUNDRY

**Group:** `robot` | **v3 3-day PnL:** +4,074 | **mr_v6 3-day PnL:** +2,151 | **Position cap (v3):** 10

## Microstructure

## Cointegration overlays where this product is a leg
- [WITHIN] `ROBOT_LAUNDRY ~ ROBOT_VACUUMING` slope=+0.3340 intercept=+7072.00 sd=234.0

## Mean-reversion (mr_study v6)
- mr_v6 mode: default MM (inside-spread bb+1/ba-1 with inv_skew=−pos·0.2)

## Reconciled findings (citations)
- ROUND_5/autoresearch/mr_study/07_findings/per_product/ROBOT_LAUNDRY.md
- ROUND_5/autoresearch/01_eda/per_product/ROBOT_LAUNDRY/summary.png
- ROUND_5/autoresearch/14_lag_research/E_ar_extended/sign_switching.csv
- ROUND_5/autoresearch/mr_study/01_fair_value_zoo/per_product/ROBOT_LAUNDRY/diagnostics.csv
- ROUND_5/autoresearch/mr_study/01_fair_value_zoo/per_product/ROBOT_LAUNDRY/ranking.csv
- ROUND_5/autoresearch/05_cross_product/groups/robot/price_corr.csv
- ROUND_5/autoresearch/14_lag_research/D_var/decision.md
- ROUND_5/autoresearch/mr_study/02_threshold_search/per_product/ROBOT_LAUNDRY/top20.csv
- ROUND_5/autoresearch/05_cross_product/groups/robot/basket_residual.csv
- ROUND_5/autoresearch/07_hidden_patterns/per_product/ROBOT_LAUNDRY.json
- ROUND_5/autoresearch/04_statistical_patterns/intraday/ROBOT_LAUNDRY.csv
- ROUND_5/autoresearch/05_cross_product/groups/robot/ret_corr.csv

## Recommendation (final algo)
- **Primary mechanism:** `inside_spread_mm`
- **Secondary signals:** inv_skew(-pos*0.2), coint_pairs(n=1)
- **Rationale:** v3 PnL +4,074 — moderate; baseline kept

## 2 ranked alternatives
2. Inside-spread MM only (drop overlays) — baseline before v3 layering
