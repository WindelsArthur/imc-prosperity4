# Phase A — per-product attribution

- baseline 3-day total: **1,083,016**, fold_min=354,448, fold_median=363,578, sharpe=63.08
- tuned 3-day total: **1,436,024**, fold_min=450,479, fold_median=465,320, sharpe=13.03
- delta total = **+353,008** (fold_min +96,031, fold_median +101,742)

## Top 5 winners (Δ3day desc)

| product             |   baseline_3day |   tuned_3day |   delta_3day |   baseline_fold_min |   tuned_fold_min |   fold_min_delta |   added_n_pairs |
|:--------------------|----------------:|-------------:|-------------:|--------------------:|-----------------:|-----------------:|----------------:|
| PEBBLES_XS          |            8527 |        68331 |        59804 |               -7425 |            20168 |            27593 |              11 |
| SNACKPACK_CHOCOLATE |           -8223 |        31346 |        39569 |               -4591 |             9150 |            13741 |               3 |
| SNACKPACK_RASPBERRY |          -15948 |        20673 |        36621 |              -10282 |             1868 |            12150 |               0 |
| MICROCHIP_CIRCLE    |           10381 |        40045 |        29664 |               -1208 |             9165 |            10373 |               8 |
| SNACKPACK_VANILLA   |            3873 |        29969 |        26096 |               -3475 |             8069 |            11544 |               6 |

## Top 5 losers (Δ3day asc)

| product                |   baseline_3day |   tuned_3day |   delta_3day |   baseline_fold_min |   tuned_fold_min |   fold_min_delta |   added_n_pairs |
|:-----------------------|----------------:|-------------:|-------------:|--------------------:|-----------------:|-----------------:|----------------:|
| OXYGEN_SHAKE_CHOCOLATE |           23573 |         -539 |       -24112 |                4864 |           -13891 |           -18755 |               5 |
| UV_VISOR_AMBER         |           24028 |        19966 |        -4062 |                 752 |            -4156 |            -4908 |              17 |
| MICROCHIP_OVAL         |           11011 |         7227 |        -3784 |                 970 |               81 |             -889 |               2 |
| OXYGEN_SHAKE_GARLIC    |           60605 |        57658 |        -2947 |               17994 |            13645 |            -4349 |              12 |
| SLEEP_POD_POLYESTER    |           39798 |        37550 |        -2248 |                5429 |             5172 |             -257 |              13 |

## Fragility (median up, fold_min down)

| product                |   delta_median |   fold_min_delta |   added_n_pairs |
|:-----------------------|---------------:|-----------------:|----------------:|
| PANEL_1X2              |           1126 |            -3731 |               7 |
| PANEL_1X4              |           4913 |            -2412 |               4 |
| UV_VISOR_YELLOW        |           1016 |            -1654 |               4 |
| ROBOT_IRONING          |            118 |             -202 |              13 |
| TRANSLATOR_ASTRO_BLACK |           2348 |             -146 |               1 |