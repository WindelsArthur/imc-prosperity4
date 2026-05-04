# MICROCHIP_TRIANGLE

**Group:** `microchip` | **v3 3-day PnL:** +8,286 | **mr_v6 3-day PnL:** +9,033 | **Position cap (v3):** 10

## Microstructure

## Mean-reversion (mr_study v6)
- mr_v6 mode: default MM (inside-spread bb+1/ba-1 with inv_skew=−pos·0.2)

## Stability flag
- ⚠️ Days 2/3/4 distributions diverge (KS p < 1e-9) — directional drift between days. Strategy uses inv_skew=−pos·0.2 to absorb.

## Reconciled findings (citations)
- ROUND_5/autoresearch/logs/progress.md
- ROUND_5/autoresearch/14_lag_research/F_flow_lag/decision.md
- ROUND_5/autoresearch/13_round2_research/G_intraday/decision.md
- ROUND_5/autoresearch/mr_study/01_fair_value_zoo/per_product/MICROCHIP_TRIANGLE/diagnostics.csv
- ROUND_5/autoresearch/11_findings/exploitable_patterns.md
- ROUND_5/autoresearch/mr_study/02_threshold_search/per_product/MICROCHIP_TRIANGLE/top20.csv
- ROUND_5/autoresearch/04_statistical_patterns/intraday/MICROCHIP_TRIANGLE.csv
- ROUND_5/autoresearch/05_cross_product/groups/microchip/basket_residual.csv
- ROUND_5/autoresearch/07_hidden_patterns/findings.md
- ROUND_5/autoresearch/07_hidden_patterns/per_product/MICROCHIP_TRIANGLE.json
- ROUND_5/autoresearch/05_cross_product/groups/microchip/ret_corr.csv
- ROUND_5/autoresearch/08_signals/run.py
- ROUND_5/autoresearch/01_eda/per_product/MICROCHIP_TRIANGLE/summary.png
- ROUND_5/autoresearch/mr_study/07_findings/per_product/MICROCHIP_TRIANGLE.md
- ROUND_5/autoresearch/mr_study/01_fair_value_zoo/per_product/MICROCHIP_TRIANGLE/ranking.csv
- ROUND_5/autoresearch/03_trade_flow/bot_candidates.md
- ROUND_5/autoresearch/14_lag_research/A_atlas/decision.md
- ROUND_5/autoresearch/05_cross_product/groups/microchip/price_corr.csv

## Recommendation (final algo)
- **Primary mechanism:** `inside_spread_mm`
- **Secondary signals:** inv_skew(-pos*0.2)
- **Rationale:** Strong v3 contributor (+8,286) — keep current setup; Day-of-day KS break flagged — conservative inventory skew

## 2 ranked alternatives
2. Inside-spread MM only (drop overlays) — baseline before v3 layering
