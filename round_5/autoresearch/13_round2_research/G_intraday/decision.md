# Phase G — Intraday Seasonality

## Most cross-day stable seasonality (avg pairwise corr of bin-mean curves)

| product                     | group         |   cross_day_avg_corr |   oos_corr_2to3 |   oos_corr_3to4 |   f_stat |   max_abs_mean_ret_d2 |
|:----------------------------|:--------------|---------------------:|----------------:|----------------:|---------:|----------------------:|
| TRANSLATOR_ECLIPSE_CHARCOAL | translator    |            0.131431  |       0.181131  |       0.109852  | 0.977733 |                 2.32  |
| MICROCHIP_TRIANGLE          | microchip     |            0.115848  |       0.0662821 |       0.0996383 | 0.915749 |                 3.3   |
| MICROCHIP_OVAL              | microchip     |            0.102699  |       0.162533  |       0.156046  | 0.818703 |                 3.295 |
| MICROCHIP_RECTANGLE         | microchip     |            0.0940419 |       0.161143  |      -0.0100116 | 0.865674 |                 3.43  |
| PANEL_1X4                   | panel         |            0.090523  |       0.127141  |       0.115196  | 1.21463  |                 3.285 |
| OXYGEN_SHAKE_GARLIC         | oxygen_shake  |            0.0816269 |      -0.0517197 |       0.035436  | 0.897112 |                 2.855 |
| SLEEP_POD_POLYESTER         | sleep_pod     |            0.06715   |       0.0935881 |      -0.032405  | 1.12035  |                 3.685 |
| PEBBLES_M                   | pebbles       |            0.0627279 |       0.0359104 |       0.0261051 | 0.95658  |                 3.91  |
| GALAXY_SOUNDS_BLACK_HOLES   | galaxy_sounds |            0.0435529 |      -0.0220699 |       0.0030357 | 1.13092  |                 3.915 |
| GALAXY_SOUNDS_DARK_MATTER   | galaxy_sounds |            0.0391256 |       0.115048  |       0.0604849 | 0.78814  |                 2.72  |
| ROBOT_DISHES                | robot         |            0.0357099 |       0.154495  |      -0.0728125 | 0.79463  |                 2.105 |
| ROBOT_VACUUMING             | robot         |            0.0205738 |       0.067549  |      -0.027748  | 1.17348  |                 2.945 |
| UV_VISOR_YELLOW             | uv_visor      |            0.0194881 |       0.0993038 |      -0.103977  | 0.685586 |                 2.44  |
| GALAXY_SOUNDS_SOLAR_FLAMES  | galaxy_sounds |            0.018678  |      -0.0183178 |       0.0627108 | 1.04269  |                 3.065 |
| PEBBLES_XS                  | pebbles       |            0.0181954 |       0.09056   |      -0.0651021 | 0.865795 |                 3.45  |

## Decision rule
- Adopt intraday overlay only for products with cross_day_avg_corr ≥ 0.30.
- Apply as a small fair-value tilt: `fair += alpha * curve[bin]` with α=0.5.
