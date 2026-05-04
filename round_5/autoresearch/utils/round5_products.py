"""Round-5 product universe and group taxonomy.

50 products across 10 groups of 5, all sharing a per-product position limit of 10.
"""
from __future__ import annotations

POSITION_LIMIT = 10

ROUND5_GROUPS: dict[str, list[str]] = {
    "galaxy_sounds": [
        "GALAXY_SOUNDS_BLACK_HOLES",
        "GALAXY_SOUNDS_DARK_MATTER",
        "GALAXY_SOUNDS_PLANETARY_RINGS",
        "GALAXY_SOUNDS_SOLAR_FLAMES",
        "GALAXY_SOUNDS_SOLAR_WINDS",
    ],
    "microchip": [
        "MICROCHIP_CIRCLE",
        "MICROCHIP_OVAL",
        "MICROCHIP_RECTANGLE",
        "MICROCHIP_SQUARE",
        "MICROCHIP_TRIANGLE",
    ],
    "oxygen_shake": [
        "OXYGEN_SHAKE_CHOCOLATE",
        "OXYGEN_SHAKE_EVENING_BREATH",
        "OXYGEN_SHAKE_GARLIC",
        "OXYGEN_SHAKE_MINT",
        "OXYGEN_SHAKE_MORNING_BREATH",
    ],
    "panel": [
        "PANEL_1X2",
        "PANEL_1X4",
        "PANEL_2X2",
        "PANEL_2X4",
        "PANEL_4X4",
    ],
    "pebbles": [
        "PEBBLES_L",
        "PEBBLES_M",
        "PEBBLES_S",
        "PEBBLES_XL",
        "PEBBLES_XS",
    ],
    "robot": [
        "ROBOT_DISHES",
        "ROBOT_IRONING",
        "ROBOT_LAUNDRY",
        "ROBOT_MOPPING",
        "ROBOT_VACUUMING",
    ],
    "sleep_pod": [
        "SLEEP_POD_COTTON",
        "SLEEP_POD_LAMB_WOOL",
        "SLEEP_POD_NYLON",
        "SLEEP_POD_POLYESTER",
        "SLEEP_POD_SUEDE",
    ],
    "snackpack": [
        "SNACKPACK_CHOCOLATE",
        "SNACKPACK_PISTACHIO",
        "SNACKPACK_RASPBERRY",
        "SNACKPACK_STRAWBERRY",
        "SNACKPACK_VANILLA",
    ],
    "translator": [
        "TRANSLATOR_ASTRO_BLACK",
        "TRANSLATOR_ECLIPSE_CHARCOAL",
        "TRANSLATOR_GRAPHITE_MIST",
        "TRANSLATOR_SPACE_GRAY",
        "TRANSLATOR_VOID_BLUE",
    ],
    "uv_visor": [
        "UV_VISOR_AMBER",
        "UV_VISOR_MAGENTA",
        "UV_VISOR_ORANGE",
        "UV_VISOR_RED",
        "UV_VISOR_YELLOW",
    ],
}

ROUND5_PRODUCTS: list[str] = [p for products in ROUND5_GROUPS.values() for p in products]

assert len(ROUND5_PRODUCTS) == 50
assert len(set(ROUND5_PRODUCTS)) == 50
assert all(len(v) == 5 for v in ROUND5_GROUPS.values())

LIMIT_FLAGS: list[str] = [f"--limit={p}:{POSITION_LIMIT}" for p in ROUND5_PRODUCTS]


def group_of(product: str) -> str | None:
    """Return the group name for a product, or None if not found."""
    for g, prods in ROUND5_GROUPS.items():
        if product in prods:
            return g
    return None