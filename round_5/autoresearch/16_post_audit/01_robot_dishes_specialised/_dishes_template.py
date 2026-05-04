"""Template: ROBOT_DISHES dedicated-handler variant of algo1_drop_harmful_only.py.

Differences vs baseline:
1. ROBOT_DISHES is removed from the global `_pair_skews_all` output (the 4
   PEBBLES_XL→ROBOT_DISHES pairs still contribute to PEBBLES_XL but no longer
   to ROBOT_DISHES).
2. A dedicated `_dishes_skew(mids, td)` function returns a price-space tilt
   built from:
     - AR(1) overlay:   -DISHES_AR1_COEF * Δmid * DISHES_AR1_ALPHA
     - log-pair skew:   sum over 4 novel log-pairs, per-pair clip = DISHES_LOG_CLIP
3. ROBOT_DISHES uses its own inv_skew β = DISHES_INV_BETA (not global 0.20).
4. The `run` method threads `td["pmd"]` (previous mid) through traderData.

PARAMS (replaced by sweep):
  DISHES_AR1_ALPHA   — AR(1) multiplier; 0 disables.
  DISHES_LOG_CLIP    — per-pair clip on the log-pair tilt (price-space dollars).
  DISHES_INV_BETA    — inventory skew β for ROBOT_DISHES alone.
  DISHES_USE_AR1     — bool gate.
  DISHES_USE_LOG     — bool gate.
"""
from typing import List, Dict, Any, Tuple
import json
import math
import jsonpickle
from datamodel import Listing, Observation, Order, OrderDepth, ProsperityEncoder, Symbol, Trade, TradingState


class Logger:
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
# CONSTANTS (unchanged from baseline)
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

PROD_CAP = {
    "SLEEP_POD_LAMB_WOOL": 10,
    "UV_VISOR_MAGENTA": 4,
    "PANEL_1X2": 3,
    "TRANSLATOR_SPACE_GRAY": 4,
    "ROBOT_MOPPING": 2,
    "PANEL_4X4": 4,
    "GALAXY_SOUNDS_SOLAR_FLAMES": 4,
    "SNACKPACK_RASPBERRY": 10,
    "SNACKPACK_CHOCOLATE": 10,
    "PEBBLES_L": 4,
}

PEBBLES_SUM_TARGET = 50000.0
SNACKPACK_SUM_TARGET = 50221.0
PEBBLES_SKEW_DIVISOR = 8.0
SNACKPACK_SKEW_DIVISOR = 5.0
PEBBLES_SKEW_CLIP = 5.0
SNACKPACK_SKEW_CLIP = 3.0
PEBBLES_BIG_SKEW = 3.5
SNACKPACK_BIG_SKEW = 3.5

PAIR_TILT_DIVISOR = 3.0
PAIR_TILT_CLIP = 7.0

INV_SKEW_BETA = 0.2
QUOTE_BASE_SIZE_CAP = 8
QUOTE_AGGRESSIVE_SIZE = 2

# ═══════════════════════════════════════════════════════════════════════════
# DEDICATED ROBOT_DISHES PARAMS  (replaced by sweep)
# ═══════════════════════════════════════════════════════════════════════════
DISHES_AR1_COEF = -0.232          # documented; matches pooled fit -0.232
DISHES_AR1_ALPHA = __AR1_ALPHA__  # 0 → disabled
DISHES_LOG_CLIP = __LOG_CLIP__    # per-pair clip (price-space dollars)
DISHES_INV_BETA = __INV_BETA__
DISHES_USE_AR1 = __USE_AR1__
DISHES_USE_LOG = __USE_LOG__

# 4 truly novel log-space pairs (from log_study Phase 6 ship_list_dedup.csv).
# Stored as (i, j, beta_log, alpha_log) with: residual = log(mid_i) - β log(mid_j) - α.
DISHES_LOG_PAIRS = [
    ("PEBBLES_S",                "ROBOT_DISHES",         -1.424539615179072,  22.21380995919832),
    ("ROBOT_DISHES",             "PANEL_2X4",             0.7852940330682344,  1.885458055632914),
    ("GALAXY_SOUNDS_BLACK_HOLES","ROBOT_DISHES",          1.234892829761178,  -2.0303511860381143),
    ("ROBOT_DISHES",             "SNACKPACK_STRAWBERRY",  1.2191408531743275, -2.100596770515793),
]

# Baseline pair set — unchanged literal (omitted here for brevity in the
# template; the sweep code substitutes the full list at write time).
ALL_PAIRS = []  # overwritten at variant assembly time


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
    if prod in PEBBLES and all(p in mids for p in PEBBLES):
        resid = sum(mids[p] for p in PEBBLES) - PEBBLES_SUM_TARGET
        return _clip(-resid / PEBBLES_SKEW_DIVISOR, -PEBBLES_SKEW_CLIP, PEBBLES_SKEW_CLIP)
    if prod in SNACKPACKS and all(p in mids for p in SNACKPACKS):
        resid = sum(mids[p] for p in SNACKPACKS) - SNACKPACK_SUM_TARGET
        return _clip(-resid / SNACKPACK_SKEW_DIVISOR, -SNACKPACK_SKEW_CLIP, SNACKPACK_SKEW_CLIP)
    return 0.0


def _pair_skews_all(mids: Dict[str, float]) -> Dict[str, float]:
    """Same as baseline EXCEPT: ROBOT_DISHES gets ZERO contribution from any
    global pair (its tilt comes only from the dedicated handler). Other
    products' tilts are unchanged."""
    out: Dict[str, float] = {}
    for a, b, slope, intercept in ALL_PAIRS:
        if a not in mids or b not in mids:
            continue
        spread_val = mids[a] - slope * mids[b] - intercept
        tilt = _clip(-spread_val / PAIR_TILT_DIVISOR, -PAIR_TILT_CLIP, PAIR_TILT_CLIP)
        if a != "ROBOT_DISHES":
            out[a] = out.get(a, 0.0) + tilt
        if b != "ROBOT_DISHES":
            out[b] = out.get(b, 0.0) - slope * tilt / max(abs(slope), 1.0)
    return out


def _is_aggressive(prod: str, basket_skew: float) -> Tuple[bool, bool]:
    if prod in PEBBLES:
        return basket_skew >= PEBBLES_BIG_SKEW, basket_skew <= -PEBBLES_BIG_SKEW
    if prod in SNACKPACKS:
        return basket_skew >= SNACKPACK_BIG_SKEW, basket_skew <= -SNACKPACK_BIG_SKEW
    return False, False


def _dishes_log_pair_skew(mids: Dict[str, float]) -> float:
    """Sum log-pair tilts onto ROBOT_DISHES, in price-space dollars.

    For each pair (i, j, β, α):
      r = log(mid_i) - β log(mid_j) - α   (mean-reverts to 0)
    If ROBOT_DISHES == i:
      ∂r/∂(log p_dishes) = +1 → log_tilt = -r        (price needs to fall)
    If ROBOT_DISHES == j:
      ∂r/∂(log p_dishes) = -β → log_tilt = +sign(β) * r   (price moves with partner)
    Convert to price by multiplying by mid_dishes / divisor; clip per-pair.
    """
    if "ROBOT_DISHES" not in mids:
        return 0.0
    p_d = mids["ROBOT_DISHES"]
    log_p_d = math.log(p_d)
    total = 0.0
    for i, j, beta, alpha in DISHES_LOG_PAIRS:
        if i not in mids or j not in mids:
            continue
        if i == "ROBOT_DISHES":
            log_other = math.log(mids[j])
            log_resid = log_p_d - beta * log_other - alpha
            tilt_log = -log_resid
        else:
            log_other = math.log(mids[i])
            log_resid = log_other - beta * log_p_d - alpha
            sign_b = 1.0 if beta >= 0 else -1.0
            tilt_log = sign_b * log_resid
        # convert log tilt to price-space dollars; reuse PAIR_TILT_DIVISOR for
        # consistency with the global pair tilts, then clip per-pair
        tilt_price = (tilt_log / PAIR_TILT_DIVISOR) * p_d
        total += _clip(tilt_price, -DISHES_LOG_CLIP, DISHES_LOG_CLIP)
    return total


def _dishes_dedicated_skew(mids: Dict[str, float], td: dict) -> float:
    """Total dedicated tilt for ROBOT_DISHES: AR(1) overlay + log-pair skew.

    The AR(1) overlay reads the previous mid from traderData and writes the
    current mid back. If no previous mid is recorded yet (first tick), AR(1)
    skew is 0.
    """
    if "ROBOT_DISHES" not in mids:
        return 0.0
    cur = mids["ROBOT_DISHES"]
    skew = 0.0
    if DISHES_USE_AR1:
        prev = td.get("pmd")
        if prev is not None:
            dmid = cur - prev
            skew += -DISHES_AR1_COEF * dmid * DISHES_AR1_ALPHA
        td["pmd"] = cur
    if DISHES_USE_LOG:
        skew += _dishes_log_pair_skew(mids)
    return skew


def _fair(prod: str, mids: Dict[str, float], pair_skews: Dict[str, float],
          dishes_dedic: float, pos: int) -> Tuple[float, float]:
    """Total fair value = mid + basket_skew + pair_skew + inv_skew (+ dedicated
    for ROBOT_DISHES). Returns (fair, basket_skew_only)."""
    if prod not in mids:
        return None, 0.0
    bsk = _basket_skew(prod, mids)
    psk = pair_skews.get(prod, 0.0)
    if prod == "ROBOT_DISHES":
        beta_inv = DISHES_INV_BETA
        psk = psk + dishes_dedic
    else:
        beta_inv = INV_SKEW_BETA
    inv = -pos * beta_inv
    fair = mids[prod] + bsk + psk + inv
    return fair, bsk


# ═══════════════════════════════════════════════════════════════════════════
# Trader (unchanged from baseline EXCEPT _fair signature)
# ═══════════════════════════════════════════════════════════════════════════
class Trader:

    def takes(self, prod, od, fair, basket_skew, pos, lim, cap):
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

    def trade(self, prod, state, mids, pair_skews, dishes_dedic):
        od = state.order_depths.get(prod)
        if od is None or not od.buy_orders or not od.sell_orders:
            return []

        pos = state.position.get(prod, 0)
        lim = POSITION_LIMIT
        cap = _cap(prod)

        fair, basket_skew = _fair(prod, mids, pair_skews, dishes_dedic, pos)
        if fair is None:
            return []

        take_orders, bought, sold = self.takes(prod, od, fair, basket_skew, pos, lim, cap)
        self.clean_book_after_takes(od, take_orders)
        buy_cap = max(min(lim - pos, cap - pos) - bought, 0)
        sell_cap = max(min(lim + pos, cap + pos) - sold, 0)
        make_orders = self.make(prod, od, fair, buy_cap, sell_cap, pos)
        return take_orders + make_orders

    def run(self, state: TradingState):
        result: Dict[str, List[Order]] = {}
        td = jsonpickle.decode(state.traderData) if state.traderData else {}

        mids = _compute_mids(state)
        pair_skews = _pair_skews_all(mids)
        dishes_dedic = _dishes_dedicated_skew(mids, td)

        for prod in ALL_PRODUCTS:
            orders = self.trade(prod, state, mids, pair_skews, dishes_dedic)
            if orders:
                result[prod] = orders

        trader_data = jsonpickle.encode(td)
        logger.flush(state, result, 0, trader_data)
        return result, 0, trader_data
