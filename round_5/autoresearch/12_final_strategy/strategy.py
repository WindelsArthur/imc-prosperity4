"""Round-5 strategy.

Generic passive market-making across all 50 products with special-case logic
for the strongest signals discovered in autoresearch (see 11_findings/):

- PEBBLES (5 products): basket-residual aware quoting. The five mid prices
  satisfy sum ≈ 50,000 with std ~3 and half-life ~0.16 ticks, so we skew
  every pebble's quotes toward bringing the basket back to its target.
- SNACKPACK (5 products): same pattern around sum ≈ 50,221 (std ~190).
- Cointegrated pair overlays (slopes calibrated on days 2+3): MICROCHIP
  RECTANGLE/SQUARE, ROBOT LAUNDRY/VACUUMING, SLEEP_POD COTTON/POLYESTER,
  GALAXY DARK_MATTER/PLANETARY_RINGS, etc.
- Generic: inside-spread MM at best_bid+1 / best_ask-1 with inventory skew.

Position limit per product is 10 (enforced via --limit flags on the CLI).
"""
from __future__ import annotations

from typing import Dict, List

from datamodel import OrderDepth, Order, TradingState

POSITION_LIMIT = 10

# ── group taxonomy ─────────────────────────────────────────────────────────

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
UV_VISORS = ["UV_VISOR_AMBER", "UV_VISOR_MAGENTA", "UV_VISOR_ORANGE",
             "UV_VISOR_RED", "UV_VISOR_YELLOW"]

ALL_PRODUCTS = (
    PEBBLES + SNACKPACKS + MICROCHIPS + SLEEP_PODS + ROBOTS
    + GALAXY + OXYGEN + PANELS + TRANSLATORS + UV_VISORS
)

# Calibrated targets / coefficients (from days 2-4 stitched).
PEBBLES_SUM_TARGET = 50000.0
PEBBLES_SUM_SD = 2.8

SNACKPACK_SUM_TARGET = 50221.0
SNACKPACK_SUM_SD = 190.0

# Cointegrated pairs (a, b, slope, intercept, residual_sd) such that
# residual = a - slope*b - intercept; intercept and slope from days 2+3 fit.
COINT_PAIRS = [
    ("MICROCHIP_RECTANGLE", "MICROCHIP_SQUARE", -0.401, 14119.0, 304.0),
    ("ROBOT_LAUNDRY", "ROBOT_VACUUMING", 0.334, 7072.0, 234.0),
    ("SLEEP_POD_COTTON", "SLEEP_POD_POLYESTER", 0.519, 5144.0, 328.0),
    ("GALAXY_SOUNDS_DARK_MATTER", "GALAXY_SOUNDS_PLANETARY_RINGS", 0.183, 8285.0, 283.0),
    ("SNACKPACK_RASPBERRY", "SNACKPACK_VANILLA", 0.013, 9962.0, 161.0),
    ("SNACKPACK_CHOCOLATE", "SNACKPACK_STRAWBERRY", -0.106, 11051.0, 145.0),
    ("UV_VISOR_AMBER", "UV_VISOR_MAGENTA", -1.238, 21897.0, 371.0),
    ("OXYGEN_SHAKE_CHOCOLATE", "OXYGEN_SHAKE_GARLIC", -0.155, 11066.0, 237.0),
    ("TRANSLATOR_ECLIPSE_CHARCOAL", "TRANSLATOR_VOID_BLUE", 0.456, 4954.0, 308.0),
    ("SLEEP_POD_POLYESTER", "SLEEP_POD_SUEDE", 0.756, 2977.0, 426.0),
]


def _mid(od: OrderDepth):
    if not od or not od.buy_orders or not od.sell_orders:
        return None
    return (max(od.buy_orders) + min(od.sell_orders)) / 2.0


def _best_bid_ask(od: OrderDepth):
    bb = max(od.buy_orders) if (od and od.buy_orders) else None
    ba = min(od.sell_orders) if (od and od.sell_orders) else None
    return bb, ba


class Trader:

    def run(self, state: TradingState):
        result: Dict[str, List[Order]] = {}
        ods = state.order_depths
        positions = state.position

        mids: dict = {}
        for p in ALL_PRODUCTS:
            od = ods.get(p)
            if od is None:
                continue
            m = _mid(od)
            if m is not None:
                mids[p] = m

        # PEBBLES basket residual
        pebble_skew: dict = {p: 0.0 for p in PEBBLES}
        if all(p in mids for p in PEBBLES):
            psum = sum(mids[p] for p in PEBBLES)
            resid = psum - PEBBLES_SUM_TARGET
            base = max(-3.0, min(3.0, -resid / 5.0))
            for p in PEBBLES:
                pebble_skew[p] = base

        # SNACKPACK basket residual
        snack_skew: dict = {p: 0.0 for p in SNACKPACKS}
        if all(p in mids for p in SNACKPACKS):
            ssum = sum(mids[p] for p in SNACKPACKS)
            resid = ssum - SNACKPACK_SUM_TARGET
            base = max(-5.0, min(5.0, -resid / 5.0))
            for p in SNACKPACKS:
                snack_skew[p] = base

        # Cointegrated pair overlays
        pair_skew: dict = {}
        for a, b, slope, intercept, sd in COINT_PAIRS:
            if a not in mids or b not in mids:
                continue
            spread_val = mids[a] - slope * mids[b] - intercept
            tilt = max(-3.0, min(3.0, -spread_val / 8.0))
            pair_skew[a] = pair_skew.get(a, 0.0) + tilt
            # Counterpart leg moves opposite direction (with sign of slope).
            pair_skew[b] = pair_skew.get(b, 0.0) - slope * tilt / max(abs(slope), 1.0)

        for p in ALL_PRODUCTS:
            od = ods.get(p)
            if od is None or not od.buy_orders or not od.sell_orders:
                continue
            bb, ba = _best_bid_ask(od)
            if bb is None or ba is None:
                continue
            spread = ba - bb
            if spread < 1:
                continue
            mid = (bb + ba) / 2.0
            pos = positions.get(p, 0)
            buy_cap = POSITION_LIMIT - pos
            sell_cap = POSITION_LIMIT + pos

            skew = pebble_skew.get(p, 0.0) + snack_skew.get(p, 0.0) + pair_skew.get(p, 0.0)
            inv_skew = -pos * 0.2
            fair = mid + skew + inv_skew

            if spread >= 2:
                bid_px = bb + 1
                ask_px = ba - 1
            else:
                bid_px = bb
                ask_px = ba

            orders: List[Order] = []
            buy_left = max(buy_cap, 0)
            sell_left = max(sell_cap, 0)

            big_pos = pebble_skew.get(p, 0.0) >= 1.8 or snack_skew.get(p, 0.0) >= 3.5
            big_neg = pebble_skew.get(p, 0.0) <= -1.8 or snack_skew.get(p, 0.0) <= -3.5

            # Aggressive cross when basket clearly signals (residual >> spread cost)
            if big_pos and buy_left > 0:
                size = min(2, buy_left)
                orders.append(Order(p, ba, size))
                buy_left -= size
            if big_neg and sell_left > 0:
                size = min(2, sell_left)
                orders.append(Order(p, bb, -size))
                sell_left -= size

            # Inside-spread passive quoting
            size_buy = min(8, buy_left)
            size_sell = min(8, sell_left)
            if size_buy > 0 and fair > bid_px - 0.25:
                orders.append(Order(p, int(round(bid_px)), int(size_buy)))
            if size_sell > 0 and fair < ask_px + 0.25:
                orders.append(Order(p, int(round(ask_px)), -int(size_sell)))

            if orders:
                result[p] = orders

        return result, 0, ""
