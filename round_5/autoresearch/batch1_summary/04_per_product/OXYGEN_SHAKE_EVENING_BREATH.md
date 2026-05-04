# OXYGEN_SHAKE_EVENING_BREATH

**Group:** `oxygen_shake` | **v3 3-day PnL:** +11,905 | **mr_v6 3-day PnL:** +7,669 | **Position cap (v3):** 10

## Microstructure
- **AR(1) on Δmid:** -0.1227 (re-verified on stitched 2+3+4 mids)
- **Lattice ratio:** 0.0151 (n_distinct_mids = 453 of 30,000 ticks)

## Mean-reversion (mr_study v6)
- mr_v6 mode: **MM with signal skew** (AR(1) on Δmid)

## Stability flag
- ⚠️ Days 2/3/4 distributions diverge (KS p < 1e-9) — directional drift between days. Strategy uses inv_skew=−pos·0.2 to absorb.

## Reconciled findings (citations)
- ROUND_5/autoresearch/logs/progress.md
- ROUND_5/autoresearch/14_lag_research/E_ar_extended/sign_switching.csv
- ROUND_5/autoresearch/mr_study/07_findings/headline.md
- ROUND_5/autoresearch/10_backtesting/sweep_mr_d_3prods.py
- ROUND_5/autoresearch/05_cross_product/groups/oxygen_shake/ret_corr.csv
- ROUND_5/autoresearch/mr_study/02_threshold_search/per_product/OXYGEN_SHAKE_EVENING_BREATH/top20.csv
- ROUND_5/autoresearch/13_round2_research/D_micro/decision.md
- ROUND_5/autoresearch/mr_study/00_setup/data_sanity.md
- ROUND_5/autoresearch/11_findings/findings.md
- ROUND_5/autoresearch/mr_study/01_fair_value_zoo/per_product/OXYGEN_SHAKE_EVENING_BREATH/ranking.csv
- ROUND_5/autoresearch/04_statistical_patterns/intraday/OXYGEN_SHAKE_EVENING_BREATH.csv
- ROUND_5/autoresearch/11_findings/exploitable_patterns.md
- ROUND_5/autoresearch/mr_study/06_strategy_mr/distilled_params.py
- ROUND_5/autoresearch/12_final_strategy/pnl_estimates.md
- ROUND_5/autoresearch/01_eda/per_product/OXYGEN_SHAKE_EVENING_BREATH/summary.png
- ROUND_5/autoresearch/mr_study/07_findings/per_product/OXYGEN_SHAKE_EVENING_BREATH.md
- ROUND_5/autoresearch/07_hidden_patterns/findings.md
- ROUND_5/autoresearch/05_cross_product/groups/oxygen_shake/basket_residual.csv
- ROUND_5/autoresearch/07_hidden_patterns/per_product/OXYGEN_SHAKE_EVENING_BREATH.json
- ROUND_5/autoresearch/mr_study/01_fair_value_zoo/per_product/OXYGEN_SHAKE_EVENING_BREATH/diagnostics.csv
- ROUND_5/autoresearch/05_cross_product/groups/oxygen_shake/price_corr.csv
- ROUND_5/autoresearch/08_signals/run.py
- ROUND_5/autoresearch/03_trade_flow/bot_candidates.md
- ROUND_5/autoresearch/14_lag_research/E_ar_extended/decision.md

## Recommendation (final algo)
- **Primary mechanism:** `inside_spread_mm`
- **Secondary signals:** inv_skew(-pos*0.2)
- **Rationale:** Strong v3 contributor (+11,905) — keep current setup; Day-of-day KS break flagged — conservative inventory skew

## 2 ranked alternatives
2. Inside-spread MM only (drop overlays) — baseline before v3 layering
