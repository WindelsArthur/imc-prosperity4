# SLEEP_POD_NYLON

**Final 3-day PnL: +1066**  ·  mode = `MM`

## Universe stats (day-2)
- spread_p50 = 9  ·  mid_std = 509  ·  bucket = `WEAK_DRIFT`
- ADF p = 0.566  ·  KPSS p = 0.01  ·  OU half-life = 1382.9
- AR(1)-on-Δmid coef = -0.004  (p = 0.725)
- lattice_ratio = 0.133

## Phase 1 — best FV (composite-z ranked)
- FV: `lattice_2`  ·  IC|abs| = 0.016  ·  half-life = 0.17  ·  res/spread = 0.91

## Phase 2 — best in-sim threshold config (taker)
- FV `lattice_5`  ·  z_in=2.50  z_out=0.50  sizing=fixed
- pnl_A (day-3 OOS) = -7165  ·  pnl_B (day-4 OOS) = -18584  ·  avg_daily = -12874
- min_sharpe across folds = -8.47

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
≈ +355 (= total / 3, given walk-forward stability).
