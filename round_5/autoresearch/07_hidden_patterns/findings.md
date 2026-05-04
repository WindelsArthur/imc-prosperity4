# Phase 7 — Hidden Pattern Findings

## Ranked by deterministic-fit R² (sine or poly3)

| product                    | group         |   sine_R2 |   sine_period |   poly3_R2 |   poly5_R2 |   mod_K_best |   mod_K_best_R2 |
|:---------------------------|:--------------|----------:|--------------:|-----------:|-----------:|-------------:|----------------:|
| MICROCHIP_OVAL             | microchip     |  0.974089 |         30000 |   0.971435 |   0.97447  |        20000 |       0.105796  |
| UV_VISOR_AMBER             | uv_visor      |  0.962097 |         30000 |   0.969614 |   0.973361 |        20000 |       0.0891842 |
| PEBBLES_XS                 | pebbles       |  0.949509 |         30000 |   0.948478 |   0.950769 |        20000 |       0.203281  |
| MICROCHIP_SQUARE           | microchip     |  0.936062 |         30000 |   0.930145 |   0.941215 |        20000 |       0.271446  |
| OXYGEN_SHAKE_GARLIC        | oxygen_shake  |  0.923736 |         30000 |   0.915129 |   0.939163 |        20000 |       0.353078  |
| SLEEP_POD_POLYESTER        | sleep_pod     |  0.888966 |         30000 |   0.918334 |   0.935797 |        20000 |       0.104834  |
| SLEEP_POD_SUEDE            | sleep_pod     |  0.907121 |         30000 |   0.868823 |   0.928125 |        20000 |       0.266653  |
| SLEEP_POD_COTTON           | sleep_pod     |  0.736202 |         30000 |   0.766763 |   0.912082 |        20000 |       0.173346  |
| ROBOT_IRONING              | robot         |  0.836988 |         11875 |   0.787669 |   0.8992   |        20000 |       0.315305  |
| PEBBLES_XL                 | pebbles       |  0.868526 |         30000 |   0.842803 |   0.898061 |        20000 |       0.471042  |
| MICROCHIP_CIRCLE           | microchip     |  0.742091 |         30000 |   0.793188 |   0.893869 |        20000 |       0.531257  |
| GALAXY_SOUNDS_SOLAR_FLAMES | galaxy_sounds |  0.454513 |         30000 |   0.455122 |   0.552653 |        20000 |       0.892509  |
| PANEL_1X4                  | panel         |  0.826722 |         30000 |   0.773074 |   0.888306 |        20000 |       0.447667  |
| ROBOT_VACUUMING            | robot         |  0.865256 |         30000 |   0.854857 |   0.885163 |        20000 |       0.222938  |
| PEBBLES_S                  | pebbles       |  0.866392 |         30000 |   0.847552 |   0.885113 |        20000 |       0.246315  |

## Lattice candidates (lowest distinct-mids count)

| product                     | group         |   n_distinct_mids |   lattice_ratio |   gzip_ratio |     chi2_p |
|:----------------------------|:--------------|------------------:|----------------:|-------------:|-----------:|
| OXYGEN_SHAKE_EVENING_BREATH | oxygen_shake  |               453 |       0.0151    |    0.0881542 | 0          |
| ROBOT_IRONING               | robot         |               631 |       0.0210333 |    0.0867292 | 0          |
| SNACKPACK_RASPBERRY         | snackpack     |              1634 |       0.0544667 |    0.185271  | 0.834459   |
| SNACKPACK_VANILLA           | snackpack     |              1673 |       0.0557667 |    0.17765   | 0.070032   |
| SNACKPACK_CHOCOLATE         | snackpack     |              1900 |       0.0633333 |    0.177175  | 0.00552296 |
| SNACKPACK_PISTACHIO         | snackpack     |              1928 |       0.0642667 |    0.164421  | 0.00247128 |
| GALAXY_SOUNDS_DARK_MATTER   | galaxy_sounds |              2907 |       0.0969    |    0.197483  | 0.118998   |
| ROBOT_DISHES                | robot         |              3048 |       0.1016    |    0.148496  | 0          |
| SNACKPACK_STRAWBERRY        | snackpack     |              3089 |       0.102967  |    0.186779  | 0.0751202  |
| TRANSLATOR_ECLIPSE_CHARCOAL | translator    |              3146 |       0.104867  |    0.195796  | 0.477595   |

## Highest cross-product RF OOS R² (predictable from other products)

| product                     | group         |   rf_train_R2 |   rf_oos_R2 | rf_top_feature              |
|:----------------------------|:--------------|--------------:|------------:|:----------------------------|
| SNACKPACK_VANILLA           | snackpack     |      0.995598 |  0.673361   | SNACKPACK_CHOCOLATE         |
| SLEEP_POD_LAMB_WOOL         | sleep_pod     |      0.984079 |  0.309945   | ROBOT_DISHES                |
| PANEL_4X4                   | panel         |      0.987894 |  0.306516   | PANEL_1X2                   |
| SNACKPACK_RASPBERRY         | snackpack     |      0.980921 |  0.250682   | SNACKPACK_PISTACHIO         |
| TRANSLATOR_ECLIPSE_CHARCOAL | translator    |      0.989164 |  0.128771   | PANEL_1X4                   |
| PEBBLES_L                   | pebbles       |      0.986921 |  0.00323443 | ROBOT_IRONING               |
| SNACKPACK_CHOCOLATE         | snackpack     |      0.993647 | -0.0605704  | SNACKPACK_VANILLA           |
| UV_VISOR_ORANGE             | uv_visor      |      0.992301 | -0.0627355  | MICROCHIP_SQUARE            |
| OXYGEN_SHAKE_EVENING_BREATH | oxygen_shake  |      0.992191 | -0.199744   | OXYGEN_SHAKE_GARLIC         |
| GALAXY_SOUNDS_SOLAR_FLAMES  | galaxy_sounds |      0.987854 | -0.250979   | TRANSLATOR_SPACE_GRAY       |
| SLEEP_POD_POLYESTER         | sleep_pod     |      0.997751 | -0.307046   | SLEEP_POD_SUEDE             |
| TRANSLATOR_GRAPHITE_MIST    | translator    |      0.986242 | -0.413767   | SLEEP_POD_POLYESTER         |
| ROBOT_VACUUMING             | robot         |      0.989156 | -0.482547   | PEBBLES_XS                  |
| ROBOT_MOPPING               | robot         |      0.996849 | -0.483728   | MICROCHIP_OVAL              |
| ROBOT_IRONING               | robot         |      0.996192 | -0.526113   | OXYGEN_SHAKE_MORNING_BREATH |

## Anchor-and-revert candidates (fraction of large moves that revert)

| product                     | group        |   anchor_n_spikes |   anchor_revert_frac |
|:----------------------------|:-------------|------------------:|---------------------:|
| OXYGEN_SHAKE_CHOCOLATE      | oxygen_shake |                82 |             0.792683 |
| ROBOT_DISHES                | robot        |               831 |             0.754513 |
| ROBOT_IRONING               | robot        |                56 |             0.75     |
| OXYGEN_SHAKE_EVENING_BREATH | oxygen_shake |                66 |             0.69697  |
| MICROCHIP_OVAL              | microchip    |               434 |             0.672811 |
| MICROCHIP_TRIANGLE          | microchip    |               188 |             0.654255 |
| ROBOT_MOPPING               | robot        |               234 |             0.653846 |
| OXYGEN_SHAKE_MORNING_BREATH | oxygen_shake |               176 |             0.653409 |
| PANEL_1X2                   | panel        |               237 |             0.64135  |
| PEBBLES_S                   | pebbles      |               146 |             0.636986 |
| SNACKPACK_PISTACHIO         | snackpack    |                49 |             0.632653 |
| UV_VISOR_ORANGE             | uv_visor     |               206 |             0.631068 |
| MICROCHIP_SQUARE            | microchip    |               269 |             0.624535 |
| SNACKPACK_RASPBERRY         | snackpack    |                77 |             0.623377 |
| PANEL_4X4                   | panel        |               137 |             0.620438 |
