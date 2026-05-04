"""Phase 3c — QUOTE_AGGRESSIVE_SIZE 1D sweep."""
from __future__ import annotations

import sys
import json
from pathlib import Path

import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _harness.harness import eval_config

OUT = Path(__file__).resolve().parent
TIER1 = Path(__file__).resolve().parents[1] / "02_tier1_universal" / "tier1_winner.json"
TIER2_PEB = OUT / "tier2_pebbles_winner.json"
TIER2_SNK = OUT / "tier2_snackpack_winner.json"

GRID = [1, 2, 3, 4, 5]


def load_base():
    base = {"PAIR_TILT_DIVISOR": 3.0, "PAIR_TILT_CLIP": 7.0,
            "INV_SKEW_BETA": 0.20, "QUOTE_BASE_SIZE_CAP": 8,
            "PEBBLES_SKEW_DIVISOR": 5.0, "PEBBLES_SKEW_CLIP": 3.0,
            "PEBBLES_BIG_SKEW": 1.8,
            "SNACKPACK_SKEW_DIVISOR": 5.0, "SNACKPACK_SKEW_CLIP": 5.0,
            "SNACKPACK_BIG_SKEW": 3.5}
    gate = 0.25
    if TIER1.exists():
        d = json.loads(TIER1.read_text())
        base.update(d.get("params", {}))
        gate = float(d.get("fair_quote_gate", gate))
    if TIER2_PEB.exists():
        base.update(json.loads(TIER2_PEB.read_text()).get("params", {}))
    if TIER2_SNK.exists():
        base.update(json.loads(TIER2_SNK.read_text()).get("params", {}))
    return base, gate


def main():
    base, gate = load_base()
    print(f"[Aggr] base={base} gate={gate}")

    def _one(s):
        p = dict(base, QUOTE_AGGRESSIVE_SIZE=int(s))
        res = eval_config(p, fair_quote_gate=gate, capture_ticks=False, n_bootstrap=0)
        return {"QUOTE_AGGRESSIVE_SIZE": s,
                "fold_median": res.fold_median, "fold_mean": res.fold_mean,
                "fold_min": res.fold_min, "fold_pos": res.fold_positive_count,
                "total_3day": res.total_pnl_3day, "max_dd": res.max_dd_3day}

    rows = []
    with ThreadPoolExecutor(max_workers=2) as ex:
        futs = [ex.submit(_one, s) for s in GRID]
        for fut in as_completed(futs):
            rows.append(fut.result())
    df = pd.DataFrame(rows).sort_values("QUOTE_AGGRESSIVE_SIZE")
    df.to_csv(OUT / "quote_aggr_sweep.csv", index=False)
    print(df.to_string(index=False))

    BASELINE_MEAN = 362034
    BASELINE_MEDIAN = 363578
    cand = df[(df.fold_min > 0)
              & (df.fold_median >= BASELINE_MEDIAN)
              & (df.fold_mean >= BASELINE_MEAN + 2000)]
    winner_path = OUT / "tier2_quote_aggr_winner.json"
    if cand.empty:
        winner = {"decision": "revert_to_baseline",
                  "params": {"QUOTE_AGGRESSIVE_SIZE": 2}}
    else:
        top = cand.sort_values("fold_median", ascending=False).iloc[0]
        winner = {"decision": "tier2_aggr_uplift",
                  "params": {"QUOTE_AGGRESSIVE_SIZE": int(top.QUOTE_AGGRESSIVE_SIZE)},
                  "delta_fold_mean": float(top.fold_mean - BASELINE_MEAN)}
    import json as _json
    winner_path.write_text(_json.dumps(winner, indent=2))
    print(f"[Aggr] winner → {winner_path}: {winner['decision']}")


if __name__ == "__main__":
    main()
