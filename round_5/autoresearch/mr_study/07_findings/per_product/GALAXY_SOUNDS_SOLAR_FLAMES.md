# GALAXY_SOUNDS_SOLAR_FLAMES

**Final 3-day PnL: +0**  ·  mode = `IDLE`

## Universe stats (day-2)
- spread_p50 = 14  ·  mid_std = 450  ·  bucket = `WEAK_DRIFT`
- ADF p = 0.245  ·  KPSS p = 0.01  ·  OU half-life = 1441.2
- AR(1)-on-Δmid coef = -0.024  (p = 0.0155)
- lattice_ratio = 0.124

## Phase 1 — best FV (composite-z ranked)
- FV: `median_100`  ·  IC|abs| = 0.016  ·  half-life = 46.30  ·  res/spread = 3.61

## Phase 2 — best in-sim threshold config (taker)
- FV `mean_100`  ·  z_in=2.50  z_out=0.25  sizing=fixed
- pnl_A (day-3 OOS) = -4520  ·  pnl_B (day-4 OOS) = +1490  ·  avg_daily = -1515
- min_sharpe across folds = -1.66

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
