# Group pebbles

5 products: PEBBLES_L, PEBBLES_M, PEBBLES_S, PEBBLES_XL, PEBBLES_XS
3-day v3 PnL total: **+16,970** | mr_v6 total: +66,613

## Per-product 3-day PnL (v3 vs mr_v6)
| Product | v3 | mr_v6 |
|---|---:|---:|
| PEBBLES_XS | +12,928 | +15,016 |
| PEBBLES_XL | +9,942 | +10,865 |
| PEBBLES_S | +5,394 | +22,195 |
| PEBBLES_M | +943 | +9,103 |
| PEBBLES_L | -12,237 | +9,434 |

## Group findings
- Strongest structural alpha in the universe.
- **Sum invariant Σmid = 50,000 ± 2.8** (R²=0.999998 of any-pebble on other-four), OU half-life **0.16 ticks**.
- Strategy: passive inside-spread MM with skew_i = −resid/5 applied uniformly. PEBBLES_XL is the largest single contributor (+50,715 in v1; +9,942 in v3 after cap and pair overlays).
- PEBBLES_L is the chronic loser (-12,237 in v3). v2 ablation tested cap=5 and got +92 PnL but Sharpe 8.6→7.2. Phase H will retest.
- 5/5 products are also legs in cross-group cointegration pairs (PEBBLES_XL/PANEL_2X4 is the single largest cross-group contributor).

## Citations
- ROUND_5/autoresearch/05_cross_product/groups/pebbles/basket_residual.csv
- ROUND_5/autoresearch/11_findings/per_group_findings.md
- ROUND_5/autoresearch/11_findings/per_group_findings.md
- ROUND_5/autoresearch/mr_study/07_findings/group_summary.md
