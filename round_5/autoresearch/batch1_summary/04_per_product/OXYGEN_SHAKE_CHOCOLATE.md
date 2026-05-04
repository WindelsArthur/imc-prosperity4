# OXYGEN_SHAKE_CHOCOLATE

**Group:** `oxygen_shake` | **v3 3-day PnL:** +4,867 | **mr_v6 3-day PnL:** +8,864 | **Position cap (v3):** 10

## Microstructure
- **AR(1) on Δmid:** -0.0891 (re-verified on stitched 2+3+4 mids)

## Cointegration overlays where this product is a leg
- [WITHIN] `OXYGEN_SHAKE_CHOCOLATE ~ OXYGEN_SHAKE_GARLIC` slope=-0.1550 intercept=+11066.00 sd=237.0

## Mean-reversion (mr_study v6)
- mr_v6 mode: **TAKER** (rolling_linreg w=500, z_in=1.0)

## Stability flag
- ⚠️ Days 2/3/4 distributions diverge (KS p < 1e-9) — directional drift between days. Strategy uses inv_skew=−pos·0.2 to absorb.

## Reconciled findings (citations)
- ROUND_5/autoresearch/logs/progress.md
- ROUND_5/autoresearch/05_cross_product/groups/oxygen_shake/ret_corr.csv
- ROUND_5/autoresearch/13_round2_research/D_micro/decision.md
- ROUND_5/autoresearch/mr_study/00_setup/data_sanity.md
- ROUND_5/autoresearch/11_findings/findings.md
- ROUND_5/autoresearch/mr_study/01_fair_value_zoo/per_product/OXYGEN_SHAKE_CHOCOLATE/diagnostics.csv
- ROUND_5/autoresearch/07_hidden_patterns/per_product/OXYGEN_SHAKE_CHOCOLATE.json
- ROUND_5/autoresearch/mr_study/05_robustness/stability_report.md
- ROUND_5/autoresearch/11_findings/exploitable_patterns.md
- ROUND_5/autoresearch/14_lag_research/B_leadlag/decision.md
- ROUND_5/autoresearch/mr_study/01_fair_value_zoo/per_product/OXYGEN_SHAKE_CHOCOLATE/ranking.csv
- ROUND_5/autoresearch/mr_study/06_strategy_mr/distilled_params.py
- ROUND_5/autoresearch/mr_study/02_threshold_search/per_product/OXYGEN_SHAKE_CHOCOLATE/top20.csv
- ROUND_5/autoresearch/12_final_strategy/pnl_estimates.md
- ROUND_5/autoresearch/01_eda/per_product/OXYGEN_SHAKE_CHOCOLATE/summary.png
- ROUND_5/autoresearch/07_hidden_patterns/findings.md
- ROUND_5/autoresearch/05_cross_product/groups/oxygen_shake/basket_residual.csv
- ROUND_5/autoresearch/05_cross_product/groups/oxygen_shake/price_corr.csv
- ROUND_5/autoresearch/08_signals/run.py
- ROUND_5/autoresearch/mr_study/07_findings/per_product/OXYGEN_SHAKE_CHOCOLATE.md
- ROUND_5/autoresearch/14_lag_research/A_atlas/decision.md
- ROUND_5/autoresearch/14_lag_research/E_ar_extended/decision.md
- ROUND_5/autoresearch/04_statistical_patterns/intraday/OXYGEN_SHAKE_CHOCOLATE.csv

## Recommendation (final algo)
- **Primary mechanism:** `inside_spread_mm`
- **Secondary signals:** inv_skew(-pos*0.2), coint_pairs(n=1)
- **Rationale:** v3 PnL +4,867 — moderate; baseline kept; Day-of-day KS break flagged — conservative inventory skew; mr_v6 outperformed v3 here (+8,864 vs +4,867) — TAKER candidate for Phase H

## 2 ranked alternatives
1. mr_v6 TAKER (rolling_linreg w=500, z_in=1.0) — would yield ~+8,864 per mr_study
2. Inside-spread MM only (drop overlays) — baseline before v3 layering
