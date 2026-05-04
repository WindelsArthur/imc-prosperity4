# Group microchip

5 products: MICROCHIP_CIRCLE, MICROCHIP_OVAL, MICROCHIP_RECTANGLE, MICROCHIP_SQUARE, MICROCHIP_TRIANGLE
3-day v3 PnL total: **+27,667** | mr_v6 total: +32,822

## Per-product 3-day PnL (v3 vs mr_v6)
| Product | v3 | mr_v6 |
|---|---:|---:|
| MICROCHIP_CIRCLE | +11,367 | +10,358 |
| MICROCHIP_TRIANGLE | +8,286 | +9,033 |
| MICROCHIP_SQUARE | +6,182 | +7,985 |
| MICROCHIP_OVAL | +1,048 | +5,446 |
| MICROCHIP_RECTANGLE | +784 | +0 |

## Group findings
- Tight ~5-tick spread on 4/5 products (CIRCLE, OVAL, RECTANGLE, TRIANGLE); SQUARE wider (~12).
- Best EG pair RECTANGLE/SQUARE slope=−0.40, ADF p=0.004 (re-verified at 0.0036), OOS Sharpe 1.0–2.1.
- OVAL has sine R²=0.974 (period = full series, deemed artefact in v2).
- CIRCLE is the v3 group winner (+11,367); RECTANGLE only +784 — the cap effect from −0.40 slope pair.

## Citations
- ROUND_5/autoresearch/05_cross_product/groups/microchip/all_pair_cointegration.csv
- ROUND_5/autoresearch/13_round2_research/A_sine/oos_mse.csv
- ROUND_5/autoresearch/11_findings/per_group_findings.md
- ROUND_5/autoresearch/mr_study/07_findings/group_summary.md
