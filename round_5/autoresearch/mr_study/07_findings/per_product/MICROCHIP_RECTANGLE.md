# MICROCHIP_RECTANGLE

**Final 3-day PnL: +0**  ·  mode = `IDLE`

## Universe stats (day-2)
- spread_p50 = 8  ·  mid_std = 752  ·  bucket = `WEAK_DRIFT`
- ADF p = 0.28  ·  KPSS p = 0.01  ·  OU half-life = 908.5
- AR(1)-on-Δmid coef = -0.003  (p = 0.738)
- lattice_ratio = 0.168

## Phase 1 — best FV (composite-z ranked)
- FV: `markov_20`  ·  IC|abs| = 0.007  ·  half-life = 0.09  ·  res/spread = 1.24

## Phase 2 — best in-sim threshold config (taker)
- FV `ar3_dx`  ·  z_in=2.50  z_out=0.50  sizing=fixed
- pnl_A (day-3 OOS) = -3272  ·  pnl_B (day-4 OOS) = -6284  ·  avg_daily = -4778
- min_sharpe across folds = -5.03

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
