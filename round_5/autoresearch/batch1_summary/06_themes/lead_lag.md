# Theme: Lead-lag

## Definition
Cross-correlation of returns peaks at non-zero lag k between two products. A leads B at lag k means signed-flow or returns at time t in A predict returns at t+k in B.

## Reconciled findings (negative result, mostly)
- **Phase A of round 3** ran exhaustive CCFs on returns and signed-flow: 50² × 161 lags × 3 days = ~1.2M CCFs. Bonferroni-corrected critical |ρ| = 0.040.
- Top-100 candidate lead-lag pairs reduced to **1 decay-stable signal**: PANEL_1X4 → PANEL_1X2 at lag 33 (~2K PnL/day, ≤6K total over 3 days).
- That single survivor was **omitted from v3** "to keep the strategy pure mean-reversion" (per `findings_v3.md`).

*Sources:* `ROUND_5/autoresearch/14_lag_research/A_atlas/`, `ROUND_5/autoresearch/14_lag_research/B_leadlag/decision.md`, `ROUND_5/autoresearch/14_lag_research/O_submit/findings_v3.md`.

## What lag DOES capture
Round 3 Phase C found that **the lag dimension on PRICES (not returns) is rich** — but it reduces to **cointegration with hedge ratios different from contemporaneous OLS**. That is the +201K v2→v3 jump. So:

> Lag on returns / signed flow → ~empty (1 marginal signal worth 6K/3d).  
> Lag on prices → cointegration with non-instantaneous hedge ratio. **30 surviving pairs ship in v3.**

## VAR / Granger / extended-AR (Phase D, E)
- Within-group VAR(p) → 4 trivial leaders, no PnL.
- Extended AR / lag-IC → max |IC| at k>1 is 0.038 (ROBOT_IRONING@k=96). Insufficient for positive Sharpe after spread.

## Lagged OFI / cross-flow (Phase F)
- Top |IC| = 0.090 at k=1 (own-product OFI on ROBOT_IRONING) — but this is just the AR(1) reversion already captured by inv_skew.

## Decision for final algo
- **DROP standalone lead-lag overlay.** PANEL_1X4→PANEL_1X2 at 6K/3d is below the +15K PnL threshold for inclusion.
- The PANEL_1X4 / PANEL_2X4 cointegration (within-group) and several cross-group PANEL_2X4 pairs already capture residual structure in PANEL.

## Expected PnL contribution
0 (excluded). Could be reactivated in Phase H ablation if integration test shows ≥ +2K/day.
