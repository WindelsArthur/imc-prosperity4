# Theme: Sinusoidal / deterministic level fits

## Definition
Fit `mid(t) = A·sin(ωt + φ) + ct + d` over the 30,000-tick stitched training window. R² ≥ 0.9 implies a strong deterministic component in price level.

## Round 1 candidates (R² ≥ 0.9 on stitched series)

| Product | R² | Period (ticks) |
|---|---:|---:|
| MICROCHIP_OVAL | 0.974 | 30,000 (= full series) |
| UV_VISOR_AMBER | 0.962 | 30,000 |
| GALAXY_SOUNDS_SOLAR_FLAMES | (high) | varies |
| OXYGEN_SHAKE_GARLIC | 0.924 | 30,000 |
| SLEEP_POD_POLYESTER | 0.89 | 30,000 |
| SLEEP_POD_SUEDE | 0.91 | 30,000 |
| PEBBLES_XS | 0.95 | 30,000 |
| PEBBLES_XL | 0.87 | 30,000 |

*Source:* `ROUND_5/autoresearch/13_round2_research/A_sine/`.

## The fundamental problem
For 6 of 7 products, **the fitted period equals the training-window length**. That is the smoking gun for over-fitting: a single half-cycle perfectly fit by a sine is just regression noise, and extrapolation introduces phase risk.

## Phase A round-2 walk-forward verdict
Only **UV_VISOR_AMBER** survived OOS:
- 90% MSE improvement on fold A.
- 43% MSE improvement on fold B.
- Other 6 products: unstable phase, fold-MSE worse than constant baseline.

## Ablation impact in v2
Adding the UV_VISOR_AMBER sine overlay yielded **−496 PnL** in v2's ablation. Even the lone survivor doesn't pay after factoring in the inventory MM the strategy already runs.

*Source:* `ROUND_5/autoresearch/13_round2_research/M_submit/findings_v2.md` § Phase A; `ROUND_5/autoresearch/10_backtesting/results/abl_v2_no_sine_amber.csv`.

## Decision for final algo
- **DROP sine overlay entirely.** No sine fair-value extension for any product.
- Day-5 phase risk (the fitted period equals the training window) is acknowledged but unavoidable; no signal to trade.

## Expected PnL contribution
0 (excluded).
