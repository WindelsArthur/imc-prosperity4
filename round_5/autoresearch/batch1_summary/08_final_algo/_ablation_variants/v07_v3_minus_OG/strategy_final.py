"""Ablation variant v07_v3_minus_OG — generated, do not edit."""
from __future__ import annotations
from typing import Dict, List
from datamodel import OrderDepth, Order, TradingState
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
    DISABLE_PEBBLES, DISABLE_SNACKPACK,
)

def _mid(od):
    if not od or not od.buy_orders or not od.sell_orders: return None
    return (max(od.buy_orders) + min(od.sell_orders))/2.0

def _bba(od):
    bb = max(od.buy_orders) if od and od.buy_orders else None
    ba = min(od.sell_orders) if od and od.sell_orders else None
    return bb,ba

def _cap(p):
    if p == "PEBBLES_L" and PEBBLES_L_CAP is not None:
        return PEBBLES_L_CAP
    return PROD_CAP.get(p, POSITION_LIMIT)

class Trader:
    def __init__(self):
        self._evb_prev_mid = None
    def run(self, state):
        result = {}
        ods = state.order_depths
        positions = state.position
        mids = {}
        for p in ALL_PRODUCTS:
            od = ods.get(p)
            if od is None: continue
            m = _mid(od)
            if m is not None: mids[p] = m
        pebble_skew = {p:0.0 for p in PEBBLES}
        if not DISABLE_PEBBLES and all(p in mids for p in PEBBLES):
            psum = sum(mids[p] for p in PEBBLES)
            r = psum - PEBBLES_SUM_TARGET
            base = max(-PEBBLES_SKEW_CLIP, min(PEBBLES_SKEW_CLIP, -r/PEBBLES_SKEW_DIVISOR))
            for p in PEBBLES: pebble_skew[p] = base
        snack_skew = {p:0.0 for p in SNACKPACKS}
        if not DISABLE_SNACKPACK and all(p in mids for p in SNACKPACKS):
            ssum = sum(mids[p] for p in SNACKPACKS)
            r = ssum - SNACKPACK_SUM_TARGET
            base = max(-SNACKPACK_SKEW_CLIP, min(SNACKPACK_SKEW_CLIP, -r/SNACKPACK_SKEW_DIVISOR))
            for p in SNACKPACKS: snack_skew[p] = base
        pair_skew = {}
        for a,b,sl,ic,_sd in COINT_PAIRS + CROSS_GROUP_PAIRS:
            if a not in mids or b not in mids: continue
            sv = mids[a] - sl*mids[b] - ic
            tilt = max(-PAIR_TILT_CLIP, min(PAIR_TILT_CLIP, -sv/PAIR_TILT_DIVISOR))
            pair_skew[a] = pair_skew.get(a,0.0)+tilt
            pair_skew[b] = pair_skew.get(b,0.0)-sl*tilt/max(abs(sl),1.0)
        ar1_skew = {}
        if ENABLE_AR1_EVB_SKEW:
            evb = "OXYGEN_SHAKE_EVENING_BREATH"
            if evb in mids:
                if self._evb_prev_mid is not None:
                    dmid = mids[evb] - self._evb_prev_mid
                    ar1_skew[evb] = -0.123*dmid*EVB_AR1_ALPHA
                self._evb_prev_mid = mids[evb]
        for p in ALL_PRODUCTS:
            od = ods.get(p)
            if od is None or not od.buy_orders or not od.sell_orders: continue
            bb,ba = _bba(od)
            if bb is None or ba is None: continue
            spread = ba-bb
            if spread < 1: continue
            mid = (bb+ba)/2.0
            cap = _cap(p)
            pos = positions.get(p,0)
            buy_cap = min(POSITION_LIMIT - pos, cap - pos)
            sell_cap = min(POSITION_LIMIT + pos, cap + pos)
            skew = pebble_skew.get(p,0.0)+snack_skew.get(p,0.0)+pair_skew.get(p,0.0)+ar1_skew.get(p,0.0)
            inv_skew = -pos*INV_SKEW_BETA
            fair = mid+skew+inv_skew
            if spread >= 2: bid_px,ask_px = bb+1, ba-1
            else: bid_px,ask_px = bb, ba
            orders = []
            buy_left = max(buy_cap,0)
            sell_left = max(sell_cap,0)
            big_pos = pebble_skew.get(p,0.0) >= PEBBLES_BIG_SKEW or snack_skew.get(p,0.0) >= SNACKPACK_BIG_SKEW
            big_neg = pebble_skew.get(p,0.0) <= -PEBBLES_BIG_SKEW or snack_skew.get(p,0.0) <= -SNACKPACK_BIG_SKEW
            if big_pos and buy_left > 0:
                size = min(QUOTE_AGGRESSIVE_SIZE, buy_left)
                orders.append(Order(p, ba, size)); buy_left -= size
            if big_neg and sell_left > 0:
                size = min(QUOTE_AGGRESSIVE_SIZE, sell_left)
                orders.append(Order(p, bb, -size)); sell_left -= size
            base_size = min(QUOTE_BASE_SIZE_CAP, cap)
            sb = min(base_size, buy_left); ss = min(base_size, sell_left)
            if sb > 0 and fair > bid_px - 0.25:
                orders.append(Order(p, int(round(bid_px)), int(sb)))
            if ss > 0 and fair < ask_px + 0.25:
                orders.append(Order(p, int(round(ask_px)), -int(ss)))
            if orders: result[p] = orders
        return result, 0, ""
