# Group snackpack

5 products: SNACKPACK_CHOCOLATE, SNACKPACK_PISTACHIO, SNACKPACK_RASPBERRY, SNACKPACK_STRAWBERRY, SNACKPACK_VANILLA
3-day v3 PnL total: **+10,217** | mr_v6 total: +16,425

## Per-product 3-day PnL (v3 vs mr_v6)
| Product | v3 | mr_v6 |
|---|---:|---:|
| SNACKPACK_STRAWBERRY | +13,860 | +2,614 |
| SNACKPACK_PISTACHIO | +8,711 | +1,692 |
| SNACKPACK_VANILLA | +2,573 | +1,772 |
| SNACKPACK_CHOCOLATE | -4,689 | +5,017 |
| SNACKPACK_RASPBERRY | -10,238 | +5,330 |

## Group findings
- Looser sum invariant Σmid ≈ 50,221 ± 190 (10× weaker than pebbles).
- Best within-group pair RASPBERRY/VANILLA ADF p=0.001 (re-verified); CHOCOLATE/STRAWBERRY ADF p=0.035 (re-verified).
- Off-diagonal returns correlation −0.16 (group is internally anti-correlated).
- PROD_CAP applied: CHOCOLATE=5, RASPBERRY=5 (heavy bleeders in v1).
- v3 group sum: STRAWBERRY +13.9K dominates; CHOCOLATE −4.7K, RASPBERRY −10.2K still drag despite caps.

## Citations
- ROUND_5/autoresearch/05_cross_product/groups/snackpack/basket_residual.csv
- ROUND_5/autoresearch/14_lag_research/C_lagged_coint/lagged_coint_fast.csv
- ROUND_5/autoresearch/11_findings/per_group_findings.md
- ROUND_5/autoresearch/mr_study/07_findings/group_summary.md
