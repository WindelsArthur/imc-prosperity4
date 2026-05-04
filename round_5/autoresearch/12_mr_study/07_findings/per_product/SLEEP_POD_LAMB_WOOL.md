# SLEEP_POD_LAMB_WOOL

**Final 3-day PnL: +0**  ·  mode = `IDLE`

## Universe stats (day-2)
- spread_p50 = 10  ·  mid_std = 413  ·  bucket = `WEAK_DRIFT`
- ADF p = 0.505  ·  KPSS p = 0.01  ·  OU half-life = 1996.6
- AR(1)-on-Δmid coef = -0.008  (p = 0.417)
- lattice_ratio = 0.114

## Phase 1 — best FV (composite-z ranked)
- FV: `holt`  ·  IC|abs| = 0.016  ·  half-life = 14.79  ·  res/spread = 3.05

## Phase 2 — best in-sim threshold config (taker)
- FV `holt`  ·  z_in=2.50  z_out=0.10  sizing=fixed
- pnl_A (day-3 OOS) = +371  ·  pnl_B (day-4 OOS) = +568  ·  avg_daily = +470
- min_sharpe across folds = 0.15

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
