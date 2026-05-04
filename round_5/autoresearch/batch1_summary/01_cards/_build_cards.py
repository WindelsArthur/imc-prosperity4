"""Programmatic card extraction from inventory.
Per artefact: create one ≤2KB JSON card with structured info.
Heuristic key-number extraction (PnL, Sharpe, p-values, half-life, ADF, etc.).
For CSV/parquet: schema + top rows by likely metric column.
For JSON: top-level keys.
For PY: docstring + function names.
For MD: H1/H2 + first paragraph + numeric claims via regex.
"""
import json, os, re, hashlib, sys
from pathlib import Path
import pandas as pd

ROOT = Path("/Users/arthurwindels/Documents/08_DEV/Prosperity4/IMC-Prosperity-4-Belmonte")
INV = ROOT / "ROUND_5/batch1_summary/00_inventory/inventory.jsonl"
CARDS_DIR = ROOT / "ROUND_5/batch1_summary/01_cards"

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
GROUPS = ["GALAXY_SOUNDS","MICROCHIP","OXYGEN_SHAKE","PANEL","PEBBLES","ROBOT","SLEEP_POD","SNACKPACK","TRANSLATOR","UV_VISOR"]

# canonical tags
TAG_KEYS = {
    "cointegration":["cointegrat","johansen","engle","granger","ECT","β","beta_lag"],
    "lead_lag":["lead-lag","lead_lag","leadlag","lag-1","lag_1","CCF","cross-corr"],
    "basket":["basket","invariant","sum-50000","sum_50000","SNACKPACK","PEBBLES","SLEEP_POD","total"],
    "mean_reversion":["mean-revert","mean_revert","mr_","mean reversion","half-life","ou_"],
    "lattice":["lattice","quant","tick","grid"],
    "sine":["sine","period","seasonal","sinus"],
    "ar1":["AR(1)","ar1","autoregress","φ","phi","coef"],
    "intraday":["intraday","time-of-day","tod","am_","pm_"],
    "microstructure":["spread","depth","ofi","microprice","queue","imbalance"],
    "regime":["hmm","kalman","garch","regime"],
    "ml":["lasso","gbm","random_forest","ml_"],
    "stat_test":["adf","kpss","p-value","p_val","kstest","ljung"],
    "backtest":["pnl","backtest","sharpe","drawdown","oos","walk-forward"],
}

NUM_RE = re.compile(r"(?:[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?)")
KEY_NUM_PATTERNS = [
    ("pnl_total", re.compile(r"(?:total[_ ]?pnl|pnl[_ ]?total)[^\d-]{0,5}([-+]?\d[\d,]*\.?\d*)", re.I)),
    ("avg_daily_pnl", re.compile(r"(?:avg[_ ]?daily[_ ]?pnl|daily[_ ]?avg[_ ]?pnl|avg[_ ]?pnl[_ ]?day)[^\d-]{0,5}([-+]?\d[\d,]*\.?\d*)", re.I)),
    ("sharpe", re.compile(r"sharpe[^\d-]{0,5}([-+]?\d+\.?\d*)", re.I)),
    ("max_drawdown", re.compile(r"(?:max[_ ]?dd|max[_ ]?drawdown|drawdown)[^\d-]{0,5}([-+]?\d[\d,]*\.?\d*)", re.I)),
    ("adf_p", re.compile(r"adf[^\d]{0,8}p[^\d]{0,5}([-+]?\d+\.?\d*(?:e[-+]?\d+)?)", re.I)),
    ("half_life", re.compile(r"half[_ -]?life[^\d]{0,5}([-+]?\d+\.?\d*)", re.I)),
    ("oos_sharpe", re.compile(r"oos[_ ]?sharpe[^\d-]{0,5}([-+]?\d+\.?\d*)", re.I)),
    ("oos_pnl", re.compile(r"oos[_ ]?pnl[^\d-]{0,5}([-+]?\d[\d,]*\.?\d*)", re.I)),
    ("ar1_coef", re.compile(r"(?:ar\(1\)[_ ]?coef|ar1[_ ]?coef|phi)[^\d-]{0,5}([-+]?\d+\.?\d*)", re.I)),
]

def detect_products(text: str):
    upper = text.upper()
    found = []
    for p in PRODUCTS:
        if p in upper:
            found.append(p)
    return found[:8]

def detect_tags(text: str):
    lower = text.lower()
    tags = []
    for tag, kws in TAG_KEYS.items():
        for kw in kws:
            if kw.lower() in lower:
                tags.append(tag)
                break
    return tags

def extract_key_numbers(text: str):
    out = {}
    for name, pat in KEY_NUM_PATTERNS:
        m = pat.search(text)
        if m:
            try:
                v = float(m.group(1).replace(",",""))
                out[name] = v
            except ValueError:
                pass
    return out

def hash12(p): return hashlib.sha1(p.encode()).hexdigest()[:12]

def card_for_md(path: Path, rel: str, phase_tag: str):
    text = path.read_text(errors="replace")
    head = text[:4000]
    tail = text[-1500:] if len(text) > 6000 else ""
    excerpt = head[:1500]
    # H1/H2 + first paragraph
    h1 = re.findall(r"^#\s+(.+)$", text, re.M)
    h2 = re.findall(r"^##\s+(.+)$", text, re.M)
    first_para = ""
    for line in head.splitlines():
        line = line.strip()
        if line and not line.startswith("#") and not line.startswith("```"):
            first_para = line
            break
    products = detect_products(text)
    tags = detect_tags(text)
    nums = extract_key_numbers(text)
    claim = (h1[0] if h1 else first_para)[:280]
    return {
        "card_id": hash12(rel),
        "source_path": rel,
        "phase_tag": phase_tag,
        "ext": ".md",
        "products_mentioned": products,
        "claim_summary": claim,
        "h1": h1[:6],
        "h2": h2[:12],
        "key_numbers": nums,
        "evidence_type": "narrative",
        "tags": tags,
        "confidence": "medium",
        "size": path.stat().st_size,
        "raw_excerpt": excerpt,
    }

def card_for_csv(path: Path, rel: str, phase_tag: str):
    try:
        df = pd.read_csv(path, nrows=2000)
    except Exception as e:
        return _err_card(rel, phase_tag, ".csv", str(e))
    n_rows_full = sum(1 for _ in path.open("r")) - 1
    cols = list(df.columns)
    products = []
    if "product" in df.columns:
        products = [p for p in df["product"].astype(str).unique().tolist()[:20] if p in PRODUCTS]
    if not products:
        products = detect_products(rel + " " + " ".join(cols))
    # find a sort column
    sort_col = None
    for c in ["avg_daily_pnl","oos_pnl","total_pnl","pnl","sharpe","oos_sharpe","score"]:
        if c in df.columns:
            sort_col = c; break
    top_rows = []
    if sort_col:
        try:
            d2 = df.sort_values(sort_col, ascending=False).head(5)
            top_rows = d2.to_dict(orient="records")
        except Exception:
            top_rows = df.head(5).to_dict(orient="records")
    else:
        top_rows = df.head(3).to_dict(orient="records")
    # describe numeric
    desc = {}
    try:
        nd = df.select_dtypes("number").describe().to_dict()
        for k, v in nd.items():
            desc[k] = {"mean": v.get("mean"), "max": v.get("max"), "min": v.get("min")}
        # only keep top 6 numeric cols
        desc = dict(list(desc.items())[:6])
    except Exception:
        pass
    tags = detect_tags(rel + " " + " ".join(cols))
    if "backtest" not in tags and any("pnl" in c.lower() or "sharpe" in c.lower() for c in cols):
        tags.append("backtest")
    return {
        "card_id": hash12(rel),
        "source_path": rel,
        "phase_tag": phase_tag,
        "ext": ".csv",
        "products_mentioned": products[:8],
        "claim_summary": f"CSV n={n_rows_full} cols={len(cols)} sort_col={sort_col}",
        "columns": cols[:30],
        "n_rows": n_rows_full,
        "top_rows": top_rows[:3],
        "describe": desc,
        "evidence_type": "backtest" if "backtest" in tags or sort_col else "stat_test",
        "tags": list(set(tags)),
        "confidence": "high" if sort_col else "medium",
        "size": path.stat().st_size,
        "raw_excerpt": "",
    }

def card_for_json(path: Path, rel: str, phase_tag: str):
    try:
        size = path.stat().st_size
        if size > 200_000:
            # too big — read head only
            with path.open("r") as f:
                head = f.read(8000)
            obj = head
        else:
            obj = json.loads(path.read_text())
    except Exception as e:
        return _err_card(rel, phase_tag, ".json", str(e))
    summary = ""
    keys = []
    products = []
    nums = {}
    if isinstance(obj, dict):
        keys = list(obj.keys())[:30]
        # extract numeric leaves
        def walk(o, depth=0):
            if depth > 3: return
            if isinstance(o, dict):
                for k, v in o.items():
                    if isinstance(v, (int, float)) and abs(v) < 1e10:
                        if k not in nums and len(nums) < 12:
                            nums[k] = v
                    elif isinstance(v, (dict, list)):
                        walk(v, depth+1)
            elif isinstance(o, list):
                for x in o[:10]: walk(x, depth+1)
        walk(obj)
        text = json.dumps(obj)[:3000]
        products = detect_products(text)
        summary = f"JSON keys={keys[:6]}"
    elif isinstance(obj, list):
        keys = [f"list[{len(obj)}]"]
        if obj and isinstance(obj[0], dict):
            keys += list(obj[0].keys())[:10]
        text = json.dumps(obj[:3])[:3000]
        products = detect_products(text)
        summary = f"JSON list n={len(obj)}"
    else:
        # head-only string
        text = str(obj)[:3000]
        summary = text[:200]
        products = detect_products(text)
    tags = detect_tags(rel + " " + (json.dumps(keys) if isinstance(keys, list) else "") + " " + str(nums))
    return {
        "card_id": hash12(rel),
        "source_path": rel,
        "phase_tag": phase_tag,
        "ext": ".json",
        "products_mentioned": products[:8],
        "claim_summary": summary[:280],
        "keys": keys[:20],
        "key_numbers": nums,
        "evidence_type": "stat_test" if any("p_val" in k.lower() or "adf" in k.lower() or "sharpe" in k.lower() for k in (keys or [])) else "model_fit",
        "tags": tags,
        "confidence": "medium",
        "size": path.stat().st_size,
        "raw_excerpt": "",
    }

def card_for_py(path: Path, rel: str, phase_tag: str):
    text = path.read_text(errors="replace")
    head = text[:3000]
    docstring = ""
    m = re.search(r'^"""(.*?)"""', head, re.S | re.M)
    if m:
        docstring = m.group(1).strip()[:600]
    funcs = re.findall(r"^def\s+(\w+)\s*\(", text, re.M)[:20]
    classes = re.findall(r"^class\s+(\w+)", text, re.M)[:10]
    products = detect_products(text)
    tags = detect_tags(text)
    nums = extract_key_numbers(text)
    return {
        "card_id": hash12(rel),
        "source_path": rel,
        "phase_tag": phase_tag,
        "ext": ".py",
        "products_mentioned": products[:8],
        "claim_summary": (docstring or f"py functions={funcs[:5]}")[:280],
        "functions": funcs,
        "classes": classes,
        "key_numbers": nums,
        "evidence_type": "model_fit" if "Trader" in classes or "run" in funcs else "narrative",
        "tags": tags,
        "confidence": "medium",
        "size": path.stat().st_size,
        "raw_excerpt": head[:800],
    }

def card_for_parquet(path: Path, rel: str, phase_tag: str):
    try:
        df = pd.read_parquet(path)
    except Exception as e:
        return _err_card(rel, phase_tag, ".parquet", str(e))
    cols = list(df.columns)
    products = []
    if "product" in df.columns:
        products = [p for p in df["product"].astype(str).unique().tolist()[:20] if p in PRODUCTS]
    if not products:
        products = detect_products(rel + " " + " ".join(cols))
    sort_col = None
    for c in ["avg_daily_pnl","oos_pnl","total_pnl","pnl","sharpe","oos_sharpe","score"]:
        if c in df.columns:
            sort_col = c; break
    top_rows = []
    if sort_col:
        try:
            d2 = df.sort_values(sort_col, ascending=False).head(5)
            top_rows = d2.to_dict(orient="records")
        except Exception:
            top_rows = df.head(5).to_dict(orient="records")
    else:
        top_rows = df.head(3).to_dict(orient="records")
    tags = detect_tags(rel + " " + " ".join(cols))
    return {
        "card_id": hash12(rel),
        "source_path": rel,
        "phase_tag": phase_tag,
        "ext": ".parquet",
        "products_mentioned": products[:8],
        "claim_summary": f"PARQUET n={len(df)} cols={len(cols)} sort_col={sort_col}",
        "columns": cols[:30],
        "n_rows": len(df),
        "top_rows": top_rows[:3],
        "evidence_type": "backtest" if "backtest" in tags or sort_col else "stat_test",
        "tags": tags,
        "confidence": "high" if sort_col else "medium",
        "size": path.stat().st_size,
        "raw_excerpt": "",
    }

def card_for_png(path: Path, rel: str, phase_tag: str):
    name = path.name
    products = detect_products(rel)
    tags = detect_tags(rel)
    return {
        "card_id": hash12(rel),
        "source_path": rel,
        "phase_tag": phase_tag,
        "ext": ".png",
        "products_mentioned": products[:8],
        "claim_summary": f"PLOT {name}",
        "evidence_type": "plot",
        "tags": tags,
        "confidence": "low",
        "size": path.stat().st_size,
        "raw_excerpt": "",
    }

def _err_card(rel, phase_tag, ext, err):
    return {
        "card_id": hash12(rel),
        "source_path": rel,
        "phase_tag": phase_tag,
        "ext": ext,
        "products_mentioned": [],
        "claim_summary": f"READ_ERR: {err[:200]}",
        "evidence_type": "narrative",
        "tags": [],
        "confidence": "low",
        "size": 0,
        "raw_excerpt": "",
    }

def determine_subdir(rel: str):
    if rel.startswith("ROUND_5/autoresearch"):
        return "autoresearch"
    if rel.startswith("ROUND_5/EDA/eda_full"):
        return "eda_full"
    return "other"

def main():
    rows = [json.loads(l) for l in INV.read_text().splitlines() if l.strip()]
    print(f"Processing {len(rows)} artefacts")
    written = 0
    errs = 0
    for i, r in enumerate(rows):
        rel = r["path"]
        path = ROOT / rel
        ext = r["ext"]
        phase_tag = r["phase_tag"]
        sub = determine_subdir(rel)
        out_dir = CARDS_DIR / sub
        out_dir.mkdir(parents=True, exist_ok=True)
        out = out_dir / f"{r['card_id']}.json"
        if out.exists():
            continue
        try:
            if ext == ".md":
                card = card_for_md(path, rel, phase_tag)
            elif ext == ".csv":
                card = card_for_csv(path, rel, phase_tag)
            elif ext in (".json", ".jsonl"):
                card = card_for_json(path, rel, phase_tag)
            elif ext == ".py":
                card = card_for_py(path, rel, phase_tag)
            elif ext == ".parquet":
                card = card_for_parquet(path, rel, phase_tag)
            elif ext == ".png":
                card = card_for_png(path, rel, phase_tag)
            elif ext in (".txt",):
                # Treat .txt like md
                card = card_for_md(path, rel, phase_tag)
                card["ext"] = ".txt"
            else:
                card = _err_card(rel, phase_tag, ext, "unknown ext")
            # Truncate long string fields BEFORE serialising so JSON stays valid
            for k, v in list(card.items()):
                if isinstance(v, str) and len(v) > 800:
                    card[k] = v[:800]
            payload = json.dumps(card, default=str)
            if len(payload) > 2000:
                # Drop heavy fields and try again
                for k in ("raw_excerpt","describe","top_rows","keys","columns","h2","h1","functions","classes"):
                    card.pop(k, None)
                    payload = json.dumps(card, default=str)
                    if len(payload) <= 2000:
                        break
            out.write_text(payload)
            written += 1
        except Exception as e:
            errs += 1
            out.write_text(json.dumps(_err_card(rel, phase_tag, ext, str(e)))[:2000])
        if (i+1) % 50 == 0:
            print(f"  {i+1}/{len(rows)} written={written} errs={errs}")
    print(f"DONE: written={written} errs={errs}")

if __name__ == "__main__":
    main()
