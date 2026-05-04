# GALAXY_SOUNDS_DARK_MATTER

**Final 3-day PnL: +5606**  ·  mode = `MM`

## Universe stats (day-2)
- spread_p50 = 13  ·  mid_std = 331  ·  bucket = `WEAK_DRIFT`
- ADF p = 0.355  ·  KPSS p = 0.01  ·  OU half-life = 930.3
- AR(1)-on-Δmid coef = 0.002  (p = 0.833)
- lattice_ratio = 0.097

## Phase 1 — best FV (composite-z ranked)
- FV: `ar2_dx`  ·  IC|abs| = 0.019  ·  half-life = 0.13  ·  res/spread = 0.64

## Phase 2 — best in-sim threshold config (taker)
- FV `ar3_dx`  ·  z_in=2.50  z_out=0.10  sizing=fixed
- pnl_A (day-3 OOS) = -9830  ·  pnl_B (day-4 OOS) = -11717  ·  avg_daily = -10774
- min_sharpe across folds = -6.52

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
≈ +1869 (= total / 3, given walk-forward stability).
