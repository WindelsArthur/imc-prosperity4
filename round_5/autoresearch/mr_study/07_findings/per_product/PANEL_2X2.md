# PANEL_2X2

**Final 3-day PnL: +2530**  ·  mode = `MM`

## Universe stats (day-2)
- spread_p50 = 9  ·  mid_std = 675  ·  bucket = `WEAK_DRIFT`
- ADF p = 0.192  ·  KPSS p = 0.01  ·  OU half-life = 650.7
- AR(1)-on-Δmid coef = -0.014  (p = 0.176)
- lattice_ratio = 0.147

## Phase 1 — best FV (composite-z ranked)
- FV: `ar1_dx`  ·  IC|abs| = 0.011  ·  half-life = 0.15  ·  res/spread = 0.89

## Phase 2 — best in-sim threshold config (taker)
- FV `ar2_dx`  ·  z_in=2.50  z_out=0.50  sizing=fixed
- pnl_A (day-3 OOS) = -2948  ·  pnl_B (day-4 OOS) = -1780  ·  avg_daily = -2364
- min_sharpe across folds = -3.89

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
≈ +843 (= total / 3, given walk-forward stability).
