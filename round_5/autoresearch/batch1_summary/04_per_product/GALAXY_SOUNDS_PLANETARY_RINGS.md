# GALAXY_SOUNDS_PLANETARY_RINGS

**Group:** `galaxy_sounds` | **v3 3-day PnL:** -6,912 | **mr_v6 3-day PnL:** +0 | **Position cap (v3):** 10

## Microstructure

## Cointegration overlays where this product is a leg
- [WITHIN] `GALAXY_SOUNDS_DARK_MATTER ~ GALAXY_SOUNDS_PLANETARY_RINGS` slope=+0.1830 intercept=+8285.00 sd=283.0

## Mean-reversion (mr_study v6)
- mr_v6 mode: **IDLE** — chronic MM loser; mr_study chose to skip

## Reconciled findings (citations)
- ROUND_5/autoresearch/mr_study/00_setup/product_universe.csv
- ROUND_5/autoresearch/07_hidden_patterns/per_product/PANEL_1X2.json
- ROUND_5/autoresearch/mr_study/02_threshold_search/grid_pivot.parquet
- ROUND_5/autoresearch/13_round2_research/K_strategy_v2/ablation_strategies/v3_pebbles_L_cap5.py
- ROUND_5/autoresearch/13_round2_research/K_strategy_v2/ablation_strategies/peb_div2p0_cap4p0.py
- ROUND_5/autoresearch/10_backtesting/results/wf_full_d234_all.csv
- ROUND_5/autoresearch/10_backtesting/results/v3_pebbles_L_cap6.csv
- ROUND_5/autoresearch/10_backtesting/results/5_4_worse.csv
- ROUND_5/autoresearch/10_backtesting/results/mr_v6_validate.csv
- ROUND_5/autoresearch/10_backtesting/results/mr_beta0_3.csv
- ROUND_5/autoresearch/10_backtesting/results/mr_v3_validate.csv
- ROUND_5/autoresearch/10_backtesting/results/mr_v1_validate.csv
- ROUND_5/autoresearch/14_lag_research/M_strategy_v3/strategy_v3_top100.py
- ROUND_5/autoresearch/mr_study/07_findings/headline.md
- ROUND_5/autoresearch/14_lag_research/M_strategy_v3/strategy_v3_top25.py
- ROUND_5/autoresearch/10_backtesting/results/wf_full_worse.csv
- ROUND_5/autoresearch/13_round2_research/K_strategy_v2/ablation_strategies/try_v3c.py
- ROUND_5/autoresearch/10_backtesting/results/dayrem_test34.csv
- ROUND_5/autoresearch/10_backtesting/results/strategy_v3_5-2.csv
- ROUND_5/autoresearch/13_round2_research/K_strategy_v2/ablation_strategies/v3_pebbles_L_cap4.py
- ROUND_5/autoresearch/10_backtesting/results/v3_test34.csv
- ROUND_5/autoresearch/10_backtesting/results/v3_top30.csv
- ROUND_5/autoresearch/13_round2_research/M_submit/strategy_v2.py
- ROUND_5/autoresearch/01_eda/per_product_summary.csv
- ROUND_5/autoresearch/mr_study/06_strategy_mr/utils_local.py

## Recommendation (final algo)
- **Primary mechanism:** `inside_spread_mm`
- **Secondary signals:** inv_skew(-pos*0.2), coint_pairs(n=1)
- **Rationale:** Chronic loser in v3 — Phase H ablation will test tighter cap or IDLE

## 2 ranked alternatives
1. IDLE — mr_v6 chose this (PnL=0); v3 yields -6,912
2. Inside-spread MM only (drop overlays) — baseline before v3 layering
