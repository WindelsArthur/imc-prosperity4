# SNACKPACK_PISTACHIO

**Final 3-day PnL: +1692**  ·  mode = `MM`

## Universe stats (day-2)
- spread_p50 = 16  ·  mid_std = 187  ·  bucket = `WEAK_DRIFT`
- ADF p = 0.132  ·  KPSS p = 0.01  ·  OU half-life = 756.2
- AR(1)-on-Δmid coef = -0.034  (p = 0.000657)
- lattice_ratio = 0.064

## Phase 1 — best FV (composite-z ranked)
- FV: `ar1_dx`  ·  IC|abs| = 0.018  ·  half-life = 0.16  ·  res/spread = 0.26

## Phase 2 — best in-sim threshold config (taker)
- FV `ar5_dx`  ·  z_in=2.50  z_out=0.00  sizing=fixed
- pnl_A (day-3 OOS) = -7191  ·  pnl_B (day-4 OOS) = -10675  ·  avg_daily = -8933
- min_sharpe across folds = -8.03

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
≈ +564 (= total / 3, given walk-forward stability).
