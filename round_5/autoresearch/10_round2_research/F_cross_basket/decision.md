# Phase F — Cross-Basket Hunt

## Per-group min-variance baskets

| set                        | members                                                                                                                                | weights                                 |   min_eigval |   spread_mean |   spread_std |       adf_p |   ou_half_life |      rel_std |
|:---------------------------|:---------------------------------------------------------------------------------------------------------------------------------------|:----------------------------------------|-------------:|--------------:|-------------:|------------:|---------------:|-------------:|
| group_pebbles_minvar       | PEBBLES_L,PEBBLES_M,PEBBLES_S,PEBBLES_XL,PEBBLES_XS                                                                                    | -1.0000,-1.0000,-1.0000,-1.0000,-1.0000 |      1.56626 |    -49998.8   |      2.79834 | 0           |       0.159542 |   5.5968e-05 |
| group_snackpack_minvar     | SNACKPACK_CHOCOLATE,SNACKPACK_PISTACHIO,SNACKPACK_RASPBERRY,SNACKPACK_STRAWBERRY,SNACKPACK_VANILLA                                     | -1.0000,0.1106,0.0158,-0.1379,-0.9579   |   1086.19    |    -19782.3   |     46.0097  | 0.0266643   |     384.767    |   0.0023258  |
| group_uv_visor_minvar      | UV_VISOR_AMBER,UV_VISOR_MAGENTA,UV_VISOR_ORANGE,UV_VISOR_RED,UV_VISOR_YELLOW                                                           | -0.9063,-1.0000,-0.2797,-0.6185,-0.1546 |  39042.8     |    -29735.3   |    300.059   | 0.000366747 |     526.469    |   0.010091   |
| group_robot_minvar         | ROBOT_DISHES,ROBOT_IRONING,ROBOT_LAUNDRY,ROBOT_MOPPING,ROBOT_VACUUMING                                                                 | 0.8490,0.3624,0.2739,0.7924,1.0000      |  45342.6     |     32311.3   |    340.357   | 0.000680392 |     382.637    |   0.0105337  |
| group_panel_minvar         | PANEL_1X2,PANEL_1X4,PANEL_2X2,PANEL_2X4,PANEL_4X4                                                                                      | -0.2832,-0.0744,-0.8331,-0.6943,-1.0000 |  62132.8     |    -28903.9   |    374.873   | 0.00845299  |     836.033    |   0.0129696  |
| group_oxygen_shake_minvar  | OXYGEN_SHAKE_CHOCOLATE,OXYGEN_SHAKE_EVENING_BREATH,OXYGEN_SHAKE_GARLIC,OXYGEN_SHAKE_MINT,OXYGEN_SHAKE_MORNING_BREATH                   | -0.4482,1.0000,0.5026,0.3585,0.4728     |  60492.5     |     19237.9   |    330.478   | 0.00881726  |     707.59     |   0.0171785  |
| group_translator_minvar    | TRANSLATOR_ASTRO_BLACK,TRANSLATOR_ECLIPSE_CHARCOAL,TRANSLATOR_GRAPHITE_MIST,TRANSLATOR_SPACE_GRAY,TRANSLATOR_VOID_BLUE                 | -0.7383,0.8028,0.0113,-0.4436,-1.0000   |  52914.5     |    -13979.2   |    355.362   | 0.00219234  |     699.212    |   0.0254208  |
| group_galaxy_sounds_minvar | GALAXY_SOUNDS_BLACK_HOLES,GALAXY_SOUNDS_DARK_MATTER,GALAXY_SOUNDS_PLANETARY_RINGS,GALAXY_SOUNDS_SOLAR_FLAMES,GALAXY_SOUNDS_SOLAR_WINDS | -0.0026,1.0000,-0.2244,0.0815,0.0874    |  84169.3     |      9596.84  |    299.348   | 0.0343516   |    1115.47     |   0.0311924  |
| group_microchip_minvar     | MICROCHIP_CIRCLE,MICROCHIP_OVAL,MICROCHIP_RECTANGLE,MICROCHIP_SQUARE,MICROCHIP_TRIANGLE                                                | 0.0105,-0.6614,0.6814,0.0429,1.0000     |  62198.6     |     10906.3   |    344.107   | 6.89804e-05 |     454.325    |   0.0315513  |
| group_sleep_pod_minvar     | SLEEP_POD_COTTON,SLEEP_POD_LAMB_WOOL,SLEEP_POD_NYLON,SLEEP_POD_POLYESTER,SLEEP_POD_SUEDE                                               | -0.6166,0.3158,-0.1506,1.0000,-0.5234   |  63472.5     |       694.903 |    335.804   | 0.000876674 |     625.34     |   0.483239   |
| global_minvar              | 50                                                                                                                                     | (see weights csv)                       |      1.56344 |    -49999.2   |      2.79534 | 0           |       0.154338 | nan          |

## Stationary cross-group triplets (ADF p<0.05, rel_std<0.05)

| members                                                         | weights              |   min_eigval |   spread_mean |   spread_std |       adf_p |   ou_half_life |   rel_std |
|:----------------------------------------------------------------|:---------------------|-------------:|--------------:|-------------:|------------:|---------------:|----------:|
| MICROCHIP_SQUARE,PEBBLES_XS,PANEL_2X4                           | 0.316,0.755,1.000    |      52610.7 |       21148.7 |      296.234 | 1.28657e-05 |        13.4612 | 0.0140072 |
| SNACKPACK_STRAWBERRY,UV_VISOR_AMBER,PEBBLES_M                   | 1.000,0.391,0.125    |      20436.7 |       15081.6 |      154.442 | 1.80328e-05 |        13.5668 | 0.0102404 |
| MICROCHIP_SQUARE,PEBBLES_XS,OXYGEN_SHAKE_CHOCOLATE              | 0.683,0.992,1.000    |      66792.1 |       26187.7 |      404.346 | 2.69597e-05 |        14.3393 | 0.0154403 |
| SNACKPACK_STRAWBERRY,UV_VISOR_AMBER,PANEL_1X4                   | 1.000,0.393,-0.102   |      20666.3 |       12852.7 |      155.071 | 0.000158368 |        14.4544 | 0.0120653 |
| SNACKPACK_STRAWBERRY,UV_VISOR_AMBER,GALAXY_SOUNDS_SOLAR_FLAMES  | 1.000,0.334,-0.127   |      21275.3 |       11936.7 |      154.827 | 8.20125e-05 |        14.6988 | 0.0129706 |
| SNACKPACK_STRAWBERRY,UV_VISOR_AMBER,GALAXY_SOUNDS_SOLAR_WINDS   | 1.000,0.382,0.145    |      20876.4 |       15243.2 |      156.015 | 0.000184631 |        14.7292 | 0.0102351 |
| SNACKPACK_STRAWBERRY,UV_VISOR_AMBER,OXYGEN_SHAKE_MORNING_BREATH | 1.000,0.390,-0.119   |      21548.5 |       12603.1 |      158.457 | 3.83965e-05 |        14.7581 | 0.0125729 |
| SNACKPACK_STRAWBERRY,UV_VISOR_AMBER,MICROCHIP_RECTANGLE         | 1.000,0.416,-0.131   |      21462.7 |       12855.7 |      159.743 | 5.99007e-05 |        14.9534 | 0.0124259 |
| SNACKPACK_STRAWBERRY,UV_VISOR_AMBER,ROBOT_MOPPING               | 1.000,0.387,0.100    |      21403.6 |       14876.9 |      157.494 | 4.06515e-05 |        15.1032 | 0.0105865 |
| SNACKPACK_STRAWBERRY,UV_VISOR_AMBER,PEBBLES_XS                  | 1.000,0.515,-0.127   |      22417.1 |       13842.8 |      169.425 | 0.000290066 |        15.1205 | 0.0122391 |
| PEBBLES_XS,UV_VISOR_AMBER,SNACKPACK_STRAWBERRY                  | -0.127,0.515,1.000   |      22417.1 |       13842.8 |      169.425 | 0.000290066 |        15.1205 | 0.0122391 |
| SNACKPACK_STRAWBERRY,UV_VISOR_AMBER,ROBOT_VACUUMING             | 1.000,0.433,-0.216   |      21408.6 |       12152.8 |      162.449 | 7.98756e-05 |        15.3092 | 0.0133672 |
| SNACKPACK_STRAWBERRY,UV_VISOR_AMBER,SLEEP_POD_LAMB_WOOL         | 1.000,0.335,0.113    |      22204.2 |       14566.5 |      157.954 | 4.06477e-05 |        15.4344 | 0.0108436 |
| MICROCHIP_SQUARE,UV_VISOR_AMBER,ROBOT_DISHES                    | 0.331,1.000,0.887    |      40572.2 |       21293.6 |      277.251 | 2.44762e-05 |        15.5404 | 0.0130204 |
| SNACKPACK_STRAWBERRY,UV_VISOR_AMBER,TRANSLATOR_ECLIPSE_CHARCOAL | 1.000,0.320,-0.151   |      21967.8 |       11752.8 |      157.13  | 0.000100919 |        15.5423 | 0.0133696 |
| MICROCHIP_SQUARE,PEBBLES_XS,MICROCHIP_CIRCLE                    | -0.728,-0.946,-1.000 |      73535.3 |      -26122.6 |      422.134 | 2.73708e-05 |        15.6111 | 0.0161597 |
| SNACKPACK_STRAWBERRY,UV_VISOR_AMBER,TRANSLATOR_GRAPHITE_MIST    | 1.000,0.363,0.114    |      21999.3 |       14727.7 |      158.61  | 0.000339181 |        15.6272 | 0.0107695 |
| SNACKPACK_STRAWBERRY,UV_VISOR_AMBER,SLEEP_POD_SUEDE             | 1.000,0.427,0.113    |      22443.9 |       15367.7 |      163.681 | 0.000357724 |        15.6589 | 0.010651  |
| SLEEP_POD_SUEDE,UV_VISOR_AMBER,SNACKPACK_STRAWBERRY             | 0.113,0.427,1.000    |      22443.9 |       15367.7 |      163.681 | 0.000357724 |        15.6589 | 0.010651  |
| SNACKPACK_STRAWBERRY,UV_VISOR_AMBER,MICROCHIP_OVAL              | 1.000,0.416,-0.059   |      22292.8 |       13515.3 |      161.893 | 6.49233e-05 |        15.6619 | 0.0119785 |
