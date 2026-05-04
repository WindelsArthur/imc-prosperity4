# Phase C — pair stability

- pairs analysed: 166 (of which 127 are added pairs at index ≥39)
- β shifts >30% (loose flag): **82** (61 added)
- ADF holdout (d3 OR d4) p>0.05: 166 — _bar too loose for intraday data_
- HIGHLY UNSTABLE (β>50% OR ADF>0.20 on both d3+d4): **36** (25 added)

**Note:** ADF >0.05 fires on every pair, indicating the residuals are broadly non-stationary on a daily basis even when fit globally. This suggests the strategy depends on **short-window mean-reversion** rather than true cointegration — interesting in itself. The discriminating criterion for overfit is **β-shift >30%**, with **β>50%** as the strict cut.

## Top 20 most-unstable added pairs (β shift)
|   pair_idx | a                   | b                      |   slope_full |    beta_day2 |   beta_shift_pct |   adf_p_d3_held_out |   adf_p_d4_held_out |
|-----------:|:--------------------|:-----------------------|-------------:|-------------:|-----------------:|--------------------:|--------------------:|
|        165 | SNACKPACK_PISTACHIO | TRANSLATOR_ASTRO_BLACK |    0.240865  | -0.000205101 |         1.00085  |           0.400917  |           0.482078  |
|        133 | ROBOT_MOPPING       | PANEL_1X4              |   -0.804144  | -0.0868072   |         0.89205  |           0.86148   |           0.13816   |
|        164 | SNACKPACK_PISTACHIO | MICROCHIP_OVAL         |    0.090627  |  0.15093     |         0.665398 |           0.0524267 |           0.163436  |
|        163 | SNACKPACK_PISTACHIO | MICROCHIP_OVAL         |    0.090696  |  0.15093     |         0.664131 |           0.0524267 |           0.163436  |
|        162 | SNACKPACK_PISTACHIO | MICROCHIP_OVAL         |    0.0907152 |  0.15093     |         0.663779 |           0.0524267 |           0.163436  |
|        120 | SNACKPACK_CHOCOLATE | PANEL_2X4              |   -0.219316  | -0.0931503   |         0.575269 |           0.245621  |           0.224511  |
|        122 | SNACKPACK_CHOCOLATE | PANEL_2X4              |   -0.217503  | -0.0931503   |         0.571729 |           0.245621  |           0.224511  |
|        124 | SNACKPACK_CHOCOLATE | PANEL_2X4              |   -0.217213  | -0.0931503   |         0.571157 |           0.245621  |           0.224511  |
|        119 | SNACKPACK_CHOCOLATE | PANEL_2X4              |   -0.217149  | -0.0931503   |         0.57103  |           0.245621  |           0.224511  |
|        109 | PANEL_2X4           | PEBBLES_XS             |   -0.368433  | -0.571635    |         0.551528 |           0.124121  |           0.124898  |
|         86 | PANEL_2X4           | PEBBLES_XS             |   -0.371752  | -0.571635    |         0.537679 |           0.124121  |           0.124898  |
|         87 | PANEL_2X4           | PEBBLES_XS             |   -0.371921  | -0.571635    |         0.536981 |           0.124121  |           0.124898  |
|        123 | SLEEP_POD_SUEDE     | MICROCHIP_SQUARE       |    0.451624  |  0.227213    |         0.496897 |           0.0654309 |           0.050389  |
|        121 | SLEEP_POD_SUEDE     | MICROCHIP_SQUARE       |    0.451614  |  0.227213    |         0.496886 |           0.0654309 |           0.050389  |
|        126 | SLEEP_POD_SUEDE     | MICROCHIP_SQUARE       |    0.451556  |  0.227213    |         0.496822 |           0.0654309 |           0.050389  |
|        118 | SLEEP_POD_SUEDE     | MICROCHIP_SQUARE       |    0.45111   |  0.227213    |         0.496324 |           0.0654309 |           0.050389  |
|         89 | PEBBLES_M           | ROBOT_IRONING          |   -0.728948  | -0.368586    |         0.494359 |           0.455315  |           0.0812181 |
|         97 | PEBBLES_M           | ROBOT_IRONING          |   -0.728455  | -0.368586    |         0.494017 |           0.455315  |           0.0812181 |
|         95 | PEBBLES_M           | ROBOT_IRONING          |   -0.728439  | -0.368586    |         0.494006 |           0.455315  |           0.0812181 |
|         94 | PEBBLES_M           | ROBOT_IRONING          |   -0.728435  | -0.368586    |         0.494003 |           0.455315  |           0.0812181 |

## Top 20 worst ADF holdout (max of d3,d4)
|   pair_idx | a                         | b                             | is_added_pair   |   max_adf |   adf_p_d3_held_out |   adf_p_d4_held_out |   beta_shift_pct |
|-----------:|:--------------------------|:------------------------------|:----------------|----------:|--------------------:|--------------------:|-----------------:|
|         73 | ROBOT_IRONING             | SNACKPACK_PISTACHIO           | True            |  0.916844 |            0.916844 |            0.137057 |        0.463267  |
|         50 | ROBOT_IRONING             | SNACKPACK_PISTACHIO           | True            |  0.916844 |            0.916844 |            0.137057 |        0.463042  |
|         52 | ROBOT_IRONING             | SNACKPACK_PISTACHIO           | True            |  0.916844 |            0.916844 |            0.137057 |        0.462998  |
|        133 | ROBOT_MOPPING             | PANEL_1X4                     | True            |  0.86148  |            0.86148  |            0.13816  |        0.89205   |
|         56 | ROBOT_IRONING             | PEBBLES_M                     | True            |  0.830463 |            0.830463 |            0.13149  |        0.369748  |
|         49 | ROBOT_IRONING             | PEBBLES_M                     | True            |  0.830463 |            0.830463 |            0.13149  |        0.369746  |
|         75 | ROBOT_IRONING             | PEBBLES_M                     | True            |  0.830463 |            0.830463 |            0.13149  |        0.369735  |
|         41 | ROBOT_IRONING             | PEBBLES_M                     | True            |  0.830463 |            0.830463 |            0.13149  |        0.369699  |
|          3 | GALAXY_SOUNDS_DARK_MATTER | GALAXY_SOUNDS_PLANETARY_RINGS | False           |  0.62153  |            0.62153  |            0.152816 |        1.03871   |
|        105 | MICROCHIP_CIRCLE          | OXYGEN_SHAKE_CHOCOLATE        | True            |  0.607953 |            0.533191 |            0.607953 |        0.460499  |
|         91 | MICROCHIP_CIRCLE          | OXYGEN_SHAKE_CHOCOLATE        | True            |  0.607953 |            0.533191 |            0.607953 |        0.455072  |
|        112 | MICROCHIP_CIRCLE          | OXYGEN_SHAKE_CHOCOLATE        | True            |  0.607953 |            0.533191 |            0.607953 |        0.453969  |
|        113 | MICROCHIP_CIRCLE          | OXYGEN_SHAKE_CHOCOLATE        | True            |  0.607953 |            0.533191 |            0.607953 |        0.453681  |
|         57 | GALAXY_SOUNDS_BLACK_HOLES | PEBBLES_S                     | True            |  0.57837  |            0.162304 |            0.57837  |        0.048286  |
|         63 | GALAXY_SOUNDS_BLACK_HOLES | PEBBLES_S                     | True            |  0.57837  |            0.162304 |            0.57837  |        0.0461074 |
|         44 | GALAXY_SOUNDS_BLACK_HOLES | PEBBLES_S                     | True            |  0.57837  |            0.162304 |            0.57837  |        0.0454173 |
|         45 | GALAXY_SOUNDS_BLACK_HOLES | PEBBLES_S                     | True            |  0.57837  |            0.162304 |            0.57837  |        0.0452382 |
|          2 | SLEEP_POD_COTTON          | SLEEP_POD_POLYESTER           | False           |  0.563986 |            0.427487 |            0.563986 |        0.144133  |
|         65 | SLEEP_POD_POLYESTER       | SNACKPACK_STRAWBERRY          | True            |  0.552413 |            0.552413 |            0.103513 |        0.314476  |
|         67 | SLEEP_POD_POLYESTER       | SNACKPACK_STRAWBERRY          | True            |  0.552413 |            0.552413 |            0.103513 |        0.314184  |