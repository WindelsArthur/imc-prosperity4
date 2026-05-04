# TRANSLATOR_SPACE_GRAY

**Group:** `translator` | **v3 3-day PnL:** -5,039 | **mr_v6 3-day PnL:** +0 | **Position cap (v3):** 4

## Microstructure

## Mean-reversion (mr_study v6)
- mr_v6 mode: **IDLE** — chronic MM loser; mr_study chose to skip

## Reconciled findings (citations)
- ROUND_5/autoresearch/01_eda/per_product/TRANSLATOR_SPACE_GRAY/summary.png
- ROUND_5/autoresearch/05_cross_product/groups/translator/basket_residual.csv
- ROUND_5/autoresearch/mr_study/07_findings/per_product/TRANSLATOR_SPACE_GRAY.md
- ROUND_5/autoresearch/04_statistical_patterns/intraday/TRANSLATOR_SPACE_GRAY.csv
- ROUND_5/autoresearch/data_views/prices_r5_d4.parquet
- ROUND_5/autoresearch/mr_study/02_threshold_search/per_product/TRANSLATOR_SPACE_GRAY/top20.csv
- ROUND_5/autoresearch/mr_study/01_fair_value_zoo/per_product/TRANSLATOR_SPACE_GRAY/ranking.csv
- ROUND_5/autoresearch/07_hidden_patterns/per_product/GALAXY_SOUNDS_SOLAR_FLAMES.json
- ROUND_5/autoresearch/05_cross_product/groups/translator/price_corr.csv
- ROUND_5/autoresearch/mr_study/01_fair_value_zoo/per_product/TRANSLATOR_SPACE_GRAY/diagnostics.csv
- ROUND_5/autoresearch/05_cross_product/groups/translator/ret_corr.csv
- ROUND_5/autoresearch/07_hidden_patterns/per_product/TRANSLATOR_SPACE_GRAY.json
- ROUND_5/autoresearch/13_round2_research/B_bleeders/forensics.csv

## Recommendation (final algo)
- **Primary mechanism:** `inside_spread_mm`
- **Secondary signals:** inv_skew(-pos*0.2), prod_cap=4
- **Rationale:** Chronic loser in v3 — Phase H ablation will test tighter cap or IDLE

## 2 ranked alternatives
1. IDLE — mr_v6 chose this (PnL=0); v3 yields -5,039
2. Inside-spread MM only (drop overlays) — baseline before v3 layering
