"""Walk all cards, emit one row per atomic finding to findings_index.jsonl.
Also produce by-product and by-tag pivots.
"""
import json, os, re
from pathlib import Path
from collections import defaultdict, Counter
import pandas as pd

ROOT = Path("/Users/arthurwindels/Documents/08_DEV/Prosperity4/IMC-Prosperity-4-Belmonte")
CARDS_DIR = ROOT / "ROUND_5/batch1_summary/01_cards"
OUT_INDEX = ROOT / "ROUND_5/batch1_summary/02_index/findings_index.jsonl"
OUT_PROD = ROOT / "ROUND_5/batch1_summary/02_index/findings_by_product.parquet"
OUT_TAG = ROOT / "ROUND_5/batch1_summary/02_index/findings_by_tag.parquet"
OUT_GLOSS = ROOT / "ROUND_5/batch1_summary/02_index/tag_glossary.md"

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

def card_files():
    return list((CARDS_DIR/"autoresearch").glob("*.json")) + list((CARDS_DIR/"eda_full").glob("*.json"))

def load_cards():
    cards = []
    for f in card_files():
        try:
            cards.append(json.loads(f.read_text()))
        except Exception:
            continue
    return cards

def emit_findings(card):
    """Map one card → 1+ atomic findings."""
    out = []
    base = {
        "card_id": card.get("card_id"),
        "sources": [card.get("source_path","")],
        "phase_tag": card.get("phase_tag",""),
        "evidence_type": card.get("evidence_type",""),
        "confidence": card.get("confidence","medium"),
    }
    products = card.get("products_mentioned", []) or []
    tags = card.get("tags", []) or []
    nums = card.get("key_numbers", {}) or {}
    claim = card.get("claim_summary","") or ""

    # If card has top_rows (CSV/parquet), each row is a finding
    top_rows = card.get("top_rows", []) or []
    columns = card.get("columns", []) or []

    if top_rows:
        for row in top_rows:
            # extract product
            p = None
            for k in ("product","i","prod","product_name"):
                if k in row:
                    p = row[k]; break
            # if pair: i+j
            if "i" in row and "j" in row:
                p = f"{row['i']}|{row['j']}"
            # synthesize claim
            cl_parts = []
            for k in ("avg_daily_pnl","oos_pnl","total_pnl","pnl","sharpe","oos_sharpe","fA_sharpe","fB_sharpe","adf_p","ou_hl","slope","intercept","z_in","z_out","fv_family","mode"):
                if k in row and row[k] is not None:
                    cl_parts.append(f"{k}={row[k]}")
            cl = "; ".join(cl_parts)[:280]
            # numeric extract for finding
            f_nums = {}
            for k in ("avg_daily_pnl","oos_pnl","total_pnl","pnl","sharpe","oos_sharpe","fA_sharpe","fB_sharpe","adf_p","ou_hl","slope","intercept","min_fold_sharpe"):
                if k in row:
                    try:
                        v = row[k]
                        if isinstance(v, (int,float)) and not isinstance(v, bool):
                            f_nums[k] = float(v)
                    except Exception:
                        pass
            out.append({
                **base,
                "product": p if p in PRODUCTS else None,
                "product_pair": p if p and "|" in str(p) else None,
                "claim": cl,
                "key_numbers": f_nums,
                "tags": list(set(tags + (["pair"] if p and "|" in str(p) else []))),
            })
    else:
        # one finding per card (narrative or simple)
        out.append({
            **base,
            "product": products[0] if products else None,
            "claim": claim[:280],
            "key_numbers": nums,
            "tags": tags,
            "all_products": products,
        })
    return out

def main():
    cards = load_cards()
    print(f"Loaded {len(cards)} cards")
    findings = []
    for i, c in enumerate(cards):
        for f in emit_findings(c):
            findings.append(f)
    # assign ids
    for i, f in enumerate(findings):
        f["id"] = f"f{i:05d}"
    # write index
    with OUT_INDEX.open("w") as h:
        for f in findings:
            h.write(json.dumps(f, default=str) + "\n")
    print(f"Wrote {len(findings)} findings → {OUT_INDEX}")

    # by-product pivot
    rows = []
    for f in findings:
        prods = []
        if f.get("product"):
            prods.append(f["product"])
        if f.get("all_products"):
            for p in f["all_products"]:
                if p in PRODUCTS:
                    prods.append(p)
        for p in prods:
            rows.append({
                "id": f["id"], "product": p,
                "tags": ",".join(f.get("tags",[])),
                "claim": f.get("claim","")[:200],
                "evidence_type": f.get("evidence_type",""),
                "confidence": f.get("confidence",""),
                "source": (f.get("sources") or [""])[0],
            })
    pdf = pd.DataFrame(rows)
    pdf.to_parquet(OUT_PROD)
    print(f"Wrote {len(pdf)} (id,product) rows → {OUT_PROD}")

    # by-tag pivot
    rows = []
    for f in findings:
        for t in f.get("tags", []) or []:
            rows.append({
                "id": f["id"], "tag": t,
                "product": f.get("product") or "",
                "claim": f.get("claim","")[:200],
                "source": (f.get("sources") or [""])[0],
            })
    tdf = pd.DataFrame(rows)
    tdf.to_parquet(OUT_TAG)
    print(f"Wrote {len(tdf)} (id,tag) rows → {OUT_TAG}")

    # tag counts
    tag_ct = Counter()
    for f in findings:
        for t in f.get("tags",[]) or []:
            tag_ct[t] += 1
    glossary_lines = ["# Tag Glossary",""]
    descriptions = {
        "cointegration":"Two products move with stationary residual under linear combination (Engle-Granger or Johansen).",
        "lead_lag":"Cross-correlation peaks at non-zero lag between two products.",
        "basket":"Sum / weighted-sum of group members is invariant or near-constant.",
        "mean_reversion":"Single-product mid reverts to a fair value (rolling mean, OU, AR, etc.).",
        "lattice":"Mid takes a small number of distinct values (quasi-discrete lattice).",
        "sine":"Deterministic sine fit of price level over the stitched 30k-tick training window.",
        "ar1":"Lag-1 autoregressive coefficient on Δmid.",
        "intraday":"Time-of-day pattern (mod-K) in returns or activity.",
        "microstructure":"Spread / depth / OFI / queue / imbalance signal at order-book level.",
        "regime":"HMM / Kalman / GARCH-style regime-switching model.",
        "ml":"ML-distilled (Lasso, GBM, RF) signal.",
        "stat_test":"Stationarity / distribution test (ADF, KPSS, KS, Ljung-Box).",
        "backtest":"Direct backtest result (PnL, Sharpe, drawdown).",
        "pair":"Pair-finding (two products jointly).",
    }
    for t, c in tag_ct.most_common():
        glossary_lines.append(f"- **{t}** ({c}): {descriptions.get(t,'(no description)')}")
    OUT_GLOSS.write_text("\n".join(glossary_lines))

    return len(findings)

if __name__ == "__main__":
    n = main()
    print(f"DONE: {n} findings")
