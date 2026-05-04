"""Build 10 per-group markdown files."""
import json
from pathlib import Path

ROOT = Path("/Users/arthurwindels/Documents/08_DEV/Prosperity4/IMC-Prosperity-4-Belmonte")
OUT = ROOT / "ROUND_5/batch1_summary/05_per_group"
OUT.mkdir(exist_ok=True)
MR_V6 = json.loads((ROOT/"ROUND_5/autoresearch/mr_study/04_combined_search/v6_final_metrics.json").read_text())["per_product"]

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

GROUPS = ["GALAXY_SOUNDS","MICROCHIP","OXYGEN_SHAKE","PANEL","PEBBLES","ROBOT","SLEEP_POD","SNACKPACK","TRANSLATOR","UV_VISOR"]
GROUP_NOTES = {
    "PEBBLES":[
        "Strongest structural alpha in the universe.",
        "**Sum invariant Σmid = 50,000 ± 2.8** (R²=0.999998 of any-pebble on other-four), OU half-life **0.16 ticks**.",
        "Strategy: passive inside-spread MM with skew_i = −resid/5 applied uniformly. PEBBLES_XL is the largest single contributor (+50,715 in v1; +9,942 in v3 after cap and pair overlays).",
        "PEBBLES_L is the chronic loser (-12,237 in v3). v2 ablation tested cap=5 and got +92 PnL but Sharpe 8.6→7.2. Phase H will retest.",
        "5/5 products are also legs in cross-group cointegration pairs (PEBBLES_XL/PANEL_2X4 is the single largest cross-group contributor).",
    ],
    "SNACKPACK":[
        "Looser sum invariant Σmid ≈ 50,221 ± 190 (10× weaker than pebbles).",
        "Best within-group pair RASPBERRY/VANILLA ADF p=0.001 (re-verified); CHOCOLATE/STRAWBERRY ADF p=0.035 (re-verified).",
        "Off-diagonal returns correlation −0.16 (group is internally anti-correlated).",
        "PROD_CAP applied: CHOCOLATE=5, RASPBERRY=5 (heavy bleeders in v1).",
        "v3 group sum: STRAWBERRY +13.9K dominates; CHOCOLATE −4.7K, RASPBERRY −10.2K still drag despite caps.",
    ],
    "MICROCHIP":[
        "Tight ~5-tick spread on 4/5 products (CIRCLE, OVAL, RECTANGLE, TRIANGLE); SQUARE wider (~12).",
        "Best EG pair RECTANGLE/SQUARE slope=−0.40, ADF p=0.004 (re-verified at 0.0036), OOS Sharpe 1.0–2.1.",
        "OVAL has sine R²=0.974 (period = full series, deemed artefact in v2).",
        "CIRCLE is the v3 group winner (+11,367); RECTANGLE only +784 — the cap effect from −0.40 slope pair.",
    ],
    "SLEEP_POD":[
        "Most cointegrated within-group pairs in the universe.",
        "Best Sharpe pairs: COTTON/POLYESTER (1.3–1.9), POLYESTER/SUEDE (1.1–1.9), LAMB_WOOL/SUEDE (Sharpe 2.2 fold-B).",
        "Re-verified ADF p: COTTON/POLYESTER 0.146 (above 0.05), POLYESTER/SUEDE 0.091 — borderline. Kept because fold-OOS Sharpe was positive.",
        "LAMB_WOOL is chronic loser; PROD_CAP=3 brings v3 to −2.3K (vs −24K in v1).",
        "SUEDE participates in cross-group pair MICROCHIP_SQUARE/SUEDE (slope 1.87).",
    ],
    "ROBOT":[
        "IRONING (631 distinct mids, lattice ratio 0.021) and DISHES (3048 distinct, AR(1)=−0.232) have strongest mean-reversion signals.",
        "DISHES had AR-BIC p=9 in EDA but day-of-day distributions diverge wildly (KS p≈0). Strategy treats it as plain MM.",
        "LAUNDRY/VACUUMING ADF p=0.378 in re-verify (claimed 0.026) — not stationary on full stitch but OOS Sharpe was 1.19/1.70 in folds.",
        "MOPPING is a v1 bleeder; PROD_CAP=4 brought v3 to +994 (vs −17K in v1).",
        "mr_v6 found DISHES, MOPPING as TAKER candidates with rolling_quadratic w=500 — but mr_v6 total dominated by v3.",
    ],
    "GALAXY_SOUNDS":[
        "DARK_MATTER/PLANETARY_RINGS pair slope=0.183, ADF p=0.038 (re-verified). Sharpe 1.6–2.0 in folds.",
        "BLACK_HOLES/PEBBLES_S is a strong cross-group pair (slope=−1.018) — v3's BLACK_HOLES PnL (+15K) is the group highlight.",
        "PLANETARY_RINGS bleeds in v3 (−6.9K). mr_v6 chose IDLE for this product.",
        "SOLAR_FLAMES is also a v1 bleeder, PROD_CAP=4 in v3 → +2K.",
    ],
    "OXYGEN_SHAKE":[
        "EVENING_BREATH = lattice product (453 distinct mids, ratio 0.015, AR(1)=−0.123). +11.9K in v3 from MM with inv_skew.",
        "CHOCOLATE has AR(1)=−0.089 and sees a huge KS break across days. CHOCOLATE/GARLIC pair has ADF p=**0.918** in re-verify (claimed 0.030) — pair is non-stationary; **drop in final algo**.",
        "GARLIC participates in 3 cross-group pairs (PEBBLES_S/GARLIC, PANEL_2X4/GARLIC, GARLIC/PEBBLES_S).",
        "Group total in v3 = +35.5K (5/5 products positive).",
    ],
    "PANEL":[
        "1X4 cointegrated with 2X4 (Sharpe 1.07 fold-B). 1X2 is the worst MM target (-18.7K v1, -5K v3 after cap=3).",
        "PANEL_2X4 is the most-used cross-group leg in v3 — appears in 7 cross-group pairs.",
        "v3 group total +18.6K.",
    ],
    "TRANSLATOR":[
        "ECLIPSE/VOID_BLUE pair slope=0.456, ADF p=0.041 (re-verified at 0.035), Sharpe 0.5–2.1.",
        "ECLIPSE_CHARCOAL/SLEEP_POD_LAMB_WOOL is a cross-group pair (slope=−0.531).",
        "SPACE_GRAY is the heaviest 3-day loser even with PROD_CAP=4 (-5K). VOID_BLUE is the group winner (+10.5K).",
    ],
    "UV_VISOR":[
        "AMBER/MAGENTA pair slope=−1.238, ADF p=0.046 (re-verified). MAGENTA is the perennial loser (−2.9K in v3 with cap=4).",
        "AMBER has sine R²=0.962 — only sine-fit product that survived v2's walk-forward, but dollar contribution small. Kept as inv_skew only.",
        "AMBER participates in 4 pair overlays (1 within + 3 cross-group).",
        "v3 group total +15.0K.",
    ],
}

PEBBLES = ["PEBBLES_L","PEBBLES_M","PEBBLES_S","PEBBLES_XL","PEBBLES_XS"]
SNACKPACKS = ["SNACKPACK_CHOCOLATE","SNACKPACK_PISTACHIO","SNACKPACK_RASPBERRY","SNACKPACK_STRAWBERRY","SNACKPACK_VANILLA"]
def members_of(g):
    return [p for p in V3.keys() if p.startswith(g)]

CITATIONS = {
    "PEBBLES":["ROUND_5/autoresearch/05_cross_product/groups/pebbles/basket_residual.csv","ROUND_5/autoresearch/11_findings/per_group_findings.md"],
    "SNACKPACK":["ROUND_5/autoresearch/05_cross_product/groups/snackpack/basket_residual.csv","ROUND_5/autoresearch/14_lag_research/C_lagged_coint/lagged_coint_fast.csv"],
    "MICROCHIP":["ROUND_5/autoresearch/05_cross_product/groups/microchip/all_pair_cointegration.csv","ROUND_5/autoresearch/13_round2_research/A_sine/oos_mse.csv"],
    "SLEEP_POD":["ROUND_5/autoresearch/05_cross_product/groups/sleep_pod/all_pair_cointegration.csv"],
    "ROBOT":["ROUND_5/autoresearch/04_statistical_patterns/intraday/ROBOT_DISHES.csv","ROUND_5/autoresearch/mr_study/01_fair_value_zoo/per_product/ROBOT_DISHES/ranking.csv"],
    "GALAXY_SOUNDS":["ROUND_5/autoresearch/05_cross_product/groups/galaxy_sounds/all_pair_cointegration.csv"],
    "OXYGEN_SHAKE":["ROUND_5/autoresearch/05_cross_product/groups/oxygen_shake/all_pair_cointegration.csv"],
    "PANEL":["ROUND_5/autoresearch/05_cross_product/groups/panel/all_pair_cointegration.csv"],
    "TRANSLATOR":["ROUND_5/autoresearch/05_cross_product/groups/translator/all_pair_cointegration.csv"],
    "UV_VISOR":["ROUND_5/autoresearch/13_round2_research/A_sine/oos_mse.csv","ROUND_5/autoresearch/05_cross_product/groups/uv_visor/all_pair_cointegration.csv"],
}

for g in GROUPS:
    members = members_of(g)
    pnl_rows = [(p, V3[p], MR_V6.get(p,0)) for p in members]
    pnl_rows.sort(key=lambda x:-x[1])
    total_v3 = sum(r[1] for r in pnl_rows)
    total_mr = sum(r[2] for r in pnl_rows)
    lines = [
        f"# Group {g.lower()}",
        "",
        f"5 products: {', '.join(members)}",
        f"3-day v3 PnL total: **{total_v3:+,}** | mr_v6 total: {total_mr:+,}",
        "",
        "## Per-product 3-day PnL (v3 vs mr_v6)",
        "| Product | v3 | mr_v6 |",
        "|---|---:|---:|",
    ]
    for p, v, m in pnl_rows:
        lines.append(f"| {p} | {v:+,} | {m:+,} |")
    lines.append("")
    lines += ["## Group findings"]
    for n in GROUP_NOTES.get(g, ["(no notes)"]):
        lines.append(f"- {n}")
    lines.append("")
    lines += ["## Citations"]
    for c in CITATIONS.get(g, []):
        lines.append(f"- {c}")
    lines.append("- ROUND_5/autoresearch/11_findings/per_group_findings.md")
    lines.append(f"- ROUND_5/autoresearch/mr_study/07_findings/group_summary.md")
    lines.append("")
    (OUT/f"{g.lower()}.md").write_text("\n".join(lines))

print(f"Wrote {len(GROUPS)} group files")
