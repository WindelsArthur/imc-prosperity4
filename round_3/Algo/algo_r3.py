from typing import List, Tuple
import json
import math
from datamodel import Order, OrderDepth, TradingState

LIMIT_BOTS = 90

HYDR = "HYDROGEL_PACK"
VELV = "VELVETFRUIT_EXTRACT"
VEVS = [f"VEV_{k}" for k in (4000, 4500, 5000, 5100, 5200, 5300, 5400, 5500, 6000, 6500)]

# Smile-traded VEVs (override generic vwap logic for these)
SMILE_STRIKES = {"VEV_5000": 5000, "VEV_5100": 5100, "VEV_5200": 5200,
                 "VEV_5400": 5400, "VEV_5500": 5500}  # 5300 dropped (smile underprices)
BID_PARAMS = {"a": -0.10885050, "b":  0.02657311, "c": 0.23705958}
ASK_PARAMS = {"a":  0.12353803, "b": -0.02882945, "c": 0.24392969}
SMILE_LIMIT = 300
TTE_START   = 5

# HYDR-specific config (3-stage: profit_takes -> inventory_rebalance -> penny_make)
HYDR_CFG = {
    "skew":           0.25,
    "take_threshold": 1,
    "inv_threshold":  2,
    "mm_threshold":   14,
    "limit":          200,
    "max_make":       8,
}

# VELV + VEVs configs
CONFIG = {
    VELV: {"limit": 200, "skew": 0.0, "thresh": 1.25, "alpha": 0.5, "max_make": 25},
    **{v: {"limit": 300, "skew": 0.0, "thresh": 0.25, "alpha": 0.5, "max_make": 10} for v in VEVS},
}


def vwap(od: OrderDepth) -> float:
    num = sum(p*abs(v) for p,v in od.buy_orders.items()) + \
          sum(p*abs(v) for p,v in od.sell_orders.items())
    den = sum(abs(v) for v in od.buy_orders.values()) + \
          sum(abs(v) for v in od.sell_orders.values())
    return num / den


def fair_split(bids: dict, asks: dict) -> float:
    vw_bid = sum(p * v for p, v in bids.items()) / sum(bids.values())
    vw_ask = sum(p * v for p, v in asks.items()) / sum(asks.values())
    return (vw_bid + vw_ask) / 2


# ── Smile-arb helpers ────────────────────────────────────────────────────────
def _norm_cdf(x): return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))

def bs_call(S, K, T, sigma):
    if sigma <= 0 or T <= 0:
        return max(S - K, 0.0)
    s = sigma * math.sqrt(T)
    d1 = (math.log(S / K) + 0.5 * sigma * sigma * T) / s
    d2 = d1 - s
    return S * _norm_cdf(d1) - K * _norm_cdf(d2)

def smile_iv(p, m): return p["a"] * m * m + p["b"] * m + p["c"]


# ── HYDR helpers ─────────────────────────────────────────────────────────────

def profit_takes(sym, bids, asks, fair, cfg, pos, buy_cap, sell_cap):
    orders = []
    for p in sorted(asks.keys()):
        if fair - p >= cfg["take_threshold"]:
            qty = min(asks[p], buy_cap)
            if qty > 0:
                orders.append(Order(sym, p, qty))
                buy_cap -= qty; pos += qty
                asks[p] -= qty
                if asks[p] == 0: del asks[p]
        else:
            break
    for p in sorted(bids.keys(), reverse=True):
        if p - fair >= cfg["take_threshold"]:
            qty = min(bids[p], sell_cap)
            if qty > 0:
                orders.append(Order(sym, p, -qty))
                sell_cap -= qty; pos -= qty
                bids[p] -= qty
                if bids[p] == 0: del bids[p]
        else:
            break
    return orders, pos, buy_cap, sell_cap


def inventory_rebalance(sym, bids, asks, fair, cfg, pos, buy_cap, sell_cap):
    orders = []
    if pos > 0:
        for p in sorted(bids.keys(), reverse=True):
            if p >= fair - cfg["inv_threshold"]:
                qty = min(bids[p], pos, sell_cap)
                if qty > 0:
                    orders.append(Order(sym, p, -qty))
                    sell_cap -= qty; pos -= qty
                    bids[p] -= qty
                    if bids[p] == 0: del bids[p]
                if pos <= 0: break
            else:
                break
    elif pos < 0:
        for p in sorted(asks.keys()):
            if p <= fair + cfg["inv_threshold"]:
                qty = min(asks[p], -pos, buy_cap)
                if qty > 0:
                    orders.append(Order(sym, p, qty))
                    buy_cap -= qty; pos += qty
                    asks[p] -= qty
                    if asks[p] == 0: del asks[p]
                if pos >= 0: break
            else:
                break
    return orders, pos, buy_cap, sell_cap


def penny_make(sym, bids, asks, sf, cfg, buy_cap, sell_cap):
    if not bids or not asks:
        return []
    best_bid, best_ask = max(bids.keys()), min(asks.keys())
    if best_ask - best_bid <= cfg["mm_threshold"]:
        return []
    mm_bid = min(best_bid + 1, math.floor(sf))
    mm_ask = max(best_ask - 1, math.ceil(sf))
    if mm_bid >= mm_ask:
        return []
    orders = []
    if buy_cap > 0:
        orders.append(Order(sym, mm_bid,  min(cfg["max_make"], buy_cap)))
    if sell_cap > 0:
        orders.append(Order(sym, mm_ask, -min(cfg["max_make"], sell_cap)))
    return orders


class Trader:

    # ── HYDR ────────────────────────────────────────────────────────────────

    def trade_hydr(self, state: TradingState) -> List[Order]:
        od = state.order_depths.get(HYDR)
        if od is None or not od.buy_orders or not od.sell_orders:
            return []
        bids = dict(od.buy_orders)
        asks = {p: -v for p, v in od.sell_orders.items()}
        pos = state.position.get(HYDR, 0)
        cfg = HYDR_CFG

        fair = fair_split(bids, asks)
        sf = fair - cfg["skew"] * pos

        buy_cap = cfg["limit"] - pos
        sell_cap = cfg["limit"] + pos

        takes, pos, buy_cap, sell_cap = profit_takes(HYDR, bids, asks, fair, cfg, pos, buy_cap, sell_cap)
        bal,   pos, buy_cap, sell_cap = inventory_rebalance(HYDR, bids, asks, fair, cfg, pos, buy_cap, sell_cap)
        makes = penny_make(HYDR, bids, asks, sf, cfg, buy_cap, sell_cap)

        return takes + bal + makes

    # ── VELV + VEVs ─────────────────────────────────────────────────────────

    def takes(self, sym: str, od: OrderDepth, sf: float, pos: int, limit: int, thresh: float) -> Tuple[List[Order], int]:
        orders: List[Order] = []
        for ap in sorted(od.sell_orders):
            edge = sf - ap
            if edge >= thresh:
                cap = limit - pos
                v = min(-od.sell_orders[ap], cap)
                if v > 0:
                    orders.append(Order(sym, ap, v))
                    pos += v
            else:
                break
        for bp in sorted(od.buy_orders, reverse=True):
            edge = bp - sf
            if edge >= thresh:
                cap = limit + pos
                v = min(od.buy_orders[bp], cap)
                if v > 0:
                    orders.append(Order(sym, bp, -v))
                    pos -= v
            else:
                break
        return orders, pos

    def clean(self, od: OrderDepth, takes: List[Order]):
        for o in takes:
            if o.quantity > 0:
                od.sell_orders[o.price] = od.sell_orders.get(o.price, 0) + o.quantity
                if od.sell_orders[o.price] >= 0:
                    del od.sell_orders[o.price]
            else:
                od.buy_orders[o.price] = od.buy_orders.get(o.price, 0) + o.quantity
                if od.buy_orders[o.price] <= 0:
                    del od.buy_orders[o.price]

    def makes(self, sym: str, od: OrderDepth, sf: float, rb: int, rs: int, thresh: float) -> List[Order]:
        orders: List[Order] = []
        mb = math.floor(sf - thresh)
        ma = math.ceil(sf + thresh)
        bb = max(od.buy_orders) if od.buy_orders else None
        ba = min(od.sell_orders) if od.sell_orders else None
        if rb > 0:
            bid = min(bb + 1, mb) if bb is not None else math.floor(sf - LIMIT_BOTS)
            orders.append(Order(sym, bid, rb))
        if rs > 0:
            ask = max(ba - 1, ma) if ba is not None else math.ceil(sf + LIMIT_BOTS)
            orders.append(Order(sym, ask, -rs))
        return orders

    def trade(self, sym: str, state: TradingState, ewmas: dict) -> List[Order]:
        if sym not in state.order_depths:
            return []
        od = state.order_depths[sym]
        if not od.buy_orders or not od.sell_orders:
            return []
        cfg = CONFIG[sym]
        pos = state.position.get(sym, 0)
        raw = vwap(od)
        alpha = cfg["alpha"]
        if alpha > 0:
            prev = ewmas.get(sym, raw)
            ewmas[sym] = prev + alpha * (raw - prev)
            fair = ewmas[sym]
        else:
            fair = raw
        if sym == VELV:
            mid_v = (max(od.buy_orders) + min(od.sell_orders)) / 2
            mom = 0
            for tr in (state.market_trades.get(sym) or []):
                if tr.price > mid_v: mom += tr.quantity
                elif tr.price < mid_v: mom -= tr.quantity
            prev_m = ewmas.get("_vmom", 0.0)
            ewmas["_vmom"] = prev_m + 0.07 * (mom - prev_m)
            fair = fair + 0.22 * ewmas["_vmom"]
        sf = fair - cfg["skew"] * pos
        takes, _ = self.takes(sym, od, sf, pos, cfg["limit"], cfg["thresh"])
        self.clean(od, takes)
        bt = sum(o.quantity for o in takes if o.quantity > 0)
        st = sum(-o.quantity for o in takes if o.quantity < 0)
        mk = cfg["max_make"]
        makes = self.makes(sym, od, sf,
                           min(cfg["limit"] - pos - bt, mk),
                           min(cfg["limit"] + pos - st, mk),
                           cfg["thresh"])
        return takes + makes

    # ── Smile bid/ask take + exit (VEV_5000/5100/5200/5400/5500) ────────────

    def trade_smile(self, sym: str, K: int, state: TradingState) -> List[Order]:
        u_od = state.order_depths.get(VELV)
        if u_od is None or not u_od.buy_orders or not u_od.sell_orders:
            return []
        od = state.order_depths.get(sym)
        if od is None or not od.buy_orders or not od.sell_orders:
            return []
        S = vwap(u_od)
        T = max(TTE_START - state.timestamp / 1e6, 0.1) / 365.0
        sqrtT = math.sqrt(T)
        m = math.log(K / S) / sqrtT
        sigma_b = smile_iv(BID_PARAMS, m)
        sigma_a = smile_iv(ASK_PARAMS, m)
        model_bid_px = bs_call(S, K, T, sigma_b)
        model_ask_px = bs_call(S, K, T, sigma_a)

        pos = state.position.get(sym, 0)
        orders: List[Order] = []

        # Symmetric exit — mutate `od` after each fill so subsequent branches see updated depth
        best_bid = max(od.buy_orders)
        best_ask = min(od.sell_orders)
        if pos > 0 and best_bid >= model_bid_px:
            v = min(od.buy_orders[best_bid], pos)
            if v > 0:
                o = Order(sym, best_bid, -v)
                orders.append(o); pos -= v
                self.clean(od, [o])
        elif pos < 0 and best_ask <= model_ask_px:
            v = min(-od.sell_orders[best_ask], -pos)
            if v > 0:
                o = Order(sym, best_ask, v)
                orders.append(o); pos += v
                self.clean(od, [o])

        # Cross-the-smile take (buy side) — re-derive best_ask after exit may have consumed it
        if od.sell_orders:
            best_ask = min(od.sell_orders)
            if best_ask <= model_bid_px:
                v = min(-od.sell_orders[best_ask], SMILE_LIMIT - pos)
                if v > 0:
                    o = Order(sym, best_ask, v)
                    orders.append(o); pos += v
                    self.clean(od, [o])

        # Cross-the-smile take (sell side) — re-derive best_bid after exit may have consumed it
        if od.buy_orders:
            best_bid = max(od.buy_orders)
            if best_bid >= model_ask_px:
                v = min(od.buy_orders[best_bid], SMILE_LIMIT + pos)
                if v > 0:
                    o = Order(sym, best_bid, -v)
                    orders.append(o); pos -= v
                    self.clean(od, [o])

        return orders

    # ── Driver ──────────────────────────────────────────────────────────────

    def run(self, state: TradingState):
        result = {}
        conversions = 0
        ewmas: dict = json.loads(state.traderData) if state.traderData else {}

        hydr_orders = self.trade_hydr(state)
        if hydr_orders:
            result[HYDR] = hydr_orders

        # VELV + non-smile VEVs via vwap-fair logic; smile strikes via trade_smile
        for sym in CONFIG:
            if sym in SMILE_STRIKES:
                orders = self.trade_smile(sym, SMILE_STRIKES[sym], state)
            else:
                orders = self.trade(sym, state, ewmas)
            if orders:
                result[sym] = orders

        trader_data = json.dumps(ewmas)
        return result, conversions, trader_data
