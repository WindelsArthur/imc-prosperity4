# Group oxygen_shake

5 products: OXYGEN_SHAKE_CHOCOLATE, OXYGEN_SHAKE_EVENING_BREATH, OXYGEN_SHAKE_GARLIC, OXYGEN_SHAKE_MINT, OXYGEN_SHAKE_MORNING_BREATH
3-day v3 PnL total: **+35,537** | mr_v6 total: +33,942

## Per-product 3-day PnL (v3 vs mr_v6)
| Product | v3 | mr_v6 |
|---|---:|---:|
| OXYGEN_SHAKE_EVENING_BREATH | +11,905 | +7,669 |
| OXYGEN_SHAKE_MORNING_BREATH | +8,240 | +7,544 |
| OXYGEN_SHAKE_GARLIC | +8,073 | +7,743 |
| OXYGEN_SHAKE_CHOCOLATE | +4,867 | +8,864 |
| OXYGEN_SHAKE_MINT | +2,452 | +2,122 |

## Group findings
- EVENING_BREATH = lattice product (453 distinct mids, ratio 0.015, AR(1)=−0.123). +11.9K in v3 from MM with inv_skew.
- CHOCOLATE has AR(1)=−0.089 and sees a huge KS break across days. CHOCOLATE/GARLIC pair has ADF p=**0.918** in re-verify (claimed 0.030) — pair is non-stationary; **drop in final algo**.
- GARLIC participates in 3 cross-group pairs (PEBBLES_S/GARLIC, PANEL_2X4/GARLIC, GARLIC/PEBBLES_S).
- Group total in v3 = +35.5K (5/5 products positive).

## Citations
- ROUND_5/autoresearch/05_cross_product/groups/oxygen_shake/all_pair_cointegration.csv
- ROUND_5/autoresearch/11_findings/per_group_findings.md
- ROUND_5/autoresearch/mr_study/07_findings/group_summary.md
