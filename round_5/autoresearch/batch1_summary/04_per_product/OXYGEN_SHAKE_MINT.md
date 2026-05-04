# OXYGEN_SHAKE_MINT

**Group:** `oxygen_shake` | **v3 3-day PnL:** +2,452 | **mr_v6 3-day PnL:** +2,122 | **Position cap (v3):** 10

## Microstructure

## Mean-reversion (mr_study v6)
- mr_v6 mode: default MM (inside-spread bb+1/ba-1 with inv_skew=−pos·0.2)

## Reconciled findings (citations)
- ROUND_5/autoresearch/04_statistical_patterns/intraday/OXYGEN_SHAKE_MINT.csv
- ROUND_5/autoresearch/05_cross_product/groups/oxygen_shake/ret_corr.csv
- ROUND_5/autoresearch/13_round2_research/D_micro/decision.md
- ROUND_5/autoresearch/01_eda/per_product/OXYGEN_SHAKE_MINT/summary.png
- ROUND_5/autoresearch/07_hidden_patterns/per_product/OXYGEN_SHAKE_MINT.json
- ROUND_5/autoresearch/14_lag_research/B_leadlag/decision.md
- ROUND_5/autoresearch/mr_study/02_threshold_search/per_product/OXYGEN_SHAKE_MINT/top20.csv
- ROUND_5/autoresearch/05_cross_product/groups/oxygen_shake/basket_residual.csv
- ROUND_5/autoresearch/05_cross_product/groups/oxygen_shake/price_corr.csv
- ROUND_5/autoresearch/mr_study/01_fair_value_zoo/per_product/OXYGEN_SHAKE_MINT/ranking.csv
- ROUND_5/autoresearch/07_hidden_patterns/per_product/UV_VISOR_RED.json
- ROUND_5/autoresearch/mr_study/01_fair_value_zoo/per_product/OXYGEN_SHAKE_MINT/diagnostics.csv
- ROUND_5/autoresearch/mr_study/07_findings/per_product/OXYGEN_SHAKE_MINT.md

## Recommendation (final algo)
- **Primary mechanism:** `inside_spread_mm`
- **Secondary signals:** inv_skew(-pos*0.2)
- **Rationale:** v3 PnL +2,452 — moderate; baseline kept

## 2 ranked alternatives
2. Inside-spread MM only (drop overlays) — baseline before v3 layering
