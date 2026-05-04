# PEBBLES_S

**Group:** `pebbles` | **v3 3-day PnL:** +5,394 | **mr_v6 3-day PnL:** +22,195 | **Position cap (v3):** 10

## Microstructure
- **PEBBLES basket member:** Σ_pebbles = 50,000 ± 2.8 (re-verified, std=2.80, half-life 0.16 ticks)

## Cointegration overlays where this product is a leg
- [CROSS] `OXYGEN_SHAKE_GARLIC ~ PEBBLES_S` slope=-1.0114 intercept=+20960.00 sd=200.0
- [CROSS] `GALAXY_SOUNDS_BLACK_HOLES ~ PEBBLES_S` slope=-1.0180 intercept=+20559.94 sd=200.0
- [CROSS] `PEBBLES_S ~ GALAXY_SOUNDS_BLACK_HOLES` slope=-0.7694 intercept=+17755.06 sd=200.0
- [CROSS] `PEBBLES_S ~ OXYGEN_SHAKE_GARLIC` slope=-0.7727 intercept=+18147.25 sd=200.0
- [CROSS] `PEBBLES_S ~ PANEL_2X4` slope=-1.1018 intercept=+21344.63 sd=200.0
- [CROSS] `PANEL_2X4 ~ PEBBLES_S` slope=-0.6242 intercept=+16840.75 sd=200.0

## Mean-reversion (mr_study v6)
- mr_v6 mode: default MM (inside-spread bb+1/ba-1 with inv_skew=−pos·0.2)

## Reconciled findings (citations)
- ROUND_5/autoresearch/mr_study/07_findings/per_product/PEBBLES_S.md
- ROUND_5/autoresearch/data_views/prices_r5_d2.parquet
- ROUND_5/autoresearch/mr_study/07_findings/group_summary.md
- ROUND_5/autoresearch/04_statistical_patterns/intraday/PEBBLES_S.csv
- ROUND_5/autoresearch/05_cross_product/groups/pebbles/ret_corr.csv
- ROUND_5/autoresearch/05_cross_product/groups/pebbles/basket_residual.csv
- ROUND_5/autoresearch/01_eda/per_product/PEBBLES_S/summary.png
- ROUND_5/autoresearch/mr_study/02_threshold_search/per_product/PEBBLES_S/top20.csv
- ROUND_5/autoresearch/07_hidden_patterns/per_product/PEBBLES_S.json
- ROUND_5/autoresearch/05_cross_product/groups/pebbles/price_corr.csv
- ROUND_5/autoresearch/mr_study/01_fair_value_zoo/per_product/PEBBLES_S/diagnostics.csv
- ROUND_5/autoresearch/mr_study/01_fair_value_zoo/per_product/PEBBLES_S/ranking.csv

## Recommendation (final algo)
- **Primary mechanism:** `basket_invariant_PEBBLES`
- **Secondary signals:** pebble_skew, inside_spread_mm, inv_skew, coint_pairs(n=6)
- **Rationale:** v3 PnL +5,394 — moderate; baseline kept

## 2 ranked alternatives
2. Inside-spread MM only (drop overlays) — baseline before v3 layering
