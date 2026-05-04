# TRANSLATOR_ECLIPSE_CHARCOAL

**Final 3-day PnL: +6536**  ·  mode = `MM`

## Universe stats (day-2)
- spread_p50 = 9  ·  mid_std = 356  ·  bucket = `WEAK_DRIFT`
- ADF p = 0.795  ·  KPSS p = 0.01  ·  OU half-life = 3274.2
- AR(1)-on-Δmid coef = -0.004  (p = 0.653)
- lattice_ratio = 0.105

## Phase 1 — best FV (composite-z ranked)
- FV: `ewma_10`  ·  IC|abs| = 0.012  ·  half-life = 9.38  ·  res/spread = 2.39

## Phase 2 — best in-sim threshold config (taker)
- FV `ewma_10`  ·  z_in=2.50  z_out=0.50  sizing=fixed
- pnl_A (day-3 OOS) = -2032  ·  pnl_B (day-4 OOS) = -1075  ·  avg_daily = -1554
- min_sharpe across folds = -1.19

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
≈ +2179 (= total / 3, given walk-forward stability).
