# SLEEP_POD_COTTON

**Final 3-day PnL: +8790**  ·  mode = `MM`

## Universe stats (day-2)
- spread_p50 = 10  ·  mid_std = 888  ·  bucket = `WEAK_DRIFT`
- ADF p = 0.465  ·  KPSS p = 0.01  ·  OU half-life = 1736.2
- AR(1)-on-Δmid coef = 0.009  (p = 0.348)
- lattice_ratio = 0.205

## Phase 1 — best FV (composite-z ranked)
- FV: `ewma_10`  ·  IC|abs| = 0.013  ·  half-life = 9.61  ·  res/spread = 2.50

## Phase 2 — best in-sim threshold config (taker)
- FV `ewma_10`  ·  z_in=2.50  z_out=0.00  sizing=fixed
- pnl_A (day-3 OOS) = -180  ·  pnl_B (day-4 OOS) = -6974  ·  avg_daily = -3577
- min_sharpe across folds = -1.39

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
≈ +2930 (= total / 3, given walk-forward stability).
