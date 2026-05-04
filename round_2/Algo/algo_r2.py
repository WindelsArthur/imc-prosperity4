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
M1 = 12   # INT sell premium
M2 = 8    # INT buy premium


class Trader:

    # Round 2 only: Market Access Fee bid. We opt out (top-50% bidders pay
    # their bid against R2 PnL — we already qualified via R1 so we don't pay).
    def bid(self) -> int:
        return 0

    # ─── unified take / clean / make / trade ────────────────────────────────

    def takes(self, prod: str, od: OrderDepth, fair: float, pos: int,
              lim: int, btp: float, stp: float) -> Tuple[List[Order], int]:
        """Cross the spread on mispriced bot quotes.
        btp / stp = additional buy / sell-side premium added to fair."""
        orders: List[Order] = []
        for ap in sorted(od.sell_orders):
            if ap <= math.floor(fair + btp):
                v = min(-od.sell_orders[ap], lim - pos)
                if v > 0:
                    orders.append(Order(prod, ap, v))
                    pos += v
            else:
                break
        for bp in sorted(od.buy_orders, reverse=True):
            if bp >= math.ceil(fair + stp):
                v = min(od.buy_orders[bp], lim + pos)
                if v > 0:
                    orders.append(Order(prod, bp, -v))
                    pos -= v
            else:
                break
        return orders, pos

    def clean(self, od: OrderDepth, takes: List[Order]) -> None:
        """Remove the bot quotes we just took from the local order book so
        the make step sees the post-take state."""
        for o in takes:
            if o.quantity > 0:
                od.sell_orders[o.price] = od.sell_orders.get(o.price, 0) + o.quantity
                if od.sell_orders[o.price] >= 0:
                    del od.sell_orders[o.price]
            else:
                od.buy_orders[o.price] = od.buy_orders.get(o.price, 0) + o.quantity
                if od.buy_orders[o.price] <= 0:
                    del od.buy_orders[o.price]

    def makes(self, prod: str, od: OrderDepth, fair: float,
              rb: int, rs: int, bmp: float, smp: float) -> List[Order]:
        """Post passive resting quotes inside the (post-take) spread.
        bmp / smp = make-side premium for buy / sell quote caps."""
        orders: List[Order] = []
        bb = max(od.buy_orders) if od.buy_orders else None
        ba = min(od.sell_orders) if od.sell_orders else None
        if rb > 0:
            cap = math.floor(fair + bmp)
            bid = min(bb + 1, cap) if bb is not None else cap - LIMIT_BOTS
            orders.append(Order(prod, bid, rb))
        if rs > 0:
            cap = math.ceil(fair + smp)
            ask = max(ba - 1, cap) if ba is not None else cap + LIMIT_BOTS
            orders.append(Order(prod, ask, -rs))
        return orders

    def trade(self, prod: str, state: TradingState, fair: float, lim: int,
              btp: float, stp: float, bmp: float, smp: float) -> List[Order]:
        if prod not in state.order_depths:
            return []
        od = state.order_depths[prod]
        pos = state.position.get(prod, 0)
        takes, _ = self.takes(prod, od, fair, pos, lim, btp, stp)
        self.clean(od, takes)
        bt = sum(o.quantity for o in takes if o.quantity > 0)
        st = sum(-o.quantity for o in takes if o.quantity < 0)
        makes = self.makes(prod, od, fair, lim - pos - bt, lim + pos - st, bmp, smp)
        return takes + makes

    # ─── per-product fair-value helpers ─────────────────────────────────────

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

    def int_fair(self, timestamp: int, od: OrderDepth) -> float:
        all_prices = list(od.buy_orders.keys()) + list(od.sell_orders.keys())
        base = round(all_prices[0] / 1000) * 1000 if all_prices else 12000
        step = timestamp / 100
        return base + round(step * 102.4) / 1024

    # ─── run ────────────────────────────────────────────────────────────────

    def run(self, state: TradingState):
        sd: dict = {}
        if state.traderData:
            try:
                sd = jsonpickle.decode(state.traderData)
            except Exception:
                sd = {}

        result = {}

        # ASH: fair = EMA(microprice); inventory-skewed before quoting; no premium.
        if ASH in state.order_depths:
            pos = state.position.get(ASH, 0)
            fair_ash = self.ash_fair(state.order_depths[ASH], sd) - INV_SKEW * pos
            ash_orders = self.trade(ASH, state, fair_ash, ASH_LIMIT, 0, 0, 0, 0)
            if ash_orders:
                result[ASH] = ash_orders

        # INT: fair = closed-form linear-in-time; asymmetric premiums for long bias.
        if INT in state.order_depths:
            fair_int = self.int_fair(state.timestamp, state.order_depths[INT])
            int_orders = self.trade(INT, state, fair_int, INT_LIMIT, M2, M1, 0, M1)
            if int_orders:
                result[INT] = int_orders

        return result, 0, jsonpickle.encode(sd)
