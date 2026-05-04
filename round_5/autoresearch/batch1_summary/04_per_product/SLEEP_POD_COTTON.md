# SLEEP_POD_COTTON

**Group:** `sleep_pod` | **v3 3-day PnL:** +9,177 | **mr_v6 3-day PnL:** +8,790 | **Position cap (v3):** 10

## Microstructure

## Cointegration overlays where this product is a leg
- [WITHIN] `SLEEP_POD_COTTON ~ SLEEP_POD_POLYESTER` slope=+0.5190 intercept=+5144.00 sd=328.0

## Mean-reversion (mr_study v6)
- mr_v6 mode: default MM (inside-spread bb+1/ba-1 with inv_skew=−pos·0.2)

## Reconciled findings (citations)
- ROUND_5/autoresearch/mr_study/01_fair_value_zoo/per_product/SLEEP_POD_COTTON/diagnostics.csv
- ROUND_5/autoresearch/05_cross_product/groups/sleep_pod/price_corr.csv
- ROUND_5/autoresearch/mr_study/02_threshold_search/per_product/SLEEP_POD_COTTON/top20.csv
- ROUND_5/autoresearch/05_cross_product/groups/sleep_pod/ret_corr.csv
- ROUND_5/autoresearch/mr_study/07_findings/per_product/SLEEP_POD_COTTON.md
- ROUND_5/autoresearch/05_cross_product/groups/sleep_pod/basket_residual.csv
- ROUND_5/autoresearch/07_hidden_patterns/per_product/SLEEP_POD_COTTON.json
- ROUND_5/autoresearch/mr_study/01_fair_value_zoo/per_product/SLEEP_POD_COTTON/ranking.csv
- ROUND_5/autoresearch/14_lag_research/D_var/decision.md
- ROUND_5/autoresearch/04_statistical_patterns/intraday/SLEEP_POD_COTTON.csv
- ROUND_5/autoresearch/01_eda/per_product/SLEEP_POD_COTTON/summary.png

## Recommendation (final algo)
- **Primary mechanism:** `inside_spread_mm`
- **Secondary signals:** inv_skew(-pos*0.2), coint_pairs(n=1)
- **Rationale:** Strong v3 contributor (+9,177) — keep current setup

## 2 ranked alternatives
2. Inside-spread MM only (drop overlays) — baseline before v3 layering
