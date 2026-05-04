# SNACKPACK_STRAWBERRY

**Final 3-day PnL: +2614**  ·  mode = `MM`

## Universe stats (day-2)
- spread_p50 = 18  ·  mid_std = 364  ·  bucket = `WEAK_DRIFT`
- ADF p = 0.362  ·  KPSS p = 0.01  ·  OU half-life = 1131.3
- AR(1)-on-Δmid coef = -0.011  (p = 0.268)
- lattice_ratio = 0.103

## Phase 1 — best FV (composite-z ranked)
- FV: `microprice_ewma25`  ·  IC|abs| = 0.018  ·  half-life = 20.82  ·  res/spread = 1.39

## Phase 2 — best in-sim threshold config (taker)
- FV `mean_100`  ·  z_in=1.75  z_out=0.25  sizing=fixed
- pnl_A (day-3 OOS) = +1156  ·  pnl_B (day-4 OOS) = -27  ·  avg_daily = +564
- min_sharpe across folds = -0.01

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
≈ +871 (= total / 3, given walk-forward stability).
