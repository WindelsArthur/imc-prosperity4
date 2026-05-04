#!/bin/bash
# Run all parameter-tuning phases sequentially.
# Each phase logs to its own dir; this driver appends to logs/progress.md.
set -e
set -o pipefail
cd "$(dirname "$0")/../../.."

PT="ROUND_5/autoresearch/parameter_tuning"
LOG="ROUND_5/autoresearch/logs/progress.md"

phase () {
    local label=$1
    shift
    echo "[$(date +%H:%M:%S)] === $label ==="
    "$@"
    echo "PT: phase $label completed at $(date +%H:%M:%S)" >> "$LOG"
}

# Phase 0 already done — skip if baseline_pnl.csv exists
if [ ! -f "$PT/00_baseline/baseline_pnl.csv" ]; then
    phase "0_baseline" python -u "$PT/00_baseline/build_baseline.py"
fi

# Phase 2 — Tier 1
if [ ! -f "$PT/02_tier1_universal/coarse_sweep/lhs_results.csv" ]; then
    phase "2a_lhs" python -u "$PT/02_tier1_universal/run_lhs.py"
fi
phase "2b_tpe" python -u "$PT/02_tier1_universal/run_tpe.py" 40
phase "2c_plateau" python -u "$PT/02_tier1_universal/run_plateau.py"
phase "2d_bootstrap" python -u "$PT/02_tier1_universal/run_bootstrap_top.py"
phase "2_checkpoint" python -u "$PT/_harness/checkpoints.py" tier1

# Phase 3 — Tier 2
if [ ! -f "$PT/03_tier2_group/pebbles_sweep/pebbles_sweep.csv" ]; then
    phase "3a_pebbles" python -u "$PT/03_tier2_group/run_pebbles.py"
fi
if [ ! -f "$PT/03_tier2_group/snackpack_sweep/snackpack_sweep.csv" ]; then
    phase "3b_snackpack" python -u "$PT/03_tier2_group/run_snackpack.py"
fi
if [ ! -f "$PT/03_tier2_group/quote_aggr_sweep.csv" ]; then
    phase "3c_aggr" python -u "$PT/03_tier2_group/run_quote_aggr.py"
fi

# Phase 4 — Tier 3
if [ ! -f "$PT/04_tier3_product/prod_cap_sweep/prod_cap_sweep.csv" ]; then
    phase "4_prod_cap" python -u "$PT/04_tier3_product/run_prod_cap_sweep.py"
fi

# Phase 5 — pair count
if [ ! -f "$PT/05_pair_count/n_sweep_results.csv" ]; then
    phase "5_n_pairs" python -u "$PT/05_pair_count/run_n_pairs.py"
fi
phase "5_checkpoint" python -u "$PT/_harness/checkpoints.py" pair_count

# Phase 7 — assembly (must come before stress, since stress reads winner)
phase "7_assembly" python -u "$PT/07_assembly/build_assembly.py"

# Phase 6 — stress
phase "6_stress" python -u "$PT/06_stress_battery/run_stress.py"
phase "6_checkpoint" python -u "$PT/_harness/checkpoints.py" stress

# Phase 8 — findings
phase "8_findings" python -u "$PT/08_findings/build_findings.py"

echo "[$(date +%H:%M:%S)] === ALL PHASES COMPLETE ==="
