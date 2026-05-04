# OXYGEN_SHAKE_MORNING_BREATH

**Group:** `oxygen_shake` | **v3 3-day PnL:** +8,240 | **mr_v6 3-day PnL:** +7,544 | **Position cap (v3):** 10

## Microstructure

## Cointegration overlays where this product is a leg
- [CROSS] `PEBBLES_M ~ OXYGEN_SHAKE_MORNING_BREATH` slope=-0.9037 intercept=+19300.55 sd=200.0

## Mean-reversion (mr_study v6)
- mr_v6 mode: default MM (inside-spread bb+1/ba-1 with inv_skew=−pos·0.2)

## Reconciled findings (citations)
- ROUND_5/autoresearch/05_cross_product/groups/oxygen_shake/ret_corr.csv
- ROUND_5/autoresearch/13_round2_research/D_micro/decision.md
- ROUND_5/autoresearch/01_eda/per_product/OXYGEN_SHAKE_MORNING_BREATH/summary.png
- ROUND_5/autoresearch/14_lag_research/O_submit/diff_v2_to_v3.md
- ROUND_5/autoresearch/07_hidden_patterns/per_product/OXYGEN_SHAKE_MORNING_BREATH.json
- ROUND_5/autoresearch/mr_study/01_fair_value_zoo/per_product/OXYGEN_SHAKE_MORNING_BREATH/diagnostics.csv
- ROUND_5/autoresearch/mr_study/01_fair_value_zoo/per_product/OXYGEN_SHAKE_MORNING_BREATH/ranking.csv
- ROUND_5/autoresearch/mr_study/02_threshold_search/per_product/OXYGEN_SHAKE_MORNING_BREATH/top20.csv
- ROUND_5/autoresearch/04_statistical_patterns/intraday/OXYGEN_SHAKE_MORNING_BREATH.csv
- ROUND_5/autoresearch/05_cross_product/groups/oxygen_shake/basket_residual.csv
- ROUND_5/autoresearch/14_lag_research/C_lagged_coint/decision.md
- ROUND_5/autoresearch/05_cross_product/groups/oxygen_shake/price_corr.csv
- ROUND_5/autoresearch/14_lag_research/E_ar_extended/decision.md
- ROUND_5/autoresearch/07_hidden_patterns/per_product/ROBOT_IRONING.json
- ROUND_5/autoresearch/mr_study/07_findings/per_product/OXYGEN_SHAKE_MORNING_BREATH.md

## Recommendation (final algo)
- **Primary mechanism:** `inside_spread_mm`
- **Secondary signals:** inv_skew(-pos*0.2), coint_pairs(n=1)
- **Rationale:** Strong v3 contributor (+8,240) — keep current setup

## 2 ranked alternatives
2. Inside-spread MM only (drop overlays) — baseline before v3 layering
