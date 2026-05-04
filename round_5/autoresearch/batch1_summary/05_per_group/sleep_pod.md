# Group sleep_pod

5 products: SLEEP_POD_COTTON, SLEEP_POD_LAMB_WOOL, SLEEP_POD_NYLON, SLEEP_POD_POLYESTER, SLEEP_POD_SUEDE
3-day v3 PnL total: **+18,764** | mr_v6 total: +17,905

## Per-product 3-day PnL (v3 vs mr_v6)
| Product | v3 | mr_v6 |
|---|---:|---:|
| SLEEP_POD_COTTON | +9,177 | +8,790 |
| SLEEP_POD_NYLON | +4,830 | +1,066 |
| SLEEP_POD_POLYESTER | +4,040 | +8,049 |
| SLEEP_POD_SUEDE | +3,027 | +0 |
| SLEEP_POD_LAMB_WOOL | -2,310 | +0 |

## Group findings
- Most cointegrated within-group pairs in the universe.
- Best Sharpe pairs: COTTON/POLYESTER (1.3–1.9), POLYESTER/SUEDE (1.1–1.9), LAMB_WOOL/SUEDE (Sharpe 2.2 fold-B).
- Re-verified ADF p: COTTON/POLYESTER 0.146 (above 0.05), POLYESTER/SUEDE 0.091 — borderline. Kept because fold-OOS Sharpe was positive.
- LAMB_WOOL is chronic loser; PROD_CAP=3 brings v3 to −2.3K (vs −24K in v1).
- SUEDE participates in cross-group pair MICROCHIP_SQUARE/SUEDE (slope 1.87).

## Citations
- ROUND_5/autoresearch/05_cross_product/groups/sleep_pod/all_pair_cointegration.csv
- ROUND_5/autoresearch/11_findings/per_group_findings.md
- ROUND_5/autoresearch/mr_study/07_findings/group_summary.md
