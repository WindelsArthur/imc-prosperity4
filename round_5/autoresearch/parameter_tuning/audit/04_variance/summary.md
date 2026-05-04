# Phase D — variance decomposition

- baseline per-day total std (3 days): **4,672** (sharpe=63.08)
- tuned    per-day total std (3 days): **29,999** (sharpe=13.03)
- Δ per-day std: **+25,326**
- Top-10 products account for **90.9%** of total per-product variance increase
- products with higher xday std (more volatile in tuned): 17
- products with lower xday std: 16

## Top 10 cross-day variance contributors (tuned - baseline)
| product                     |   baseline_d2 |   baseline_d3 |   baseline_d4 |   tuned_d2 |   tuned_d3 |   tuned_d4 |   baseline_xday_std |   tuned_xday_std |   delta_xday_std |
|:----------------------------|--------------:|--------------:|--------------:|-----------:|-----------:|-----------:|--------------------:|-----------------:|-----------------:|
| OXYGEN_SHAKE_CHOCOLATE      |          8866 |          9843 |          4864 |       9410 |       3942 |     -13891 |            2154.09  |          9949.05 |          7794.95 |
| PEBBLES_XL                  |         40420 |         27646 |         36663 |      35099 |      19441 |      51052 |            5360.31  |         12905.3  |          7545.01 |
| UV_VISOR_AMBER              |         14319 |           752 |          8957 |      20425 |      -4156 |       3697 |            5579.09  |         10250.9  |          4671.77 |
| PANEL_1X4                   |         14003 |          4866 |         -2550 |      21185 |       9779 |      -4962 |            6769.9   |         10703.4  |          3933.47 |
| OXYGEN_SHAKE_GARLIC         |         22970 |         17994 |         19641 |      24630 |      13645 |      19383 |            2069.77  |          4486.1  |          2416.33 |
| OXYGEN_SHAKE_MORNING_BREATH |          7756 |           238 |          9305 |      13303 |       -899 |      11090 |            3959.94  |          6239.04 |          2279.1  |
| PANEL_1X2                   |          -434 |          -632 |           -23 |       1194 |        494 |      -4363 |             253.641 |          2471.18 |          2217.54 |
| SLEEP_POD_LAMB_WOOL         |           -16 |          3114 |          2205 |       9193 |      14118 |       7460 |            1314.7   |          2820.32 |          1505.62 |
| GALAXY_SOUNDS_SOLAR_WINDS   |          -387 |         20165 |         30243 |       1180 |      24157 |      35244 |           12746     |         14186.1  |          1440.13 |
| ROBOT_IRONING               |         20096 |         14628 |          3500 |      23102 |      14746 |       3298 |            6905.38  |          8117.73 |          1212.35 |

## Bottom 10 (variance REDUCERS)
| product                   |   baseline_xday_std |   tuned_xday_std |   delta_xday_std |
|:--------------------------|--------------------:|-----------------:|-----------------:|
| PEBBLES_XS                |             9280.45 |          3354.63 |        -5925.81  |
| MICROCHIP_SQUARE          |            14127.8  |         10091.1  |        -4036.76  |
| PEBBLES_M                 |             5967.59 |          2590.66 |        -3376.93  |
| GALAXY_SOUNDS_BLACK_HOLES |            13188.9  |         10661.6  |        -2527.34  |
| GALAXY_SOUNDS_DARK_MATTER |             3486.03 |          1079.56 |        -2406.47  |
| SNACKPACK_PISTACHIO       |             4264.22 |          2045.77 |        -2218.45  |
| SNACKPACK_VANILLA         |             3467.96 |          1887.85 |        -1580.11  |
| TRANSLATOR_VOID_BLUE      |             2571.94 |          1254.94 |        -1317     |
| PANEL_2X4                 |             4615.54 |          3653.46 |         -962.074 |
| SLEEP_POD_POLYESTER       |             6872.62 |          6409.75 |         -462.874 |