"""ROUND-5 strategy_final — synthesis of all prior research.

Single-file Trader for prosperity4btest. Builds on strategy_v3 baseline
(733,320 / 3 days / Sharpe 8.34) with:

  • ALL 30 cross-group cointegration pairs (round-3 Phase C) KEPT.
  • 9 of 10 within-group cointegration pairs KEPT — OXYGEN_SHAKE_CHOCOLATE/
    OXYGEN_SHAKE_GARLIC DROPPED (reverify ADF p=0.918 vs claimed 0.030).
  • PEBBLES sum=50,000 invariant skew KEPT (reverified std 2.80).
  • SNACKPACK sum=50,221 invariant skew KEPT (reverified std 189.58).
  • PROD_CAP for 9 bleeders KEPT (round-2 Phase B; +134K v1→v2 delta).
  • inv_skew = −pos × 0.2, inside-spread MM at bb+1/ba-1 KEPT.

Phase H ablation flags live in distilled_params.py:
  PEBBLES_L_CAP, ENABLE_AR1_EVB_SKEW, ENABLE_DROP_OG_PAIR.

Provenance: see ROUND_5/batch1_summary/{02_index, 04_per_product,
06_themes, 07_strategy_design}.

Position-limit pattern: separate buy_left / sell_left counters per tick;
never mutate state.position. No mutation of state.order_depths.
"""
from __future__ import annotations

from typing import Dict, List

from datamodel import OrderDepth, Order, TradingState

# All numeric constants imported from distilled_params (single source of truth).
from distilled_params import (
    POSITION_LIMIT, PEBBLES, SNACKPACKS, ALL_PRODUCTS,
    PROD_CAP, PEBBLES_SUM_TARGET, SNACKPACK_SUM_TARGET,
    PEBBLES_SKEW_DIVISOR, SNACKPACK_SKEW_DIVISOR,
    PEBBLES_SKEW_CLIP, SNACKPACK_SKEW_CLIP,
    PEBBLES_BIG_SKEW, SNACKPACK_BIG_SKEW,
    COINT_PAIRS, CROSS_GROUP_PAIRS,
    PAIR_TILT_DIVISOR, PAIR_TILT_CLIP,
    INV_SKEW_BETA, QUOTE_BASE_SIZE_CAP, QUOTE_AGGRESSIVE_SIZE,
    PEBBLES_L_CAP, ENABLE_AR1_EVB_SKEW, EVB_AR1_ALPHA,
)


def _mid(od: OrderDepth):
    if not od or not od.buy_orders or not od.sell_orders:
        return None
    return (max(od.buy_orders) + min(od.sell_orders)) / 2.0


def _best_bid_ask(od: OrderDepth):
    bb = max(od.buy_orders) if (od and od.buy_orders) else None
    ba = min(od.sell_orders) if (od and od.sell_orders) else None
    return bb, ba


def _cap(prod: str) -> int:
    if prod == "PEBBLES_L" and PEBBLES_L_CAP is not None:
        return PEBBLES_L_CAP
    return PROD_CAP.get(prod, POSITION_LIMIT)


class Trader:
    def __init__(self) -> None:
        self._evb_prev_mid: float | None = None  # for ar_diff signal-skew on EVENING_BREATH

    def run(self, state: TradingState):
        result: Dict[str, List[Order]] = {}
        ods = state.order_depths
        positions = state.position

        # 1) compute mids ───────────────────────────────────────────────
        mids: dict = {}
        for p in ALL_PRODUCTS:
            od = ods.get(p)
            if od is None:
                continue
            m = _mid(od)
            if m is not None:
                mids[p] = m

        # 2) PEBBLES sum-50,000 invariant skew ─────────────────────────
        pebble_skew = {p: 0.0 for p in PEBBLES}
        if all(p in mids for p in PEBBLES):
            psum = sum(mids[p] for p in PEBBLES)
            resid = psum - PEBBLES_SUM_TARGET
            base = max(-PEBBLES_SKEW_CLIP,
                       min(PEBBLES_SKEW_CLIP, -resid / PEBBLES_SKEW_DIVISOR))
            for p in PEBBLES:
                pebble_skew[p] = base

        # 3) SNACKPACK sum-50,221 invariant skew ────────────────────────
        snack_skew = {p: 0.0 for p in SNACKPACKS}
        if all(p in mids for p in SNACKPACKS):
            ssum = sum(mids[p] for p in SNACKPACKS)
            resid = ssum - SNACKPACK_SUM_TARGET
            base = max(-SNACKPACK_SKEW_CLIP,
                       min(SNACKPACK_SKEW_CLIP, -resid / SNACKPACK_SKEW_DIVISOR))
            for p in SNACKPACKS:
                snack_skew[p] = base

        # 4) Cointegration pair overlays (within + cross) ───────────────
        pair_skew: dict = {}
        for a, b, slope, intercept, _sd in COINT_PAIRS + CROSS_GROUP_PAIRS:
            if a not in mids or b not in mids:
                continue
            spread_val = mids[a] - slope * mids[b] - intercept
            tilt = max(-PAIR_TILT_CLIP,
                       min(PAIR_TILT_CLIP, -spread_val / PAIR_TILT_DIVISOR))
            pair_skew[a] = pair_skew.get(a, 0.0) + tilt
            pair_skew[b] = pair_skew.get(b, 0.0) - slope * tilt / max(abs(slope), 1.0)

        # 5) AR(1) signal-skew on OXYGEN_SHAKE_EVENING_BREATH (optional) ─
        ar1_skew: dict = {}
        if ENABLE_AR1_EVB_SKEW:
            evb = "OXYGEN_SHAKE_EVENING_BREATH"
            if evb in mids:
                if self._evb_prev_mid is not None:
                    dmid = mids[evb] - self._evb_prev_mid
                    # AR(1) coef on Δmid is ≈ −0.123 (re-verified). Predict next
                    # Δmid = −0.123·dmid; therefore the skew toward fair value is
                    # −0.123·dmid. With α=1.5 amplifier:
                    ar1_skew[evb] = -0.123 * dmid * EVB_AR1_ALPHA
                self._evb_prev_mid = mids[evb]

        # 6) Per-product order generation ───────────────────────────────
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
                    + pair_skew.get(p, 0.0)
                    + ar1_skew.get(p, 0.0))
            inv_skew = -pos * INV_SKEW_BETA
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

            big_pos = (pebble_skew.get(p, 0.0) >= PEBBLES_BIG_SKEW
                       or snack_skew.get(p, 0.0) >= SNACKPACK_BIG_SKEW)
            big_neg = (pebble_skew.get(p, 0.0) <= -PEBBLES_BIG_SKEW
                       or snack_skew.get(p, 0.0) <= -SNACKPACK_BIG_SKEW)

            if big_pos and buy_left > 0:
                size = min(QUOTE_AGGRESSIVE_SIZE, buy_left)
                orders.append(Order(p, ba, size))
                buy_left -= size
            if big_neg and sell_left > 0:
                size = min(QUOTE_AGGRESSIVE_SIZE, sell_left)
                orders.append(Order(p, bb, -size))
                sell_left -= size

            base_size = min(QUOTE_BASE_SIZE_CAP, cap)
            size_buy = min(base_size, buy_left)
            size_sell = min(base_size, sell_left)
            if size_buy > 0 and fair > bid_px - 0.25:
                orders.append(Order(p, int(round(bid_px)), int(size_buy)))
            if size_sell > 0 and fair < ask_px + 0.25:
                orders.append(Order(p, int(round(ask_px)), -int(size_sell)))

            if orders:
                result[p] = orders

        return result, 0, ""
