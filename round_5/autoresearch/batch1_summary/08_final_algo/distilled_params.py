"""All numerical constants for strategy_final.py.

Provenance per block listed inline. Edit ONLY this file to retune; never
mutate at runtime.
"""
from __future__ import annotations

# ── Universe (R5 round 5 products, position limit = 10 each) ──────────────
POSITION_LIMIT = 10

PEBBLES = ["PEBBLES_L", "PEBBLES_M", "PEBBLES_S", "PEBBLES_XL", "PEBBLES_XS"]
SNACKPACKS = [
    "SNACKPACK_CHOCOLATE", "SNACKPACK_PISTACHIO",
    "SNACKPACK_RASPBERRY", "SNACKPACK_STRAWBERRY", "SNACKPACK_VANILLA",
]
MICROCHIPS = [
    "MICROCHIP_CIRCLE", "MICROCHIP_OVAL", "MICROCHIP_RECTANGLE",
    "MICROCHIP_SQUARE", "MICROCHIP_TRIANGLE",
]
SLEEP_PODS = [
    "SLEEP_POD_COTTON", "SLEEP_POD_LAMB_WOOL", "SLEEP_POD_NYLON",
    "SLEEP_POD_POLYESTER", "SLEEP_POD_SUEDE",
]
ROBOTS = [
    "ROBOT_DISHES", "ROBOT_IRONING", "ROBOT_LAUNDRY",
    "ROBOT_MOPPING", "ROBOT_VACUUMING",
]
GALAXY = [
    "GALAXY_SOUNDS_BLACK_HOLES", "GALAXY_SOUNDS_DARK_MATTER",
    "GALAXY_SOUNDS_PLANETARY_RINGS", "GALAXY_SOUNDS_SOLAR_FLAMES",
    "GALAXY_SOUNDS_SOLAR_WINDS",
]
OXYGEN = [
    "OXYGEN_SHAKE_CHOCOLATE", "OXYGEN_SHAKE_EVENING_BREATH",
    "OXYGEN_SHAKE_GARLIC", "OXYGEN_SHAKE_MINT", "OXYGEN_SHAKE_MORNING_BREATH",
]
PANELS = ["PANEL_1X2", "PANEL_1X4", "PANEL_2X2", "PANEL_2X4", "PANEL_4X4"]
TRANSLATORS = [
    "TRANSLATOR_ASTRO_BLACK", "TRANSLATOR_ECLIPSE_CHARCOAL",
    "TRANSLATOR_GRAPHITE_MIST", "TRANSLATOR_SPACE_GRAY", "TRANSLATOR_VOID_BLUE",
]
UV_VISORS = [
    "UV_VISOR_AMBER", "UV_VISOR_MAGENTA", "UV_VISOR_ORANGE",
    "UV_VISOR_RED", "UV_VISOR_YELLOW",
]

ALL_PRODUCTS = (
    PEBBLES + SNACKPACKS + MICROCHIPS + SLEEP_PODS + ROBOTS
    + GALAXY + OXYGEN + PANELS + TRANSLATORS + UV_VISORS
)

# ── PROD_CAP — round-2 Phase B bleeder analysis ──────────────────────────
# Source: ROUND_5/autoresearch/13_round2_research/M_submit/diff_v1_to_v2.md
# These 9 products had spread/vol < 0.6 and bled to MM in v1; cap restores +134K.
# PEBBLES_L added in final algo: chronic v3 loser (-12,237). Cap=5 found in v2
# ablation to give +92 PnL but Sharpe 8.6→7.2; tested in Phase H ablation.
PROD_CAP = {
    "SLEEP_POD_LAMB_WOOL": 3,
    "UV_VISOR_MAGENTA":    4,
    "PANEL_1X2":           3,
    "TRANSLATOR_SPACE_GRAY": 4,
    "ROBOT_MOPPING":       4,
    "PANEL_4X4":           4,
    "GALAXY_SOUNDS_SOLAR_FLAMES": 4,
    "SNACKPACK_RASPBERRY": 5,
    "SNACKPACK_CHOCOLATE": 5,
    # PEBBLES_L cap added if Phase H ablation justifies it (see PEBBLES_L_CAP flag).
}

# ── Basket invariants ─────────────────────────────────────────────────────
# Source: ROUND_5/autoresearch/05_cross_product/groups/pebbles/basket_residual.csv
# Reverified: PEBBLES sum mean=49,999.94 std=2.80; SNACKPACK mean=50,220.94 std=189.58.
PEBBLES_SUM_TARGET = 50000.0
SNACKPACK_SUM_TARGET = 50221.0
PEBBLES_SKEW_DIVISOR = 5.0
SNACKPACK_SKEW_DIVISOR = 5.0
PEBBLES_SKEW_CLIP = 3.0
SNACKPACK_SKEW_CLIP = 5.0

# Cross thresholds for aggressive skew (basket residual size in sigmas).
PEBBLES_BIG_SKEW = 1.8
SNACKPACK_BIG_SKEW = 3.5

# ── Within-group cointegration pairs (round-1) ────────────────────────────
# 9 of original 10 — OXYGEN_SHAKE_CHOCOLATE/OXYGEN_SHAKE_GARLIC DROPPED:
# reverify ADF p=0.918 (claimed 0.030); pair non-stationary on full stitch.
# Source: ROUND_5/batch1_summary/03_reconciliation/conflicts.jsonl c003.
COINT_PAIRS = [
    ("MICROCHIP_RECTANGLE", "MICROCHIP_SQUARE", -0.401, 14119.0, 304.0),
    ("ROBOT_LAUNDRY", "ROBOT_VACUUMING", 0.334, 7072.0, 234.0),
    ("SLEEP_POD_COTTON", "SLEEP_POD_POLYESTER", 0.519, 5144.0, 328.0),
    ("GALAXY_SOUNDS_DARK_MATTER", "GALAXY_SOUNDS_PLANETARY_RINGS", 0.183, 8285.0, 283.0),
    ("SNACKPACK_RASPBERRY", "SNACKPACK_VANILLA", 0.013, 9962.0, 161.0),
    ("SNACKPACK_CHOCOLATE", "SNACKPACK_STRAWBERRY", -0.106, 11051.0, 145.0),
    ("UV_VISOR_AMBER", "UV_VISOR_MAGENTA", -1.238, 21897.0, 371.0),
    # ("OXYGEN_SHAKE_CHOCOLATE", "OXYGEN_SHAKE_GARLIC", -0.155, 11066.0, 237.0),  # DROPPED
    ("TRANSLATOR_ECLIPSE_CHARCOAL", "TRANSLATOR_VOID_BLUE", 0.456, 4954.0, 308.0),
    ("SLEEP_POD_POLYESTER", "SLEEP_POD_SUEDE", 0.756, 2977.0, 426.0),
]

# ── Cross-group cointegration pairs (round-3 Phase C) ────────────────────
# Top 30 surviving min-fold OOS Sharpe ≥ 1.0 from lagged-EG search.
# Source: ROUND_5/autoresearch/14_lag_research/C_lagged_coint/lagged_coint_fast.csv
# Spot-checked 5 with full-stitch ADF — all p < 0.01.
CROSS_GROUP_PAIRS = [
    ("PEBBLES_XL", "PANEL_2X4", 2.4821, -14735.73, 200.0),
    ("UV_VISOR_AMBER", "SNACKPACK_STRAWBERRY", -2.4501, 34143.94, 200.0),
    ("PEBBLES_M", "OXYGEN_SHAKE_MORNING_BREATH", -0.9037, 19300.55, 200.0),
    ("UV_VISOR_YELLOW", "GALAXY_SOUNDS_DARK_MATTER", 1.5837, -5238.83, 200.0),
    ("OXYGEN_SHAKE_GARLIC", "PEBBLES_S", -1.0114, 20960.00, 200.0),
    ("PANEL_2X4", "PEBBLES_XL", 0.3093, 7174.37, 200.0),
    ("MICROCHIP_SQUARE", "SLEEP_POD_SUEDE", 1.8678, -7692.97, 200.0),
    ("GALAXY_SOUNDS_BLACK_HOLES", "PEBBLES_S", -1.0180, 20559.94, 200.0),
    ("PEBBLES_S", "GALAXY_SOUNDS_BLACK_HOLES", -0.7694, 17755.06, 200.0),
    ("PEBBLES_S", "OXYGEN_SHAKE_GARLIC", -0.7727, 18147.25, 200.0),
    ("SLEEP_POD_POLYESTER", "UV_VISOR_AMBER", -0.9226, 19139.77, 200.0),
    ("GALAXY_SOUNDS_SOLAR_WINDS", "PANEL_1X4", -0.5377, 15490.30, 200.0),
    ("PEBBLES_S", "PANEL_2X4", -1.1018, 21344.63, 200.0),
    ("ROBOT_IRONING", "PEBBLES_M", -0.9154, 18096.05, 200.0),
    ("PANEL_2X4", "OXYGEN_SHAKE_GARLIC", 0.5545, 4653.12, 200.0),
    ("GALAXY_SOUNDS_DARK_MATTER", "UV_VISOR_YELLOW", 0.3725, 6144.99, 200.0),
    ("UV_VISOR_AMBER", "SLEEP_POD_POLYESTER", -0.9595, 19272.87, 200.0),
    ("PEBBLES_M", "ROBOT_IRONING", -0.7284, 16601.80, 200.0),
    ("PANEL_2X4", "PEBBLES_S", -0.6242, 16840.75, 200.0),
    ("SNACKPACK_STRAWBERRY", "SLEEP_POD_POLYESTER", 0.3255, 6852.82, 200.0),
    ("SNACKPACK_CHOCOLATE", "PANEL_2X4", -0.2171, 12289.62, 200.0),
    ("SLEEP_POD_SUEDE", "MICROCHIP_SQUARE", 0.4516, 5257.75, 200.0),
    ("SNACKPACK_STRAWBERRY", "UV_VISOR_AMBER", -0.3259, 13284.98, 200.0),
    ("TRANSLATOR_ECLIPSE_CHARCOAL", "SLEEP_POD_LAMB_WOOL", -0.5308, 15493.89, 200.0),
    ("SNACKPACK_VANILLA", "PANEL_1X2", 0.1461, 8793.78, 200.0),
    ("SNACKPACK_VANILLA", "PANEL_2X4", 0.1490, 8418.80, 200.0),
    ("SLEEP_POD_LAMB_WOOL", "TRANSLATOR_ECLIPSE_CHARCOAL", -0.7159, 17727.49, 200.0),
    ("SNACKPACK_PISTACHIO", "OXYGEN_SHAKE_GARLIC", -0.1488, 11269.91, 200.0),
    ("SNACKPACK_PISTACHIO", "PEBBLES_XS", 0.0992, 8761.10, 200.0),
    ("SNACKPACK_PISTACHIO", "MICROCHIP_OVAL", 0.0907, 8753.81, 200.0),
]

# ── Pair tilt parameters ──────────────────────────────────────────────────
PAIR_TILT_DIVISOR = 8.0
PAIR_TILT_CLIP = 3.0

# ── Inventory skew ────────────────────────────────────────────────────────
INV_SKEW_BETA = 0.20  # − pos × β

# ── Quote sizing ──────────────────────────────────────────────────────────
QUOTE_BASE_SIZE_CAP = 8     # min(8, prod_cap)
QUOTE_AGGRESSIVE_SIZE = 2   # cross size when basket skew > big threshold

# ── Phase H feature flags (defaults to v3 baseline = 733,320) ─────────────
PEBBLES_L_CAP = 4           # Phase H ablation v09: PEBBLES_L cap=4 → +914 PnL, Sharpe 8.83→10.80, DD 23990→21786
ENABLE_AR1_EVB_SKEW = False  # Phase H ablation v11: AR1 EVB skew added −74 PnL on baseline; rejected
EVB_AR1_ALPHA = 1.5
ENABLE_DROP_OG_PAIR = True  # OXYGEN_SHAKE_CHOCOLATE/GARLIC pair dropped (reverify ADF=0.918)
