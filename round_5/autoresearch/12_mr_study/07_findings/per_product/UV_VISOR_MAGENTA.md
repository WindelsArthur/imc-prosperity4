# UV_VISOR_MAGENTA

**Final 3-day PnL: +0**  ·  mode = `IDLE`

## Universe stats (day-2)
- spread_p50 = 14  ·  mid_std = 614  ·  bucket = `WEAK_DRIFT`
- ADF p = 0.892  ·  KPSS p = 0.01  ·  OU half-life = 5662.9
- AR(1)-on-Δmid coef = -0.008  (p = 0.436)
- lattice_ratio = 0.142

## Phase 1 — best FV (composite-z ranked)
- FV: `median_50`  ·  IC|abs| = 0.012  ·  half-life = 22.99  ·  res/spread = 2.52

## Phase 2 — best in-sim threshold config (taker)
- FV `ewma_25`  ·  z_in=2.50  z_out=0.25  sizing=fixed
- pnl_A (day-3 OOS) = +1087  ·  pnl_B (day-4 OOS) = -2876  ·  avg_daily = -894
- min_sharpe across folds = -0.86

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
