"""Build inventory.jsonl: one row per artefact, metadata-only.
DO NOT load full file contents. For text files: filename + first 200 chars head.
For binaries (png, parquet): description from filename only."""
import json, os, hashlib, sys
from pathlib import Path
from collections import Counter

ROOT = Path("/Users/arthurwindels/Documents/08_DEV/Prosperity4/IMC-Prosperity-4-Belmonte")
TREES = [
    ROOT / "ROUND_5/batch1_summary/00_inventory/tree_autoresearch.txt",
    ROOT / "ROUND_5/batch1_summary/00_inventory/tree_eda_full.txt",
]
OUT = ROOT / "ROUND_5/batch1_summary/00_inventory/inventory.jsonl"
STATS = ROOT / "ROUND_5/batch1_summary/00_inventory/inventory_stats.md"

TEXT_EXTS = {".md", ".csv", ".json", ".jsonl", ".py", ".ipynb", ".txt"}
BIN_EXTS = {".png", ".parquet"}

PRODUCTS = [
    "RAINFOREST_RESIN","KELP","SQUID_INK","CROISSANTS","JAMS","DJEMBES","PICNIC_BASKET1","PICNIC_BASKET2",
    "VOLCANIC_ROCK","VOLCANIC_ROCK_VOUCHER_9500","VOLCANIC_ROCK_VOUCHER_9750","VOLCANIC_ROCK_VOUCHER_10000",
    "VOLCANIC_ROCK_VOUCHER_10250","VOLCANIC_ROCK_VOUCHER_10500","MAGNIFICENT_MACARONS",
]

def hash12(p):
    return hashlib.sha1(p.encode()).hexdigest()[:12]

def head200(path: Path) -> str:
    try:
        with path.open("rb") as f:
            raw = f.read(400)
        s = raw.decode("utf-8", errors="replace")
        return " ".join(s.split())[:200]
    except Exception as e:
        return f"<read_err:{e}>"

def detect_products(s: str) -> list:
    found = []
    upper = s.upper()
    for p in PRODUCTS:
        if p in upper:
            found.append(p)
    return found

rows = []
for tf in TREES:
    for line in tf.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        p = ROOT / line
        try:
            stat = p.stat()
        except FileNotFoundError:
            continue
        ext = p.suffix.lower()
        rel = str(p.relative_to(ROOT))
        # phase tag = first 3 path components or fewer
        parts = rel.split("/")
        phase_tag = "/".join(parts[1:4]) if len(parts) > 3 else "/".join(parts[1:3])

        if ext in TEXT_EXTS:
            head = head200(p)
            desc = f"{p.name} :: {head[:160]}"
        elif ext == ".png":
            desc = f"PLOT :: {p.name}"
            head = ""
        elif ext == ".parquet":
            desc = f"PARQUET :: {p.name}"
            head = ""
        else:
            desc = f"OTHER :: {p.name}"
            head = ""

        # detect products from full path + head
        prods = detect_products(rel + " " + head)

        row = {
            "card_id": hash12(rel),
            "path": rel,
            "ext": ext,
            "size": stat.st_size,
            "mtime": int(stat.st_mtime),
            "phase_tag": phase_tag,
            "products_in_name": prods,
            "desc": desc[:240],
        }
        rows.append(row)

# write
with OUT.open("w") as f:
    for r in rows:
        f.write(json.dumps(r) + "\n")

# stats
ext_ct = Counter(r["ext"] for r in rows)
phase_ct = Counter(r["phase_tag"] for r in rows)
total_bytes = sum(r["size"] for r in rows)
text_files = [r for r in rows if r["ext"] in TEXT_EXTS]
plots = [r for r in rows if r["ext"] == ".png"]
parquets = [r for r in rows if r["ext"] == ".parquet"]

prods_set = set()
for r in rows:
    for p in r["products_in_name"]:
        prods_set.add(p)

mtimes = [r["mtime"] for r in rows]
import datetime as dt
date_min = dt.datetime.fromtimestamp(min(mtimes)).isoformat() if mtimes else ""
date_max = dt.datetime.fromtimestamp(max(mtimes)).isoformat() if mtimes else ""

lines = [
    "# Inventory Stats",
    "",
    f"- Total artefacts: {len(rows)}",
    f"- Total bytes: {total_bytes:,} ({total_bytes/1e6:.1f} MB)",
    f"- Text files: {len(text_files)}",
    f"- PNG plots: {len(plots)}",
    f"- Parquet files: {len(parquets)}",
    f"- Distinct products in filenames: {len(prods_set)}",
    f"- Date range: {date_min} → {date_max}",
    "",
    "## By extension",
]
for k, v in ext_ct.most_common():
    lines.append(f"- {k or '(none)'}: {v}")
lines.append("")
lines.append("## Top 30 phase tags")
for k, v in phase_ct.most_common(30):
    lines.append(f"- {k}: {v}")

STATS.write_text("\n".join(lines))
print(f"Wrote {len(rows)} rows to {OUT}")
print(f"Text: {len(text_files)}, PNG: {len(plots)}, Parquet: {len(parquets)}")
print(f"Total bytes: {total_bytes:,}")
