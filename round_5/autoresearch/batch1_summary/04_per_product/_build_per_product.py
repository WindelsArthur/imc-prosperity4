"""Build per-product markdown files from cards + reverified stats.

For each of 50 products:
- Top contributing findings (with citations).
- v3 PnL contribution (from strategy_v3_all.csv).
- Microstructure stats (spread, lattice, AR(1)).
- Cointegration overlays where this product is a leg.
- Final decision with 2 alternatives.
"""
from __future__ import annotations
import json, os, re
from pathlib import Path
from collections import defaultdict
import pandas as pd

ROOT = Path("/Users/arthurwindels/Documents/08_DEV/Prosperity4/IMC-Prosperity-4-Belmonte")
CARDS_DIR = ROOT / "ROUND_5/batch1_summary/01_cards"
INDEX = ROOT / "ROUND_5/batch1_summary/02_index/findings_index.jsonl"
OUT_DIR = ROOT / "ROUND_5/batch1_summary/04_per_product"
OUT_DIR.mkdir(exist_ok=True)
REVER = ROOT / "ROUND_5/batch1_summary/03_reconciliation/reverify_results/stats_reverify.csv"
V3_PER_PRODUCT = ROOT / "ROUND_5/autoresearch/12_final_strategy/pnl_estimates.md"
V3_FULL = ROOT / "ROUND_5/autoresearch/10_backtesting/results/v3_full_worse.csv"
MR_V6 = ROOT / "ROUND_5/autoresearch/mr_study/04_combined_search/v6_final_metrics.json"

PRODUCTS = [
    "GALAXY_SOUNDS_BLACK_HOLES","GALAXY_SOUNDS_DARK_MATTER","GALAXY_SOUNDS_PLANETARY_RINGS",
    "GALAXY_SOUNDS_SOLAR_FLAMES","GALAXY_SOUNDS_SOLAR_WINDS",
    "MICROCHIP_CIRCLE","MICROCHIP_OVAL","MICROCHIP_RECTANGLE","MICROCHIP_SQUARE","MICROCHIP_TRIANGLE",
    "OXYGEN_SHAKE_CHOCOLATE","OXYGEN_SHAKE_EVENING_BREATH","OXYGEN_SHAKE_GARLIC","OXYGEN_SHAKE_MINT",
    "OXYGEN_SHAKE_MORNING_BREATH",
    "PANEL_1X2","PANEL_1X4","PANEL_2X2","PANEL_2X4","PANEL_4X4",
    "PEBBLES_L","PEBBLES_M","PEBBLES_S","PEBBLES_XL","PEBBLES_XS",
    "ROBOT_DISHES","ROBOT_IRONING","ROBOT_LAUNDRY","ROBOT_MOPPING","ROBOT_VACUUMING",
    "SLEEP_POD_COTTON","SLEEP_POD_LAMB_WOOL","SLEEP_POD_NYLON","SLEEP_POD_POLYESTER","SLEEP_POD_SUEDE",
    "SNACKPACK_CHOCOLATE","SNACKPACK_PISTACHIO","SNACKPACK_RASPBERRY","SNACKPACK_STRAWBERRY","SNACKPACK_VANILLA",
    "TRANSLATOR_ASTRO_BLACK","TRANSLATOR_ECLIPSE_CHARCOAL","TRANSLATOR_GRAPHITE_MIST","TRANSLATOR_SPACE_GRAY",
    "TRANSLATOR_VOID_BLUE",
    "UV_VISOR_AMBER","UV_VISOR_MAGENTA","UV_VISOR_ORANGE","UV_VISOR_RED","UV_VISOR_YELLOW",
]

# v3 cointegration pairs (within + cross)
V3_PAIRS = [
    # within
    ("MICROCHIP_RECTANGLE","MICROCHIP_SQUARE",-0.401,14119.0,304.0,"within"),
    ("ROBOT_LAUNDRY","ROBOT_VACUUMING",0.334,7072.0,234.0,"within"),
    ("SLEEP_POD_COTTON","SLEEP_POD_POLYESTER",0.519,5144.0,328.0,"within"),
    ("GALAXY_SOUNDS_DARK_MATTER","GALAXY_SOUNDS_PLANETARY_RINGS",0.183,8285.0,283.0,"within"),
    ("SNACKPACK_RASPBERRY","SNACKPACK_VANILLA",0.013,9962.0,161.0,"within"),
    ("SNACKPACK_CHOCOLATE","SNACKPACK_STRAWBERRY",-0.106,11051.0,145.0,"within"),
    ("UV_VISOR_AMBER","UV_VISOR_MAGENTA",-1.238,21897.0,371.0,"within"),
    ("OXYGEN_SHAKE_CHOCOLATE","OXYGEN_SHAKE_GARLIC",-0.155,11066.0,237.0,"within"),
    ("TRANSLATOR_ECLIPSE_CHARCOAL","TRANSLATOR_VOID_BLUE",0.456,4954.0,308.0,"within"),
    ("SLEEP_POD_POLYESTER","SLEEP_POD_SUEDE",0.756,2977.0,426.0,"within"),
    # cross-group
    ("PEBBLES_XL","PANEL_2X4",2.4821,-14735.73,200.0,"cross"),
    ("UV_VISOR_AMBER","SNACKPACK_STRAWBERRY",-2.4501,34143.94,200.0,"cross"),
    ("PEBBLES_M","OXYGEN_SHAKE_MORNING_BREATH",-0.9037,19300.55,200.0,"cross"),
    ("UV_VISOR_YELLOW","GALAXY_SOUNDS_DARK_MATTER",1.5837,-5238.83,200.0,"cross"),
    ("OXYGEN_SHAKE_GARLIC","PEBBLES_S",-1.0114,20960.00,200.0,"cross"),
    ("PANEL_2X4","PEBBLES_XL",0.3093,7174.37,200.0,"cross"),
    ("MICROCHIP_SQUARE","SLEEP_POD_SUEDE",1.8678,-7692.97,200.0,"cross"),
    ("GALAXY_SOUNDS_BLACK_HOLES","PEBBLES_S",-1.0180,20559.94,200.0,"cross"),
    ("PEBBLES_S","GALAXY_SOUNDS_BLACK_HOLES",-0.7694,17755.06,200.0,"cross"),
    ("PEBBLES_S","OXYGEN_SHAKE_GARLIC",-0.7727,18147.25,200.0,"cross"),
    ("SLEEP_POD_POLYESTER","UV_VISOR_AMBER",-0.9226,19139.77,200.0,"cross"),
    ("GALAXY_SOUNDS_SOLAR_WINDS","PANEL_1X4",-0.5377,15490.30,200.0,"cross"),
    ("PEBBLES_S","PANEL_2X4",-1.1018,21344.63,200.0,"cross"),
    ("ROBOT_IRONING","PEBBLES_M",-0.9154,18096.05,200.0,"cross"),
    ("PANEL_2X4","OXYGEN_SHAKE_GARLIC",0.5545,4653.12,200.0,"cross"),
    ("GALAXY_SOUNDS_DARK_MATTER","UV_VISOR_YELLOW",0.3725,6144.99,200.0,"cross"),
    ("UV_VISOR_AMBER","SLEEP_POD_POLYESTER",-0.9595,19272.87,200.0,"cross"),
    ("PEBBLES_M","ROBOT_IRONING",-0.7284,16601.80,200.0,"cross"),
    ("PANEL_2X4","PEBBLES_S",-0.6242,16840.75,200.0,"cross"),
    ("SNACKPACK_STRAWBERRY","SLEEP_POD_POLYESTER",0.3255,6852.82,200.0,"cross"),
    ("SNACKPACK_CHOCOLATE","PANEL_2X4",-0.2171,12289.62,200.0,"cross"),
    ("SLEEP_POD_SUEDE","MICROCHIP_SQUARE",0.4516,5257.75,200.0,"cross"),
    ("SNACKPACK_STRAWBERRY","UV_VISOR_AMBER",-0.3259,13284.98,200.0,"cross"),
    ("TRANSLATOR_ECLIPSE_CHARCOAL","SLEEP_POD_LAMB_WOOL",-0.5308,15493.89,200.0,"cross"),
    ("SNACKPACK_VANILLA","PANEL_1X2",0.1461,8793.78,200.0,"cross"),
    ("SNACKPACK_VANILLA","PANEL_2X4",0.1490,8418.80,200.0,"cross"),
    ("SLEEP_POD_LAMB_WOOL","TRANSLATOR_ECLIPSE_CHARCOAL",-0.7159,17727.49,200.0,"cross"),
    ("SNACKPACK_PISTACHIO","OXYGEN_SHAKE_GARLIC",-0.1488,11269.91,200.0,"cross"),
    ("SNACKPACK_PISTACHIO","PEBBLES_XS",0.0992,8761.10,200.0,"cross"),
    ("SNACKPACK_PISTACHIO","MICROCHIP_OVAL",0.0907,8753.81,200.0,"cross"),
]

PROD_CAP = {
    "SLEEP_POD_LAMB_WOOL": 3, "UV_VISOR_MAGENTA": 4, "PANEL_1X2": 3,
    "TRANSLATOR_SPACE_GRAY": 4, "ROBOT_MOPPING": 4, "PANEL_4X4": 4,
    "GALAXY_SOUNDS_SOLAR_FLAMES": 4, "SNACKPACK_RASPBERRY": 5, "SNACKPACK_CHOCOLATE": 5,
}

PEBBLES = ["PEBBLES_L","PEBBLES_M","PEBBLES_S","PEBBLES_XL","PEBBLES_XS"]
SNACKPACKS = ["SNACKPACK_CHOCOLATE","SNACKPACK_PISTACHIO","SNACKPACK_RASPBERRY","SNACKPACK_STRAWBERRY","SNACKPACK_VANILLA"]

# Read v3 per-product PnL
def load_v3_per_product():
    df = pd.read_csv(V3_FULL)
    return dict(zip(df["product"].astype(str), df["pnl"].astype(int)))

# v3 official per-product PnLs (from strategy_v3_all.csv tail)
V3_PNL_OVERRIDE = {
    "GALAXY_SOUNDS_BLACK_HOLES":15158,"GALAXY_SOUNDS_DARK_MATTER":7456,
    "GALAXY_SOUNDS_PLANETARY_RINGS":-6912,"GALAXY_SOUNDS_SOLAR_FLAMES":2060,
    "GALAXY_SOUNDS_SOLAR_WINDS":10270,
    "MICROCHIP_CIRCLE":11367,"MICROCHIP_OVAL":1048,"MICROCHIP_RECTANGLE":784,
    "MICROCHIP_SQUARE":6182,"MICROCHIP_TRIANGLE":8286,
    "OXYGEN_SHAKE_CHOCOLATE":4867,"OXYGEN_SHAKE_EVENING_BREATH":11905,
    "OXYGEN_SHAKE_GARLIC":8073,"OXYGEN_SHAKE_MINT":2452,"OXYGEN_SHAKE_MORNING_BREATH":8240,
    "PANEL_1X2":509,"PANEL_1X4":8268,"PANEL_2X2":-87,"PANEL_2X4":6762,"PANEL_4X4":3116,
    "PEBBLES_L":-12237,"PEBBLES_M":943,"PEBBLES_S":5394,"PEBBLES_XL":9942,"PEBBLES_XS":12928,
    "ROBOT_DISHES":-2982,"ROBOT_IRONING":1064,"ROBOT_LAUNDRY":4074,
    "ROBOT_MOPPING":994,"ROBOT_VACUUMING":423,
    "SLEEP_POD_COTTON":9177,"SLEEP_POD_LAMB_WOOL":-2310,"SLEEP_POD_NYLON":4830,
    "SLEEP_POD_POLYESTER":4040,"SLEEP_POD_SUEDE":3027,
    "SNACKPACK_CHOCOLATE":-4689,"SNACKPACK_PISTACHIO":8711,
    "SNACKPACK_RASPBERRY":-10238,"SNACKPACK_STRAWBERRY":13860,"SNACKPACK_VANILLA":2573,
    "TRANSLATOR_ASTRO_BLACK":8030,"TRANSLATOR_ECLIPSE_CHARCOAL":5648,
    "TRANSLATOR_GRAPHITE_MIST":4278,"TRANSLATOR_SPACE_GRAY":-5039,"TRANSLATOR_VOID_BLUE":10529,
    "UV_VISOR_AMBER":8853,"UV_VISOR_MAGENTA":-2880,"UV_VISOR_ORANGE":9194,
    "UV_VISOR_RED":110,"UV_VISOR_YELLOW":802,
}

# mr_v6 per-product
MR_V6_PNL = json.loads(MR_V6.read_text())["per_product"]

# Reverify stats
def load_reverify():
    df = pd.read_csv(REVER)
    out = defaultdict(dict)
    for _, r in df.iterrows():
        if r["kind"] == "ar1":
            out[r["product"]]["ar1"] = float(r["ar1"]) if pd.notna(r["ar1"]) else None
        if r["kind"] == "lattice":
            out[r["product"]]["n_distinct_mids"] = int(r["n_distinct_mids"])
            out[r["product"]]["lattice_ratio"] = float(r["lattice_ratio"])
    return out

# mr_study mode + FV
MR_TAKER = {
    "ROBOT_DISHES":("rolling_mean w=50",2.5),
    "PEBBLES_M":("rolling_quadratic w=2000",1.0),
    "SLEEP_POD_POLYESTER":("range_mid w=500",1.75),
    "ROBOT_MOPPING":("rolling_quadratic w=500",1.25),
    "PEBBLES_XS":("rolling_quadratic w=500",1.25),
    "OXYGEN_SHAKE_CHOCOLATE":("rolling_linreg w=500",1.0),
    "PEBBLES_L":("rolling_median w=100",1.5),
}
MR_IDLE = {"ROBOT_IRONING","MICROCHIP_RECTANGLE","TRANSLATOR_SPACE_GRAY","GALAXY_SOUNDS_PLANETARY_RINGS",
           "SLEEP_POD_SUEDE","SLEEP_POD_LAMB_WOOL","GALAXY_SOUNDS_SOLAR_FLAMES","UV_VISOR_MAGENTA"}
MR_MM_SKEW = {"OXYGEN_SHAKE_EVENING_BREATH","SNACKPACK_CHOCOLATE"}

def pairs_for(product):
    out = []
    for a,b,sl,ic,sd,kind in V3_PAIRS:
        if a == product or b == product:
            out.append({"a":a,"b":b,"slope":sl,"intercept":ic,"sd":sd,"kind":kind})
    return out

def group_of(p):
    for g in ["GALAXY_SOUNDS","MICROCHIP","OXYGEN_SHAKE","PANEL","PEBBLES","ROBOT","SLEEP_POD","SNACKPACK","TRANSLATOR","UV_VISOR"]:
        if p.startswith(g):
            return g.lower()
    return "?"

def find_card_paths_for(product):
    """Return source paths from cards mentioning this product."""
    paths = []
    for sub in ("autoresearch","eda_full"):
        for f in (CARDS_DIR/sub).glob("*.json"):
            try:
                c = json.loads(f.read_text())
                if product in (c.get("products_mentioned") or []):
                    paths.append(c.get("source_path",""))
            except Exception:
                continue
    return paths

def write_product(product, rever_stats, all_paths_cache):
    pnl_v3 = V3_PNL_OVERRIDE.get(product, 0)
    pnl_mr_v6 = MR_V6_PNL.get(product, 0)
    g = group_of(product)
    pairs = pairs_for(product)
    in_pebbles = product in PEBBLES
    in_snackpack = product in SNACKPACKS
    cap = PROD_CAP.get(product, 10)
    rs = rever_stats.get(product, {})
    paths = all_paths_cache.get(product, [])

    lines = [
        f"# {product}",
        "",
        f"**Group:** `{g}` | **v3 3-day PnL:** {pnl_v3:+,} | **mr_v6 3-day PnL:** {pnl_mr_v6:+,} | **Position cap (v3):** {cap}",
        "",
    ]

    # Microstructure
    lines += ["## Microstructure"]
    if rs:
        if "ar1" in rs and rs["ar1"] is not None:
            lines.append(f"- **AR(1) on Δmid:** {rs['ar1']:+.4f} (re-verified on stitched 2+3+4 mids)")
        if "lattice_ratio" in rs:
            lines.append(f"- **Lattice ratio:** {rs['lattice_ratio']:.4f} (n_distinct_mids = {rs['n_distinct_mids']:,} of 30,000 ticks)")
    if in_pebbles:
        lines.append(f"- **PEBBLES basket member:** Σ_pebbles = 50,000 ± 2.8 (re-verified, std=2.80, half-life 0.16 ticks)")
    if in_snackpack:
        lines.append(f"- **SNACKPACK basket member:** Σ_snack = 50,221 ± 190 (re-verified, std=189.6)")
    lines.append("")

    # Cointegration
    if pairs:
        lines += ["## Cointegration overlays where this product is a leg"]
        for pp in pairs:
            tag = "WITHIN" if pp["kind"]=="within" else "CROSS"
            lines.append(f"- [{tag}] `{pp['a']} ~ {pp['b']}` slope={pp['slope']:+.4f} intercept={pp['intercept']:+.2f} sd={pp['sd']}")
        lines.append("")

    # MR study
    lines += ["## Mean-reversion (mr_study v6)"]
    if product in MR_TAKER:
        fv, z_in = MR_TAKER[product]
        lines.append(f"- mr_v6 mode: **TAKER** ({fv}, z_in={z_in})")
    elif product in MR_MM_SKEW:
        lines.append(f"- mr_v6 mode: **MM with signal skew** (AR(1) on Δmid)")
    elif product in MR_IDLE:
        lines.append(f"- mr_v6 mode: **IDLE** — chronic MM loser; mr_study chose to skip")
    else:
        lines.append("- mr_v6 mode: default MM (inside-spread bb+1/ba-1 with inv_skew=−pos·0.2)")
    lines.append("")

    # Day-of-day instability (KS p≈0 list from per_group_findings)
    KS_BREAKS = {"ROBOT_DISHES","OXYGEN_SHAKE_CHOCOLATE","MICROCHIP_OVAL","MICROCHIP_SQUARE",
                 "UV_VISOR_AMBER","SLEEP_POD_POLYESTER","MICROCHIP_TRIANGLE",
                 "OXYGEN_SHAKE_EVENING_BREATH","PANEL_1X4","GALAXY_SOUNDS_BLACK_HOLES"}
    if product in KS_BREAKS:
        lines += ["## Stability flag"]
        lines += ["- ⚠️ Days 2/3/4 distributions diverge (KS p < 1e-9) — directional drift between days. Strategy uses inv_skew=−pos·0.2 to absorb.",""]

    # Findings citations
    lines += ["## Reconciled findings (citations)"]
    src_seen = set()
    for p in paths[:25]:
        if p and p not in src_seen:
            src_seen.add(p)
            lines.append(f"- {p}")
    if not paths:
        lines.append("- (no cards mention this product directly — see group findings)")
    lines.append("")

    # Recommendation
    lines += ["## Recommendation (final algo)"]
    primary = "inside_spread_mm"
    secondary = ["inv_skew(-pos*0.2)"]
    if in_pebbles:
        primary = "basket_invariant_PEBBLES"
        secondary = ["pebble_skew", "inside_spread_mm","inv_skew"]
    elif in_snackpack:
        primary = "basket_invariant_SNACKPACK"
        secondary = ["snack_skew","inside_spread_mm","inv_skew"]
    if pairs:
        secondary.append(f"coint_pairs(n={len(pairs)})")
    if cap < 10:
        secondary.append(f"prod_cap={cap}")
    rationale = []
    if pnl_v3 < -5000:
        rationale.append("Chronic loser in v3 — Phase H ablation will test tighter cap or IDLE")
    elif pnl_v3 > 8000:
        rationale.append(f"Strong v3 contributor ({pnl_v3:+,}) — keep current setup")
    else:
        rationale.append(f"v3 PnL {pnl_v3:+,} — moderate; baseline kept")
    if product in KS_BREAKS:
        rationale.append("Day-of-day KS break flagged — conservative inventory skew")
    if product in MR_TAKER and pnl_v3 < pnl_mr_v6:
        rationale.append(f"mr_v6 outperformed v3 here ({pnl_mr_v6:+,} vs {pnl_v3:+,}) — TAKER candidate for Phase H")

    lines.append(f"- **Primary mechanism:** `{primary}`")
    lines.append(f"- **Secondary signals:** {', '.join(secondary)}")
    lines.append(f"- **Rationale:** {'; '.join(rationale)}")
    lines.append("")

    # Alternatives
    lines += ["## 2 ranked alternatives"]
    if product in MR_TAKER:
        fv, z_in = MR_TAKER[product]
        lines.append(f"1. mr_v6 TAKER ({fv}, z_in={z_in}) — would yield ~{pnl_mr_v6:+,} per mr_study")
    if product in MR_IDLE:
        lines.append(f"1. IDLE — mr_v6 chose this (PnL=0); v3 yields {pnl_v3:+,}")
    lines.append(f"2. Inside-spread MM only (drop overlays) — baseline before v3 layering")
    lines.append("")

    out_path = OUT_DIR / f"{product}.md"
    out_path.write_text("\n".join(lines))
    return out_path

def build_paths_cache():
    cache = defaultdict(list)
    for sub in ("autoresearch","eda_full"):
        for f in (CARDS_DIR/sub).glob("*.json"):
            try:
                c = json.loads(f.read_text())
            except Exception:
                continue
            for p in c.get("products_mentioned") or []:
                cache[p].append(c.get("source_path",""))
    return cache

def main():
    rever_stats = load_reverify()
    paths_cache = build_paths_cache()
    for p in PRODUCTS:
        write_product(p, rever_stats, paths_cache)
    print(f"Wrote {len(PRODUCTS)} per-product files")

if __name__ == "__main__":
    main()
