# UV_VISOR_MAGENTA

**Group:** `uv_visor` | **v3 3-day PnL:** -2,880 | **mr_v6 3-day PnL:** +0 | **Position cap (v3):** 4

## Microstructure

## Cointegration overlays where this product is a leg
- [WITHIN] `UV_VISOR_AMBER ~ UV_VISOR_MAGENTA` slope=-1.2380 intercept=+21897.00 sd=371.0

## Mean-reversion (mr_study v6)
- mr_v6 mode: **IDLE** — chronic MM loser; mr_study chose to skip

## Reconciled findings (citations)
- ROUND_5/autoresearch/07_hidden_patterns/per_product/UV_VISOR_MAGENTA.json
- ROUND_5/autoresearch/mr_study/01_fair_value_zoo/per_product/UV_VISOR_MAGENTA/diagnostics.csv
- ROUND_5/autoresearch/07_hidden_patterns/per_product/GALAXY_SOUNDS_BLACK_HOLES.json
- ROUND_5/autoresearch/05_cross_product/groups/uv_visor/price_corr.csv
- ROUND_5/autoresearch/mr_study/02_threshold_search/per_product/UV_VISOR_MAGENTA/top20.csv
- ROUND_5/autoresearch/07_hidden_patterns/per_product/PEBBLES_XL.json
- ROUND_5/autoresearch/04_statistical_patterns/intraday/UV_VISOR_MAGENTA.csv
- ROUND_5/autoresearch/07_hidden_patterns/per_product/UV_VISOR_YELLOW.json
- ROUND_5/autoresearch/07_hidden_patterns/per_product/PANEL_2X4.json
- ROUND_5/autoresearch/05_cross_product/groups/uv_visor/ret_corr.csv
- ROUND_5/autoresearch/mr_study/07_findings/per_product/UV_VISOR_MAGENTA.md
- ROUND_5/autoresearch/13_round2_research/B_bleeders/forensics.csv
- ROUND_5/autoresearch/05_cross_product/groups/uv_visor/basket_residual.csv
- ROUND_5/autoresearch/mr_study/01_fair_value_zoo/per_product/UV_VISOR_MAGENTA/ranking.csv
- ROUND_5/autoresearch/01_eda/per_product/UV_VISOR_MAGENTA/summary.png

## Recommendation (final algo)
- **Primary mechanism:** `inside_spread_mm`
- **Secondary signals:** inv_skew(-pos*0.2), coint_pairs(n=1), prod_cap=4
- **Rationale:** v3 PnL -2,880 — moderate; baseline kept

## 2 ranked alternatives
1. IDLE — mr_v6 chose this (PnL=0); v3 yields -2,880
2. Inside-spread MM only (drop overlays) — baseline before v3 layering
