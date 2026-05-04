# Phase B — Bleeder Forensics

## Forensics summary

| product                    |   avg_drift |   max_abs_drift |   avg_vol |   avg_spread |   avg_spread_to_vol |   avg_trend_dom |
|:---------------------------|------------:|----------------:|----------:|-------------:|--------------------:|----------------:|
| GALAXY_SOUNDS_SOLAR_FLAMES |     277.333 |          1345.5 |   41.5625 |     14.0715  |            0.338932 |      0.00832663 |
| PANEL_1X2                  |     -99     |          1568.5 |   34.5597 |     11.5098  |            0.333773 |      0.0128824  |
| PANEL_4X4                  |    -291.667 |          1127   |   37.7486 |      8.75047 |            0.232326 |      0.00846596 |
| PEBBLES_L                  |    -297     |          1888.5 |   56.0579 |     13.0205  |            0.232364 |      0.00804434 |
| PEBBLES_M                  |     229.833 |          2039   |   57.0173 |     13.1209  |            0.230082 |      0.00935264 |
| ROBOT_MOPPING              |     530.167 |          2352.5 |   40.8428 |      7.97067 |            0.195114 |      0.0116644  |
| SLEEP_POD_LAMB_WOOL        |     272     |           404.5 |   43.0483 |      9.4001  |            0.218386 |      0.00323112 |
| SNACKPACK_CHOCOLATE        |    -113.667 |           181.5 |   24.5249 |     16.4712  |            0.672611 |      0.0021764  |
| SNACKPACK_RASPBERRY        |     103.167 |           239.5 |   29.5741 |     16.8425  |            0.570265 |      0.00273503 |
| TRANSLATOR_SPACE_GRAY      |    -519.667 |          1689.5 |   36.1886 |      8.40217 |            0.232291 |      0.0128005  |
| UV_VISOR_MAGENTA           |     501.5   |          1299.5 |   41.0211 |     14.0916  |            0.343735 |      0.00627931 |

## Recipes

| product                    | recipe   |   avg_trend_dom |   avg_spread_to_vol |
|:---------------------------|:---------|----------------:|--------------------:|
| GALAXY_SOUNDS_SOLAR_FLAMES | cap_3    |      0.00832663 |            0.338932 |
| PANEL_1X2                  | cap_3    |      0.0128824  |            0.333773 |
| PANEL_4X4                  | cap_3    |      0.00846596 |            0.232326 |
| PEBBLES_L                  | cap_3    |      0.00804434 |            0.232364 |
| PEBBLES_M                  | cap_3    |      0.00935264 |            0.230082 |
| ROBOT_MOPPING              | cap_3    |      0.0116644  |            0.195114 |
| SLEEP_POD_LAMB_WOOL        | cap_3    |      0.00323112 |            0.218386 |
| SNACKPACK_CHOCOLATE        | keep_v1  |      0.0021764  |            0.672611 |
| SNACKPACK_RASPBERRY        | cap_3    |      0.00273503 |            0.570265 |
| TRANSLATOR_SPACE_GRAY      | cap_3    |      0.0128005  |            0.232291 |
| UV_VISOR_MAGENTA           | cap_3    |      0.00627931 |            0.343735 |

## Interpretation
- `avg_trend_dom`: ratio of net drift to total absolute movement. >0.1 = strong directional day.
- `avg_spread_to_vol`: bid-ask spread ÷ rolling mid vol (100-tick). <1 means moves outpace spread → MM loses to informed flow.
- `idle`: do not quote (set position cap = 0).
- `cap_3`: cap position at ±3 to limit downside.
- `wider_spread_filter`: only quote when spread ≥ 4.
- `keep_v1`: leave behavior unchanged.
