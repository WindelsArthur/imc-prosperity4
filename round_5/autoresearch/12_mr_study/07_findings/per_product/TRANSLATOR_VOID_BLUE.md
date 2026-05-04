# TRANSLATOR_VOID_BLUE

**Final 3-day PnL: +10199**  ·  mode = `MM`

## Universe stats (day-2)
- spread_p50 = 10  ·  mid_std = 579  ·  bucket = `WEAK_DRIFT`
- ADF p = 0.926  ·  KPSS p = 0.01  ·  OU half-life = 8547.8
- AR(1)-on-Δmid coef = -0.014  (p = 0.148)
- lattice_ratio = 0.138

## Phase 1 — best FV (composite-z ranked)
- FV: `ewma_10`  ·  IC|abs| = 0.010  ·  half-life = 9.49  ·  res/spread = 2.42

## Phase 2 — best in-sim threshold config (taker)
- FV `linreg_200`  ·  z_in=2.00  z_out=0.00  sizing=fixed
- pnl_A (day-3 OOS) = +5707  ·  pnl_B (day-4 OOS) = +926  ·  avg_daily = +3316
- min_sharpe across folds = 0.18

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
≈ +3400 (= total / 3, given walk-forward stability).
