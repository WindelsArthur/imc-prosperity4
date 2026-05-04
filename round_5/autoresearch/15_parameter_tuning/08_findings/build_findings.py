"""Phase 8 — generate headline.md, parameter_decisions.md, what_was_dropped.md.

Reads:
  00_baseline/baseline_pnl.csv
  07_assembly/ablation_vs_baseline.csv
  06_stress_battery/stress_summary.csv
  02_tier1_universal/tier1_winner.json
  03_tier2_group/tier2_*.json
  04_tier3_product/tier3_winner.json
  05_pair_count/pair_count_winner.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

OUT = Path(__file__).resolve().parent
PT = Path(__file__).resolve().parents[1]
BASELINE = PT / "00_baseline" / "baseline_pnl.csv"
ABLATION = PT / "07_assembly" / "ablation_vs_baseline.csv"
STRESS = PT / "06_stress_battery" / "stress_summary.csv"


def main():
    if not BASELINE.exists():
        print("[findings] baseline_pnl.csv missing — Phase 0 not done")
        return
    base = pd.read_csv(BASELINE).iloc[0]
    abl = pd.read_csv(ABLATION) if ABLATION.exists() else None
    stress = pd.read_csv(STRESS) if STRESS.exists() else None

    # tier winners
    winners = {}
    for tier_path, key in [
        (PT / "02_tier1_universal" / "tier1_winner.json", "tier1"),
        (PT / "03_tier2_group" / "tier2_pebbles_winner.json", "tier2_pebbles"),
        (PT / "03_tier2_group" / "tier2_snackpack_winner.json", "tier2_snackpack"),
        (PT / "03_tier2_group" / "tier2_quote_aggr_winner.json", "tier2_aggr"),
        (PT / "04_tier3_product" / "tier3_winner.json", "tier3"),
        (PT / "05_pair_count" / "pair_count_winner.json", "pair_count"),
    ]:
        if tier_path.exists():
            winners[key] = json.loads(tier_path.read_text())

    # ── headline.md ────────────────────────────────────────────────────────
    if abl is not None:
        v_final = abl[abl.name.str.startswith("v05")]
        v00 = abl[abl.name.str.startswith("v00")]
        if not v_final.empty and not v00.empty:
            vf = v_final.iloc[0]
            v0 = v00.iloc[0]
            headline = f"""# Headline — algo1 robust hyperparameter tuning

## Key numbers (5-fold protocol, --match-trades worse, limit=10)

| Metric | baseline (v00) | tuned (v_final) | Δ |
|---|---|---|---|
| fold mean PnL    | {v0.fold_mean:>12,.0f} | {vf.fold_mean:>12,.0f} | {vf.fold_mean - v0.fold_mean:+,.0f} |
| **fold median**  | **{v0.fold_median:>10,.0f}** | **{vf.fold_median:>10,.0f}** | {vf.fold_median - v0.fold_median:+,.0f} |
| fold min         | {v0.fold_min:>12,.0f} | {vf.fold_min:>12,.0f} | {vf.fold_min - v0.fold_min:+,.0f} |
| fold max         | {v0.fold_max:>12,.0f} | {vf.fold_max:>12,.0f} | {vf.fold_max - v0.fold_max:+,.0f} |
| 3-day total      | {v0.total_3day:>12,.0f} | {vf.total_3day:>12,.0f} | {vf.total_3day - v0.total_3day:+,.0f} |
| Sharpe (3-day)   | {v0.sharpe:>12.2f}    | {vf.sharpe:>12.2f}    | {vf.sharpe - v0.sharpe:+.2f} |
| max DD (3-day)   | {v0.max_dd:>12,.0f} | {vf.max_dd:>12,.0f} | {vf.max_dd - v0.max_dd:+,.0f} |
| bootstrap q05    | {v0.boot_q05:>12,.0f} | {vf.boot_q05:>12,.0f} | {vf.boot_q05 - v0.boot_q05:+,.0f} |

## Day-5 PnL projection

Anchored on per-day fold floors:
- **Low** (anchor: fold min)        ≈ {vf.fold_min:>12,.0f}
- **Mid** (anchor: fold median)     ≈ {vf.fold_median:>12,.0f}
- **High** (anchor: fold max)       ≈ {vf.fold_max:>12,.0f}

The mid is the natural point estimate. The low is the realistic floor —
a day-5 below this would be unprecedented in our 3-day calibration sample.

## Stress summary
{stress.to_string(index=False) if stress is not None else "(stress battery not yet run)"}
"""
            (OUT / "headline.md").write_text(headline)
            print(f"[findings] wrote {OUT}/headline.md")

    # ── parameter_decisions.md ─────────────────────────────────────────────
    decisions = ["# Parameter decisions\n"]
    for k, w in winners.items():
        decisions.append(f"## {k}")
        decisions.append("```json")
        decisions.append(json.dumps(w, indent=2))
        decisions.append("```\n")
    if not winners:
        decisions.append("(no tier winners — all phases reverted to baseline)\n")
    (OUT / "parameter_decisions.md").write_text("\n".join(decisions))

    # ── what_was_dropped.md ─────────────────────────────────────────────────
    dropped = ["# Configurations dropped during tuning\n"]
    for path, label in [
        (PT / "02_tier1_universal" / "coarse_sweep" / "lhs_results.csv", "Tier-1 LHS"),
        (PT / "02_tier1_universal" / "tpe_results" / "tpe_trials.csv", "Tier-1 TPE"),
        (PT / "02_tier1_universal" / "fine_sweep" / "plateau_sweep.csv", "Tier-1 plateau"),
        (PT / "03_tier2_group" / "pebbles_sweep" / "pebbles_sweep.csv", "PEBBLES"),
        (PT / "03_tier2_group" / "snackpack_sweep" / "snackpack_sweep.csv", "SNACKPACK"),
    ]:
        if not path.exists():
            continue
        df = pd.read_csv(path)
        if "fold_median" not in df.columns:
            continue
        # Configs that beat baseline median but failed gate (a) or (c)
        dropped.append(f"## {label}\n")
        beat = df[df.fold_median > base.fold_median_pnl] if "fold_median_pnl" in base.index else df[df.fold_median > 363578]
        failing_a = beat[beat.fold_mean < (362034 + 2000)]
        failing_c = beat[beat.fold_min <= 0]
        dropped.append(f"- beat baseline median: {len(beat)}")
        dropped.append(f"- failed gate (a) mean uplift: {len(failing_a)}")
        dropped.append(f"- failed gate (c) all-folds-positive: {len(failing_c)}")
        dropped.append("")
    (OUT / "what_was_dropped.md").write_text("\n".join(dropped))
    print(f"[findings] wrote {OUT}/what_was_dropped.md")


if __name__ == "__main__":
    main()
