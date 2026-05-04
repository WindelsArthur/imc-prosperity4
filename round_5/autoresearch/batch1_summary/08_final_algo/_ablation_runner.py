"""Phase H ablation harness.

Builds a sequence of strategy_final variants by patching distilled_params,
runs each through prosperity4btest, records (component, total_pnl, sharpe,
max_dd, delta_vs_prev) → ablation.csv.

Each variant is written to a temp file in 08_final_algo/_ablation_variants/
so we keep an audit trail.
"""
from __future__ import annotations
import csv, os, shutil, sys
from pathlib import Path
from typing import Dict
sys.path.insert(0, "ROUND_5/autoresearch")
from utils.backtester import run_backtest

ROOT = Path("/Users/arthurwindels/Documents/08_DEV/Prosperity4/IMC-Prosperity-4-Belmonte")
ALGO_DIR = ROOT / "ROUND_5/batch1_summary/08_final_algo"
VARIANTS_DIR = ALGO_DIR / "_ablation_variants"
VARIANTS_DIR.mkdir(parents=True, exist_ok=True)
OUT_CSV = ALGO_DIR / "ablation.csv"

DAYS = ["5-2","5-3","5-4"]
DATA = "ROUND_5/autoresearch/10_backtesting/data"
EXTRA = ["--match-trades","worse"]

# Each variant: (name, dict of flag overrides). Run additively.
VARIANTS = [
    # baseline 1: pure inside-spread MM with NOTHING (no inv_skew, no caps, no overlays)
    ("v01_mm_only", {
        "INV_SKEW_BETA": 0.0,
        "PROD_CAP_OVERRIDE": {},  # disable caps
        "DISABLE_PEBBLES": True,
        "DISABLE_SNACKPACK": True,
        "DISABLE_PAIRS": True,
    }),
    # +inv_skew
    ("v02_mm_invskew", {
        "INV_SKEW_BETA": 0.20,
        "PROD_CAP_OVERRIDE": {},
        "DISABLE_PEBBLES": True,
        "DISABLE_SNACKPACK": True,
        "DISABLE_PAIRS": True,
    }),
    # +PROD_CAP (9 bleeders)
    ("v03_mm_invskew_caps", {
        "INV_SKEW_BETA": 0.20,
        "DISABLE_PEBBLES": True,
        "DISABLE_SNACKPACK": True,
        "DISABLE_PAIRS": True,
    }),
    # +PEBBLES invariant
    ("v04_mm_caps_pebbles", {
        "INV_SKEW_BETA": 0.20,
        "DISABLE_SNACKPACK": True,
        "DISABLE_PAIRS": True,
    }),
    # +SNACKPACK invariant
    ("v05_mm_caps_pebbles_snack", {
        "INV_SKEW_BETA": 0.20,
        "DISABLE_PAIRS": True,
    }),
    # +9 within-group pairs (OG dropped)
    ("v06_v2_minus_OG", {
        "INV_SKEW_BETA": 0.20,
        "DISABLE_CROSS_PAIRS": True,
    }),
    # +30 cross-group pairs (= our final v3 with OG dropped)
    ("v07_v3_minus_OG", {
        "INV_SKEW_BETA": 0.20,
    }),
    # try PEBBLES_L cap 5
    ("v08_pebL_cap5", {
        "INV_SKEW_BETA": 0.20,
        "PEBBLES_L_CAP": 5,
    }),
    # try PEBBLES_L cap 4
    ("v09_pebL_cap4", {
        "INV_SKEW_BETA": 0.20,
        "PEBBLES_L_CAP": 4,
    }),
    # try PEBBLES_L cap 6
    ("v10_pebL_cap6", {
        "INV_SKEW_BETA": 0.20,
        "PEBBLES_L_CAP": 6,
    }),
    # AR1 EVB skew on top of best (we'll patch best below)
    ("v11_ar1_evb", {
        "INV_SKEW_BETA": 0.20,
        "ENABLE_AR1_EVB_SKEW": True,
    }),
    # restore OG within-group pair (sanity: should match v3 = 733,320)
    ("v12_v3_full_with_OG", {
        "INV_SKEW_BETA": 0.20,
        "RESTORE_OG_PAIR": True,
    }),
]


PARAMS_TEMPLATE = '''"""Distilled params for ablation variant {name}."""
from __future__ import annotations

POSITION_LIMIT = 10
PEBBLES = ["PEBBLES_L","PEBBLES_M","PEBBLES_S","PEBBLES_XL","PEBBLES_XS"]
SNACKPACKS = ["SNACKPACK_CHOCOLATE","SNACKPACK_PISTACHIO","SNACKPACK_RASPBERRY","SNACKPACK_STRAWBERRY","SNACKPACK_VANILLA"]
MICROCHIPS = ["MICROCHIP_CIRCLE","MICROCHIP_OVAL","MICROCHIP_RECTANGLE","MICROCHIP_SQUARE","MICROCHIP_TRIANGLE"]
SLEEP_PODS = ["SLEEP_POD_COTTON","SLEEP_POD_LAMB_WOOL","SLEEP_POD_NYLON","SLEEP_POD_POLYESTER","SLEEP_POD_SUEDE"]
ROBOTS = ["ROBOT_DISHES","ROBOT_IRONING","ROBOT_LAUNDRY","ROBOT_MOPPING","ROBOT_VACUUMING"]
GALAXY = ["GALAXY_SOUNDS_BLACK_HOLES","GALAXY_SOUNDS_DARK_MATTER","GALAXY_SOUNDS_PLANETARY_RINGS","GALAXY_SOUNDS_SOLAR_FLAMES","GALAXY_SOUNDS_SOLAR_WINDS"]
OXYGEN = ["OXYGEN_SHAKE_CHOCOLATE","OXYGEN_SHAKE_EVENING_BREATH","OXYGEN_SHAKE_GARLIC","OXYGEN_SHAKE_MINT","OXYGEN_SHAKE_MORNING_BREATH"]
PANELS = ["PANEL_1X2","PANEL_1X4","PANEL_2X2","PANEL_2X4","PANEL_4X4"]
TRANSLATORS = ["TRANSLATOR_ASTRO_BLACK","TRANSLATOR_ECLIPSE_CHARCOAL","TRANSLATOR_GRAPHITE_MIST","TRANSLATOR_SPACE_GRAY","TRANSLATOR_VOID_BLUE"]
UV_VISORS = ["UV_VISOR_AMBER","UV_VISOR_MAGENTA","UV_VISOR_ORANGE","UV_VISOR_RED","UV_VISOR_YELLOW"]
ALL_PRODUCTS = PEBBLES + SNACKPACKS + MICROCHIPS + SLEEP_PODS + ROBOTS + GALAXY + OXYGEN + PANELS + TRANSLATORS + UV_VISORS

PROD_CAP = {prod_cap}
PEBBLES_SUM_TARGET = 50000.0
SNACKPACK_SUM_TARGET = 50221.0
PEBBLES_SKEW_DIVISOR = 5.0
SNACKPACK_SKEW_DIVISOR = 5.0
PEBBLES_SKEW_CLIP = 3.0
SNACKPACK_SKEW_CLIP = 5.0
PEBBLES_BIG_SKEW = 1.8
SNACKPACK_BIG_SKEW = 3.5

COINT_PAIRS = {coint_pairs}
CROSS_GROUP_PAIRS = {cross_pairs}

PAIR_TILT_DIVISOR = 8.0
PAIR_TILT_CLIP = 3.0
INV_SKEW_BETA = {inv_beta}
QUOTE_BASE_SIZE_CAP = 8
QUOTE_AGGRESSIVE_SIZE = 2

PEBBLES_L_CAP = {peb_l_cap}
ENABLE_AR1_EVB_SKEW = {enable_ar1}
EVB_AR1_ALPHA = 1.5

DISABLE_PEBBLES = {disable_pebbles}
DISABLE_SNACKPACK = {disable_snack}
'''

# canonical pair definitions
WITHIN_PAIRS_NO_OG = [
    ("MICROCHIP_RECTANGLE","MICROCHIP_SQUARE",-0.401,14119.0,304.0),
    ("ROBOT_LAUNDRY","ROBOT_VACUUMING",0.334,7072.0,234.0),
    ("SLEEP_POD_COTTON","SLEEP_POD_POLYESTER",0.519,5144.0,328.0),
    ("GALAXY_SOUNDS_DARK_MATTER","GALAXY_SOUNDS_PLANETARY_RINGS",0.183,8285.0,283.0),
    ("SNACKPACK_RASPBERRY","SNACKPACK_VANILLA",0.013,9962.0,161.0),
    ("SNACKPACK_CHOCOLATE","SNACKPACK_STRAWBERRY",-0.106,11051.0,145.0),
    ("UV_VISOR_AMBER","UV_VISOR_MAGENTA",-1.238,21897.0,371.0),
    ("TRANSLATOR_ECLIPSE_CHARCOAL","TRANSLATOR_VOID_BLUE",0.456,4954.0,308.0),
    ("SLEEP_POD_POLYESTER","SLEEP_POD_SUEDE",0.756,2977.0,426.0),
]
WITHIN_PAIRS_WITH_OG = WITHIN_PAIRS_NO_OG + [
    ("OXYGEN_SHAKE_CHOCOLATE","OXYGEN_SHAKE_GARLIC",-0.155,11066.0,237.0),
]
CROSS_PAIRS_FULL = [
    ("PEBBLES_XL","PANEL_2X4",2.4821,-14735.73,200.0),
    ("UV_VISOR_AMBER","SNACKPACK_STRAWBERRY",-2.4501,34143.94,200.0),
    ("PEBBLES_M","OXYGEN_SHAKE_MORNING_BREATH",-0.9037,19300.55,200.0),
    ("UV_VISOR_YELLOW","GALAXY_SOUNDS_DARK_MATTER",1.5837,-5238.83,200.0),
    ("OXYGEN_SHAKE_GARLIC","PEBBLES_S",-1.0114,20960.00,200.0),
    ("PANEL_2X4","PEBBLES_XL",0.3093,7174.37,200.0),
    ("MICROCHIP_SQUARE","SLEEP_POD_SUEDE",1.8678,-7692.97,200.0),
    ("GALAXY_SOUNDS_BLACK_HOLES","PEBBLES_S",-1.0180,20559.94,200.0),
    ("PEBBLES_S","GALAXY_SOUNDS_BLACK_HOLES",-0.7694,17755.06,200.0),
    ("PEBBLES_S","OXYGEN_SHAKE_GARLIC",-0.7727,18147.25,200.0),
    ("SLEEP_POD_POLYESTER","UV_VISOR_AMBER",-0.9226,19139.77,200.0),
    ("GALAXY_SOUNDS_SOLAR_WINDS","PANEL_1X4",-0.5377,15490.30,200.0),
    ("PEBBLES_S","PANEL_2X4",-1.1018,21344.63,200.0),
    ("ROBOT_IRONING","PEBBLES_M",-0.9154,18096.05,200.0),
    ("PANEL_2X4","OXYGEN_SHAKE_GARLIC",0.5545,4653.12,200.0),
    ("GALAXY_SOUNDS_DARK_MATTER","UV_VISOR_YELLOW",0.3725,6144.99,200.0),
    ("UV_VISOR_AMBER","SLEEP_POD_POLYESTER",-0.9595,19272.87,200.0),
    ("PEBBLES_M","ROBOT_IRONING",-0.7284,16601.80,200.0),
    ("PANEL_2X4","PEBBLES_S",-0.6242,16840.75,200.0),
    ("SNACKPACK_STRAWBERRY","SLEEP_POD_POLYESTER",0.3255,6852.82,200.0),
    ("SNACKPACK_CHOCOLATE","PANEL_2X4",-0.2171,12289.62,200.0),
    ("SLEEP_POD_SUEDE","MICROCHIP_SQUARE",0.4516,5257.75,200.0),
    ("SNACKPACK_STRAWBERRY","UV_VISOR_AMBER",-0.3259,13284.98,200.0),
    ("TRANSLATOR_ECLIPSE_CHARCOAL","SLEEP_POD_LAMB_WOOL",-0.5308,15493.89,200.0),
    ("SNACKPACK_VANILLA","PANEL_1X2",0.1461,8793.78,200.0),
    ("SNACKPACK_VANILLA","PANEL_2X4",0.1490,8418.80,200.0),
    ("SLEEP_POD_LAMB_WOOL","TRANSLATOR_ECLIPSE_CHARCOAL",-0.7159,17727.49,200.0),
    ("SNACKPACK_PISTACHIO","OXYGEN_SHAKE_GARLIC",-0.1488,11269.91,200.0),
    ("SNACKPACK_PISTACHIO","PEBBLES_XS",0.0992,8761.10,200.0),
    ("SNACKPACK_PISTACHIO","MICROCHIP_OVAL",0.0907,8753.81,200.0),
]
PROD_CAP_FULL = {
    "SLEEP_POD_LAMB_WOOL":3,"UV_VISOR_MAGENTA":4,"PANEL_1X2":3,
    "TRANSLATOR_SPACE_GRAY":4,"ROBOT_MOPPING":4,"PANEL_4X4":4,
    "GALAXY_SOUNDS_SOLAR_FLAMES":4,"SNACKPACK_RASPBERRY":5,"SNACKPACK_CHOCOLATE":5,
}

def render_params(opts: Dict, name: str):
    prod_cap = opts.get("PROD_CAP_OVERRIDE", PROD_CAP_FULL)
    if opts.get("DISABLE_PAIRS"):
        coint = []
        cross = []
    else:
        if opts.get("RESTORE_OG_PAIR"):
            coint = WITHIN_PAIRS_WITH_OG
        else:
            coint = WITHIN_PAIRS_NO_OG
        cross = [] if opts.get("DISABLE_CROSS_PAIRS") else CROSS_PAIRS_FULL
    return PARAMS_TEMPLATE.format(
        name=name,
        prod_cap=repr(prod_cap),
        coint_pairs=repr(coint),
        cross_pairs=repr(cross),
        inv_beta=opts.get("INV_SKEW_BETA",0.20),
        peb_l_cap=opts.get("PEBBLES_L_CAP","None"),
        enable_ar1=str(opts.get("ENABLE_AR1_EVB_SKEW",False)),
        disable_pebbles=str(opts.get("DISABLE_PEBBLES",False)),
        disable_snack=str(opts.get("DISABLE_SNACKPACK",False)),
    )

# strategy template — same as strategy_final.py but reads DISABLE_* flags
STRATEGY_TEMPLATE = '''"""Ablation variant {name} — generated, do not edit."""
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
        result = {{}}
        ods = state.order_depths
        positions = state.position
        mids = {{}}
        for p in ALL_PRODUCTS:
            od = ods.get(p)
            if od is None: continue
            m = _mid(od)
            if m is not None: mids[p] = m
        pebble_skew = {{p:0.0 for p in PEBBLES}}
        if not DISABLE_PEBBLES and all(p in mids for p in PEBBLES):
            psum = sum(mids[p] for p in PEBBLES)
            r = psum - PEBBLES_SUM_TARGET
            base = max(-PEBBLES_SKEW_CLIP, min(PEBBLES_SKEW_CLIP, -r/PEBBLES_SKEW_DIVISOR))
            for p in PEBBLES: pebble_skew[p] = base
        snack_skew = {{p:0.0 for p in SNACKPACKS}}
        if not DISABLE_SNACKPACK and all(p in mids for p in SNACKPACKS):
            ssum = sum(mids[p] for p in SNACKPACKS)
            r = ssum - SNACKPACK_SUM_TARGET
            base = max(-SNACKPACK_SKEW_CLIP, min(SNACKPACK_SKEW_CLIP, -r/SNACKPACK_SKEW_DIVISOR))
            for p in SNACKPACKS: snack_skew[p] = base
        pair_skew = {{}}
        for a,b,sl,ic,_sd in COINT_PAIRS + CROSS_GROUP_PAIRS:
            if a not in mids or b not in mids: continue
            sv = mids[a] - sl*mids[b] - ic
            tilt = max(-PAIR_TILT_CLIP, min(PAIR_TILT_CLIP, -sv/PAIR_TILT_DIVISOR))
            pair_skew[a] = pair_skew.get(a,0.0)+tilt
            pair_skew[b] = pair_skew.get(b,0.0)-sl*tilt/max(abs(sl),1.0)
        ar1_skew = {{}}
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
'''

def main():
    rows = []
    prev_pnl = None
    for name, opts in VARIANTS:
        # write variant directory
        vd = VARIANTS_DIR / name
        vd.mkdir(parents=True, exist_ok=True)
        (vd/"distilled_params.py").write_text(render_params(opts, name))
        (vd/"strategy_final.py").write_text(STRATEGY_TEMPLATE.format(name=name))
        # run
        algo_path = vd / "strategy_final.py"
        try:
            res = run_backtest(
                str(algo_path), DAYS,
                data_dir="ROUND_5/autoresearch/10_backtesting/data",
                run_name=f"abl_{name}",
                extra_flags=EXTRA,
            )
        except Exception as e:
            print(f"  {name}: ERROR {e}")
            rows.append({"name":name,"total_pnl":None,"sharpe":None,"max_dd":None,"delta":None,"err":str(e)})
            continue
        delta = (res.total_pnl - prev_pnl) if (res.total_pnl is not None and prev_pnl is not None) else None
        rows.append({
            "name": name,
            "total_pnl": res.total_pnl,
            "sharpe": res.sharpe_ratio,
            "max_dd": res.max_drawdown_abs,
            "delta_vs_prev": delta,
        })
        prev_pnl = res.total_pnl
        print(f"  {name}: pnl={res.total_pnl} sharpe={res.sharpe_ratio} dd={res.max_drawdown_abs} delta={delta}")

    # write csv
    with OUT_CSV.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["name","total_pnl","sharpe","max_dd","delta_vs_prev"])
        w.writeheader()
        for r in rows: w.writerow({k:r.get(k) for k in ["name","total_pnl","sharpe","max_dd","delta_vs_prev"]})
    print(f"DONE: wrote {OUT_CSV}")

if __name__ == "__main__":
    main()
