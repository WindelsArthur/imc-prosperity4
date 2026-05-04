# Phase 0 — Data Inventory
Days available: [2, 3, 4]

## Per-day summary
### Day 2
- prices rows: 500,000  trades rows: 11,090
- distinct products in prices: 50
- distinct symbols in trades: 50
- timestamp range prices: 0..999900
- per-product row counts min/max/median: 10000/10000/10000
- top tick spacings (product 0): {100.0: 9999}
### Day 3
- prices rows: 500,000  trades rows: 12,320
- distinct products in prices: 50
- distinct symbols in trades: 50
- timestamp range prices: 0..999900
- per-product row counts min/max/median: 10000/10000/10000
- top tick spacings (product 0): {100.0: 9999}
### Day 4
- prices rows: 500,000  trades rows: 11,975
- distinct products in prices: 50
- distinct symbols in trades: 50
- timestamp range prices: 0..999900
- per-product row counts min/max/median: 10000/10000/10000
- top tick spacings (product 0): {100.0: 9999}

## Group taxonomy
- **galaxy_sounds**: GALAXY_SOUNDS_BLACK_HOLES, GALAXY_SOUNDS_DARK_MATTER, GALAXY_SOUNDS_PLANETARY_RINGS, GALAXY_SOUNDS_SOLAR_FLAMES, GALAXY_SOUNDS_SOLAR_WINDS
- **microchip**: MICROCHIP_CIRCLE, MICROCHIP_OVAL, MICROCHIP_RECTANGLE, MICROCHIP_SQUARE, MICROCHIP_TRIANGLE
- **oxygen_shake**: OXYGEN_SHAKE_CHOCOLATE, OXYGEN_SHAKE_EVENING_BREATH, OXYGEN_SHAKE_GARLIC, OXYGEN_SHAKE_MINT, OXYGEN_SHAKE_MORNING_BREATH
- **panel**: PANEL_1X2, PANEL_1X4, PANEL_2X2, PANEL_2X4, PANEL_4X4
- **pebbles**: PEBBLES_L, PEBBLES_M, PEBBLES_S, PEBBLES_XL, PEBBLES_XS
- **robot**: ROBOT_DISHES, ROBOT_IRONING, ROBOT_LAUNDRY, ROBOT_MOPPING, ROBOT_VACUUMING
- **sleep_pod**: SLEEP_POD_COTTON, SLEEP_POD_LAMB_WOOL, SLEEP_POD_NYLON, SLEEP_POD_POLYESTER, SLEEP_POD_SUEDE
- **snackpack**: SNACKPACK_CHOCOLATE, SNACKPACK_PISTACHIO, SNACKPACK_RASPBERRY, SNACKPACK_STRAWBERRY, SNACKPACK_VANILLA
- **translator**: TRANSLATOR_ASTRO_BLACK, TRANSLATOR_ECLIPSE_CHARCOAL, TRANSLATOR_GRAPHITE_MIST, TRANSLATOR_SPACE_GRAY, TRANSLATOR_VOID_BLUE
- **uv_visor**: UV_VISOR_AMBER, UV_VISOR_MAGENTA, UV_VISOR_ORANGE, UV_VISOR_RED, UV_VISOR_YELLOW

## Counterparties
Total distinct counterparties: 0

**CRITICAL FINDING — buyer/seller fields are empty in every trade row across all 3 days.**
Round 5 strips counterparty IDs (contradicting the assumption noted in the prompt).
Phase 3 bot-detection cannot be done at the counterparty level. Lee-Ready signed-flow
classification on aggregate trades is still feasible.


## Notes
- 50 expected products: 50
- Files: see sanity_checks.csv (per-day-product row coverage), counterparties.csv, nan_map.csv
