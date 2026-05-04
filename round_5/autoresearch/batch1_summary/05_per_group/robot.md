# Group robot

5 products: ROBOT_DISHES, ROBOT_IRONING, ROBOT_LAUNDRY, ROBOT_MOPPING, ROBOT_VACUUMING
3-day v3 PnL total: **+3,573** | mr_v6 total: +25,195

## Per-product 3-day PnL (v3 vs mr_v6)
| Product | v3 | mr_v6 |
|---|---:|---:|
| ROBOT_LAUNDRY | +4,074 | +2,151 |
| ROBOT_IRONING | +1,064 | +0 |
| ROBOT_MOPPING | +994 | +10,225 |
| ROBOT_VACUUMING | +423 | +1,600 |
| ROBOT_DISHES | -2,982 | +11,219 |

## Group findings
- IRONING (631 distinct mids, lattice ratio 0.021) and DISHES (3048 distinct, AR(1)=−0.232) have strongest mean-reversion signals.
- DISHES had AR-BIC p=9 in EDA but day-of-day distributions diverge wildly (KS p≈0). Strategy treats it as plain MM.
- LAUNDRY/VACUUMING ADF p=0.378 in re-verify (claimed 0.026) — not stationary on full stitch but OOS Sharpe was 1.19/1.70 in folds.
- MOPPING is a v1 bleeder; PROD_CAP=4 brought v3 to +994 (vs −17K in v1).
- mr_v6 found DISHES, MOPPING as TAKER candidates with rolling_quadratic w=500 — but mr_v6 total dominated by v3.

## Citations
- ROUND_5/autoresearch/04_statistical_patterns/intraday/ROBOT_DISHES.csv
- ROUND_5/autoresearch/mr_study/01_fair_value_zoo/per_product/ROBOT_DISHES/ranking.csv
- ROUND_5/autoresearch/11_findings/per_group_findings.md
- ROUND_5/autoresearch/mr_study/07_findings/group_summary.md
