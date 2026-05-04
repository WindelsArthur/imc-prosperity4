# ROBOT_IRONING

**Final 3-day PnL: +0**  ·  mode = `IDLE`

## Universe stats (day-2)
- spread_p50 = 6  ·  mid_std = 771  ·  bucket = `DETERMINISTIC`
- ADF p = 0.451  ·  KPSS p = 0.01  ·  OU half-life = 1234.7
- AR(1)-on-Δmid coef = -0.162  (p = 0)
- lattice_ratio = 0.021

## Phase 1 — best FV (composite-z ranked)
- FV: `ar1_dx`  ·  IC|abs| = 0.100  ·  half-life = 0.14  ·  res/spread = 1.15

## Phase 2 — best in-sim threshold config (taker)
- FV `ar5_dx`  ·  z_in=2.50  z_out=0.10  sizing=fixed
- pnl_A (day-3 OOS) = +93  ·  pnl_B (day-4 OOS) = -77  ·  avg_daily = +8
- min_sharpe across folds = -0.39

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
