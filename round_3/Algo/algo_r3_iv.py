import json
import math
import jsonpickle
from typing import Any, List, Tuple, Optional, Dict
from datamodel import Listing, Observation, Order, OrderDepth, ProsperityEncoder, Symbol, Trade, TradingState


class Logger:
    def __init__(self) -> None:
        self.logs = ""
        self.max_log_length = 3750

    def print(self, *objects: Any, sep: str = " ", end: str = "\n") -> None:
        self.logs += sep.join(map(str, objects)) + end

    def flush(self, state: TradingState, orders: dict[Symbol, list[Order]], conversions: int, trader_data: str) -> None:
        base_length = len(self.to_json([self.compress_state(state, ""), self.compress_orders(orders), conversions, "", ""]))
        max_item_length = (self.max_log_length - base_length) // 3
        print(self.to_json([
            self.compress_state(state, self.truncate(state.traderData, max_item_length)),
            self.compress_orders(orders),
            conversions,
            self.truncate(trader_data, max_item_length),
            self.truncate(self.logs, max_item_length),
        ]))
        self.logs = ""

    def compress_state(self, state: TradingState, trader_data: str) -> list[Any]:
        return [state.timestamp, trader_data, self.compress_listings(state.listings),
                self.compress_order_depths(state.order_depths), self.compress_trades(state.own_trades),
                self.compress_trades(state.market_trades), state.position, self.compress_observations(state.observations)]

    def compress_listings(self, listings: dict[Symbol, Listing]) -> list[list[Any]]:
        return [[l.symbol, l.product, l.denomination] for l in listings.values()]

    def compress_order_depths(self, order_depths: dict[Symbol, OrderDepth]) -> dict[Symbol, list[Any]]:
        return {s: [od.buy_orders, od.sell_orders] for s, od in order_depths.items()}

    def compress_trades(self, trades: dict[Symbol, list[Trade]]) -> list[list[Any]]:
        return [[t.symbol, t.price, t.quantity, t.buyer, t.seller, t.timestamp]
                for arr in trades.values() for t in arr]

    def compress_observations(self, observations: Observation) -> list[Any]:
        conversion_observations = {}
        for product, observation in observations.conversionObservations.items():
            conversion_observations[product] = [observation.bidPrice, observation.askPrice,
                observation.transportFees, observation.exportTariff, observation.importTariff,
                observation.sugarPrice, observation.sunlightIndex]
        return [observations.plainValueObservations, conversion_observations]

    def compress_orders(self, orders: dict[Symbol, list[Order]]) -> list[list[Any]]:
        return [[o.symbol, o.price, o.quantity] for arr in orders.values() for o in arr]

    def to_json(self, value: Any) -> str:
        return json.dumps(value, cls=ProsperityEncoder, separators=(",", ":"))

    def truncate(self, value: str, max_length: int) -> str:
        lo, hi, out = 0, min(len(value), max_length), ""
        while lo <= hi:
            mid = (lo + hi) // 2
            candidate = value[:mid]
            if len(candidate) < len(value): candidate += "..."
            if len(json.dumps(candidate)) <= max_length: out = candidate; lo = mid + 1
            else: hi = mid - 1
        return out


logger = Logger()


# ═══════════════ SELECT VOUCHER TO TRADE ═══════════════
PRODS = ["VEV_5000", "VEV_5100", "VEV_5200", "VEV_5300", "VEV_5400", "VEV_5500"]

# ═══════════════ CONSTANTS ═══════════════
UND        = "VELVETFRUIT_EXTRACT"
POS_LIM    = 300
UND_LIM    = 200

STRIKES: Dict[str, int] = {
    "VEV_4000": 4000, "VEV_4500": 4500, "VEV_5000": 5000,
    "VEV_5100": 5100, "VEV_5200": 5200, "VEV_5300": 5300,
    "VEV_5400": 5400, "VEV_5500": 5500, "VEV_6000": 6000,
    "VEV_6500": 6500,
}

SMILE      = (0.01760, 0.01091, 0.24269)

TTE_START  = 6
DAYS_YEAR  = 365

# Tuned (3-day OOS validated, with per-day seeds + per-day TTE_START)
Z_OPEN    = 1.5
Z_FULL    = 4.0
Z_CLOSE   = 0.5
MIN_FRAC  = 0.40
SIGMA_MIN = 0.10
HL_BIAS   = 500
HL_VOL    = 200

A_BIAS     = 1 - 0.5 ** (1 / HL_BIAS)
A_VOL      = 1 - 0.5 ** (1 / HL_VOL)

# ═══════════════ HEDGING ═══════════════
# Deadband + fractional reduction: never targets Δ=0, only trims when |Δ|>thr.
HEDGE_THR  = 0.0      # |net Δ| (in UND-equivalents) deadband; below → no action
HEDGE_FRAC = 0.0   # fraction of |total Δ| to neutralize when triggered

# END OF DAY 1 SEED
SEEDS = {
    "VEV_4000": (  0.0693,  0.6742),
    "VEV_4500": (  0.0327,  0.4847),
    "VEV_5000": ( -0.0795,  0.6957),
    "VEV_5100": ( -0.6072,  0.5515),
    "VEV_5200": (  0.3232,  0.4945),
    "VEV_5300": (  2.2232,  0.3221),
    "VEV_5400": ( -3.2783,  0.1721),
    "VEV_5500": ( -0.0797,  0.1846),
    "VEV_6000": (  0.4951,  0.0100),
    "VEV_6500": (  0.4993,  0.0100),
}


class Trader:

    # ─── pricing helpers ───
    def vwap(self, od: OrderDepth) -> Optional[float]:
        if not od.buy_orders or not od.sell_orders: return None
        num, den = 0.0, 0
        for p, v in od.buy_orders.items():
            num += p * v;  den += v
        for p, v in od.sell_orders.items():
            num += p * (-v); den += (-v)
        if den <= 0: return None
        return num / den

    def ncdf(self, x: float) -> float:
        return 0.5 * (1 + math.erf(x / math.sqrt(2)))

    def bs_call(self, S: float, K: float, T: float, s: float) -> float:
        if s <= 0 or T <= 0: return max(S - K, 0.0)
        sT = math.sqrt(T)
        d1 = (math.log(S / K) + 0.5 * s * s * T) / (s * sT)
        return S * self.ncdf(d1) - K * self.ncdf(d1 - s * sT)

    def theo(self, S: float, K: float, T: float) -> float:
        m = math.log(K / S) / math.sqrt(T)
        a, b, c = SMILE
        iv = max(a*m*m + b*m + c, 0.01)
        return self.bs_call(S, K, T, iv)

    def tte(self, ts: int) -> float:
        return max(TTE_START - ts / 1e6, 0.1) / DAYS_YEAR

    # ─── NEW: delta helpers (smile-consistent) ───
    def bs_delta(self, S: float, K: float, T: float, s: float) -> float:
        if s <= 0 or T <= 0:
            return 1.0 if S > K else 0.0
        d1 = (math.log(S / K) + 0.5 * s * s * T) / (s * math.sqrt(T))
        return self.ncdf(d1)

    def voucher_delta(self, S: float, K: float, T: float) -> float:
        m = math.log(K / S) / math.sqrt(T)
        a, b, c = SMILE
        iv = max(a*m*m + b*m + c, 0.01)
        return self.bs_delta(S, K, T, iv)

    # ─── EMA update (returns PRIOR values for no look-ahead) ───
    def update_emas(self, sd: dict, prod: str, bias: float) -> Tuple[float, float]:
        eb_seed, evb_seed = SEEDS[prod]
        eb_prev  = sd.get(f"eb_{prod}",  eb_seed)
        evb_prev = sd.get(f"evb_{prod}", evb_seed)
        dev = bias - eb_prev
        sd[f"eb_{prod}"]  = (1 - A_BIAS) * eb_prev  + A_BIAS * bias
        sd[f"evb_{prod}"] = (1 - A_VOL)  * evb_prev + A_VOL  * abs(dev)
        return eb_prev, evb_prev

    # ─── position sizing helper ───
    def target_size(self, z_abs: float) -> int:
        if z_abs <= Z_OPEN:
            return 0
        ramp = min((z_abs - Z_OPEN) / (Z_FULL - Z_OPEN), 1.0)
        frac = MIN_FRAC + (1.0 - MIN_FRAC) * ramp
        return int(POS_LIM * frac)

    # ─── strategy: z-score driven, z-scaled sizing ───
    def vou_orders(self, prod: str, od: OrderDepth, theo: float, eb: float, evb: float, pos: int) -> List[Order]:
        if not od.buy_orders or not od.sell_orders: return []
        bb, ba = max(od.buy_orders), min(od.sell_orders)
        bv, av = od.buy_orders[bb], -od.sell_orders[ba]

        if evb < SIGMA_MIN:
            if pos > 0: return [Order(prod, bb, -min(pos, bv))]
            if pos < 0: return [Order(prod, ba,  min(-pos, av))]
            return []

        z_bid = (bb - theo - eb) / evb
        z_ask = (ba - theo - eb) / evb

        if z_ask < -Z_OPEN:
            target_long = self.target_size(abs(z_ask))
            delta = target_long - pos
            q = min(av, max(0, delta), POS_LIM - pos)
            if q > 0: return [Order(prod, ba, q)]

        if z_bid > Z_OPEN:
            target_short = self.target_size(abs(z_bid))
            delta = target_short + pos
            q = min(bv, max(0, delta), POS_LIM + pos)
            if q > 0: return [Order(prod, bb, -q)]

        if pos > 0 and z_bid > -Z_CLOSE:
            q = min(pos, bv)
            if q > 0: return [Order(prod, bb, -q)]

        if pos < 0 and z_ask < Z_CLOSE:
            q = min(-pos, av)
            if q > 0: return [Order(prod, ba, q)]

        return []

    def trade_vou(self, prod: str, state: TradingState, sd: dict) -> List[Order]:
        if prod not in state.order_depths or UND not in state.order_depths: return []
        S   = self.vwap(state.order_depths[UND])
        mid = self.vwap(state.order_depths[prod])
        if S is None or mid is None: return []

        K  = STRIKES[prod]
        T  = self.tte(state.timestamp)
        th = self.theo(S, K, T)
        bias = mid - th
        eb_prev, evb_prev = self.update_emas(sd, prod, bias)

        pos = state.position.get(prod, 0)
        return self.vou_orders(prod, state.order_depths[prod], th, eb_prev, evb_prev, pos)

    # ─── NEW: smart partial delta hedge ───
    def hedge_orders(self, state: TradingState) -> List[Order]:
        """
        Trims net portfolio delta by HEDGE_FRAC whenever |Δ| > HEDGE_THR.
        Uses *current* (filled) positions only — one-tick lag is intentional:
        if a voucher quote doesn't fill we won't have built a naked UND leg.
        Crosses bid/ask only (consistent with voucher trading), respects UND_LIM.
        """
        if UND not in state.order_depths: return []
        od = state.order_depths[UND]
        if not od.buy_orders or not od.sell_orders: return []
        S = self.vwap(od)
        if S is None: return []
        T = self.tte(state.timestamp)

        # Aggregate Δ from voucher book (smile-consistent BS Δ)
        d_book = 0.0
        for prod, K in STRIKES.items():
            p = state.position.get(prod, 0)
            if p: d_book += p * self.voucher_delta(S, K, T)

        und_pos = state.position.get(UND, 0)
        d_total = d_book + und_pos                       # UND has Δ = 1

        if abs(d_total) <= HEDGE_THR: return []          # inside deadband

        qty = int(HEDGE_FRAC * abs(d_total))
        if qty <= 0: return []

        bb, ba = max(od.buy_orders), min(od.sell_orders)
        bv, av = od.buy_orders[bb], -od.sell_orders[ba]

        if d_total > 0:                                  # net long Δ → sell UND
            q = min(qty, bv, UND_LIM + und_pos)
            if q > 0: return [Order(UND, bb, -q)]
        else:                                            # net short Δ → buy UND
            q = min(qty, av, UND_LIM - und_pos)
            if q > 0: return [Order(UND, ba, q)]
        return []

    def run(self, state: TradingState):
        sd: dict = {}
        if state.traderData:
            try: sd = jsonpickle.decode(state.traderData)
            except Exception: sd = {}

        result = {}
        for prod in PRODS:
            orders = self.trade_vou(prod, state, sd)
            if orders:
                result[prod] = orders

        # NEW: partial delta hedge on UND
        h = self.hedge_orders(state)
        if h: result[UND] = h

        trader_data = jsonpickle.encode(sd)
        logger.flush(state, result, 0, trader_data)
        return result, 0, trader_data