"""Round-5 strategy v3 — round 3 lag/pairs research output.

Diff vs v2:
- Adds **cross-group cointegration pair overlays** discovered in Phase C of
  round 3 (lag=1 EG cointegration on top-300 price-CCF pairs).
  These are pairs round 1's within-group EG never tested. Each surviving
  pair has min-fold OOS Sharpe ≥ 1.4 across the (d2→d3, d2+3→d4) walk-forward.
- The skew on each leg is computed from the residual of the OLS fit in
  exactly the same way as the existing within-group pair overlays.
- Phase B's lone surviving lead-lag pair (PANEL_1X4→PANEL_1X2 lag=33) is
  optionally added behind a feature flag — it accounts for ≤2K PnL/day so
  it is omitted to keep the strategy pure mean-reversion.

Calibrations are from days 2-4 (training) using the OLS slope/intercept
reported in `14_lag_research/C_lagged_coint/lagged_coint_fast.csv`.
"""
from __future__ import annotations

from typing import Dict, List

from datamodel import OrderDepth, Order, TradingState

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
UV_VISORS = ["UV_VISOR_AMBER", "UV_VISOR_MAGENTA", "UV_VISOR_ORANGE",
             "UV_VISOR_RED", "UV_VISOR_YELLOW"]

ALL_PRODUCTS = (
    PEBBLES + SNACKPACKS + MICROCHIPS + SLEEP_PODS + ROBOTS
    + GALAXY + OXYGEN + PANELS + TRANSLATORS + UV_VISORS
)

PROD_CAP = {
    "SLEEP_POD_LAMB_WOOL": 3,
    "UV_VISOR_MAGENTA": 4,
    "PANEL_1X2": 3,
    "TRANSLATOR_SPACE_GRAY": 4,
    "ROBOT_MOPPING": 4,
    "PANEL_4X4": 4,
    "GALAXY_SOUNDS_SOLAR_FLAMES": 4,
    "SNACKPACK_RASPBERRY": 5,
    "SNACKPACK_CHOCOLATE": 5,
}

PEBBLES_SUM_TARGET = 50000.0
SNACKPACK_SUM_TARGET = 50221.0

# Round-2 within-group cointegration pairs.
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

# Round-3 NEW cross-group cointegration pairs (Phase C, lag=1).
# Format: (a, b, slope, intercept, residual_sd) with residual = a − slope·b − intercept.
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
]


def _mid(od):
    if not od or not od.buy_orders or not od.sell_orders:
        return None
    return (max(od.buy_orders) + min(od.sell_orders)) / 2.0


def _best_bid_ask(od):
    bb = max(od.buy_orders) if (od and od.buy_orders) else None
    ba = min(od.sell_orders) if (od and od.sell_orders) else None
    return bb, ba


def _cap(prod):
    return PROD_CAP.get(prod, POSITION_LIMIT)


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

        # PEBBLES sum-invariant
        pebble_skew = {p: 0.0 for p in PEBBLES}
        if all(p in mids for p in PEBBLES):
            psum = sum(mids[p] for p in PEBBLES)
            resid = psum - PEBBLES_SUM_TARGET
            base = max(-3.0, min(3.0, -resid / 5.0))
            for p in PEBBLES:
                pebble_skew[p] = base

        # SNACKPACK sum-50221 (kept from v2)
        snack_skew = {p: 0.0 for p in SNACKPACKS}
        if all(p in mids for p in SNACKPACKS):
            ssum = sum(mids[p] for p in SNACKPACKS)
            resid = ssum - SNACKPACK_SUM_TARGET
            base = max(-5.0, min(5.0, -resid / 5.0))
            for p in SNACKPACKS:
                snack_skew[p] = base

        # Cointegration pair overlays — both within-group (v2) and cross-group (v3).
        pair_skew: dict = {}
        for a, b, slope, intercept, sd in COINT_PAIRS + CROSS_GROUP_PAIRS:
            if a not in mids or b not in mids:
                continue
            spread_val = mids[a] - slope * mids[b] - intercept
            tilt = max(-3.0, min(3.0, -spread_val / 8.0))
            pair_skew[a] = pair_skew.get(a, 0.0) + tilt
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
            cap = _cap(p)
            pos = positions.get(p, 0)
            buy_cap = min(POSITION_LIMIT - pos, cap - pos)
            sell_cap = min(POSITION_LIMIT + pos, cap + pos)

            skew = (pebble_skew.get(p, 0.0)
                    + snack_skew.get(p, 0.0)
                    + pair_skew.get(p, 0.0))
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

            if big_pos and buy_left > 0:
                size = min(2, buy_left)
                orders.append(Order(p, ba, size))
                buy_left -= size
            if big_neg and sell_left > 0:
                size = min(2, sell_left)
                orders.append(Order(p, bb, -size))
                sell_left -= size

            base_size = min(8, cap)
            size_buy = min(base_size, buy_left)
            size_sell = min(base_size, sell_left)
            if size_buy > 0 and fair > bid_px - 0.25:
                orders.append(Order(p, int(round(bid_px)), int(size_buy)))
            if size_sell > 0 and fair < ask_px + 0.25:
                orders.append(Order(p, int(round(ask_px)), -int(size_sell)))

            if orders:
                result[p] = orders

        return result, 0, ""
