# Phase 3 — Trade Flow & Bot Candidates

## Data limitation

Round-5 trade rows have **empty buyer/seller fields for all 3 days**, so per-counterparty
profiling and bot-fingerprinting are impossible. Phase 3 instead focuses on aggregate
signed flow (Lee-Ready), trade location, and inter-arrival statistics.

## Top |IC(signed_flow, forward mid)| at h=5

| product                     | group         |   n_trades |   ic_signed_flow_h1 |   ic_signed_flow_h5 |   ic_signed_flow_h20 |   frac_at_ask |   frac_at_bid |
|:----------------------------|:--------------|-----------:|--------------------:|--------------------:|---------------------:|--------------:|--------------:|
| PEBBLES_M                   | pebbles       |        644 |         0.0126802   |          0.015694   |          0.00618283  |      0.498447 |      0.501553 |
| UV_VISOR_RED                | uv_visor      |        733 |         0.00725717  |          0.0124728  |          0.00765628  |      0.488404 |      0.511596 |
| UV_VISOR_YELLOW             | uv_visor      |        733 |         0.014439    |          0.0117131  |          0.0026552   |      0.488404 |      0.511596 |
| PANEL_1X2                   | panel         |        733 |         0.00350678  |          0.0110321  |          0.00468267  |      0.488404 |      0.511596 |
| MICROCHIP_SQUARE            | microchip     |        569 |        -0.000631783 |         -0.0109625  |         -0.00633243  |      0.527241 |      0.472759 |
| ROBOT_DISHES                | robot         |        733 |         0.00311968  |          0.0100152  |          0.00771161  |      0.488404 |      0.511596 |
| GALAXY_SOUNDS_SOLAR_WINDS   | galaxy_sounds |        733 |        -0.00524839  |         -0.00863316 |         -0.000780299 |      0.488404 |      0.511596 |
| PEBBLES_XL                  | pebbles       |        644 |        -0.00656909  |         -0.00850167 |         -0.00644902  |      0.498447 |      0.501553 |
| ROBOT_MOPPING               | robot         |        733 |         0.00734221  |          0.00808867 |          0.00337607  |      0.488404 |      0.511596 |
| OXYGEN_SHAKE_EVENING_BREATH | oxygen_shake  |        733 |        -0.00390526  |         -0.00786016 |         -0.00047509  |      0.488404 |      0.511596 |
| PANEL_4X4                   | panel         |        733 |         0.00346101  |         -0.00761291 |         -0.00347509  |      0.488404 |      0.511596 |
| ROBOT_LAUNDRY               | robot         |        733 |        -0.00563057  |         -0.00756427 |         -0.00609967  |      0.488404 |      0.511596 |
| UV_VISOR_MAGENTA            | uv_visor      |        733 |         0.00121653  |          0.00675038 |          0.00341132  |      0.488404 |      0.511596 |
| TRANSLATOR_GRAPHITE_MIST    | translator    |        733 |         0.0121712   |          0.00601606 |         -0.00422025  |      0.488404 |      0.511596 |
| TRANSLATOR_VOID_BLUE        | translator    |        733 |        -0.00269138  |          0.00597325 |         -0.00455566  |      0.488404 |      0.511596 |

## Trade location asymmetry — products where flow is one-sided

| product                   | group         |   n_trades |   frac_at_ask |   frac_at_bid |   frac_between |      asym |
|:--------------------------|:--------------|-----------:|--------------:|--------------:|---------------:|----------:|
| MICROCHIP_CIRCLE          | microchip     |        569 |      0.527241 |      0.472759 |    5.55112e-17 | 0.0544815 |
| MICROCHIP_OVAL            | microchip     |        569 |      0.527241 |      0.472759 |    5.55112e-17 | 0.0544815 |
| MICROCHIP_RECTANGLE       | microchip     |        569 |      0.527241 |      0.472759 |    5.55112e-17 | 0.0544815 |
| MICROCHIP_SQUARE          | microchip     |        569 |      0.527241 |      0.472759 |    5.55112e-17 | 0.0544815 |
| MICROCHIP_TRIANGLE        | microchip     |        569 |      0.527241 |      0.472759 |    5.55112e-17 | 0.0544815 |
| GALAXY_SOUNDS_BLACK_HOLES | galaxy_sounds |        733 |      0.488404 |      0.511596 |    0           | 0.0231924 |
| SNACKPACK_VANILLA         | snackpack     |        733 |      0.488404 |      0.511596 |    0           | 0.0231924 |
| SLEEP_POD_COTTON          | sleep_pod     |        733 |      0.488404 |      0.511596 |    0           | 0.0231924 |
| SLEEP_POD_LAMB_WOOL       | sleep_pod     |        733 |      0.488404 |      0.511596 |    0           | 0.0231924 |
| SLEEP_POD_NYLON           | sleep_pod     |        733 |      0.488404 |      0.511596 |    0           | 0.0231924 |
| SLEEP_POD_POLYESTER       | sleep_pod     |        733 |      0.488404 |      0.511596 |    0           | 0.0231924 |
| SLEEP_POD_SUEDE           | sleep_pod     |        733 |      0.488404 |      0.511596 |    0           | 0.0231924 |
| SNACKPACK_CHOCOLATE       | snackpack     |        733 |      0.488404 |      0.511596 |    0           | 0.0231924 |
| SNACKPACK_PISTACHIO       | snackpack     |        733 |      0.488404 |      0.511596 |    0           | 0.0231924 |
| SNACKPACK_RASPBERRY       | snackpack     |        733 |      0.488404 |      0.511596 |    0           | 0.0231924 |

## Bursty trading (low CV inter-arrival → regular)

| product                   | group         |   n_trades |   mean_iat_ticks |   cv_iat |
|:--------------------------|:--------------|-----------:|-----------------:|---------:|
| GALAXY_SOUNDS_BLACK_HOLES | galaxy_sounds |        733 |          4092.05 |   0.9041 |
| ROBOT_LAUNDRY             | robot         |        733 |          4092.05 |   0.9041 |
| ROBOT_MOPPING             | robot         |        733 |          4092.05 |   0.9041 |
| ROBOT_VACUUMING           | robot         |        733 |          4092.05 |   0.9041 |
| SLEEP_POD_COTTON          | sleep_pod     |        733 |          4092.05 |   0.9041 |
| SLEEP_POD_LAMB_WOOL       | sleep_pod     |        733 |          4092.05 |   0.9041 |
| SLEEP_POD_NYLON           | sleep_pod     |        733 |          4092.05 |   0.9041 |
| SLEEP_POD_POLYESTER       | sleep_pod     |        733 |          4092.05 |   0.9041 |
| SLEEP_POD_SUEDE           | sleep_pod     |        733 |          4092.05 |   0.9041 |
| SNACKPACK_CHOCOLATE       | snackpack     |        733 |          4092.05 |   0.9041 |
| SNACKPACK_PISTACHIO       | snackpack     |        733 |          4092.05 |   0.9041 |
| SNACKPACK_RASPBERRY       | snackpack     |        733 |          4092.05 |   0.9041 |
| SNACKPACK_STRAWBERRY      | snackpack     |        733 |          4092.05 |   0.9041 |
| SNACKPACK_VANILLA         | snackpack     |        733 |          4092.05 |   0.9041 |
| TRANSLATOR_ASTRO_BLACK    | translator    |        733 |          4092.05 |   0.9041 |
