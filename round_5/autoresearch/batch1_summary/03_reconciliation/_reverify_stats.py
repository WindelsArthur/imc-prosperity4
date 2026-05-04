"""Reverify the headline statistical claims:
- PEBBLES sum = 50,000 invariant (std)
- SNACKPACK sum = 50,221 invariant (std)
- 10 within-group cointegration pairs (ADF p-values)
- 30 cross-group cointegration pairs (sample of 5 spot-checks)
- AR(1) coefficients on top products
- Lattice (n_distinct_mids) for OXYGEN_SHAKE_EVENING_BREATH and ROBOT_IRONING

Output: reverify_results/stats_reverify.csv + .md
"""
from __future__ import annotations
import json, os, sys
from pathlib import Path
import numpy as np
import pandas as pd
from statsmodels.tsa.stattools import adfuller

ROOT = Path("/Users/arthurwindels/Documents/08_DEV/Prosperity4/IMC-Prosperity-4-Belmonte")
DATA = ROOT / "ROUND_5/Data"
OUT_DIR = ROOT / "ROUND_5/batch1_summary/03_reconciliation/reverify_results"
OUT_DIR.mkdir(parents=True, exist_ok=True)

DAYS = [2, 3, 4]
PEBBLES = ["PEBBLES_L","PEBBLES_M","PEBBLES_S","PEBBLES_XL","PEBBLES_XS"]
SNACKPACKS = ["SNACKPACK_CHOCOLATE","SNACKPACK_PISTACHIO","SNACKPACK_RASPBERRY",
              "SNACKPACK_STRAWBERRY","SNACKPACK_VANILLA"]

WITHIN_PAIRS = [
    ("MICROCHIP_RECTANGLE","MICROCHIP_SQUARE",-0.401,14119.0,0.004),
    ("ROBOT_LAUNDRY","ROBOT_VACUUMING",0.334,7072.0,0.026),
    ("SLEEP_POD_COTTON","SLEEP_POD_POLYESTER",0.519,5144.0,0.033),
    ("GALAXY_SOUNDS_DARK_MATTER","GALAXY_SOUNDS_PLANETARY_RINGS",0.183,8285.0,0.037),
    ("SNACKPACK_RASPBERRY","SNACKPACK_VANILLA",0.013,9962.0,0.001),
    ("SNACKPACK_CHOCOLATE","SNACKPACK_STRAWBERRY",-0.106,11051.0,0.009),
    ("UV_VISOR_AMBER","UV_VISOR_MAGENTA",-1.238,21897.0,0.023),
    ("OXYGEN_SHAKE_CHOCOLATE","OXYGEN_SHAKE_GARLIC",-0.155,11066.0,0.030),
    ("TRANSLATOR_ECLIPSE_CHARCOAL","TRANSLATOR_VOID_BLUE",0.456,4954.0,0.041),
    ("SLEEP_POD_POLYESTER","SLEEP_POD_SUEDE",0.756,2977.0,0.052),
]

CROSS_PAIRS_SPOT = [
    ("PEBBLES_XL","PANEL_2X4",2.4821,-14735.73),
    ("UV_VISOR_AMBER","SNACKPACK_STRAWBERRY",-2.4501,34143.94),
    ("PEBBLES_M","OXYGEN_SHAKE_MORNING_BREATH",-0.9037,19300.55),
    ("ROBOT_IRONING","PEBBLES_M",-0.9154,18096.05),
    ("MICROCHIP_SQUARE","SLEEP_POD_SUEDE",1.8678,-7692.97),
]

AR1_TARGETS = ["ROBOT_DISHES","OXYGEN_SHAKE_EVENING_BREATH","ROBOT_IRONING",
               "OXYGEN_SHAKE_CHOCOLATE","SNACKPACK_CHOCOLATE"]

LATTICE_TARGETS = ["OXYGEN_SHAKE_EVENING_BREATH","ROBOT_IRONING","ROBOT_DISHES"]

def load_mid_series(product: str, days=DAYS) -> pd.Series:
    """Stitch mid_price for a product across days."""
    pieces = []
    for d in days:
        f = DATA / f"prices_round_5_day_{d}.csv"
        df = pd.read_csv(f, sep=";")
        df = df[df["product"] == product].copy()
        df = df.sort_values("timestamp")
        df["mid"] = (df["bid_price_1"].astype(float) + df["ask_price_1"].astype(float)) / 2.0
        pieces.append(df["mid"].reset_index(drop=True))
    return pd.concat(pieces, ignore_index=True).dropna()

def basket_stats(group: list, target: float, name: str):
    series = []
    for p in group:
        s = load_mid_series(p)
        series.append(s)
    L = min(len(s) for s in series)
    s = pd.concat([sx.iloc[:L].reset_index(drop=True) for sx in series], axis=1).sum(axis=1)
    return {
        "claim": f"{name} sum invariant",
        "n": int(L),
        "mean": float(s.mean()),
        "std": float(s.std()),
        "min": float(s.min()),
        "max": float(s.max()),
        "target": target,
        "deviation_mean": float(s.mean() - target),
    }

def adf_pair(a, b, slope, intercept):
    sa = load_mid_series(a)
    sb = load_mid_series(b)
    L = min(len(sa), len(sb))
    sa = sa.iloc[:L].values
    sb = sb.iloc[:L].values
    resid = sa - slope * sb - intercept
    try:
        adf_stat, pval, *_ = adfuller(resid, maxlag=5, autolag=None)
    except Exception as e:
        return {"a":a,"b":b,"adf_p":None,"err":str(e)}
    # Half-life via OU
    dr = np.diff(resid)
    r = resid[:-1]
    if r.std() > 0:
        beta = np.cov(dr, r, ddof=0)[0,1] / np.var(r)
    else:
        beta = 0.0
    if beta < 0:
        hl = -np.log(2) / beta
    else:
        hl = float("inf")
    return {"a":a,"b":b,"slope":slope,"intercept":intercept,
            "adf_stat":float(adf_stat),"adf_p":float(pval),
            "half_life":float(hl),"resid_std":float(resid.std()),"n":int(L)}

def ar1_coef(product: str):
    s = load_mid_series(product)
    d = np.diff(s.values)
    if len(d) < 100: return {"product":product,"ar1":None}
    x = d[:-1]
    y = d[1:]
    if x.std() == 0: return {"product":product,"ar1":None}
    coef = np.corrcoef(x, y)[0,1]
    return {"product":product,"ar1":float(coef),"n":int(len(d))}

def lattice_stats(product: str):
    s = load_mid_series(product)
    n = len(s)
    nd = int(s.nunique())
    return {"product":product,"n":n,"n_distinct_mids":nd,"lattice_ratio":nd/n}

def main():
    rows = []
    print("Computing PEBBLES basket...")
    rows.append({"check":"PEBBLES","kind":"basket", **basket_stats(PEBBLES, 50000, "PEBBLES")})
    print("Computing SNACKPACK basket...")
    rows.append({"check":"SNACKPACK","kind":"basket", **basket_stats(SNACKPACKS, 50221, "SNACKPACK")})
    print("Computing within-group ADF pairs...")
    for a,b,sl,ic,p in WITHIN_PAIRS:
        r = adf_pair(a,b,sl,ic)
        r["check"] = f"WITHIN:{a}|{b}"; r["kind"] = "coint"; r["claimed_p"] = p
        rows.append(r)
        print(f"  {a}|{b}: ADF p={r.get('adf_p')} (claimed {p})")
    print("Computing cross-group ADF spot-checks...")
    for a,b,sl,ic in CROSS_PAIRS_SPOT:
        r = adf_pair(a,b,sl,ic)
        r["check"] = f"CROSS:{a}|{b}"; r["kind"] = "cross_coint"
        rows.append(r)
        print(f"  {a}|{b}: ADF p={r.get('adf_p')}")
    print("Computing AR(1) coefs...")
    for p in AR1_TARGETS:
        r = ar1_coef(p)
        r["check"] = f"AR1:{p}"; r["kind"] = "ar1"
        rows.append(r)
        print(f"  {p}: AR(1)={r.get('ar1')}")
    print("Computing lattice stats...")
    for p in LATTICE_TARGETS:
        r = lattice_stats(p)
        r["check"] = f"LATTICE:{p}"; r["kind"] = "lattice"
        rows.append(r)
        print(f"  {p}: n_distinct={r['n_distinct_mids']} ratio={r['lattice_ratio']:.4f}")

    # write csv + md
    df = pd.DataFrame(rows)
    df.to_csv(OUT_DIR/"stats_reverify.csv", index=False)
    with (OUT_DIR/"stats_reverify.md").open("w") as f:
        f.write("# Stats reverify\n\n")
        f.write(df.to_markdown(index=False))
    print(f"DONE: wrote {len(df)} rows")

if __name__ == "__main__":
    main()
