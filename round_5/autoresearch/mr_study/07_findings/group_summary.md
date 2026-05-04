# MR Study — group summary

10 groups × 5 products. Final 3-day PnL by group from v6:

| group | TAKER | MM | IDLE | sum_pnl |
| --- | ---:| ---:| ---:| ---:|
| galaxy_sounds  | 0 | 3 | 2 | +29,754 |
| microchip      | 0 | 4 | 1 | +32,822 |
| oxygen_shake   | 1 | 4 | 0 | +33,942 |
| panel          | 0 | 5 | 0 | +17,378 |
| pebbles        | 3 | 2 | 0 | +66,613 |
| robot          | 2 | 2 | 1 | +25,195 |
| sleep_pod      | 1 | 2 | 2 | +17,905 |
| snackpack      | 0 | 5 | 0 | +16,425 |
| translator     | 0 | 4 | 1 | +23,303 |
| uv_visor       | 0 | 4 | 1 | +19,886 |
| **TOTAL**      | 7 | 35 | 8 | **+283,223** |

(Per-product final PnL from `04_combined_search/v6_final_metrics.json`.)

## Observations
- **PEBBLES** is the strongest group — 66.6K, 24% of total PnL — driven by
  PEBBLES_S/XS/XL all in the top-10 contributors. The size-tagged
  pebbles share enough microstructure that inside-spread MM works
  consistently; PEBBLES_M and PEBBLES_XS additionally have a stable
  rolling-quadratic FV that makes them tradeable as TAKERs.
- **Pure-MM groups** (panel, snackpack, translator, uv_visor) earn modestly
  through inventory-skew quoting plus the in-spread clamp. The signal-skew
  on SNACKPACK_CHOCOLATE is small but consistent.
- **IDLE-heavy groups**: galaxy_sounds (2/5) and sleep_pod (2/5). Both have
  wide-spread, high-drift members where inside-spread MM gets steamrolled
  by directional moves.
- **Robot** has the most divergent profile: 2 TAKERs (DISHES, MOPPING)
  earning 21.4K, plus an IDLE on ROBOT_IRONING — the strongest Phase-1 IC
  product ironically dropped from the strategy because passive MR-MM needs
  a better fill model than the in-process simulator can give.
