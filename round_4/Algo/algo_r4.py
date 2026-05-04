from typing import List
import json
import math
from datamodel import Order, OrderDepth, TradingState

TRAIN_OFFSET = 40000
LIMIT_BOTS = 95

CONFIG = {
    "HYDROGEL_PACK":       {"method": "C", "lim": 200, "slope": 0.000445, "intercept": 9984.834, "buy_t": 9.0, "sell_t": 9.0},
    "VELVETFRUIT_EXTRACT": {"method": "A", "lim": 200, "fair": 5250.098, "buy_t": 15.0, "sell_t": 15.0},
    "VEV_4000":            {"method": "A", "lim": 300, "fair": 1250.110, "buy_t": 15.0, "sell_t": 15.0},
    "VEV_4500":            {"method": "A", "lim": 300, "fair": 750.110,  "buy_t": 15.0, "sell_t": 15.0},
    "VEV_5000":            {"method": "A", "lim": 300, "fair": 255.022,  "buy_t": 10.0, "sell_t": 10.0},
    "VEV_5100":            {"method": "A", "lim": 300, "fair": 166.805,  "buy_t": 10.0, "sell_t": 10.0},
    "VEV_5200":            {"method": "F", "lim": 300, "fair": 95.549,   "buy_t": 5.0,  "sell_t": 8.0},
    "VEV_5300":            {"method": "D", "lim": 300, "fair_init": 35.36, "alpha": 0.0003, "buy_t": 5.0, "sell_t": 5.0},
    "VEV_5400":            {"method": "D", "lim": 300, "fair_init": 8.6480, "alpha": 0.0003, "buy_t": 2.0, "sell_t": 2.0},
    "VEV_5500":            {"method": "D", "lim": 300, "fair_init": 2.2325,  "alpha": 0.001, "buy_t": 1.0, "sell_t": 1.0},
    "VEV_6000":            {"method": "Z", "lim": 300},
    "VEV_6500":            {"method": "Z", "lim": 300},
}

MM_ASSETS = {"HYDROGEL_PACK", "VELVETFRUIT_EXTRACT", "VEV_4000"}
MM_SIZE = 10
MM_MIN_SPREAD = 3
MM_POS_GATE = 100


def fair_static(sym, od, tick, ema):
    return CONFIG[sym]["fair"]

def fair_trend(sym, od, tick, ema):
    c = CONFIG[sym]
    return c["slope"] * (TRAIN_OFFSET + tick) + c["intercept"]

def fair_ema(sym, od, tick, ema):
    c = CONFIG[sym]
    mid = 0.5 * (max(od.buy_orders) + min(od.sell_orders))
    prev = ema.get(sym, c["fair_init"])
    new = prev + c["alpha"] * (mid - prev)
    ema[sym] = new
    return new

FAIR_FN = {
    "HYDROGEL_PACK": fair_trend,
    "VELVETFRUIT_EXTRACT": fair_static,
    "VEV_4000": fair_static,
    "VEV_4500": fair_static,
    "VEV_5000": fair_static,
    "VEV_5100": fair_static,
    "VEV_5200": fair_static,
    "VEV_5300": fair_ema,
    "VEV_5400": fair_ema,
    "VEV_5500": fair_ema,
}


class Trader:

    def takes(self, sym, od, fair, buy_t, sell_t, pos, lim):
        orders: List[Order] = []
        bought = 0
        sold = 0
        for ap in sorted(od.sell_orders):
            if ap <= fair - buy_t:
                v = min(-od.sell_orders[ap], lim - pos - bought)
                if v > 0:
                    orders.append(Order(sym, ap, v))
                    bought += v
            else:
                break
        for bp in sorted(od.buy_orders, reverse=True):
            if bp >= fair + sell_t:
                v = min(od.buy_orders[bp], lim + pos - sold)
                if v > 0:
                    orders.append(Order(sym, bp, -v))
                    sold += v
            else:
                break
        return orders

    def trade_zero(self, sym, od, pos, lim):
        orders: List[Order] = []
        buy_cap = lim - pos
        if buy_cap > 0:
            orders.append(Order(sym, 0, buy_cap))
        sell_cap = min(lim + pos, 10)
        if sell_cap > 0:
            orders.append(Order(sym, 1, -sell_cap))
        return orders

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

    def make(self, sym, fair, od, buy_cap, sell_cap, pos):
        if sym not in MM_ASSETS or abs(pos) >= MM_POS_GATE:
            return []
        if not od.buy_orders or not od.sell_orders:
            return []
        bb = max(od.buy_orders) if od.buy_orders else max(0, math.floor(fair - LIMIT_BOTS))
        ba = min(od.sell_orders) if od.sell_orders else math.ceil(fair + LIMIT_BOTS)
        mb = math.floor(fair - 1)
        ma = math.ceil(fair + 1)
        if ba - bb < MM_MIN_SPREAD:
            return []

        orders: List[Order] = []
        if buy_cap > 0:
            bid = min(bb + 1, mb)
            orders.append(Order(sym, bid, min(MM_SIZE, buy_cap)))
        if sell_cap > 0:
            ask = max(ba - 1, ma)
            orders.append(Order(sym, ask, -min(MM_SIZE, sell_cap)))
        return orders

    def trade(self, sym, state, tick, ema):
        if sym not in state.order_depths:
            return []
        od = state.order_depths[sym]
        if not od.buy_orders or not od.sell_orders:
            return []
        cfg = CONFIG[sym]
        pos = state.position.get(sym, 0)

        if cfg["method"] == "Z":
            return self.trade_zero(sym, od, pos, cfg["lim"])

        fair = FAIR_FN[sym](sym, od, tick, ema)
        takes = self.takes(sym, od, fair, cfg["buy_t"], cfg["sell_t"], pos, cfg["lim"])
        self.clean_book_after_takes(od, takes)
        bt = sum(o.quantity for o in takes if o.quantity > 0)
        st = sum(-o.quantity for o in takes if o.quantity < 0)
        buy_cap = cfg["lim"] - pos - bt
        sell_cap = cfg["lim"] + pos - st
        makes = self.make(sym, fair, od, buy_cap, sell_cap, pos)
        return takes + makes

    def run(self, state: TradingState):
        result = {}
        td = json.loads(state.traderData) if state.traderData else {}
        tick = td.get("tick", 0)
        ema = td.get("ema", {})
        for sym in CONFIG:
            orders = self.trade(sym, state, tick, ema)
            if orders:
                result[sym] = orders
        td["tick"] = tick + 1
        td["ema"] = ema
        return result, 0, json.dumps(td)
