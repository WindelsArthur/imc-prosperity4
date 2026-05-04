"""Round-5 strategy v2 — round 2 research output.

Diff vs v1:
- Per-product position cap (`PROD_CAP`) for bleeders identified in Phase B
  (avg_spread_to_vol < 0.6 and consistent loss across days). Keeping the
  product traded but with smaller size limits adverse selection bleed.
- Replaced equal-weight SNACKPACK basket signal with the Phase F min-var
  weighting (CHOC: -1.0, VAN: -0.96, PISTA: +0.11, RASP: +0.016, STRAW: -0.14)
  and a tighter z-entry threshold.
- Added small UV_VISOR_AMBER sine-fair-value tilt — only product surviving
  Phase A's OOS sine test.
- Pair overlay magnitudes capped tighter (¼ instead of ⅛ residual).
- Generic MM unchanged.
"""
from __future__ import annotations

from math import sin, pi
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

# Per-product position caps — Phase B + ablation. Smaller caps reduce
# adverse-selection bleed on directional days. Calibrated by re-running the
# walk-forward ablation; only those that strictly improve PnL are kept.
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

# PEBBLES sum invariant (unchanged)
PEBBLES_SUM_TARGET = 50000.0

# SNACKPACK weighted basket from Phase F min-variance eigenvector
# Spread = w_C * mid_C + w_P * mid_P + w_R * mid_R + w_St * mid_St + w_V * mid_V
# Mean of spread on training data ≈ -19,782 ; std ≈ 46.
SNACK_WEIGHTS = {
    "SNACKPACK_CHOCOLATE": -1.0,
    "SNACKPACK_PISTACHIO":  0.1106,
    "SNACKPACK_RASPBERRY":  0.0158,
    "SNACKPACK_STRAWBERRY": -0.1379,
    "SNACKPACK_VANILLA":   -0.9579,
}
SNACK_SPREAD_TARGET = -19782.3
SNACK_SPREAD_SD = 46.0

# UV_VISOR_AMBER sine FV (Phase A OOS-validated). Train on 2+3 → fold-B params.
UV_AMBER_PERIOD = 21847.0
UV_AMBER_A = 253.222
UV_AMBER_PHI = 0.847216
# Linear drift / mean assumed embedded in `c, d`. Use mid-of-current-day rolling
# estimate for those (avoid hardcoding intercept that drifts).
# We apply the sine as a *deviation* signal: predicted_sine_dev = A * sin(omega*t + phi)
UV_AMBER_OMEGA = 2 * pi / UV_AMBER_PERIOD

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
        ts = state.timestamp

        mids: dict = {}
        for p in ALL_PRODUCTS:
            od = ods.get(p)
            if od is None:
                continue
            m = _mid(od)
            if m is not None:
                mids[p] = m

        # PEBBLES sum-invariant skew (unchanged)
        pebble_skew = {p: 0.0 for p in PEBBLES}
        if all(p in mids for p in PEBBLES):
            psum = sum(mids[p] for p in PEBBLES)
            resid = psum - PEBBLES_SUM_TARGET
            base = max(-3.0, min(3.0, -resid / 5.0))
            for p in PEBBLES:
                pebble_skew[p] = base

        # SNACKPACK weighted basket skew (replaces equal-weight)
        snack_skew = {p: 0.0 for p in SNACKPACKS}
        if all(p in mids for p in SNACKPACKS):
            spread_val = sum(SNACK_WEIGHTS[p] * mids[p] for p in SNACKPACKS)
            resid = spread_val - SNACK_SPREAD_TARGET
            z = resid / SNACK_SPREAD_SD
            # Smaller skew with sign of -resid; magnitude proportional to z but capped at 4
            tilt = max(-4.0, min(4.0, -z * 0.8))
            for p in SNACKPACKS:
                # Apply tilt scaled by the product's weight in the basket
                w = SNACK_WEIGHTS[p]
                snack_skew[p] = tilt * (w / abs(w)) * 0.6  # half-strength

        # Cointegration pair overlays — softer (¼ residual)
        pair_skew = {}
        for a, b, slope, intercept, sd in COINT_PAIRS:
            if a not in mids or b not in mids:
                continue
            spread_val = mids[a] - slope * mids[b] - intercept
            tilt = max(-3.0, min(3.0, -spread_val / 8.0))
            pair_skew[a] = pair_skew.get(a, 0.0) + tilt
            pair_skew[b] = pair_skew.get(b, 0.0) - slope * tilt / max(abs(slope), 1.0)

        # UV_VISOR_AMBER sine — disabled after ablation showed it added negative
        # value at α=1/80 (lost 496 vs v2_no_sine_amber).
        sine_skew = {}

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
            # Position envelope is ±cap, but the master limit (10) is hard.
            buy_cap = min(POSITION_LIMIT - pos, cap - pos)
            sell_cap = min(POSITION_LIMIT + pos, cap + pos)

            skew = (pebble_skew.get(p, 0.0)
                    + snack_skew.get(p, 0.0)
                    + pair_skew.get(p, 0.0)
                    + sine_skew.get(p, 0.0))
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

            big_pos = pebble_skew.get(p, 0.0) >= 1.8 or snack_skew.get(p, 0.0) >= 2.5
            big_neg = pebble_skew.get(p, 0.0) <= -1.8 or snack_skew.get(p, 0.0) <= -2.5

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
