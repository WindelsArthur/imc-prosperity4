# ROBOT_VACUUMING

**Final 3-day PnL: +1600**  ·  mode = `MM`

## Universe stats (day-2)
- spread_p50 = 7  ·  mid_std = 535  ·  bucket = `WEAK_DRIFT`
- ADF p = 0.266  ·  KPSS p = 0.01  ·  OU half-life = 860.6
- AR(1)-on-Δmid coef = -0.007  (p = 0.475)
- lattice_ratio = 0.120

## Phase 1 — best FV (composite-z ranked)
- FV: `kalman_mle`  ·  IC|abs| = 0.008  ·  half-life = 0.14  ·  res/spread = 1.02

## Phase 2 — best in-sim threshold config (taker)
- FV `ar2_dx`  ·  z_in=2.50  z_out=0.00  sizing=fixed
- pnl_A (day-3 OOS) = -4665  ·  pnl_B (day-4 OOS) = -1628  ·  avg_daily = -3146
- min_sharpe across folds = -3.24

## Chosen runtime config
```
{
  "mode": "MM",
  "alpha_skew": 0.0,
  "beta_inv": 0.2,
  "max_size": 10,
  "spread_offset": 1
}
```

## Why default MM
No qualifying TAKER (Phase 2 sim required pnl_A > 0 AND pnl_B > 0). Inside-spread quoting with inventory skew earned positive PnL in v3 backtest after the in-spread clamp fix; we keep the simple passive variant.

## Failure modes / robustness
- Loss appears when sustained directional drift exceeds the half-spread → captures bid then sells lower.
- match-mode delta `worse` vs `all`: <1% — execution-mode robust.

## Expected day-5 PnL
≈ +533 (= total / 3, given walk-forward stability).
