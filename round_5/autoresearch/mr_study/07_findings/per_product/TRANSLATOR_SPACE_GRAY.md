# TRANSLATOR_SPACE_GRAY

**Final 3-day PnL: +0**  ·  mode = `IDLE`

## Universe stats (day-2)
- spread_p50 = 9  ·  mid_std = 503  ·  bucket = `WEAK_DRIFT`
- ADF p = 0.438  ·  KPSS p = 0.01  ·  OU half-life = 1317.0
- AR(1)-on-Δmid coef = 0.020  (p = 0.048)
- lattice_ratio = 0.124

## Phase 1 — best FV (composite-z ranked)
- FV: `lattice_5`  ·  IC|abs| = 0.011  ·  half-life = 0.16  ·  res/spread = 0.89

## Phase 2 — best in-sim threshold config (taker)
- FV `lattice_2`  ·  z_in=2.50  z_out=0.00  sizing=fixed
- pnl_A (day-3 OOS) = -10422  ·  pnl_B (day-4 OOS) = -6572  ·  avg_daily = -8497
- min_sharpe across folds = -5.73

## Chosen runtime config
```
{
  "mode": "IDLE"
}
```

## Why IDLE
Phase-2 simulator yielded no qualifying taker; Phase-3 real backtest with default MM lost money chronically. Quoting any size on this product injects net-negative PnL via adverse selection on directional moves.

## Expected day-5 PnL
0 (no orders).
