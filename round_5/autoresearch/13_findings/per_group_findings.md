# Per-Group Findings

Stats are stitched across days 2,3,4. PnL columns are 3-day cumulatives from
the `--match-trades worse` walk-forward (parsed from
`10_backtesting/results/walk_forward_summary.csv`).

## pebbles
- **Sum invariant:** Σmid ≈ 50,000, std **2.8**, range [49,981, 50,016].
- Basket residual half-life **0.16 ticks** ≈ instantaneous reversion.
- All 5 products linearly determine each other: regressing any pebble on
  the other four gives R² = 0.999998 with coefficients ≈ −1 each and
  intercept ≈ 50,000.
- Strategy: passive inside-spread MM with `skew_i = -resid/5`.
- 3-day per-pebble PnL: XL +50,715; S +15,783; XS +9,685; M −17,298;
  L −3,346 — net +55K.

## snackpack
- **Sum invariant:** Σmid ≈ 50,221, std 190 (10× weaker than pebbles).
- Best EG pair RASPBERRY/VANILLA, ADF p=0.0013, OOS Sharpe 1.5–1.8.
- Highest negative ret-corr off-diagonals (-0.16) — products move opposite.
- Days 2/3 vs day 4 KS distance modest (p > 0.01 for most pairs).
- 3-day PnL is dominated by the basket signal and is uneven —
  STRAWBERRY +22.9K, RASPBERRY −31.9K, CHOCOLATE −16.4K.
  Net +9.0K. Future work: shrink the basket skew when individual residual
  exceeds 2σ to avoid one-sided runs.

## microchip
- 3 products with very tight ~5-tick spread: CIRCLE, OVAL, RECTANGLE,
  TRIANGLE. SQUARE wider (~12).
- Best EG pair RECTANGLE/SQUARE, slope −0.40, ADF p=0.004, OOS Sharpe 1.0–2.1.
- OVAL has sine R²=0.974 over the 30,000-tick stitched series (period = full
  series); same for SQUARE (0.94).
- Day-of-day stability is broken (KS p≈0) for OVAL and SQUARE — the level
  drifts with the sine.
- 3-day group PnL ≈ +68K.

## sleep_pod
- Most cointegrated pairs in the universe.
- Best WF Sharpe pairs: COTTON/POLYESTER 1.3–1.9, POLYESTER/SUEDE 1.1–1.9,
  LAMB_WOOL/SUEDE 2.2 fold-B (NaN fold-A).
- LAMB_WOOL is the noisiest leg — strategy lost −24.2K on it across 3 days.
- Group total +52K.

## robot
- IRONING (631 distinct mids) and DISHES (3,048) are lattice / quasi-discrete.
- DISHES has AR-BIC p=9, AR(1)=−0.265 — strongest short-horizon mean-reversion.
- LAUNDRY/VACUUMING cointegrated, slope 0.33, ADF p=0.026, OOS Sharpe 1.2–1.7.
- 3-day group PnL: +32.2K.

## galaxy_sounds
- DARK_MATTER/PLANETARY_RINGS cointegrated, slope 0.18, ADF p=0.04, Sharpe 1.6–2.0.
- SOLAR_FLAMES has the highest mod-K R² in this group (0.89 at K=20,000).
- 3-day group PnL: +42.3K.

## oxygen_shake
- EVENING_BREATH is one of the two lattice products (453 distinct mids).
  AR(1)=−0.13, AR-BIC p=2.
- CHOCOLATE has AR-BIC p=9, AR(1)=−0.09.
- CHOCOLATE/GARLIC pair, slope −0.16, ADF p=0.03.
- Days 2/3/4 KS p≈0 for CHOCOLATE — large structural break.
- 3-day group PnL: +68.2K.

## panel
- 1X4 cointegrated with 2X4 (Sharpe 1.07 fold-B).
- 1X2 is the worst MM target — −18.7K across 3 days (strong directional drift).
- 3-day group PnL: +31.2K.

## translator
- ECLIPSE/VOID_BLUE pair, slope 0.46, ADF p=0.04, Sharpe 0.5–2.1.
- SPACE_GRAY is the heaviest 3-day loser in the group: −4.8K.
- 3-day group PnL: +29.1K.

## uv_visor
- AMBER/MAGENTA pair, slope −1.24, ADF p=0.023, Sharpe 0.6 fold-B.
- AMBER has sine R²=0.962, period = full series.
- MAGENTA is the loser, −7.0K across 3 days.
- 3-day group PnL: +45.0K.
