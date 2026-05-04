# Phase A — Sine Decision

## Per-product OOS MSE comparison (lower = better)

| product             | fold   |   test_day |   n_train |   n_test |   train_r2_sine |   train_period |   train_A |   train_phi |         mse_sine |         mse_2sin |       mse_linear |         mse_flat |   mse_rw |     mse_test_var | sine_beats_flat   | sine_beats_linear   | sine_beats_rw   |   improvement_vs_flat |   improvement_vs_linear |
|:--------------------|:-------|-----------:|----------:|---------:|----------------:|---------------:|----------:|------------:|-----------------:|-----------------:|-----------------:|-----------------:|---------:|-----------------:|:------------------|:--------------------|:----------------|----------------------:|------------------------:|
| MICROCHIP_OVAL      | A      |          3 |     10000 |    10000 |        0.448169 |           5412 |   303.365 |  -0.98903   |      2.00024e+06 |      2.01305e+06 |      1.85802e+06 | 886479           | 167.633  | 379213           | False             | False               | False           |             -1.25639  |              -0.0765441 |
| MICROCHIP_OVAL      | B      |          4 |     20000 |    10000 |        0.876264 |          18061 |   401.827 |  -1.75674   |      2.27676e+06 |      2.31534e+06 |      1.46538e+06 |      1.73461e+06 |  87.3498 | 294945           | False             | False               | False           |             -0.312548 |              -0.553694  |
| UV_VISOR_AMBER      | A      |          3 |     10000 |    10000 |        0.926997 |           3941 |   124.491 |  -0.0992656 |  70206.9         |  79686.2         |  76869.8         | 749819           |  59.5769 |  64899.7         | True              | True                | False           |              0.906368 |               0.0866779 |
| UV_VISOR_AMBER      | B      |          4 |     20000 |    10000 |        0.960308 |          21847 |   253.222 |   0.847216  | 163394           | 202050           | 463038           | 284878           |  48.9971 |  31850.2         | True              | True                | False           |              0.426442 |               0.647126  |
| OXYGEN_SHAKE_GARLIC | A      |          3 |     10000 |    10000 |        0.960651 |           7432 |   449.118 |  -2.33867   |      2.30384e+06 |      2.31231e+06 |      1.76611e+06 |  77982           | 142.351  |  77555.2         | False             | False               | False           |            -28.5432   |              -0.304473  |
| OXYGEN_SHAKE_GARLIC | B      |          4 |     20000 |    10000 |        0.861829 |          30000 |  1319.33  |   0.635182  |      2.75601e+06 |      2.64089e+06 | 271114           |      1.43084e+06 | 166.751  | 477620           | False             | False               | False           |             -0.92615  |              -9.16551   |
| SLEEP_POD_POLYESTER | A      |          3 |     10000 |    10000 |        0.891061 |           3941 |   233.092 |  -1.92381   | 312368           | 370476           | 304343           | 235484           | 143.603  | 173057           | False             | False               | False           |             -0.32649  |              -0.0263667 |
| SLEEP_POD_POLYESTER | B      |          4 |     20000 |    10000 |        0.927015 |          12344 |   277.021 |   2.77684   | 606926           | 616015           | 742932           | 108825           | 163.421  | 100912           | False             | True                | False           |             -4.57707  |               0.183067  |
| SLEEP_POD_SUEDE     | A      |          3 |     10000 |    10000 |        0.876518 |           9578 |   505.844 |   1.05824   | 411265           | 421613           | 500031           | 795910           | 141.435  | 155605           | True              | True                | False           |              0.483277 |               0.177522  |
| SLEEP_POD_SUEDE     | B      |          4 |     20000 |    10000 |        0.938661 |          16951 |   478.534 |   2.56787   |      1.09711e+06 |      1.18366e+06 |      1.9745e+06  |  83681           | 143.757  |  74687.3         | False             | True                | False           |            -12.1106   |               0.444361  |
| PEBBLES_XS          | A      |          3 |     10000 |    10000 |        0.928029 |           5766 |   137.106 |  -0.162493  | 176298           | 174770           | 154446           |      1.65128e+06 | 226.163  | 484686           | True              | False               | False           |              0.893235 |              -0.141489  |
| PEBBLES_XS          | B      |          4 |     20000 |    10000 |        0.963361 |          11586 |   214.348 |   2.73351   |      1.90277e+06 |      1.86721e+06 |      1.77855e+06 | 885319           | 223.195  | 239873           | False             | False               | False           |             -1.14925  |              -0.0698426 |
| PEBBLES_XL          | A      |          3 |     10000 |    10000 |        0.912487 |           5766 |   531.356 |  -0.579644  |      1.07564e+07 |      1.0774e+07  |      9.80322e+06 | 436518           | 919.344  | 391403           | False             | False               | False           |            -23.6413   |              -0.0972308 |
| PEBBLES_XL          | B      |          4 |     20000 |    10000 |        0.8534   |          30000 |  1761.51  |  -0.964053  |      1.00542e+07 |      1.05915e+07 |      1.44178e+06 |      8.78515e+06 | 920.221  |      2.08531e+06 | False             | False               | False           |             -0.144457 |              -5.9735    |

## Decision

### Per-day single-sine R² stability

| product             |        2 |        3 |        4 |
|:--------------------|---------:|---------:|---------:|
| MICROCHIP_OVAL      | 0.448169 | 0.896532 | 0.949033 |
| OXYGEN_SHAKE_GARLIC | 0.960651 | 0.735532 | 0.931571 |
| PEBBLES_XL          | 0.912487 | 0.637491 | 0.931442 |
| PEBBLES_XS          | 0.928029 | 0.899105 | 0.880978 |
| SLEEP_POD_POLYESTER | 0.891061 | 0.835144 | 0.821021 |
| SLEEP_POD_SUEDE     | 0.876518 | 0.762745 | 0.650256 |
| UV_VISOR_AMBER      | 0.926997 | 0.792219 | 0.555054 |

### Per-day periods (stability check)

| product             |    2 |     3 |     4 |
|:--------------------|-----:|------:|------:|
| MICROCHIP_OVAL      | 5412 |  3258 | 30000 |
| OXYGEN_SHAKE_GARLIC | 7432 |  7432 |  3471 |
| PEBBLES_XL          | 5766 |  6546 |  4199 |
| PEBBLES_XS          | 5766 | 30000 | 30000 |
| SLEEP_POD_POLYESTER | 3941 | 14014 | 30000 |
| SLEEP_POD_SUEDE     | 9578 | 10205 |  4474 |
| UV_VISOR_AMBER      | 3941 |  2373 | 30000 |

### Final yes/no per product

| product | foldA sine<flat | foldB sine<flat | foldA sine<linear | foldB sine<linear | exploitable |
|---|---|---|---|---|---|
| MICROCHIP_OVAL | False | False | False | False | **no** |
| UV_VISOR_AMBER | True | True | True | True | **YES** |
| OXYGEN_SHAKE_GARLIC | False | False | False | False | **no** |
| SLEEP_POD_POLYESTER | False | False | False | True | **no** |
| SLEEP_POD_SUEDE | True | False | True | True | **no** |
| PEBBLES_XS | True | False | False | False | **no** |
| PEBBLES_XL | False | False | False | False | **no** |
