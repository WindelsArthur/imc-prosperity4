# GALAXY_SOUNDS_SOLAR_WINDS

**Final 3-day PnL: +9320**  ·  mode = `MM`

## Universe stats (day-2)
- spread_p50 = 14  ·  mid_std = 541  ·  bucket = `WEAK_DRIFT`
- ADF p = 0.728  ·  KPSS p = 0.01  ·  OU half-life = 2373.3
- AR(1)-on-Δmid coef = -0.012  (p = 0.242)
- lattice_ratio = 0.140

## Phase 1 — best FV (composite-z ranked)
- FV: `quad_500`  ·  IC|abs| = 0.014  ·  half-life = 64.30  ·  res/spread = 4.38

## Phase 2 — best in-sim threshold config (taker)
- FV `median_500`  ·  z_in=2.00  z_out=0.50  sizing=fixed
- pnl_A (day-3 OOS) = +8360  ·  pnl_B (day-4 OOS) = -2025  ·  avg_daily = +3168
- min_sharpe across folds = -0.34

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
≈ +3107 (= total / 3, given walk-forward stability).
