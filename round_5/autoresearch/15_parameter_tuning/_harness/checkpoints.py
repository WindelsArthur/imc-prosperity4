"""Generate checkpoint.md after each phase as required by the mission spec."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

PT = Path(__file__).resolve().parents[1]


def tier1_checkpoint() -> str:
    """checkpoint after Phase 2: what changed in Tier 1, plateau widths."""
    out = ["# Phase 2 (Tier-1 Universal) Checkpoint\n"]
    lhs_p = PT / "02_tier1_universal" / "coarse_sweep" / "lhs_results.csv"
    tpe_p = PT / "02_tier1_universal" / "tpe_results" / "tpe_trials.csv"
    plateau_p = PT / "02_tier1_universal" / "fine_sweep" / "plateau_summary.csv"
    winner_p = PT / "02_tier1_universal" / "tier1_winner.json"

    out.append("## LHS coarse sweep")
    if lhs_p.exists():
        d = pd.read_csv(lhs_p)
        out.append(f"- {len(d)} configs evaluated")
        if "fold_median" in d.columns:
            out.append(f"- baseline rank by fold_median: see lhs_results.csv")
            out.append(f"- top fold_median: {d.fold_median.max():,.0f}")
            out.append(f"- median across all configs: {d.fold_median.median():,.0f}")
    out.append("")

    out.append("## TPE optimization")
    if tpe_p.exists():
        d = pd.read_csv(tpe_p)
        out.append(f"- {len(d)} TPE trials")
        if "fold_median" in d.columns:
            out.append(f"- best fold_median: {d.fold_median.max():,.0f}")
    out.append("")

    out.append("## Plateau analysis")
    if plateau_p.exists():
        d = pd.read_csv(plateau_p)
        out.append(d.to_markdown(index=False) if hasattr(d, 'to_markdown') else d.to_string(index=False))
    out.append("")

    out.append("## Decision")
    if winner_p.exists():
        w = json.loads(winner_p.read_text())
        out.append(f"- Decision: **{w.get('decision', 'unknown')}**")
        if w.get("decision") == "tier1_uplift":
            out.append(f"- Params: {w.get('params')}")
            out.append(f"- fair_quote_gate: {w.get('fair_quote_gate')}")
            up = w.get("uplift_vs_baseline", {})
            out.append(f"- Δ fold_mean: {up.get('delta_fold_mean'):+,.0f}")
            out.append(f"- Δ fold_median: {up.get('delta_fold_median'):+,.0f}")
            out.append(f"- Δ boot_q05: {up.get('delta_boot_q05'):+,.0f}")
        elif w.get("decision") == "revert_to_baseline":
            out.append(f"- Reverted: {w.get('rationale', '')}")
            out.append(f"- Params kept at: {w.get('params')}")

    (PT / "02_tier1_universal" / "checkpoint.md").write_text("\n".join(out))
    return "\n".join(out)


def pair_count_checkpoint() -> str:
    out = ["# Phase 5 (Pair Count) Checkpoint\n"]
    fp = PT / "05_pair_count" / "n_sweep_results.csv"
    wp = PT / "05_pair_count" / "pair_count_winner.json"
    if fp.exists():
        d = pd.read_csv(fp)
        out.append(f"## Sweep results ({len(d)} configurations)")
        out.append(d.to_markdown(index=False) if hasattr(d, 'to_markdown') else d.to_string(index=False))
    out.append("")
    if wp.exists():
        w = json.loads(wp.read_text())
        out.append(f"## Decision: **{w.get('decision', '')}**")
        out.append(f"- N: {w.get('N')}")
        out.append(f"- rank_method: {w.get('rank_method')}")
    (PT / "05_pair_count" / "checkpoint.md").write_text("\n".join(out))
    return "\n".join(out)


def stress_checkpoint() -> str:
    out = ["# Phase 6 (Stress Battery) Checkpoint\n"]
    sp = PT / "06_stress_battery" / "stress_results.csv"
    sm = PT / "06_stress_battery" / "stress_summary.csv"
    if sp.exists():
        d = pd.read_csv(sp)
        out.append("## Headline stress results")
        for stress in ["match_mode", "latency", "limit", "day_only"]:
            sub = d[d.stress == stress]
            if not sub.empty:
                out.append(f"### {stress}")
                cols = [c for c in ["mode", "lagged", "limit", "day", "fold_median",
                                     "fold_mean", "fold_min", "total_3day", "max_dd",
                                     "pnl"] if c in sub.columns]
                out.append(sub[cols].to_markdown(index=False) if hasattr(sub[cols], 'to_markdown') else sub[cols].to_string(index=False))
                out.append("")
        pert = d[d.stress == "perturbation"].copy()
        if not pert.empty and "fold_median" in pert.columns:
            med = pert.fold_median.dropna()
            out.append("### perturbation (LHS ±20%)")
            out.append(f"- n_samples: {len(med)}")
            out.append(f"- q05 fold_median: {med.quantile(0.05):,.0f}")
            out.append(f"- median fold_median: {med.median():,.0f}")
            out.append(f"- q95 fold_median: {med.quantile(0.95):,.0f}")
    (PT / "06_stress_battery" / "checkpoint.md").write_text("\n".join(out))
    return "\n".join(out)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: checkpoints.py [tier1|pair_count|stress]")
        sys.exit(1)
    fn = {"tier1": tier1_checkpoint, "pair_count": pair_count_checkpoint,
          "stress": stress_checkpoint}.get(sys.argv[1])
    if fn:
        print(fn())
