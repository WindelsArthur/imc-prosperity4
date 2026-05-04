# Theme: Lattice / quasi-discrete products

## Definition
Mid takes a small number of distinct values across the 30,000-tick training window. Implies the true price moves between a small set of grid levels and the residual reverts predictably.

## Products affected (re-verified)

| Product | n_distinct_mids | Lattice ratio | AR(1) on Δmid | v3 PnL (3-day) | mr_v6 mode |
|---|---:|---:|---:|---:|---|
| OXYGEN_SHAKE_EVENING_BREATH | **453** | **0.0151** | −0.123 | +11,905 | MM-skew (ar_diff p=1) |
| ROBOT_IRONING | 631 | 0.0210 | −0.125 | +1,064 | IDLE |
| ROBOT_DISHES | 3,048 | 0.1016 | −0.232 | −2,982 | TAKER (rolling_mean w=50, z_in=2.5) |

*Sources:* `ROUND_5/autoresearch/02_microstructure/`, `ROUND_5/batch1_summary/03_reconciliation/reverify_results/stats_reverify.csv`, `ROUND_5/autoresearch/mr_study/06_strategy_mr/distilled_params.py`.

## Findings
- **OXYGEN_SHAKE_EVENING_BREATH is the standout**: only 453 distinct mid levels in 30,000 ticks. AR(1) = −0.123 makes Δmid mean-revert at lag 1. v3 gets +11.9K with default MM + inv_skew. mr_v6 layered an `ar_diff p=1` signal skew on top.
- **ROBOT_IRONING** has even tighter discreteness (631 / 30,000 = 2.1%). AR(1) = −0.125. But its tight ~6-tick spread combined with directional drift makes inside-spread MM lose to flow — mr_v6 chose IDLE. v3 keeps default MM and earns +1K only.
- **ROBOT_DISHES** has AR-BIC depth p=9 with AR(1) = −0.232 (strongest in universe). Day-of-day distributions diverge (KS p≈0). v3 loses 3K with passive MM — mr_v6 found that a TAKER on rolling_mean(w=50) with z_in=2.5 captures +11.2K.

## Decision for final algo
- Keep all three products in default MM (preserve v3 baseline).
- **TEST in Phase H ablation:**
  1. Adding `ar_diff` skew on OXYGEN_SHAKE_EVENING_BREATH (mr_v6 logic).
  2. Switching ROBOT_DISHES to TAKER mode (rolling_mean w=50, z_in=2.5σ).
  3. IDLE-ing ROBOT_IRONING.

## Expected PnL contribution
v3 baseline contribution from these three: +10.0K total. Upside if ablation succeeds: +5–15K.
