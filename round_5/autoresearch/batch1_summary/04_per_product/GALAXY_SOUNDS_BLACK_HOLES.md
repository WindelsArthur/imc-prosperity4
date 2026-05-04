# GALAXY_SOUNDS_BLACK_HOLES

**Group:** `galaxy_sounds` | **v3 3-day PnL:** +15,158 | **mr_v6 3-day PnL:** +14,828 | **Position cap (v3):** 10

## Microstructure

## Cointegration overlays where this product is a leg
- [CROSS] `GALAXY_SOUNDS_BLACK_HOLES ~ PEBBLES_S` slope=-1.0180 intercept=+20559.94 sd=200.0
- [CROSS] `PEBBLES_S ~ GALAXY_SOUNDS_BLACK_HOLES` slope=-0.7694 intercept=+17755.06 sd=200.0

## Mean-reversion (mr_study v6)
- mr_v6 mode: default MM (inside-spread bb+1/ba-1 with inv_skew=−pos·0.2)

## Stability flag
- ⚠️ Days 2/3/4 distributions diverge (KS p < 1e-9) — directional drift between days. Strategy uses inv_skew=−pos·0.2 to absorb.

## Reconciled findings (citations)
- ROUND_5/autoresearch/mr_study/00_setup/product_universe.csv
- ROUND_5/autoresearch/mr_study/02_threshold_search/grid_pivot.parquet
- ROUND_5/autoresearch/13_round2_research/K_strategy_v2/ablation_strategies/v3_pebbles_L_cap5.py
- ROUND_5/autoresearch/13_round2_research/K_strategy_v2/ablation_strategies/peb_div2p0_cap4p0.py
- ROUND_5/autoresearch/10_backtesting/results/wf_full_d234_all.csv
- ROUND_5/autoresearch/10_backtesting/results/v3_pebbles_L_cap6.csv
- ROUND_5/autoresearch/10_backtesting/results/5_4_worse.csv
- ROUND_5/autoresearch/logs/progress.md
- ROUND_5/autoresearch/10_backtesting/results/mr_v6_validate.csv
- ROUND_5/autoresearch/10_backtesting/results/mr_beta0_3.csv
- ROUND_5/autoresearch/mr_study/02_threshold_search/per_product/GALAXY_SOUNDS_BLACK_HOLES/top20.csv
- ROUND_5/autoresearch/10_backtesting/results/mr_v3_validate.csv
- ROUND_5/autoresearch/10_backtesting/results/mr_v1_validate.csv
- ROUND_5/autoresearch/14_lag_research/M_strategy_v3/strategy_v3_top100.py
- ROUND_5/autoresearch/mr_study/07_findings/headline.md
- ROUND_5/autoresearch/14_lag_research/M_strategy_v3/strategy_v3_top25.py
- ROUND_5/autoresearch/10_backtesting/results/wf_full_worse.csv
- ROUND_5/autoresearch/13_round2_research/K_strategy_v2/ablation_strategies/try_v3c.py
- ROUND_5/autoresearch/01_eda/per_product/GALAXY_SOUNDS_BLACK_HOLES/summary.png
- ROUND_5/autoresearch/04_statistical_patterns/intraday/GALAXY_SOUNDS_BLACK_HOLES.csv
- ROUND_5/autoresearch/07_hidden_patterns/per_product/GALAXY_SOUNDS_BLACK_HOLES.json
- ROUND_5/autoresearch/10_backtesting/results/dayrem_test34.csv
- ROUND_5/autoresearch/10_backtesting/results/strategy_v3_5-2.csv
- ROUND_5/autoresearch/13_round2_research/K_strategy_v2/ablation_strategies/v3_pebbles_L_cap4.py
- ROUND_5/autoresearch/10_backtesting/results/v3_test34.csv

## Recommendation (final algo)
- **Primary mechanism:** `inside_spread_mm`
- **Secondary signals:** inv_skew(-pos*0.2), coint_pairs(n=2)
- **Rationale:** Strong v3 contributor (+15,158) — keep current setup; Day-of-day KS break flagged — conservative inventory skew

## 2 ranked alternatives
2. Inside-spread MM only (drop overlays) — baseline before v3 layering
