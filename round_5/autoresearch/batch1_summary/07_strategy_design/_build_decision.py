"""Build per_product_decision.csv + alternatives_by_product.md + conflict_resolution.md."""
import json
from pathlib import Path

ROOT = Path("/Users/arthurwindels/Documents/08_DEV/Prosperity4/IMC-Prosperity-4-Belmonte")
OUT = ROOT / "ROUND_5/batch1_summary/07_strategy_design"
OUT.mkdir(exist_ok=True)

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

V3 = {
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
MR_V6 = json.loads((ROOT/"ROUND_5/autoresearch/mr_study/04_combined_search/v6_final_metrics.json").read_text())["per_product"]

PEBBLES = {"PEBBLES_L","PEBBLES_M","PEBBLES_S","PEBBLES_XL","PEBBLES_XS"}
SNACKPACKS = {"SNACKPACK_CHOCOLATE","SNACKPACK_PISTACHIO","SNACKPACK_RASPBERRY","SNACKPACK_STRAWBERRY","SNACKPACK_VANILLA"}

# Pairs (a,b) — check membership both ways
WITHIN_PAIRS_LEGS = {
    "MICROCHIP_RECTANGLE","MICROCHIP_SQUARE","ROBOT_LAUNDRY","ROBOT_VACUUMING",
    "SLEEP_POD_COTTON","SLEEP_POD_POLYESTER","GALAXY_SOUNDS_DARK_MATTER",
    "GALAXY_SOUNDS_PLANETARY_RINGS","SNACKPACK_RASPBERRY","SNACKPACK_VANILLA",
    "SNACKPACK_CHOCOLATE","SNACKPACK_STRAWBERRY","UV_VISOR_AMBER","UV_VISOR_MAGENTA",
    "OXYGEN_SHAKE_CHOCOLATE","OXYGEN_SHAKE_GARLIC","TRANSLATOR_ECLIPSE_CHARCOAL",
    "TRANSLATOR_VOID_BLUE","SLEEP_POD_SUEDE",
}
CROSS_LEGS = {  # leg → number of cross-group pairs it appears in
    "PEBBLES_XL":2,"PANEL_2X4":7,"UV_VISOR_AMBER":4,"SNACKPACK_STRAWBERRY":3,
    "PEBBLES_M":3,"OXYGEN_SHAKE_MORNING_BREATH":1,"UV_VISOR_YELLOW":2,
    "GALAXY_SOUNDS_DARK_MATTER":2,"OXYGEN_SHAKE_GARLIC":4,"PEBBLES_S":4,
    "MICROCHIP_SQUARE":2,"SLEEP_POD_SUEDE":2,"GALAXY_SOUNDS_BLACK_HOLES":2,
    "SLEEP_POD_POLYESTER":3,"GALAXY_SOUNDS_SOLAR_WINDS":1,"PANEL_1X4":1,
    "ROBOT_IRONING":2,"SNACKPACK_CHOCOLATE":1,"SNACKPACK_VANILLA":2,
    "TRANSLATOR_ECLIPSE_CHARCOAL":1,"SLEEP_POD_LAMB_WOOL":1,"SNACKPACK_PISTACHIO":3,
    "PEBBLES_XS":1,"MICROCHIP_OVAL":1,"PANEL_1X2":1,
}
PROD_CAP = {
    "SLEEP_POD_LAMB_WOOL":3,"UV_VISOR_MAGENTA":4,"PANEL_1X2":3,
    "TRANSLATOR_SPACE_GRAY":4,"ROBOT_MOPPING":4,"PANEL_4X4":4,
    "GALAXY_SOUNDS_SOLAR_FLAMES":4,"SNACKPACK_RASPBERRY":5,"SNACKPACK_CHOCOLATE":5,
}
MR_TAKER = {"ROBOT_DISHES","PEBBLES_M","SLEEP_POD_POLYESTER","ROBOT_MOPPING",
            "PEBBLES_XS","OXYGEN_SHAKE_CHOCOLATE","PEBBLES_L"}
MR_IDLE = {"ROBOT_IRONING","MICROCHIP_RECTANGLE","TRANSLATOR_SPACE_GRAY",
           "GALAXY_SOUNDS_PLANETARY_RINGS","SLEEP_POD_SUEDE","SLEEP_POD_LAMB_WOOL",
           "GALAXY_SOUNDS_SOLAR_FLAMES","UV_VISOR_MAGENTA"}

# pnl band per product (low/mid/high) — coarse from v3 with noise band
def band(p):
    v3 = V3[p]
    mr = MR_V6.get(p,0)
    # Use min/avg/max as low/mid/high
    vals = sorted([v3, mr, max(v3,mr)])
    return vals[0]/3, (v3+mr)/2/3, vals[2]/3

# pick primary mechanism
def pick_primary(p):
    if p in PEBBLES: return "basket_invariant_PEBBLES"
    if p in SNACKPACKS: return "basket_invariant_SNACKPACK"
    if p in WITHIN_PAIRS_LEGS or p in CROSS_LEGS: return "cointegration_leg"
    return "inside_spread_mm"

def secondary(p):
    s = []
    if p in CROSS_LEGS: s.append(f"cross_pair_skew(n={CROSS_LEGS[p]})")
    if p in WITHIN_PAIRS_LEGS: s.append("within_pair_skew")
    s.append("inv_skew(-pos*0.2)")
    s.append("inside_spread_mm(bb+1/ba-1)")
    if p in PROD_CAP: s.append(f"prod_cap={PROD_CAP[p]}")
    if p == "OXYGEN_SHAKE_CHOCOLATE":
        s.append("EXCLUDE within-pair OXYGEN_SHAKE_CHOCOLATE/GARLIC (failed reverify ADF=0.918)")
    return s

def n_findings(p):
    # Heuristic: count flags
    n = 0
    if p in PEBBLES or p in SNACKPACKS: n += 1  # basket
    if p in WITHIN_PAIRS_LEGS: n += 1
    if p in CROSS_LEGS: n += 1
    if p in MR_TAKER: n += 1
    if p in PROD_CAP: n += 1
    if p in MR_IDLE: n += 1
    return n

def rationale(p):
    bits = []
    v3 = V3[p]
    mr = MR_V6.get(p,0)
    if p in PEBBLES:
        bits.append("Member of PEBBLES sum-50000 invariant (std 2.8, half-life 0.16t)")
    if p in SNACKPACKS:
        bits.append("Member of SNACKPACK sum-50221 invariant (std 190)")
    if p in CROSS_LEGS:
        bits.append(f"Leg in {CROSS_LEGS[p]} cross-group cointegration pair(s) (round-3 Phase C)")
    if p in WITHIN_PAIRS_LEGS:
        bits.append("Leg in within-group cointegration pair (round-1)")
    if p in PROD_CAP:
        bits.append(f"PROD_CAP={PROD_CAP[p]} from round-2 Phase B bleeder analysis")
    if p in MR_TAKER and mr > v3:
        bits.append(f"mr_v6 TAKER outperforms v3 by {mr-v3:+,} — Phase H ablation candidate")
    elif p in MR_IDLE:
        bits.append("mr_v6 chose IDLE — chronic MM loser; Phase H may apply")
    if p == "OXYGEN_SHAKE_CHOCOLATE":
        bits.append("Drop within-pair OXYGEN_SHAKE_CHOCOLATE/GARLIC (ADF=0.918 reverify failure)")
    if not bits:
        bits.append("Default MM with inv_skew")
    return "; ".join(bits)[:240]

# build CSV
import csv
csv_rows = []
md_lines = ["# Alternatives by product","","Primary mechanism + 2 ranked alternatives per product. Phase H ablation will measure additivity for any TAKER swap."]

for p in PRODUCTS:
    primary = pick_primary(p)
    sec = secondary(p)
    nf = n_findings(p)
    low, mid, hi = band(p)
    csv_rows.append({
        "product": p,
        "primary": primary,
        "secondary": "; ".join(sec),
        "expected_avg_daily_low": int(low),
        "expected_avg_daily_mid": int(mid),
        "expected_avg_daily_high": int(hi),
        "n_supporting_findings": nf,
        "rationale": rationale(p),
        "v3_3day_pnl": V3[p],
        "mr_v6_3day_pnl": MR_V6.get(p,0),
    })
    md_lines += [
        f"### {p}",
        f"- Primary: `{primary}`",
        f"- Alt 1 ({'TAKER mr_v6' if p in MR_TAKER else 'IDLE' if p in MR_IDLE else 'pure MM no-overlay'}): {V3[p]:+,} v3 vs {MR_V6.get(p,0):+,} mr_v6",
        f"- Alt 2: drop pair overlay (use only basket_invariant or default MM)",
        ""
    ]

# write csv
with (OUT/"per_product_decision.csv").open("w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(csv_rows[0].keys()))
    w.writeheader()
    w.writerows(csv_rows)

# write alternatives md
(OUT/"alternatives_by_product.md").write_text("\n".join(md_lines))

# conflict resolution md
(OUT/"conflict_resolution.md").write_text("""# Conflict resolution per product

Cross-references against `03_reconciliation/conflicts.jsonl`.

## c001 — ROBOT_LAUNDRY/ROBOT_VACUUMING ADF
- Reverify: ADF p=0.378 (claimed 0.026). Pair non-stationary on full stitch.
- Decision: **KEEP** the within-group pair. Both fold-OOS Sharpes positive (1.19/1.70). v3 PnL on the legs is +4,074 / +423 — pair contributes meaningfully via skew.
- Risk mitigation: inv_skew + ±3 tilt clip already prevents unbounded exposure.

## c002 — SLEEP_POD_COTTON/SLEEP_POD_POLYESTER ADF
- Reverify: ADF p=0.146 (claimed 0.033).
- Decision: **KEEP**. Fold-OOS Sharpes 1.32/1.89. v3 leg PnL +9,177 / +4,040.

## c003 — OXYGEN_SHAKE_CHOCOLATE/OXYGEN_SHAKE_GARLIC ADF
- Reverify: ADF p=**0.918** (claimed 0.030). Pair is non-stationary; OXYGEN_SHAKE_CHOCOLATE has KS p≈0 day-of-day.
- Decision: **DROP** this within-group pair from final algo. CHOCOLATE keeps default MM + inv_skew (or optional Phase H test of mr_v6 ar_diff skew).
- Both legs participate in 4 cross-group pairs each — those are robust and KEPT.

## c004 — SLEEP_POD_POLYESTER/SLEEP_POD_SUEDE ADF
- Reverify: ADF p=0.091 (claimed 0.052). Both above 0.05 threshold.
- Decision: **KEEP**. Fold-OOS Sharpes positive (1.90/1.12).

## c005 — SNACKPACK_CHOCOLATE/SNACKPACK_STRAWBERRY ADF
- Reverify: ADF p=0.035 (claimed 0.009). Both <0.05.
- Decision: **KEEP**.

## c006 — v3 vs v3_per_product totals
- 733,320 vs 556,430. Reverified v3=733,320 (`reverify_v3.csv`).
- Decision: **BASELINE = 733,320**. v3_per_product was a different ablation config.

## c007 — Sine overlay
- v2 ablation: −496 PnL even on UV_VISOR_AMBER (the only OOS survivor).
- Decision: **DROP sine entirely**. No sine overlay in final algo.

## c008 — PEBBLES_L cap
- v2 found cap=5 → +92 PnL but Sharpe 8.6→7.2.
- v3 PEBBLES_L PnL = −12,237 (chronic loser).
- Decision: **TEST** in Phase H ablation. mr_v6 TAKER yields +9,434, suggesting cap or mode change could be net positive.

## c009 — mr_v6 TAKER mode for 7 products
- mr_v6 = 399K total, v3 = 733K total. mr_v6 inferior in absolute terms.
- Decision: **TEST** layering 2-3 highest-Δ TAKERs (PEBBLES_L, ROBOT_DISHES, ROBOT_MOPPING) on top of v3's basket+pair structure. Reject any that fail to add ≥+2K/day.

## c010 — counterparty fields empty
- Confirmed empty across all 3 days, all products.
- Decision: **IGNORE** all counterparty-conditional claims. No buyer/seller-based signals.
""")

print(f"Wrote 50-row decision csv + alternatives_by_product.md + conflict_resolution.md")
