# SLEEP_POD_SUEDE

**Final 3-day PnL: +0**  ·  mode = `IDLE`

## Universe stats (day-2)
- spread_p50 = 10  ·  mid_std = 900  ·  bucket = `WEAK_DRIFT`
- ADF p = 0.919  ·  KPSS p = 0.01  ·  OU half-life = 7757.6
- AR(1)-on-Δmid coef = -0.000  (p = 0.978)
- lattice_ratio = 0.161

## Phase 1 — best FV (composite-z ranked)
- FV: `ewma_10`  ·  IC|abs| = 0.008  ·  half-life = 9.70  ·  res/spread = 2.38

## Phase 2 — best in-sim threshold config (taker)
- FV `linreg_500`  ·  z_in=2.00  z_out=0.00  sizing=fixed
- pnl_A (day-3 OOS) = -3652  ·  pnl_B (day-4 OOS) = +12927  ·  avg_daily = +4638
- min_sharpe across folds = -0.62

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
