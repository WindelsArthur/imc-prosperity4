# OXYGEN_SHAKE_MINT

**Final 3-day PnL: +2122**  ·  mode = `MM`

## Universe stats (day-2)
- spread_p50 = 13  ·  mid_std = 508  ·  bucket = `WEAK_DRIFT`
- ADF p = 0.193  ·  KPSS p = 0.01  ·  OU half-life = 667.5
- AR(1)-on-Δmid coef = 0.011  (p = 0.274)
- lattice_ratio = 0.132

## Phase 1 — best FV (composite-z ranked)
- FV: `rangemid_500`  ·  IC|abs| = 0.023  ·  half-life = 261.39  ·  res/spread = 9.34

## Phase 2 — best in-sim threshold config (taker)
- FV `median_500`  ·  z_in=2.50  z_out=0.25  sizing=fixed
- pnl_A (day-3 OOS) = +2200  ·  pnl_B (day-4 OOS) = -2040  ·  avg_daily = +80
- min_sharpe across folds = -0.72

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
≈ +707 (= total / 3, given walk-forward stability).
