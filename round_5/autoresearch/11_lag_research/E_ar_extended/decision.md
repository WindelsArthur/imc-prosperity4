# Phase E — Extended AR / lag-IC peaks

## Top 20 by |IC| beyond lag-1

| product                     | group         |      ic_lag1 |      ic_lag2 |      ic_lag5 |     ic_lag10 |   top_ic_after_lag1 |   top_lag_after_lag1 |   sign_switch_lag |   sign_switch_ic |
|:----------------------------|:--------------|-------------:|-------------:|-------------:|-------------:|--------------------:|---------------------:|------------------:|-----------------:|
| ROBOT_IRONING               | robot         | -0.16424     | -0.0105019   |  0.00890329  |  0.00608909  |           0.0376149 |                   96 |                82 |        0.024341  |
| OXYGEN_SHAKE_EVENING_BREATH | oxygen_shake  | -0.144358    |  0.00275996  | -0.0129894   | -0.00619722  |          -0.0243425 |                   82 |                63 |        0.0211636 |
| OXYGEN_SHAKE_MORNING_BREATH | oxygen_shake  | -0.00662027  | -0.00309181  |  0.00413568  | -0.00211983  |          -0.0220967 |                    6 |                -1 |      nan         |
| MICROCHIP_CIRCLE            | microchip     | -0.00590163  |  0.0134861   |  0.00101912  |  0.00557103  |          -0.0204991 |                   12 |                -1 |      nan         |
| MICROCHIP_SQUARE            | microchip     | -0.0193367   | -0.00942455  |  0.00480487  |  0.00939851  |          -0.0204376 |                   94 |                -1 |      nan         |
| ROBOT_LAUNDRY               | robot         |  0.00435113  |  0.000941754 | -0.00381442  | -0.00513475  |          -0.0203042 |                   37 |                37 |       -0.0203042 |
| OXYGEN_SHAKE_CHOCOLATE      | oxygen_shake  | -0.0458495   |  0.00553577  |  0.00900501  | -5.60947e-05 |          -0.0201999 |                    7 |                -1 |      nan         |
| UV_VISOR_YELLOW             | uv_visor      |  0.00238777  |  0.0012445   |  0.00532614  |  0.00383331  |          -0.0200743 |                   41 |                41 |       -0.0200743 |
| PEBBLES_S                   | pebbles       |  0.00744361  |  0.00224925  |  0.000523753 |  0.0079396   |           0.0196939 |                   55 |                -1 |      nan         |
| UV_VISOR_ORANGE             | uv_visor      |  0.000804363 |  0.0137907   | -0.00353979  |  0.00790866  |          -0.0196109 |                   58 |                -1 |      nan         |
| ROBOT_DISHES                | robot         | -0.0351513   | -0.0100915   | -0.000770909 |  0.000939316 |          -0.0190926 |                   98 |                -1 |      nan         |
| GALAXY_SOUNDS_SOLAR_WINDS   | galaxy_sounds | -0.00422033  |  0.00367168  |  0.00468187  |  0.00648755  |           0.0185648 |                   13 |                -1 |      nan         |
| GALAXY_SOUNDS_SOLAR_FLAMES  | galaxy_sounds | -0.0136282   | -0.000693687 | -0.000385927 |  0.0100104   |          -0.0185421 |                   16 |                -1 |      nan         |
| TRANSLATOR_SPACE_GRAY       | translator    |  0.00848524  |  0.00783063  | -0.00161137  | -0.00892297  |          -0.0182628 |                   67 |                -1 |      nan         |
| PANEL_1X2                   | panel         | -0.00225033  | -0.000869716 |  0.0103003   | -0.0126788   |          -0.0181373 |                   27 |                -1 |      nan         |
| PEBBLES_M                   | pebbles       | -0.00308638  |  0.00677843  |  0.00826519  |  0.0102506   |          -0.0175661 |                   12 |                -1 |      nan         |
| TRANSLATOR_ECLIPSE_CHARCOAL | translator    | -0.00605502  |  0.000803176 | -0.00721     | -0.00979254  |           0.0174401 |                   46 |                -1 |      nan         |
| UV_VISOR_AMBER              | uv_visor      | -0.00669217  | -0.000658591 |  0.00451668  |  0.00657588  |           0.0174116 |                   50 |                -1 |      nan         |
| SNACKPACK_STRAWBERRY        | snackpack     | -0.0125736   |  0.0107271   |  0.00471759  | -0.00726257  |          -0.0172965 |                   43 |                -1 |      nan         |
| UV_VISOR_MAGENTA            | uv_visor      | -0.00312495  |  0.00384751  |  0.00293108  | -0.00756426  |          -0.0172481 |                   98 |                -1 |      nan         |

## Sign-switching products

| product                     | group        |     ic_lag1 |   switch_lag |   switch_ic |
|:----------------------------|:-------------|------------:|-------------:|------------:|
| OXYGEN_SHAKE_EVENING_BREATH | oxygen_shake | -0.144358   |           63 |   0.0211636 |
| ROBOT_IRONING               | robot        | -0.16424    |           82 |   0.024341  |
| ROBOT_LAUNDRY               | robot        |  0.00435113 |           37 |  -0.0203042 |
| UV_VISOR_YELLOW             | uv_visor     |  0.00238777 |           41 |  -0.0200743 |
