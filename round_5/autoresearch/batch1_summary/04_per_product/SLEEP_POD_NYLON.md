# SLEEP_POD_NYLON

**Group:** `sleep_pod` | **v3 3-day PnL:** +4,830 | **mr_v6 3-day PnL:** +1,066 | **Position cap (v3):** 10

## Microstructure

## Mean-reversion (mr_study v6)
- mr_v6 mode: default MM (inside-spread bb+1/ba-1 with inv_skew=−pos·0.2)

## Reconciled findings (citations)
- ROUND_5/autoresearch/01_eda/per_product/SLEEP_POD_NYLON/summary.png
- ROUND_5/autoresearch/05_cross_product/groups/sleep_pod/price_corr.csv
- ROUND_5/autoresearch/data_views/prices_r5_d4.parquet
- ROUND_5/autoresearch/05_cross_product/groups/sleep_pod/ret_corr.csv
- ROUND_5/autoresearch/mr_study/02_threshold_search/per_product/SLEEP_POD_NYLON/top20.csv
- ROUND_5/autoresearch/07_hidden_patterns/per_product/SLEEP_POD_NYLON.json
- ROUND_5/autoresearch/04_statistical_patterns/intraday/SLEEP_POD_NYLON.csv
- ROUND_5/autoresearch/05_cross_product/groups/sleep_pod/basket_residual.csv
- ROUND_5/autoresearch/mr_study/07_findings/per_product/SLEEP_POD_NYLON.md
- ROUND_5/autoresearch/14_lag_research/D_var/decision.md
- ROUND_5/autoresearch/mr_study/01_fair_value_zoo/per_product/SLEEP_POD_NYLON/diagnostics.csv
- ROUND_5/autoresearch/mr_study/01_fair_value_zoo/per_product/SLEEP_POD_NYLON/ranking.csv

## Recommendation (final algo)
- **Primary mechanism:** `inside_spread_mm`
- **Secondary signals:** inv_skew(-pos*0.2)
- **Rationale:** v3 PnL +4,830 — moderate; baseline kept

## 2 ranked alternatives
2. Inside-spread MM only (drop overlays) — baseline before v3 layering
