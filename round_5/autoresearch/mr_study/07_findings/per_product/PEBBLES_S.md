# PEBBLES_S

**Final 3-day PnL: +22195**  ·  mode = `MM`

## Universe stats (day-2)
- spread_p50 = 12  ·  mid_std = 833  ·  bucket = `WEAK_DRIFT`
- ADF p = 0.516  ·  KPSS p = 0.01  ·  OU half-life = 1333.6
- AR(1)-on-Δmid coef = 0.014  (p = 0.153)
- lattice_ratio = 0.207

## Phase 1 — best FV (composite-z ranked)
- FV: `ewma_25`  ·  IC|abs| = 0.017  ·  half-life = 25.38  ·  res/spread = 4.60

## Phase 2 — best in-sim threshold config (taker)
- FV `ewma_50`  ·  z_in=1.25  z_out=0.00  sizing=fixed
- pnl_A (day-3 OOS) = +12323  ·  pnl_B (day-4 OOS) = -12966  ·  avg_daily = -322
- min_sharpe across folds = -1.29

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
≈ +7398 (= total / 3, given walk-forward stability).
