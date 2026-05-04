# UV_VISOR_RED

**Final 3-day PnL: -220**  ·  mode = `MM`

## Universe stats (day-2)
- spread_p50 = 14  ·  mid_std = 588  ·  bucket = `WEAK_DRIFT`
- ADF p = 0.0348  ·  KPSS p = 0.01  ·  OU half-life = 618.9
- AR(1)-on-Δmid coef = -0.002  (p = 0.875)
- lattice_ratio = 0.146

## Phase 1 — best FV (composite-z ranked)
- FV: `lattice_2`  ·  IC|abs| = 0.010  ·  half-life = 0.13  ·  res/spread = 0.61

## Phase 2 — best in-sim threshold config (taker)
- FV `mid_anchor`  ·  z_in=2.50  z_out=0.25  sizing=fixed
- pnl_A (day-3 OOS) = -8828  ·  pnl_B (day-4 OOS) = -31750  ·  avg_daily = -20289
- min_sharpe across folds = -9.89

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
≈ -73 (= total / 3, given walk-forward stability).
