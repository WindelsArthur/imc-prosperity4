"""Phase 7 — Assemble winners into algo1_tuned.py + ablation v00..v05."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _harness.harness import eval_config, render_algo

OUT = Path(__file__).resolve().parent
PT = Path(__file__).resolve().parents[1]
TIER1_F = PT / "02_tier1_universal" / "tier1_winner.json"
TIER2_PEB_F = PT / "03_tier2_group" / "tier2_pebbles_winner.json"
TIER2_SNK_F = PT / "03_tier2_group" / "tier2_snackpack_winner.json"
TIER3_F = PT / "04_tier3_product" / "tier3_winner.json"
TIER4_F = PT / "05_pair_count" / "pair_count_winner.json"

DEFAULT_TIER1 = {"PAIR_TILT_DIVISOR": 3.0, "PAIR_TILT_CLIP": 7.0,
                 "INV_SKEW_BETA": 0.20, "QUOTE_BASE_SIZE_CAP": 8}
DEFAULT_TIER2 = {"PEBBLES_SKEW_DIVISOR": 5.0, "PEBBLES_SKEW_CLIP": 3.0,
                 "PEBBLES_BIG_SKEW": 1.8,
                 "SNACKPACK_SKEW_DIVISOR": 5.0, "SNACKPACK_SKEW_CLIP": 5.0,
                 "SNACKPACK_BIG_SKEW": 3.5,
                 "QUOTE_AGGRESSIVE_SIZE": 2}
DEFAULT_GATE = 0.25


def _load_or(path, key, default):
    if not path.exists():
        return default
    d = json.loads(path.read_text())
    return d.get(key, default)


def main():
    # Compose final config from per-tier winners
    tier1 = DEFAULT_TIER1.copy()
    tier1_gate = DEFAULT_GATE
    if TIER1_F.exists():
        d = json.loads(TIER1_F.read_text())
        tier1.update(d.get("params", {}))
        tier1_gate = float(d.get("fair_quote_gate", DEFAULT_GATE))

    tier2 = DEFAULT_TIER2.copy()
    if TIER2_PEB_F.exists():
        tier2.update(json.loads(TIER2_PEB_F.read_text()).get("params", {}))
    if TIER2_SNK_F.exists():
        tier2.update(json.loads(TIER2_SNK_F.read_text()).get("params", {}))

    prod_cap = None
    if TIER3_F.exists():
        prod_cap = json.loads(TIER3_F.read_text()).get("prod_cap")

    pairs = None
    if TIER4_F.exists():
        pairs = json.loads(TIER4_F.read_text()).get("pairs")

    final_params = {**tier1, **tier2}
    final_gate = tier1_gate

    # Build ablation v00 → v05
    ablation = []
    print("[assembly] building ablation v00..v05")

    # v00: baseline
    res = eval_config(None, capture_ticks=True, n_bootstrap=1000)
    ablation.append(("v00_baseline", "default algo1", res, None))

    # v01: tier1 only
    res = eval_config(tier1, fair_quote_gate=tier1_gate,
                      capture_ticks=True, n_bootstrap=1000)
    ablation.append(("v01_tier1", "+ Tier-1 winner", res, None))

    # v02: tier1 + tier2
    res = eval_config(final_params, fair_quote_gate=tier1_gate,
                      capture_ticks=True, n_bootstrap=1000)
    ablation.append(("v02_tier12", "+ Tier-2 winners", res, None))

    # v03: tier1 + tier2 + tier3 (prod_cap)
    res = eval_config(final_params, fair_quote_gate=tier1_gate,
                      prod_cap=prod_cap, capture_ticks=True, n_bootstrap=1000)
    ablation.append(("v03_tier123", "+ Tier-3 prod_cap", res, prod_cap))

    # v04: + pair_count
    res = eval_config(final_params, fair_quote_gate=tier1_gate,
                      prod_cap=prod_cap, pairs=pairs,
                      capture_ticks=True, n_bootstrap=1000)
    ablation.append(("v04_full", "+ pair count winner", res, prod_cap))

    # v05: same as v04 (no stress relaxation applied unless winner provided)
    ablation.append(("v05_final", "Phase 6 stress relaxations applied (none yet)", res, prod_cap))

    rows = []
    for name, desc, r, _ in ablation:
        rows.append({
            "name": name, "desc": desc,
            "fold_mean": r.fold_mean, "fold_median": r.fold_median,
            "fold_min": r.fold_min, "fold_max": r.fold_max,
            "fold_pos": r.fold_positive_count,
            "total_3day": r.total_pnl_3day, "sharpe": r.sharpe_3day,
            "max_dd": r.max_dd_3day,
            "boot_q05": r.bootstrap_q05, "boot_q50": r.bootstrap_q50,
            "boot_q95": r.bootstrap_q95,
        })
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "ablation_vs_baseline.csv", index=False)
    print("\n=== ABLATION ===")
    print(df.to_string(index=False))

    # write algo1_tuned.py with all winners hardcoded
    src = render_algo(final_params, pairs=pairs, prod_cap=prod_cap, fair_quote_gate=final_gate)
    (OUT / "algo1_tuned.py").write_text(src)

    # write distilled_params_tuned.py for archival
    dp = []
    dp.append("# Tuned distilled params (ROUND_5/autoresearch/parameter_tuning/Phase 7).")
    dp.append("from __future__ import annotations\n")
    for k, v in final_params.items():
        dp.append(f"{k} = {v!r}")
    dp.append(f"FAIR_QUOTE_GATE = {final_gate!r}")
    if prod_cap:
        dp.append(f"PROD_CAP = {prod_cap!r}")
    if pairs:
        dp.append(f"\n# {len(pairs)} pairs")
        dp.append(f"ALL_PAIRS = {pairs!r}")
    (OUT / "distilled_params_tuned.py").write_text("\n".join(dp) + "\n")

    # walk-forward verification: rerun final config to confirm
    res_final = ablation[-1][2]
    wf = pd.DataFrame([
        {"fold": f["name"], "train": ",".join(map(str, f["train"])),
         "test_day": f["test"], "test_pnl": f["test_pnl"]}
        for f in res_final.folds
    ])
    wf.to_csv(OUT / "walk_forward_final.csv", index=False)
    print(f"\n[assembly] wrote {OUT}/algo1_tuned.py")


if __name__ == "__main__":
    main()
