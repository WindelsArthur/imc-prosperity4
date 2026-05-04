# Group galaxy_sounds

5 products: GALAXY_SOUNDS_BLACK_HOLES, GALAXY_SOUNDS_DARK_MATTER, GALAXY_SOUNDS_PLANETARY_RINGS, GALAXY_SOUNDS_SOLAR_FLAMES, GALAXY_SOUNDS_SOLAR_WINDS
3-day v3 PnL total: **+28,032** | mr_v6 total: +29,754

## Per-product 3-day PnL (v3 vs mr_v6)
| Product | v3 | mr_v6 |
|---|---:|---:|
| GALAXY_SOUNDS_BLACK_HOLES | +15,158 | +14,828 |
| GALAXY_SOUNDS_SOLAR_WINDS | +10,270 | +9,320 |
| GALAXY_SOUNDS_DARK_MATTER | +7,456 | +5,606 |
| GALAXY_SOUNDS_SOLAR_FLAMES | +2,060 | +0 |
| GALAXY_SOUNDS_PLANETARY_RINGS | -6,912 | +0 |

## Group findings
- DARK_MATTER/PLANETARY_RINGS pair slope=0.183, ADF p=0.038 (re-verified). Sharpe 1.6–2.0 in folds.
- BLACK_HOLES/PEBBLES_S is a strong cross-group pair (slope=−1.018) — v3's BLACK_HOLES PnL (+15K) is the group highlight.
- PLANETARY_RINGS bleeds in v3 (−6.9K). mr_v6 chose IDLE for this product.
- SOLAR_FLAMES is also a v1 bleeder, PROD_CAP=4 in v3 → +2K.

## Citations
- ROUND_5/autoresearch/05_cross_product/groups/galaxy_sounds/all_pair_cointegration.csv
- ROUND_5/autoresearch/11_findings/per_group_findings.md
- ROUND_5/autoresearch/mr_study/07_findings/group_summary.md
