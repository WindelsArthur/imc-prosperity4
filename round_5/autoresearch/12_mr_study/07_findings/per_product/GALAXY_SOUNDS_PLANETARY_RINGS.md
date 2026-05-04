# GALAXY_SOUNDS_PLANETARY_RINGS

**Final 3-day PnL: +0**  ·  mode = `IDLE`

## Universe stats (day-2)
- spread_p50 = 14  ·  mid_std = 766  ·  bucket = `WEAK_DRIFT`
- ADF p = 0.985  ·  KPSS p = 0.01  ·  OU half-life = inf
- AR(1)-on-Δmid coef = -0.006  (p = 0.577)
- lattice_ratio = 0.172

## Phase 1 — best FV (composite-z ranked)
- FV: `quad_500`  ·  IC|abs| = 0.019  ·  half-life = 61.00  ·  res/spread = 4.08

## Phase 2 — best in-sim threshold config (taker)
- FV `ewma_50`  ·  z_in=2.00  z_out=0.10  sizing=fixed
- pnl_A (day-3 OOS) = +7120  ·  pnl_B (day-4 OOS) = -1995  ·  avg_daily = +2562
- min_sharpe across folds = -0.35

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
