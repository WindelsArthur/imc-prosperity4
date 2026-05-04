# Phase C — Lagged Cointegration (fast)

- Pairs × lags tested: 1200
- Passing ADF<0.05 + HL∈[5,1000]: 221
- Min-fold OOS Sharpe ≥ 0.7: 171

## Top 30 surviving pairs

| i                         | j                           |   lag | group_i       | group_j      |     slope |   intercept |       adf_p |   ou_hl |   fA_sharpe |   fA_pnl |   fB_sharpe |   fB_pnl |   min_fold_sharpe |
|:--------------------------|:----------------------------|------:|:--------------|:-------------|----------:|------------:|------------:|--------:|------------:|---------:|------------:|---------:|------------------:|
| SNACKPACK_VANILLA         | SNACKPACK_CHOCOLATE         |   100 | snackpack     | snackpack    | -0.781613 |    17791.8  | 6.23313e-05 | 147.354 |     4.24683 | 2678.41  |     2.84106 | 1407.87  |           2.84106 |
| SNACKPACK_CHOCOLATE       | SNACKPACK_VANILLA           |   100 | snackpack     | snackpack    | -0.970774 |    19644.3  | 0.000501917 | 173.898 |     2.81407 | 2034.79  |     2.63196 | 1884.32  |           2.63196 |
| MICROCHIP_SQUARE          | SLEEP_POD_SUEDE             |   100 | microchip     | sleep_pod    |  1.84918  |    -7466.62 | 0.00670758  | 845.222 |     2.43742 | 2479.77  |     2.38448 | 3503.22  |           2.38448 |
| PEBBLES_M                 | OXYGEN_SHAKE_MORNING_BREATH |     5 | pebbles       | oxygen_shake | -0.903857 |    19302.3  | 0.000827571 | 551.952 |     2.10357 | 2697.8   |     2.2375  | 2974.36  |           2.10357 |
| SNACKPACK_CHOCOLATE       | PANEL_2X4                   |     1 | snackpack     | panel        | -0.217149 |    12289.6  | 0.00110575  | 610.992 |     2.18488 |  863.796 |     2.04196 |  926.081 |           2.04196 |
| OXYGEN_SHAKE_GARLIC       | PEBBLES_S                   |   100 | oxygen_shake  | pebbles      | -1.01048  |    20961.4  | 0.0018472   | 703.929 |     2.32134 | 2798     |     2.04084 | 2406.99  |           2.04084 |
| SNACKPACK_CHOCOLATE       | PANEL_2X4                   |    20 | snackpack     | panel        | -0.217503 |    12293.4  | 0.000894044 | 605.522 |     2.25781 |  854.136 |     1.98331 |  895.01  |           1.98331 |
| SNACKPACK_CHOCOLATE       | PANEL_2X4                   |     5 | snackpack     | panel        | -0.217213 |    12290.3  | 0.00115079  | 607.209 |     2.21606 |  847.138 |     1.94494 |  890.719 |           1.94494 |
| GALAXY_SOUNDS_SOLAR_WINDS | PANEL_1X4                   |    20 | galaxy_sounds | panel        | -0.537941 |    15493.2  | 0.0139226   | 937.081 |     1.94216 | 1351.98  |     1.97975 | 1678.52  |           1.94216 |
| SNACKPACK_CHOCOLATE       | PANEL_2X4                   |   100 | snackpack     | panel        | -0.219316 |    12312.9  | 0.00108277  | 591.786 |     2.25442 |  899.273 |     1.92498 |  888.608 |           1.92498 |
| GALAXY_SOUNDS_SOLAR_WINDS | PANEL_1X4                   |   100 | galaxy_sounds | panel        | -0.539336 |    15507.6  | 0.0156275   | 922.298 |     1.90717 | 1332.5   |     2.57374 | 2044.77  |           1.90717 |
| PEBBLES_M                 | OXYGEN_SHAKE_MORNING_BREATH |    20 | pebbles       | oxygen_shake | -0.904519 |    19309.3  | 0.000461525 | 548.95  |     2.41869 | 3117.7   |     1.89779 | 2523.55  |           1.89779 |
| PEBBLES_M                 | OXYGEN_SHAKE_MORNING_BREATH |     1 | pebbles       | oxygen_shake | -0.903687 |    19300.5  | 0.000406805 | 554.573 |     2.07712 | 2652.68  |     1.86505 | 2507.03  |           1.86505 |
| GALAXY_SOUNDS_SOLAR_WINDS | PANEL_1X4                   |     1 | galaxy_sounds | panel        | -0.537663 |    15490.3  | 0.0157293   | 940.783 |     1.85666 | 1304.3   |     2.42576 | 2028.77  |           1.85666 |
| UV_VISOR_AMBER            | SNACKPACK_STRAWBERRY        |   100 | uv_visor      | snackpack    | -2.43058  |    33927.3  | 0.00134793  | 628.62  |     1.9168  | 3371.05  |     1.84421 | 2659.1   |           1.84421 |
| PANEL_2X4                 | PEBBLES_XL                  |     1 | panel         | pebbles      |  0.30933  |     7174.37 | 0.000634067 | 585.542 |     1.8707  | 2103.5   |     1.84093 | 2066.63  |           1.84093 |
| SLEEP_POD_POLYESTER       | UV_VISOR_AMBER              |   100 | sleep_pod     | uv_visor     | -0.915906 |    19095.6  | 0.00721363  | 819.522 |     2.05243 | 1496.8   |     1.83605 | 1752.82  |           1.83605 |
| SLEEP_POD_POLYESTER       | UV_VISOR_AMBER              |     5 | sleep_pod     | uv_visor     | -0.922343 |    19138.3  | 0.00483088  | 814.146 |     2.2026  | 1927.69  |     1.82402 | 1648.31  |           1.82402 |
| PEBBLES_M                 | OXYGEN_SHAKE_MORNING_BREATH |   100 | pebbles       | oxygen_shake | -0.907103 |    19337.1  | 0.000284721 | 539.348 |     1.82189 | 2345.49  |     2.29138 | 2914.22  |           1.82189 |
| GALAXY_SOUNDS_SOLAR_WINDS | PANEL_1X4                   |     5 | galaxy_sounds | panel        | -0.537719 |    15490.9  | 0.0129976   | 928.348 |     1.79675 | 1278.42  |     2.00116 | 1711.03  |           1.79675 |
| SLEEP_POD_POLYESTER       | UV_VISOR_AMBER              |     1 | sleep_pod     | uv_visor     | -0.922573 |    19139.8  | 0.00324453  | 814.287 |     2.31474 | 1992.25  |     1.77842 | 1616.8   |           1.77842 |
| GALAXY_SOUNDS_DARK_MATTER | UV_VISOR_YELLOW             |   100 | galaxy_sounds | uv_visor     |  0.368938 |     6183.88 | 0.000524563 | 550.019 |     1.75282 | 1651.37  |     2.50555 | 1128.62  |           1.75282 |
| PANEL_2X4                 | PEBBLES_XL                  |     5 | panel         | pebbles      |  0.309234 |     7175.93 | 0.000729898 | 583.404 |     1.75204 | 1976.11  |     1.8132  | 2050.95  |           1.75204 |
| PEBBLES_XL                | PANEL_2X4                   |     1 | pebbles       | panel        |  2.48208  |   -14735.7  | 0.000739591 | 602.718 |     1.74695 | 5142.85  |     2.33262 | 5840.57  |           1.74695 |
| PEBBLES_XL                | PANEL_2X4                   |     5 | pebbles       | panel        |  2.48223  |   -14736.6  | 0.000763872 | 600.66  |     1.74547 | 5163.67  |     2.32867 | 5912.13  |           1.74547 |
| SNACKPACK_STRAWBERRY      | UV_VISOR_AMBER              |   100 | snackpack     | uv_visor     | -0.324013 |    13273.3  | 0.000182355 | 497.569 |     2.0446  | 1040.37  |     1.74415 |  862.53  |           1.74415 |
| SLEEP_POD_SUEDE           | MICROCHIP_SQUARE            |     5 | sleep_pod     | microchip    |  0.451614 |     5258.07 | 0.00946422  | 817.938 |     1.73763 |  588.92  |     1.76815 | 1176.63  |           1.73763 |
| SLEEP_POD_POLYESTER       | UV_VISOR_AMBER              |    20 | sleep_pod     | uv_visor     | -0.921475 |    19132.7  | 0.00647515  | 810.205 |     2.2858  | 1936.3   |     1.7321  | 1674.38  |           1.7321  |
| PEBBLES_S                 | PANEL_2X4                   |   100 | pebbles       | panel        | -1.10022  |    21318.9  | 0.00512871  | 796.583 |     1.93735 | 2204.58  |     1.72638 | 2679.75  |           1.72638 |
| SNACKPACK_STRAWBERRY      | UV_VISOR_AMBER              |    20 | snackpack     | uv_visor     | -0.325581 |    13283.2  | 0.00021268  | 503.362 |     1.71244 |  842.116 |     1.73359 |  861.268 |           1.71244 |
