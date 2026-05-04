"""Phase 4 — per-product PROD_CAP sweep.

For each of the 10 currently-capped products, holding all other caps + Tier 1+2
at winners, sweep cap ∈ {2..10}. Save per-product results.
"""
from __future__ import annotations

import sys
import json
from pathlib import Path

import pandas as pd
from joblib import Parallel, delayed

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _harness.harness import eval_config

OUT = Path(__file__).resolve().parent / "prod_cap_sweep"
OUT.mkdir(parents=True, exist_ok=True)
TIER1 = Path(__file__).resolve().parents[1] / "02_tier1_universal" / "tier1_winner.json"
TIER2_PEB = Path(__file__).resolve().parents[1] / "03_tier2_group" / "tier2_pebbles_winner.json"
TIER2_SNK = Path(__file__).resolve().parents[1] / "03_tier2_group" / "tier2_snackpack_winner.json"

DEFAULT_PROD_CAP = {
    "SLEEP_POD_LAMB_WOOL": 3, "UV_VISOR_MAGENTA": 4, "PANEL_1X2": 3,
    "TRANSLATOR_SPACE_GRAY": 4, "ROBOT_MOPPING": 4, "PANEL_4X4": 4,
    "GALAXY_SOUNDS_SOLAR_FLAMES": 4, "SNACKPACK_RASPBERRY": 5,
    "SNACKPACK_CHOCOLATE": 5, "PEBBLES_L": 4,
}

CAP_GRID = [2, 3, 4, 5, 6, 8, 10]


def load_base():
    base_params = {"PAIR_TILT_DIVISOR": 3.0, "PAIR_TILT_CLIP": 7.0,
                   "INV_SKEW_BETA": 0.20, "QUOTE_BASE_SIZE_CAP": 8,
                   "QUOTE_AGGRESSIVE_SIZE": 2,
                   "PEBBLES_SKEW_DIVISOR": 5.0, "PEBBLES_SKEW_CLIP": 3.0,
                   "PEBBLES_BIG_SKEW": 1.8,
                   "SNACKPACK_SKEW_DIVISOR": 5.0, "SNACKPACK_SKEW_CLIP": 5.0,
                   "SNACKPACK_BIG_SKEW": 3.5}
    gate = 0.25
    if TIER1.exists():
        w = json.loads(TIER1.read_text())
        base_params.update(w.get("params", {}))
        gate = float(w.get("fair_quote_gate", gate))
    if TIER2_PEB.exists():
        base_params.update(json.loads(TIER2_PEB.read_text()).get("params", {}))
    if TIER2_SNK.exists():
        base_params.update(json.loads(TIER2_SNK.read_text()).get("params", {}))
    return base_params, gate


def main():
    base, gate = load_base()
    print(f"[prod_cap] base={base} gate={gate}")
    print(f"[prod_cap] sweeping {len(DEFAULT_PROD_CAP)} products × {len(CAP_GRID)} caps")

    jobs = []
    for prod, cur_cap in DEFAULT_PROD_CAP.items():
        for c in CAP_GRID:
            jobs.append((prod, c))

    def _one(prod, cap):
        cap_dict = dict(DEFAULT_PROD_CAP)
        cap_dict[prod] = int(cap)
        res = eval_config(base, prod_cap=cap_dict, fair_quote_gate=gate,
                          capture_ticks=False, n_bootstrap=0)
        return {
            "product": prod, "cap": cap, "current_cap": DEFAULT_PROD_CAP[prod],
            "fold_median": res.fold_median, "fold_mean": res.fold_mean,
            "fold_min": res.fold_min, "fold_pos": res.fold_positive_count,
            "total_3day": res.total_pnl_3day, "sharpe": res.sharpe_3day,
            "max_dd": res.max_dd_3day,
            "prod_pnl": res.per_product_3day.get(prod, 0),
        }

    from concurrent.futures import ThreadPoolExecutor, as_completed
    rows = []
    with ThreadPoolExecutor(max_workers=3) as ex:
        futs = [ex.submit(_one, p, c) for p, c in jobs]
        for fut in as_completed(futs):
            rows.append(fut.result())
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "prod_cap_sweep.csv", index=False)
    print(df.sort_values(["product", "cap"]).to_string(index=False))

    # Pick winner per product: gate on +1K incremental over current cap config
    BASELINE_MEDIAN = 363578
    BASELINE_MEAN = 362034
    BASELINE_MIN = 354448
    chosen = dict(DEFAULT_PROD_CAP)
    decisions = {}
    for prod in DEFAULT_PROD_CAP:
        sub = df[df["product"] == prod].copy()
        cur_cap = DEFAULT_PROD_CAP[prod]
        # baseline-cap row for this product
        base_row = sub[sub["cap"] == cur_cap]
        base_med = base_row["fold_median"].iloc[0] if not base_row.empty else BASELINE_MEDIAN
        base_min = base_row["fold_min"].iloc[0] if not base_row.empty else BASELINE_MIN
        # Candidates: pass all-folds-positive AND fold_median > base_med + 1000
        cand = sub[(sub["fold_min"] > 0)
                   & (sub["fold_median"] >= base_med + 1000)
                   & (sub["fold_min"] >= base_min - 500)]
        if cand.empty:
            chosen[prod] = cur_cap
            decisions[prod] = {"old": int(cur_cap), "new": int(cur_cap),
                               "decision": "revert"}
        else:
            top = cand.sort_values("fold_median", ascending=False).iloc[0]
            new_cap = int(top["cap"])
            chosen[prod] = new_cap
            decisions[prod] = {"old": int(cur_cap), "new": new_cap,
                               "delta_median": float(top["fold_median"] - base_med),
                               "decision": "uplift"}

    winner = {
        "decision": "tier3_caps",
        "prod_cap": chosen,
        "per_product": decisions,
    }
    import json as _json
    (Path(__file__).resolve().parent / "tier3_winner.json").write_text(_json.dumps(winner, indent=2))
    print(f"\n[prod_cap] decisions: {decisions}")


if __name__ == "__main__":
    main()
