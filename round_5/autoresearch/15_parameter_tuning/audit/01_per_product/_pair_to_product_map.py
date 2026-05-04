"""Cross-reference: which pairs touch each loser/fragility product?

Reads:
  - 03_pair_stability/pair_stability.csv  (β-shift per pair)
  - distilled_params_tuned.ALL_PAIRS

Writes a table: per loser/fragility product, which added pairs touch it,
their β-shift status. Helps decide which pairs to drop in Phase E.
"""
from __future__ import annotations
import json
from pathlib import Path

import pandas as pd

OUT = Path(__file__).resolve().parent
PT_DIR = Path(__file__).resolve().parents[2]
STABILITY_CSV = PT_DIR / "audit" / "03_pair_stability" / "pair_stability.csv"


def main():
    spec = PT_DIR / "07_assembly" / "distilled_params_tuned.py"
    ns: dict = {}
    exec(spec.read_text(), ns)
    all_pairs = ns["ALL_PAIRS"]
    stab = pd.read_csv(STABILITY_CSV)
    stab_lookup = {(r["a"], r["b"], float(r["slope_full"]), float(r["intercept_full"])): r
                   for _, r in stab.iterrows()}

    targets = [
        # losers
        "OXYGEN_SHAKE_CHOCOLATE", "UV_VISOR_AMBER", "MICROCHIP_OVAL",
        "OXYGEN_SHAKE_GARLIC", "SLEEP_POD_POLYESTER",
        # fragility
        "PANEL_1X2", "PANEL_1X4", "UV_VISOR_YELLOW", "ROBOT_IRONING",
        "TRANSLATOR_ASTRO_BLACK",
    ]

    rows = []
    for prod in targets:
        for idx, tup in enumerate(all_pairs):
            a, b, slope, intercept = tup[0], tup[1], float(tup[2]), float(tup[3])
            if prod not in (a, b):
                continue
            key = (a, b, slope, intercept)
            r = stab_lookup.get(key)
            beta_shift = float(r["beta_shift_pct"]) if r is not None else None
            adf_d3 = float(r["adf_p_d3_held_out"]) if r is not None else None
            adf_d4 = float(r["adf_p_d4_held_out"]) if r is not None else None
            rows.append({
                "product": prod,
                "pair_idx": idx,
                "is_added": idx >= 39,
                "a": a, "b": b, "slope": slope, "intercept": intercept,
                "role": "a" if a == prod else "b",
                "beta_shift_pct": beta_shift,
                "unstable_30pct": (beta_shift is not None and beta_shift > 0.30),
                "adf_p_d3": adf_d3, "adf_p_d4": adf_d4,
            })
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "loser_fragility_pairs.csv", index=False)

    md = ["# Loser / fragility products — pair touches\n"]
    for prod in targets:
        sub = df[df["product"] == prod].sort_values("beta_shift_pct", ascending=False)
        n = len(sub)
        n_add = int(sub["is_added"].sum())
        n_unst = int(sub["unstable_30pct"].sum())
        md.append(f"## {prod}  ({n} pairs touching it; {n_add} added; {n_unst} β-unstable)")
        if len(sub):
            md.append(sub[["pair_idx", "is_added", "a", "b", "role",
                          "beta_shift_pct", "unstable_30pct"]].to_markdown(index=False))
        md.append("")
    (OUT / "loser_fragility_pairs.md").write_text("\n".join(md))
    print(f"[touch_map] wrote loser_fragility_pairs.csv (rows={len(df)})")


if __name__ == "__main__":
    main()
