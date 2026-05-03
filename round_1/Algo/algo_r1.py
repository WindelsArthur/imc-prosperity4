import math
import jsonpickle
from typing import List, Tuple
from datamodel import OrderDepth, Order, TradingState

LIMIT_BOTS = 95

# ── ASH params ──
ASH = "ASH_COATED_OSMIUM"
ASH_LIMIT = 80
EMA_ALPHA = 0.215
DEFAULT_FAIR = 10000
INV_SKEW = 0.10

# ── INT params ──
INT = "INTARIAN_PEPPER_ROOT"
INT_LIMIT = 80
M1 = 12
M2 = 8


class Trader:

    # ═══════════════ ASH ═══════════════

    def ash_microprice(self, od: OrderDepth) -> float | None:
        if not od.buy_orders or not od.sell_orders:
            return None
        bb = max(od.buy_orders)
        ba = min(od.sell_orders)
        bv = od.buy_orders[bb]
        av = -od.sell_orders[ba]
        if bv + av == 0:
            return (bb + ba) / 2.0
        return (bb * av + ba * bv) / (bv + av)

    def ash_fair(self, od: OrderDepth, sd: dict) -> float:
        mp = self.ash_microprice(od)
        if mp is not None:
            ema = sd.get("ema_fair", mp)
            ema += EMA_ALPHA * (mp - ema)
            sd["ema_fair"] = ema
            return ema
        return sd.get("ema_fair", DEFAULT_FAIR)

    def ash_takes(self, od: OrderDepth, sf: float, pos: int) -> Tuple[List[Order], int]:
        orders: List[Order] = []
        for ap in sorted(od.sell_orders):
            if ap <= math.floor(sf):
                v = min(-od.sell_orders[ap], ASH_LIMIT - pos)
                if v > 0:
                    orders.append(Order(ASH, ap, v))
                    pos += v
            else:
                break
        for bp in sorted(od.buy_orders, reverse=True):
            if bp >= math.ceil(sf):
                v = min(od.buy_orders[bp], ASH_LIMIT + pos)
                if v > 0:
                    orders.append(Order(ASH, bp, -v))
                    pos -= v
            else:
                break
        return orders, pos

    def ash_clean(self, od: OrderDepth, takes: List[Order]):
        for o in takes:
            if o.quantity > 0:
                od.sell_orders[o.price] = od.sell_orders.get(o.price, 0) + o.quantity
                if od.sell_orders[o.price] >= 0:
                    del od.sell_orders[o.price]
            else:
                od.buy_orders[o.price] = od.buy_orders.get(o.price, 0) + o.quantity
                if od.buy_orders[o.price] <= 0:
                    del od.buy_orders[o.price]

    def ash_makes(self, od: OrderDepth, sf: float, rb: int, rs: int) -> List[Order]:
        orders: List[Order] = []
        mb = math.floor(sf)
        ma = math.ceil(sf)
        bb = max(od.buy_orders) if od.buy_orders else None
        ba = min(od.sell_orders) if od.sell_orders else None
        if rb > 0:
            bid = min(bb + 1, mb) if bb is not None else math.floor(sf - LIMIT_BOTS)
            orders.append(Order(ASH, bid, rb))
        if rs > 0:
            ask = max(ba - 1, ma) if ba is not None else math.ceil(sf + LIMIT_BOTS)
            orders.append(Order(ASH, ask, -rs))
        return orders

    def trade_ash(self, state: TradingState, sd: dict) -> List[Order]:
        if ASH not in state.order_depths:
            return []
        od = state.order_depths[ASH]
        pos = state.position.get(ASH, 0)
        fair = self.ash_fair(od, sd)
        sf = fair - INV_SKEW * pos
        takes, _ = self.ash_takes(od, sf, pos)
        self.ash_clean(od, takes)
        bt = sum(o.quantity for o in takes if o.quantity > 0)
        st = sum(-o.quantity for o in takes if o.quantity < 0)
        makes = self.ash_makes(od, sf, ASH_LIMIT - pos - bt, ASH_LIMIT + pos - st)
        return takes + makes

    # ═══════════════ INT ═══════════════

    def int_fair(self, timestamp: int, od: OrderDepth) -> float:
        all_prices = list(od.buy_orders.keys()) + list(od.sell_orders.keys())
        if all_prices:
            base = round(all_prices[0] / 1000) * 1000
        else:
            base = 12000
        step = timestamp / 100
        return base + round(step * 102.4) / 1024

    def int_takes(self, od: OrderDepth, f: float, pos: int) -> Tuple[List[Order], int]:
        orders: List[Order] = []
        for ap, av in sorted(od.sell_orders.items()):
            if ap <= math.floor(f + M2):
                v = min(-av, INT_LIMIT - pos)
                if v > 0:
                    orders.append(Order(INT, ap, v))
                    pos += v
            else:
                break
        for bp, bv in sorted(od.buy_orders.items(), reverse=True):
            if bp >= math.ceil(f + M1):
                v = min(bv, INT_LIMIT + pos)
                if v > 0:
                    orders.append(Order(INT, bp, -v))
                    pos -= v
            else:
                break
        return orders, pos
    
    def int_clean(self, od: OrderDepth, takes: List[Order]):
        for o in takes:
            if o.quantity > 0:
                od.sell_orders[o.price] = od.sell_orders.get(o.price, 0) + o.quantity
                if od.sell_orders[o.price] >= 0:
                    del od.sell_orders[o.price]
            else:
                od.buy_orders[o.price] = od.buy_orders.get(o.price, 0) + o.quantity
                if od.buy_orders[o.price] <= 0:
                    del od.buy_orders[o.price]

    def int_makes(self, od: OrderDepth, f: float, rb: int, rs: int) -> List[Order]:
        orders: List[Order] = []
        bb = max(od.buy_orders) if od.buy_orders else None
        ba = min(od.sell_orders) if od.sell_orders else None
        if rb > 0:
            cap = math.floor(f)
            bid = min(bb + 1, cap) if bb is not None else cap - LIMIT_BOTS
            orders.append(Order(INT, bid, rb))
        if rs > 0:
            cap = math.ceil(f + M1)
            ask = max(ba - 1, cap) if ba is not None else cap + LIMIT_BOTS
            orders.append(Order(INT, ask, -rs))
        return orders

    def trade_int(self, state: TradingState) -> List[Order]:
        if INT not in state.order_depths:
            return []
        od = state.order_depths[INT]
        pos = state.position.get(INT, 0)
        f = self.int_fair(state.timestamp, od)
        takes, _ = self.int_takes(od, f, pos)
        self.int_clean(od, takes)
        bt = sum(o.quantity for o in takes if o.quantity > 0)
        st = sum(o.quantity for o in takes if o.quantity < 0)
        makes = self.int_makes(od, f, INT_LIMIT - pos - bt, INT_LIMIT + pos + st)
        return takes + makes

    # ═══════════════ RUN ═══════════════

    def run(self, state: TradingState):
        sd: dict = {}
        if state.traderData:
            try:
                sd = jsonpickle.decode(state.traderData)
            except Exception:
                sd = {}

        result = {}
        ash_orders = self.trade_ash(state, sd)
        if ash_orders:
            result[ASH] = ash_orders
        int_orders = self.trade_int(state)
        if int_orders:
            result[INT] = int_orders

        return result, 0, jsonpickle.encode(sd)