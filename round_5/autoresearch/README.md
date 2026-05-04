# Round 5 — autoresearch

A structured, multi-phase research pipeline run with [Claude Code](https://www.anthropic.com/claude-code), inspired by <https://github.com/karpathy/autoresearch>.  It takes the 50-product Round-5 universe from raw CSVs to the shipped trading algorithm, with every decision (kept or rejected) backed by an artifact in the corresponding folder.

The pipeline is split into two blocks:

- **Numbered phases `00_…` → `12_…`** are the *experiments* — descriptive statistics, microstructure, statistical-pattern discovery, cross-product structure, signal hunting.
- **Numbered phases `13_…` → `16_…`** are the *deliverables* — synthesised findings, the first shippable strategy, parameter tuning, and the post-tuning audit that produced the final algo.

Each folder is self-auditable: open any phase, read its `decision.md` / `findings.md` / `headline.md`, and you'll see exactly what was tested and why we kept or dropped it.

---

## Headline numbers — strategy evolution

| Stage | Algorithm | 3-day backtest PnL | Sharpe | Max DD | Source |
|---|---|---:|---:|---:|---|
| First-pass strategy | `14_final_strategy/strategy.py` | 396 749 | 4.22 | 30 772 | [`13_findings/findings.md`](13_findings/findings.md) |
| Round-2 with PROD_CAP for bleeders | `10_round2_research/M_submit/strategy_v2.py` | 531 525 | 8.61 | 26 286 | [`10_round2_research/M_submit/findings_v2.md`](10_round2_research/M_submit/findings_v2.md) |
| Tuned (157 cross-group pairs) | `15_parameter_tuning/algo1.py` | 1 436 024 | 13.0 | 27 243 | [`15_parameter_tuning/08_findings/headline.md`](15_parameter_tuning/08_findings/headline.md) |
| **Final shipped** (post-audit `v04`) | `16_post_audit/04_combined_assembly/algo1_post_audit_v04.py` | **1 420 758** | **22.81** | **25 532** | [`16_post_audit/06_findings/headline.md`](16_post_audit/06_findings/headline.md) |

The final shipped algo trades −15 K of total PnL for **higher Sharpe (22.8 vs 13.0)** and **+13 K fold-min** vs the tuned version — a deliberate risk-adjusted choice, validated by 5-fold OOS testing.

The shipped algorithm appears in this repo at [`../Algo/algo_r5.py`](../Algo/algo_r5.py).

---

## Universe (recap)

50 products in 10 groups of 5, position limit **10** for every product:

```
PEBBLES        L M S XL XS
SNACKPACK      CHOCOLATE PISTACHIO RASPBERRY STRAWBERRY VANILLA
MICROCHIP      CIRCLE OVAL RECTANGLE SQUARE TRIANGLE
SLEEP_POD      COTTON LAMB_WOOL NYLON POLYESTER SUEDE
ROBOT          DISHES IRONING LAUNDRY MOPPING VACUUMING
GALAXY_SOUNDS  BLACK_HOLES DARK_MATTER PLANETARY_RINGS SOLAR_FLAMES SOLAR_WINDS
OXYGEN_SHAKE   CHOCOLATE EVENING_BREATH GARLIC MINT MORNING_BREATH
PANEL          1X2 1X4 2X2 2X4 4X4
TRANSLATOR     ASTRO_BLACK ECLIPSE_CHARCOAL GRAPHITE_MIST SPACE_GRAY VOID_BLUE
UV_VISOR       AMBER MAGENTA ORANGE RED YELLOW
```

3 days of historical data (5-2, 5-3, 5-4); the algo is graded on a 4th unseen day.

---

## Folder map

### Experiments (numbered `00`–`12`)

| Phase | Question it answers |
|---|---|
| [`00_data_inventory/`](00_data_inventory/) | Raw schema, sanity checks, missing-data audit (counterparty fields are empty — bot fingerprinting impossible). |
| [`01_eda/`](01_eda/) | Per-product / per-group / global descriptive stats and distributions. |
| [`02_microstructure/`](02_microstructure/) | Order-book depth, quoted spread, queue dynamics, tick-level autocorrelation. |
| [`03_trade_flow/`](03_trade_flow/) | Aggressor inference (Lee-Ready), trade imbalance, signed-flow IC. |
| [`04_statistical_patterns/`](04_statistical_patterns/) | ADF / KPSS stationarity, regime detection, vol clustering, distribution checks. |
| [`05_within_group_cointegration/`](05_within_group_cointegration/) | Pairwise cointegration **inside** each group; basket-residual analysis. |
| [`06_cross_group_cointegration/`](06_cross_group_cointegration/) | Cointegration **across** groups; currency-basket-style invariants. |
| [`07_hidden_patterns/`](07_hidden_patterns/) | Lattice / quasi-discrete products, intraday seasonality, sine-fit candidates. |
| [`08_signals/`](08_signals/) | Distilled signals: feature → expected edge → IC, half-life, capacity. |
| [`09_strategy_design/`](09_strategy_design/) | Per-product strategy notes (mostly empty — promoted to phase 14). |
| [`10_round2_research/`](10_round2_research/) | Advanced studies: Johansen rank ≥ 2, sine OOS, multi-level OFI, intraday seasonality, min-var baskets, Markov-VECM. Submission `v2` lives in `M_submit/`. |
| [`11_lag_research/`](11_lag_research/) | Lagged cointegration sweep (1 200 pair × lag), lead-lag validation, AR-extended models, VAR / Granger, lagged OFI. Source of the 30 (later 157) cross-group pairs. |
| [`12_mr_study/`](12_mr_study/) | Pure mean-reversion ablation: 45 fair-value families × thresholds × sizing across 50 products. Standalone PnL 399 K, used as a sanity-floor benchmark. |

### Deliverables (numbered `13`–`16`)

| Phase | Contents |
|---|---|
| [`13_findings/`](13_findings/) | [`findings.md`](13_findings/findings.md) — top-15 patterns ranked by PnL contribution; [`per_group_findings.md`](13_findings/per_group_findings.md) — per-group breakdowns; [`exploitable_patterns.md`](13_findings/exploitable_patterns.md) — mechanism / capacity / strategy-slot for each surviving pattern. |
| [`14_final_strategy/`](14_final_strategy/) | First shippable strategy ([`strategy.py`](14_final_strategy/strategy.py)) and its [PnL estimates](14_final_strategy/pnl_estimates.md). |
| [`15_parameter_tuning/`](15_parameter_tuning/) | 5-tier hyperparameter sweep that took the baseline from 1 083 K to 1 436 K. Includes `audit/`, the audit-of-the-tuning that flagged loser fragility and pair stability. Final tuned algo: [`algo1.py`](15_parameter_tuning/algo1.py). |
| [`16_post_audit/`](16_post_audit/) | Three targeted alpha-extraction studies on top of the tuned algo: ROBOT_DISHES dedicated handler, AR(1) skew overlay, drift-aware inv-skew. The shipped variant `v04` lives in `04_combined_assembly/`. |

### Cross-cutting

- [`utils/`](utils/) — shared helpers: data loader, statistics, plotting, backtester wrapper.
- [`logs/`](logs/) — append-only timeline of decisions across the whole pipeline.
- `notebooks/` — exploratory notebooks; promoted findings get migrated into the numbered folders.
- `plots/` — saved figures referenced from markdown files.

> **Excluded from the repo:** the `10_backtesting/` results dir (~21 GB of sweep logs), `preship_validation/` (~3.8 GB), `log_study/` (~2.5 GB), and the `data_views/` parquet caches.  All are trivially regenerable from the raw CSVs in [`../Data/`](../Data/) by re-running the sweeps.

---

## Key findings — what worked

Each item below is an alpha that **made it into the shipped algorithm**.  Evidence locations are the canonical CSVs / markdown produced by the corresponding phase.

### 1. PEBBLES sum ≡ 50 000 (deterministic basket invariant)

- `Σ mid_i ∈ [49 981, 50 016]` over 30 000 ticks; std **2.8**; OU half-life **0.16 ticks** (essentially instantaneous reversion).
- Any pebble regressed on the other four: R² = **0.999998**, slope ≈ −1 each, intercept ≈ 50 000.
- Spread on each individual pebble ~13 ticks → the residual is too small to *cross*; we exploit it as a **passive skew** instead: each pebble's quote price is tilted by `−resid_residual / divisor` so the inside-spread market-make picks up the residual on the way back to zero.

### 2. SNACKPACK sum ≈ 50 221 (looser basket)

- Same construction, ~10× noisier (`Σ_i mid_i = 50 221 ± 190`).  Off-diagonal returns correlation **−0.16** (group is internally anti-correlated).
- Best within-group cointegration: `RASPBERRY/VANILLA` ADF **p = 0.001**, OOS Sharpe 1.5–1.8.
- Same passive-skew mechanism with a smaller divisor; aggressive cross only fires when residual exceeds 3.5 σ (very rare in practice, effectively a safety valve).

### 3. Within-group cointegrating pairs (9 kept)

| Pair | slope | ADF p | OOS Sharpe (A / B) |
|---|---:|---:|---:|
| `MICROCHIP_RECTANGLE / MICROCHIP_SQUARE` | −0.40 | 0.004 | 1.91 / 1.37 |
| `ROBOT_LAUNDRY / ROBOT_VACUUMING` | 0.33 | 0.026 | 1.19 / 1.70 |
| `SLEEP_POD_COTTON / SLEEP_POD_POLYESTER` | 0.52 | 0.033 | 1.32 / 1.89 |
| `GALAXY_SOUNDS_DARK_MATTER / PLANETARY_RINGS` | 0.18 | 0.037 | 1.61 / 2.00 |
| `SNACKPACK_RASPBERRY / SNACKPACK_VANILLA` | 0.01 | 0.001 | 1.77 / 1.45 |
| `SNACKPACK_CHOCOLATE / SNACKPACK_STRAWBERRY` | −0.11 | 0.009 | 1.50 / 1.98 |
| `UV_VISOR_AMBER / UV_VISOR_MAGENTA` | −1.24 | 0.023 | 0.98 / 0.85 |
| `TRANSLATOR_ECLIPSE_CHARCOAL / TRANSLATOR_VOID_BLUE` | 0.46 | 0.041 | 2.10 / 0.72 |
| `SLEEP_POD_POLYESTER / SLEEP_POD_SUEDE` | 0.76 | 0.052 | 1.90 / 1.12 |

Each pair contributes a `pair_skew` term to **both** legs.

### 4. Cross-group cointegrating pairs (30 → 157)

The Phase-11 lagged-EG sweep produced 1 200 candidate pairs.  221 passed the joint filter (ADF p < 0.05 AND OU half-life ∈ [5, 1000] AND |β| within bounds), 171 cleared a min-fold OOS Sharpe ≥ 0.7.  Top examples (full list in [`11_lag_research/C_lagged_coint/lagged_coint_surviving.csv`](11_lag_research/C_lagged_coint/)):

- `PEBBLES_XL ↔ PANEL_2X4` (slope ≈ 2.48, β stable across days)
- `UV_VISOR_AMBER ↔ SNACKPACK_STRAWBERRY` (slope ≈ −2.45)
- `OXYGEN_SHAKE_GARLIC ↔ PEBBLES_S` (slope ≈ −1.01, ADF p = 0.002)
- `PEBBLES_M ↔ OXYGEN_SHAKE_MORNING_BREATH` (slope ≈ −0.90)
- `MICROCHIP_SQUARE ↔ SLEEP_POD_SUEDE` (slope ≈ 1.85)

Phase-15 parameter tuning showed PnL is **monotonic in pair count** up to N = 157 — every additional surviving pair adds incremental edge with no observed capacity collision.  N = 30 → 157 was the single largest tuning win (+178 K incremental).

### 5. Lattice / quasi-deterministic products

- `OXYGEN_SHAKE_EVENING_BREATH` — only **453 distinct mids** in 30 000 ticks (lattice ratio 0.015), gzip-ratio 0.088, AR(1) **−0.124**.
- `ROBOT_IRONING` — 631 distinct mids (ratio 0.021), AR(1) **−0.129**.
- Treated as standard inside-spread MM with the global inv-skew β = 0.20.  Tested as TAKER targets but the AR(1) skew magnitude (`|φ · Δmid · α|` ≈ 0.24 $) is below the maker's `fair > bid − 0.25` order-gate, so the overlay would fire zero orders.

### 6. ROBOT_DISHES dedicated handler

- Strongest AR coefficient in the universe: AR(1) = **−0.27**, BIC selects p = 9.  But day-of-day distributions break (KS p ≈ 0).
- Per-day AR(1) regime: φ_d2 = −0.001, φ_d3 = −0.004, φ_d4 = **−0.290** — the textbook AR(1) is a Day-4 artefact, not a stable signal.
- Solution (Phase 16): a **dedicated handler** that removes ROBOT_DISHES from the global pair-skew dict and replaces it with tilts derived from 4 novel log-space pairs (`PEBBLES_S`, `PANEL_2X4`, `GALAXY_SOUNDS_BLACK_HOLES`, `SNACKPACK_STRAWBERRY` against `ROBOT_DISHES`), plus a tighter `inv_skew_β = 0.6`.  Per-pair clip 10 dollars.
- Result: +10 500 fold-min uplift, +20 803 ROBOT_DISHES 3-day, all 5 folds positive Δ.  Winning config `1c_c10_b0.6` in [`16_post_audit/01_robot_dishes_specialised/winner.json`](16_post_audit/01_robot_dishes_specialised/).

### 7. Per-product position caps (`PROD_CAP`)

Phase-10 bleeder forensics (Phase B) identified 9 products where `spread / vol < 0.6` → MM was being adversely selected and bleeding to informed flow.  Capping each at ±3 to ±5 recovered **+134 K** in v2's ablation (the entire v1 → v2 delta).  Phase-15 tuning later released some of those caps (`SLEEP_POD_LAMB_WOOL`, `SNACKPACK_RASPBERRY`, `SNACKPACK_CHOCOLATE` back to ±10) because the looser Tier-2 PEBBLES/SNACKPACK skews made them profitable bleeders, and tightened `ROBOT_MOPPING` to ±2.  The final cap dict is inlined into [`../Algo/algo_r5.py`](../Algo/algo_r5.py).

### 8. Per-product inv-skew β overrides (Phase 16)

- `MICROCHIP_OVAL`: β = **0.40** (vs global 0.20).
- `SLEEP_POD_POLYESTER`: β = **0.40**.
- `ROBOT_DISHES`: β = **0.60** (combined with the dedicated handler).

These overrides failed the strict 5-gate as **standalone** changes (mean uplift below +2 K threshold) but were promoted into the combined v04 assembly because they ride along nicely with the ROBOT_DISHES dedicated handler — combined Δfold-min = +13 026.

### 9. Inside-spread market-making (the workhorse)

Generic `bid_at_bb+1`, `ask_at_ba−1` with inventory skew applied to all 50 products.  This is not exotic alpha — it's the floor every other signal sits on top of.  Per-tick spread capture is the dominant PnL contributor in absolute terms.

---

## What was dropped — and why

Every item below was **tested** by the pipeline and **excluded** from the shipped algorithm.  The reasons matter as much as the headline findings: each of these would be tempting to include if you only looked at one in-sample number.

### Failed reverify on full data

- **`OXYGEN_SHAKE_CHOCOLATE / OXYGEN_SHAKE_GARLIC` cointegration** — claimed ADF p = 0.030 (round 1), reverified p = **0.918** on the full stitched window.  Dropped.  Both legs still participate in cross-group pairs, which spot-check at p < 0.01.

### Failed walk-forward OOS

- **Sine-fit overlay on 7 products** (`MICROCHIP_OVAL`, `UV_VISOR_AMBER`, `OXYGEN_SHAKE_GARLIC`, `SLEEP_POD_POLYESTER`/`SUEDE`, `PEBBLES_XS`/`XL`).  In-sample R² ≥ 0.96 with `A·sin(ωt + φ) + ct + d`, but the fitted period **equals the training-window length** — extrapolation to day 5 introduces phase risk.  Per-day OOS MSE comparison: only `UV_VISOR_AMBER` improves on the flat-mean baseline (−90 % MSE fold A, −43 % fold B).  v2 ablation of the AMBER overlay alone: **−496 PnL**.  All seven dropped.  See [`10_round2_research/A_sine/decision.md`](10_round2_research/A_sine/decision.md).
- **`SNACKPACK` min-var weighted basket** — minimum-variance weights tighter than equal-weight (rel-std 0.0023 vs 0.004), but ablation: **−68 PnL** swap.  Dropped — keep the equal-weight Σ = 50 221 invariant.
- **Cross-group min-var triplets** — 157 stationary triplets exist (e.g. `MICROCHIP_SQUARE/PEBBLES_XS/PANEL_2X4`), but residual std is too large vs spread cost.  Dropped.

### Dominated by a simpler alternative

- **Lead-lag pairs** — Phase-A leadlag scan found only 1 of 100 candidates surviving the decay-stability filter (`PANEL_1X4 → PANEL_1X2` at lag 33, ~2 K/day).  Below the +15 K PnL threshold for inclusion, and PANEL_1X2/1X4 already participate in within-group cointegration.  Dropped.
- **`mr_study` TAKER mode for 7 products** — `12_mr_study/strategy_mr.py` (399 K) earns +63 K cumulative on TAKER mode for 7 products that v3 doesn't TAKE.  But v3 TOTAL = 733 K, so layering basket+pair overlays on passive MM **dominates per-product TAKER selection**.  Dropped for products already winners under passive MM.
- **Higher-rank Johansen cointegration** — only `PEBBLES` has rank 1 (already used as Σ = 50 000); `SNACKPACK` has rank 5 but the second cointegrating vector has residual std 0.96 → tiny capacity.  No other group has rank > 0.  Dropped.
- **Multi-level OFI** — max IC = **0.10**; negative on lattice products.  Embedded in `PROD_CAP` via Phase-B bleeder analysis instead.  Dropped as standalone signal.
- **Lagged OFI / cross-flow** — strongest signal is just AR(1) restated (max |IC| = 0.090 at k = 1, own `ROBOT_IRONING`).  Cross-product OFI(i) → ret(j) max |IC| = 0.017.  Dropped.
- **Extended AR / lag-IC** — AR-BIC selects p > 1 for some products, but max |IC| at k > 1 is **0.038** (`ROBOT_IRONING@k=96`).  Insufficient after spread.  Dropped.
- **VAR / Granger within-group** — 4 trivial leaders, no positive Sharpe.  Dropped.
- **Intraday seasonality** — 100-bin mod-day patterns; max cross-day correlation **0.13**, all below the 0.30 inclusion threshold.  Dropped.
- **AR(1) maker-skew on priority products** — Phase-16 Hypothesis 2.  Three products survive cross-day stability (`OXYGEN_SHAKE_EVENING_BREATH`, `ROBOT_IRONING`, `OXYGEN_SHAKE_CHOCOLATE`) but the skew magnitude `|φ · Δmid · α|` ≈ 0.24 $ falls **below** the maker's `fair > bid − 0.25` order-gate, so the overlay fires zero orders.  Dropped (would require a TAKER reformulation, out of scope).

### Failed strict 5-gate joint test (single-metric overfit)

Phase-15 Tier-1 (universal hyperparameters) ran a 50-trial Latin Hypercube + 40-trial TPE sweep, plus a 24-cell plateau analysis.  Best candidates beat the baseline on **mean** PnL but lost on **median** by ≥ 0.2 % — classic overfitting.  Verdict: **revert to baseline**, the parameters sit on a robust plateau where no neighbour uniformly dominates.

Notable rejected candidates:

- `lhs_011` (div = 1.81, clip = 10.56, β = 0.135) — mean +8 608, fold-min +8 391 (HIGHER than baseline) **but** median −740.  Killed by the strict median gate.
- `lhs_023` (β = 0.335) — Sharpe **73.7** vs baseline 63 (higher!), but mean −531, median −5 366.  Sharpe alone is misleading when total PnL is the goal.

### Deferred for compute / diminishing returns

- **LightGBM residual signals** (Phase-10 E) — would have to train + integrate; v3's pure-OLS approach found +201 K already.  Diminishing returns.
- **Markov-switching VECM / Kalman β** (Phase-10 H, also Phase-11) — implicit handling via inv-skew + tilt-clip is a reasonable approximation.
- **Multi-lag basket invariants** — PEBBLES Σ = 50 000 already captures the strongest invariant.
- **Avellaneda-Stoikov optimal MM** (Phase-10 I) — replaced by `PROD_CAP`, which is a special case of optimal sizing on bleeders.
- **Multi-level quote depth tapering** (Phase-10 J) — strategy already passive at `bb+1 / ba−1`.

Full audit lives in [`15_parameter_tuning/08_findings/what_was_dropped.md`](15_parameter_tuning/08_findings/what_was_dropped.md) and [`16_post_audit/06_findings/what_was_dropped.md`](16_post_audit/06_findings/what_was_dropped.md).

---

## Anti-overfitting protocol

Three gates that any candidate signal had to clear before being shipped:

1. **Walk-forward OOS** — rotating folds (train 2 days, test on the 3rd, rotate).  Required min-fold OOS Sharpe ≥ 1 (≥ 0.7 for a few raw cointegration filters, but the tuning later required min-fold ≥ 1).  Phase-15 used a 5-fold protocol (F1 = day3, F2 = day4, F3 = day3, F4 = day2, F5 = day3) for a stricter test.

2. **ADF re-verify on full stitched window** — every claimed cointegration was re-checked on the full 30 000-tick stitched series, not just on the fold that produced it.  This is what dropped `OXYGEN_SHAKE_CHOCOLATE / OXYGEN_SHAKE_GARLIC` (claimed p = 0.03, full-stitch p = 0.92).

3. **Strict 5-gate ablation** in `15_parameter_tuning/` and `16_post_audit/`:
   - **(a)** mean uplift ≥ +2 K vs the locked baseline,
   - **(b)** median PnL ≥ baseline median (no median regression allowed),
   - **(c)** all 5 folds positive Δ (no fold may go backwards),
   - **(d)** fold-min ≥ baseline fold-min (worst-day floor must improve),
   - **(e)** max-DD ≤ 1.20× baseline DD (drawdown gate).

   "Beating baseline on one number while losing on another is a classic overfitting signature."  Phase-15 dropped 0 of 50 LHS candidates and 0 of 40 TPE candidates against this gate, and reverted Tier-1 to baseline.

Beyond the automated gates, every conclusion was hand-verified by reading raw CSVs and reproducing headline statistics from scratch.  Stress battery in `15_parameter_tuning/06_stress_battery/` covers match-mode (`worse` vs `all`), latency +1 tick, limit-8 (capacity stress), day-removal, and ±20 % LHS perturbation on the parameter vector.

### Critical absence — counterparty fields

Phase-3 found that `Trade.buyer` and `Trade.seller` are **empty in every row** of `trades_round_5_day_*.csv`.  The original prompt assumed counterparty fingerprinting (Round-4-style "Mark" identification) would be possible; it is not.  Aggregate signed-flow IC ≈ 0.01 — flow is not informed.  See [`00_data_inventory/inventory.md`](00_data_inventory/inventory.md).

---

## Final shipped algorithm (one-screen description)

[`../Algo/algo_r5.py`](../Algo/algo_r5.py) is one Trader class with a single `take + clean + make` template applied to all 50 products.  Per-product fair value:

```
fair_i = mid_i  +  basket_skew_i  +  pair_skew_i  +  inventory_skew_i (+ dishes_dedicated_i)
```

| Component | Source | Effect |
|---|---|---|
| `basket_skew` | PEBBLES Σ = 50 000 / SNACKPACK Σ = 50 221 | residual basket → quote tilt |
| `pair_skew` | 9 within-group + 30 cross-group cointegration pairs | per-pair tilt aggregated per product |
| `inventory_skew` | β = 0.20 globally; 0.40 for `MICROCHIP_OVAL`, `SLEEP_POD_POLYESTER`; 0.60 for `ROBOT_DISHES` | `−β · pos` keeps net inventory near zero |
| `dishes_dedicated` | 4 novel log-pair residuals + dedicated handler | ROBOT_DISHES only — replaces its global pair-skew contribution |
| `PROD_CAP` | 10 historical bleeders | hard cap below the ±10 limit |
| Aggressive cross | basket residual ≥ `BIG_SKEW` σ | size-2 cross when basket is far from invariant |

Otherwise the algorithm sits passively one tick inside the inside-spread.

3-day backtest on R5 days 2/3/4: **1 420 758 PnL · Sharpe 22.81 · max DD 25 532 · Calmar 55.6**.

5-fold OOS protocol (mission rule, `match_mode = worse`):

| Fold (test day) | PnL |
|---|---:|
| F1 (day 3) | 464 142 |
| F2 (day 4) | 459 226 |
| F3 (day 3) | 464 142 |
| F4 (day 2) | 497 389 |
| F5 (day 3) | 464 142 |
| **fold-min** | **459 226** |
| fold-median | 464 142 |
| fold-mean | 469 808 |

---

## Reproducing

```bash
imcp/bin/prosperity4btest cli round_5/Algo/algo_r5.py 5-2 5-3 5-4 \
    --no-progress --merge-pnl
```

Expected total: **1 420 758**; Sharpe 22.81; max DD 25 532.  Run-to-run engine variance for the matching engine is roughly ±20 K on tied prices, so 1.40 M – 1.44 M is an acceptable band.
