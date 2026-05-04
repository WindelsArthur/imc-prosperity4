from typing import List, Dict, Any, Tuple
import json
import math
import jsonpickle
from datamodel import Listing, Observation, Order, OrderDepth, ProsperityEncoder, Symbol, Trade, TradingState


class Logger:
    # ... unchanged, keep your existing Logger class ...
    def __init__(self) -> None:
        self.logs = ""
        self.max_log_length = 3750
    def print(self, *objects, sep=" ", end="\n"):
        self.logs += sep.join(map(str, objects)) + end
    def flush(self, state, orders, conversions, trader_data):
        base_length = len(self.to_json([self.compress_state(state, ""), self.compress_orders(orders), conversions, "", ""]))
        max_item_length = (self.max_log_length - base_length) // 3
        print(self.to_json([
            self.compress_state(state, self.truncate(state.traderData, max_item_length)),
            self.compress_orders(orders), conversions,
            self.truncate(trader_data, max_item_length),
            self.truncate(self.logs, max_item_length),
        ]))
        self.logs = ""
    def compress_state(self, state, trader_data):
        return [state.timestamp, trader_data,
                self.compress_listings(state.listings),
                self.compress_order_depths(state.order_depths),
                self.compress_trades(state.own_trades),
                self.compress_trades(state.market_trades),
                state.position,
                self.compress_observations(state.observations)]
    def compress_listings(self, listings):
        return [[l.symbol, l.product, l.denomination] for l in listings.values()]
    def compress_order_depths(self, ods):
        return {s: [o.buy_orders, o.sell_orders] for s, o in ods.items()}
    def compress_trades(self, trades):
        return [[t.symbol, t.price, t.quantity, t.buyer, t.seller, t.timestamp]
                for arr in trades.values() for t in arr]
    def compress_observations(self, obs):
        co = {p: [o.bidPrice, o.askPrice, o.transportFees, o.exportTariff, o.importTariff, o.sugarPrice, o.sunlightIndex]
              for p, o in obs.conversionObservations.items()}
        return [obs.plainValueObservations, co]
    def compress_orders(self, orders):
        return [[o.symbol, o.price, o.quantity] for arr in orders.values() for o in arr]
    def to_json(self, value):
        return json.dumps(value, cls=ProsperityEncoder, separators=(",", ":"))
    def truncate(self, value, max_length):
        lo, hi = 0, min(len(value), max_length)
        out = ""
        while lo <= hi:
            mid = (lo + hi) // 2
            cand = value[:mid]
            if len(cand) < len(value):
                cand += "..."
            if len(json.dumps(cand)) <= max_length:
                out = cand
                lo = mid + 1
            else:
                hi = mid - 1
        return out

logger = Logger()


# ═══════════════════════════════════════════════════════════════════════════
# CONSTANTS 
# ═══════════════════════════════════════════════════════════════════════════
POSITION_LIMIT = 10

PEBBLES = ["PEBBLES_L", "PEBBLES_M", "PEBBLES_S", "PEBBLES_XL", "PEBBLES_XS"]
SNACKPACKS = ["SNACKPACK_CHOCOLATE", "SNACKPACK_PISTACHIO",
              "SNACKPACK_RASPBERRY", "SNACKPACK_STRAWBERRY", "SNACKPACK_VANILLA"]
MICROCHIPS = ["MICROCHIP_CIRCLE", "MICROCHIP_OVAL", "MICROCHIP_RECTANGLE",
              "MICROCHIP_SQUARE", "MICROCHIP_TRIANGLE"]
SLEEP_PODS = ["SLEEP_POD_COTTON", "SLEEP_POD_LAMB_WOOL", "SLEEP_POD_NYLON",
              "SLEEP_POD_POLYESTER", "SLEEP_POD_SUEDE"]
ROBOTS = ["ROBOT_DISHES", "ROBOT_IRONING", "ROBOT_LAUNDRY",
          "ROBOT_MOPPING", "ROBOT_VACUUMING"]
GALAXY = ["GALAXY_SOUNDS_BLACK_HOLES", "GALAXY_SOUNDS_DARK_MATTER",
          "GALAXY_SOUNDS_PLANETARY_RINGS", "GALAXY_SOUNDS_SOLAR_FLAMES",
          "GALAXY_SOUNDS_SOLAR_WINDS"]
OXYGEN = ["OXYGEN_SHAKE_CHOCOLATE", "OXYGEN_SHAKE_EVENING_BREATH",
          "OXYGEN_SHAKE_GARLIC", "OXYGEN_SHAKE_MINT", "OXYGEN_SHAKE_MORNING_BREATH"]
PANELS = ["PANEL_1X2", "PANEL_1X4", "PANEL_2X2", "PANEL_2X4", "PANEL_4X4"]
TRANSLATORS = ["TRANSLATOR_ASTRO_BLACK", "TRANSLATOR_ECLIPSE_CHARCOAL",
               "TRANSLATOR_GRAPHITE_MIST", "TRANSLATOR_SPACE_GRAY", "TRANSLATOR_VOID_BLUE"]
UV_VISORS = ["UV_VISOR_AMBER", "UV_VISOR_MAGENTA", "UV_VISOR_ORANGE",
             "UV_VISOR_RED", "UV_VISOR_YELLOW"]

ALL_PRODUCTS = (PEBBLES + SNACKPACKS + MICROCHIPS + SLEEP_PODS + ROBOTS
                + GALAXY + OXYGEN + PANELS + TRANSLATORS + UV_VISORS)

# Per-product stricter caps (round-2 Phase B bleeders + Phase H PEBBLES_L).
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
    "PEBBLES_L":           4,
}

# Basket invariants.
PEBBLES_SUM_TARGET = 50000.0
SNACKPACK_SUM_TARGET = 50221.0
PEBBLES_SKEW_DIVISOR = 5.0
SNACKPACK_SKEW_DIVISOR = 5.0
PEBBLES_SKEW_CLIP = 3.0
SNACKPACK_SKEW_CLIP = 5.0
PEBBLES_BIG_SKEW = 1.8
SNACKPACK_BIG_SKEW = 3.5

# Cointegration pair tilt
PAIR_TILT_DIVISOR = 3.0  
PAIR_TILT_CLIP    = 7.0

# Inventory + sizing.
INV_SKEW_BETA = 0.20
QUOTE_BASE_SIZE_CAP = 8
QUOTE_AGGRESSIVE_SIZE = 2

# 9 within-group cointegration pairs
COINT_PAIRS = [
    ("MICROCHIP_RECTANGLE", "MICROCHIP_SQUARE", -0.401, 14119.0),
    ("ROBOT_LAUNDRY", "ROBOT_VACUUMING", 0.334, 7072.0),
    ("SLEEP_POD_COTTON", "SLEEP_POD_POLYESTER", 0.519, 5144.0),
    ("GALAXY_SOUNDS_DARK_MATTER", "GALAXY_SOUNDS_PLANETARY_RINGS", 0.183, 8285.0),
    ("SNACKPACK_RASPBERRY", "SNACKPACK_VANILLA", 0.013, 9962.0),
    ("SNACKPACK_CHOCOLATE", "SNACKPACK_STRAWBERRY", -0.106, 11051.0),
    ("UV_VISOR_AMBER", "UV_VISOR_MAGENTA", -1.238, 21897.0),
    ("TRANSLATOR_ECLIPSE_CHARCOAL", "TRANSLATOR_VOID_BLUE", 0.456, 4954.0),
    ("SLEEP_POD_POLYESTER", "SLEEP_POD_SUEDE", 0.756, 2977.0),
]

# 30 cross-group cointegration pairs
CROSS_GROUP_PAIRS = [
    ("PEBBLES_XL", "PANEL_2X4", 2.4821, -14735.73),
    ("UV_VISOR_AMBER", "SNACKPACK_STRAWBERRY", -2.4501, 34143.94),
    ("PEBBLES_M", "OXYGEN_SHAKE_MORNING_BREATH", -0.9037, 19300.55),
    ("UV_VISOR_YELLOW", "GALAXY_SOUNDS_DARK_MATTER", 1.5837, -5238.83),
    ("OXYGEN_SHAKE_GARLIC", "PEBBLES_S", -1.0114, 20960.00),
    ("PANEL_2X4", "PEBBLES_XL", 0.3093, 7174.37),
    ("MICROCHIP_SQUARE", "SLEEP_POD_SUEDE", 1.8678, -7692.97),
    ("GALAXY_SOUNDS_BLACK_HOLES", "PEBBLES_S", -1.0180, 20559.94),
    ("PEBBLES_S", "GALAXY_SOUNDS_BLACK_HOLES", -0.7694, 17755.06),
    ("PEBBLES_S", "OXYGEN_SHAKE_GARLIC", -0.7727, 18147.25),
    ("SLEEP_POD_POLYESTER", "UV_VISOR_AMBER", -0.9226, 19139.77),
    ("GALAXY_SOUNDS_SOLAR_WINDS", "PANEL_1X4", -0.5377, 15490.30),
    ("PEBBLES_S", "PANEL_2X4", -1.1018, 21344.63),
    ("ROBOT_IRONING", "PEBBLES_M", -0.9154, 18096.05),
    ("PANEL_2X4", "OXYGEN_SHAKE_GARLIC", 0.5545, 4653.12),
    ("GALAXY_SOUNDS_DARK_MATTER", "UV_VISOR_YELLOW", 0.3725, 6144.99),
    ("UV_VISOR_AMBER", "SLEEP_POD_POLYESTER", -0.9595, 19272.87),
    ("PEBBLES_M", "ROBOT_IRONING", -0.7284, 16601.80),
    ("PANEL_2X4", "PEBBLES_S", -0.6242, 16840.75),
    ("SNACKPACK_STRAWBERRY", "SLEEP_POD_POLYESTER", 0.3255, 6852.82),
    ("SNACKPACK_CHOCOLATE", "PANEL_2X4", -0.2171, 12289.62),
    ("SLEEP_POD_SUEDE", "MICROCHIP_SQUARE", 0.4516, 5257.75),
    ("SNACKPACK_STRAWBERRY", "UV_VISOR_AMBER", -0.3259, 13284.98),
    ("TRANSLATOR_ECLIPSE_CHARCOAL", "SLEEP_POD_LAMB_WOOL", -0.5308, 15493.89),
    ("SNACKPACK_VANILLA", "PANEL_1X2", 0.1461, 8793.78),
    ("SNACKPACK_VANILLA", "PANEL_2X4", 0.1490, 8418.80),
    ("SLEEP_POD_LAMB_WOOL", "TRANSLATOR_ECLIPSE_CHARCOAL", -0.7159, 17727.49),
    ("SNACKPACK_PISTACHIO", "OXYGEN_SHAKE_GARLIC", -0.1488, 11269.91),
    ("SNACKPACK_PISTACHIO", "PEBBLES_XS", 0.0992, 8761.10),
    ("SNACKPACK_PISTACHIO", "MICROCHIP_OVAL", 0.0907, 8753.81),
]

ALL_PAIRS = COINT_PAIRS + CROSS_GROUP_PAIRS


# ═══════════════════════════════════════════════════════════════════════════
# HELPERS 
# ═══════════════════════════════════════════════════════════════════════════
def _mid(od: OrderDepth):
    if not od or not od.buy_orders or not od.sell_orders:
        return None
    return (max(od.buy_orders) + min(od.sell_orders)) / 2.0


def _best_bid_ask(od: OrderDepth):
    bb = max(od.buy_orders) if (od and od.buy_orders) else None
    ba = min(od.sell_orders) if (od and od.sell_orders) else None
    return bb, ba


def _cap(prod: str) -> int:
    return PROD_CAP.get(prod, POSITION_LIMIT)


def _clip(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def _compute_mids(state: TradingState) -> Dict[str, float]:
    mids = {}
    for p in ALL_PRODUCTS:
        m = _mid(state.order_depths.get(p))
        if m is not None:
            mids[p] = m
    return mids


def _basket_skew(prod: str, mids: Dict[str, float]) -> float:
    """PEBBLES Σ=50,000 and SNACKPACK Σ=50,221 invariant skew."""
    if prod in PEBBLES and all(p in mids for p in PEBBLES):
        resid = sum(mids[p] for p in PEBBLES) - PEBBLES_SUM_TARGET
        return _clip(-resid / PEBBLES_SKEW_DIVISOR, -PEBBLES_SKEW_CLIP, PEBBLES_SKEW_CLIP)
    if prod in SNACKPACKS and all(p in mids for p in SNACKPACKS):
        resid = sum(mids[p] for p in SNACKPACKS) - SNACKPACK_SUM_TARGET
        return _clip(-resid / SNACKPACK_SKEW_DIVISOR, -SNACKPACK_SKEW_CLIP, SNACKPACK_SKEW_CLIP)
    return 0.0


def _pair_skews_all(mids: Dict[str, float]) -> Dict[str, float]:
    """Sum cointegration tilts across all pairs into per-product skew."""
    out: Dict[str, float] = {}
    for a, b, slope, intercept in ALL_PAIRS:
        if a not in mids or b not in mids:
            continue
        spread_val = mids[a] - slope * mids[b] - intercept
        tilt = _clip(-spread_val / PAIR_TILT_DIVISOR, -PAIR_TILT_CLIP, PAIR_TILT_CLIP)
        out[a] = out.get(a, 0.0) + tilt
        out[b] = out.get(b, 0.0) - slope * tilt / max(abs(slope), 1.0)
    return out


def _is_aggressive(prod: str, basket_skew: float) -> Tuple[bool, bool]:
    """Big-cross flags: (long_aggressive, short_aggressive) on basket residual size."""
    if prod in PEBBLES:
        return basket_skew >= PEBBLES_BIG_SKEW, basket_skew <= -PEBBLES_BIG_SKEW
    if prod in SNACKPACKS:
        return basket_skew >= SNACKPACK_BIG_SKEW, basket_skew <= -SNACKPACK_BIG_SKEW
    return False, False


def _fair(prod: str, mids: Dict[str, float], pair_skews: Dict[str, float], pos: int) -> Tuple[float, float]:
    """Total fair value = mid + basket_skew + pair_skew + inv_skew.
    Returns (fair, basket_skew_only) so trade() can decide aggressive crossing."""
    if prod not in mids:
        return None, 0.0
    bsk = _basket_skew(prod, mids)
    psk = pair_skews.get(prod, 0.0)
    inv = -pos * INV_SKEW_BETA
    fair = mids[prod] + bsk + psk + inv
    return fair, bsk


# ═══════════════════════════════════════════════════════════════════════════
# Trader 
# ═══════════════════════════════════════════════════════════════════════════
class Trader:

    def takes(self, prod, od, fair, basket_skew, pos, lim, cap):
        """Aggressive crossing only when basket invariant is far. Returns
        (take_orders, bought, sold) — bought/sold consume cap inside trade()."""
        orders: List[Order] = []
        bought = 0
        sold = 0
        big_long, big_short = _is_aggressive(prod, basket_skew)
        bb, ba = _best_bid_ask(od)
        if bb is None or ba is None:
            return orders, bought, sold

        buy_left = min(lim - pos, cap - pos)
        sell_left = min(lim + pos, cap + pos)

        if big_long and buy_left > 0:
            size = min(QUOTE_AGGRESSIVE_SIZE, buy_left)
            orders.append(Order(prod, ba, size))
            bought += size
        if big_short and sell_left > 0:
            size = min(QUOTE_AGGRESSIVE_SIZE, sell_left)
            orders.append(Order(prod, bb, -size))
            sold += size
        return orders, bought, sold
    
    def clean_book_after_takes(self, od: OrderDepth, takes: List[Order]):
        for o in takes:
            if o.quantity > 0:  
                od.sell_orders[o.price] = od.sell_orders.get(o.price, 0) + o.quantity
                if od.sell_orders[o.price] >= 0:
                    del od.sell_orders[o.price]
            else:
                od.buy_orders[o.price] = od.buy_orders.get(o.price, 0) + o.quantity
                if od.buy_orders[o.price] <= 0:
                    del od.buy_orders[o.price]

    def make(self, prod, od, fair, buy_cap, sell_cap, pos):
        """Passive quotes inside the spread, gated on fair sanity."""
        bb, ba = _best_bid_ask(od)
        if bb is None or ba is None or ba - bb < 1:
            return []

        inside = ba - bb >= 2
        bid_px = bb + 1 if inside else bb
        ask_px = ba - 1 if inside else ba

        size_buy  = min(QUOTE_BASE_SIZE_CAP, max(buy_cap,  0))
        size_sell = min(QUOTE_BASE_SIZE_CAP, max(sell_cap, 0))

        orders = []
        if size_buy  and fair > bid_px - 0.25: orders.append(Order(prod, bid_px, size_buy))
        if size_sell and fair < ask_px + 0.25: orders.append(Order(prod, ask_px, -size_sell))
        return orders

    def trade(self, prod, state, mids, pair_skews):
        od = state.order_depths.get(prod)
        if od is None or not od.buy_orders or not od.sell_orders:
            return []

        pos = state.position.get(prod, 0)
        lim = POSITION_LIMIT
        cap = _cap(prod)

        fair, basket_skew = _fair(prod, mids, pair_skews, pos)
        if fair is None:
            return []

        # takes (aggressive cross on big basket residual)
        take_orders, bought, sold = self.takes(prod, od, fair, basket_skew, pos, lim, cap)

        # clean book so make() can see updated best bid/ask and avoid self-crossing
        self.clean_book_after_takes(od, take_orders)
        
        # make (passive inside-spread, accounting for whatever takes consumed)
        buy_cap = max(min(lim - pos, cap - pos) - bought, 0)
        sell_cap = max(min(lim + pos, cap + pos) - sold, 0)
        make_orders = self.make(prod, od, fair, buy_cap, sell_cap, pos)

        return take_orders + make_orders

    def run(self, state: TradingState):
        result: Dict[str, List[Order]] = {}
        td = jsonpickle.decode(state.traderData) if state.traderData else {}

        # Compute per-tick state ONCE for all products.
        mids = _compute_mids(state)
        pair_skews = _pair_skews_all(mids)

        for prod in ALL_PRODUCTS:
            orders = self.trade(prod, state, mids, pair_skews)
            if orders:
                result[prod] = orders

        trader_data = jsonpickle.encode(td)
        logger.flush(state, result, 0, trader_data)
        return result, 0, trader_data