# Audit progress log

Robustness audit of `algo1_tuned` (3-day total 1,436,024 / fold_min 450,479 / Sharpe 13.03)
against `algo1` baseline (3-day total 1,083,016 / fold_min 354,448 / Sharpe 63.08).

Day-5 floor = fold_min, not fold_median.

---

## 2026-04-29 22:12 — Smoke tests

- `imcp/bin/prosperity4btest --help` — OK.
- `algo1_tuned.py` exists at `07_assembly/algo1_tuned.py`.
- Re-ran tuned on F2 (day-4 standalone via merged 5-2 5-3 5-4 with statelessness):
  observed day-2=520,225, day-3=465,320, day-4=450,479, total=1,436,024,
  Sharpe=13.0284 — exact match to `walk_forward_final.csv`.
- Re-ran baseline: total=1,083,016 / Sharpe=63.0810 — matches `00_baseline/baseline_pnl.csv`.

**Stateless trick confirmed**: per-day per-product PnL is invariant under merge,
so each fold's PnL = test-day standalone PnL. One 3-day merged run per algo
covers all 5 folds. F1=F3=F5 share day-3, F2=day-4, F4=day-2.

Audit infra: `audit/_audit_lib.py` parses per-day per-product blocks from the
merged stdout and renders `ALL_PAIRS` substitutions.

---

## 2026-04-29 22:18 — Phase A (per-product attribution)

Source: `audit/01_per_product/per_product_attribution.csv`,
        `audit/01_per_product/summary.json`,
        `audit/01_per_product/summary.md`,
        plots/{winner,loser}*.png.

Headline ledger:
- Δ total = **+353,008** (fold_min +96,031, fold_median +101,742).

**Top 5 winners (Δ3day desc, where the +353K comes from):**

| product             | base 3d | tuned 3d |  Δ3day | base fold_min | tuned fold_min | Δfold_min | added pairs |
|:--------------------|--------:|---------:|-------:|--------------:|---------------:|----------:|------------:|
| PEBBLES_XS          |   8,527 |   68,331 | +59,804|        -7,425 |         20,168 |  +27,593 |          11 |
| SNACKPACK_CHOCOLATE |  -8,223 |   31,346 | +39,569|        -4,591 |          9,150 |  +13,741 |           3 |
| SNACKPACK_RASPBERRY | -15,948 |   20,673 | +36,621|       -10,282 |          1,868 |  +12,150 |           0 |
| MICROCHIP_CIRCLE    |  10,381 |   40,045 | +29,664|        -1,208 |          9,165 |  +10,373 |           8 |
| SNACKPACK_VANILLA   |   3,873 |   29,969 | +26,096|        -3,475 |          8,069 |  +11,544 |           6 |

These 5 products = 191,754 of the +353K (54%). Note SNACKPACK_RASPBERRY gains
36.6K with **0 added pairs** — pure parameter-driven win (PROD_CAP 5→10,
SNACKPACK_BIG_SKEW 1.8→3.5, etc.).

**Top 5 losers (Δ3day asc, the cost):**

| product                | base 3d | tuned 3d |   Δ3day | base fold_min | tuned fold_min | Δfold_min | added pairs |
|:-----------------------|--------:|---------:|--------:|--------------:|---------------:|----------:|------------:|
| OXYGEN_SHAKE_CHOCOLATE |  23,573 |     -539 | -24,112 |         4,864 |        -13,891 |   -18,755 |           5 |
| UV_VISOR_AMBER         |  24,028 |   19,966 |  -4,062 |           752 |         -4,156 |    -4,908 |          17 |
| MICROCHIP_OVAL         |  11,011 |    7,227 |  -3,784 |           970 |             81 |      -889 |           2 |
| OXYGEN_SHAKE_GARLIC    |  60,605 |   57,658 |  -2,947 |        17,994 |         13,645 |    -4,349 |          12 |
| SLEEP_POD_POLYESTER    |  39,798 |   37,550 |  -2,248 |         5,429 |          5,172 |      -257 |          13 |

**OXYGEN_SHAKE_CHOCOLATE is the worst case**: lost -24K with fold_min collapsed
from +4.8K to **-13.9K**. That's a structural loss, not noise — the day-4 PnL
went to -13,891 in the tuned version.

**Fragility (median UP but fold_min DOWN — these gains are noise):**

| product                | Δmedian | Δfold_min | added pairs |
|:-----------------------|--------:|----------:|------------:|
| PANEL_1X2              |  +1,126 |    -3,731 |           7 |
| PANEL_1X4              |  +4,913 |    -2,412 |           4 |
| UV_VISOR_YELLOW        |  +1,016 |    -1,654 |           4 |
| ROBOT_IRONING          |    +118 |      -202 |          13 |
| TRANSLATOR_ASTRO_BLACK |  +2,348 |      -146 |           1 |

5 products. PANEL_1X2 and PANEL_1X4 are the standouts — small positive median
move masks meaningful tail risk.

---

## 2026-04-29 22:23 — Phase C (pair stability)

Source: `audit/03_pair_stability/pair_stability.csv`, `summary.json`, `summary.md`.

Method: for each tuned pair (a, b, slope_full, intercept_full), refit OLS
`a = β·b + α` on day-2 only, then test the day-2-fit (β,α) on days 3 and 4
(out-of-sample).

Findings:
- **β-shift >30%**: 82 / 166 pairs (61 of which are added pairs). This is
  the discriminating signal.
- **ADF holdout p>0.05**: fires on **166 / 166** pairs — the bar is too loose
  for intraday Prosperity series. Implication: the strategy is exploiting
  short-window mean-reversion, not true cointegration. ADF on 10K-tick
  intraday residuals naturally fails — interesting in itself.
- **Highly unstable** (β shift >50% OR ADF >0.20 on both d3 and d4):
  36 pairs (25 of which are added).

Decision: use β-shift >30% as the practical "unstable" cut for Phase E/F.

---

## 2026-04-29 22:27 — Phase D (variance decomposition)

Source: `audit/04_variance/variance_per_product.csv`, `summary.json`, `summary.md`,
        `top_variance_contributors.png`.

- baseline 3-day per-day std = **4,672** (Sharpe 63.08)
- tuned    3-day per-day std = **29,999** (Sharpe 13.03)
- Δ per-day std = **+25,326**.

Variance is **highly concentrated**: top-10 products account for **90.9%** of
the total per-product variance increase. The major contributors:

| product                 | base xday_std | tuned xday_std | Δxday_std |
|:------------------------|--------------:|---------------:|----------:|
| OXYGEN_SHAKE_CHOCOLATE  |         2,154 |          9,949 |    +7,795 |
| PEBBLES_XL              |         5,360 |         12,905 |    +7,545 |
| UV_VISOR_AMBER          |         5,579 |         10,251 |    +4,672 |
| PANEL_1X4               |         6,770 |         10,703 |    +3,933 |
| OXYGEN_SHAKE_GARLIC     |         2,070 |          4,486 |    +2,416 |
| OXYGEN_SHAKE_MORN_BR.   |         3,960 |          6,239 |    +2,279 |
| PANEL_1X2               |           254 |          2,471 |    +2,218 |
| SLEEP_POD_LAMB_WOOL     |         1,315 |          2,820 |    +1,506 |
| GALAXY_SOUNDS_SOLAR_W.  |        12,746 |         14,186 |    +1,440 |
| ROBOT_IRONING           |         6,905 |          8,118 |    +1,212 |

Same products keep recurring across Phases A, C and D:
**OXYGEN_SHAKE_CHOCOLATE, UV_VISOR_AMBER, PANEL_1X2, PANEL_1X4** are flagged in
multiple slices — they are the candidates for Phase E caps + pair pruning.

---

## 2026-04-29 22:55 — Phase B (pair LOO): COMPLETE

Source: `audit/02_pair_loo/pair_loo.csv`, `pair_loo_full.csv`, `harmful_pairs.csv`,
        `helpful_strong_pairs.csv`, `summary.json`.

127 LOO backtests in 29.0 min (n_jobs=4). For each pair at indices 39..165
(rank 31..157 in the cross-group ranking), removed it from `ALL_PAIRS` and
re-ran the 3-day merged backtest, comparing per-day PnL and fold metrics
against the full tuned reference (1,436,024 / fold_min 450,479).

- **HARMFUL** (removing improves total ≥+1K AND fold_min ≥ 0): **38 pair instances**.
- These 38 instances cluster on **10 unique (a,b) signatures** — each appearing
  3-4× (slope/intercept refits at multiple lags). Top contributors when one
  copy is dropped:

| (a,b) signature                                  | copies | max LOO Δtotal | max LOO Δfold_min |
|:-------------------------------------------------|-------:|---------------:|-------------------:|
| TRANSLATOR_ECLIPSE_CHARCOAL × PANEL_1X2          |      4 |         +6,277 |             +3,097 |
| PEBBLES_S × GALAXY_SOUNDS_BLACK_HOLES            |      3 |         +5,246 |             +1,385 |
| PEBBLES_XS × UV_VISOR_AMBER                      |      4 |         +4,438 |             +1,864 |
| SLEEP_POD_POLYESTER × SNACKPACK_STRAWBERRY       |      4 |         +4,176 |               +843 |
| GALAXY_SOUNDS_DARK_MATTER × UV_VISOR_YELLOW      |      4 |             —  |             +1,896 |
| UV_VISOR_AMBER × SLEEP_POD_POLYESTER             |      4 |             —  |             +1,588 |
| SNACKPACK_STRAWBERRY × UV_VISOR_AMBER            |      4 |             —  |             +1,516 |
| SLEEP_POD_POLYESTER × UV_VISOR_AMBER             |      4 |             —  |             +1,173 |
| SNACKPACK_PISTACHIO × MICROCHIP_OVAL             |      3 |             —  |               +589 |
| SNACKPACK_STRAWBERRY × SLEEP_POD_POLYESTER       |      4 |             —  |               +443 |

- **Helpful-strong** (removing hurts ≥-2K AND fold_min ≤ 0): 13 pair instances.
- Naive sum of per-LOO uplifts if all 38 dropped = +130,700. Joint dropping
  (Phase E) achieved only -44K total — the harmful pairs are mostly duplicates
  that substitute for each other when any one is removed.
- Distribution by rank: 7 in ranks 31-50, 17 in 51-100, 14 in 101-157 — harmful
  pairs are NOT concentrated at the bottom of the ranking. The Tier-4 ranking
  used `combined_pnl` from a 2-fold split that does not isolate them.

---

## 2026-04-29 22:48 — Phase E (conservative variant)

Source: `audit/05_conservative/algo1_conservative.py`, `variants.csv`,
        `summary.json`, `summary.md`.

Tested 4 variants vs full tuned (166 pairs, fold_min 450,479):

| variant                  | n_pairs | total_3day  | fold_min | sharpe | day-2  | day-3  | day-4  |
|:-------------------------|--------:|------------:|---------:|-------:|-------:|-------:|-------:|
| v_full_tuned             |     166 |   1,436,024 |  450,479 |  13.03 | 520,225| 465,320| 450,479|
| v_drop_harmful           |     128 |   1,392,280 |  446,200 |  20.32 | 489,823| 456,258| 446,200|
| v_drop_harmful_unstable  |     119 |   1,371,865 |  437,722 |  17.04 | 487,888| 437,722| 446,256|
| v_conservative           |     119 |   1,326,576 |  419,783 |  21.23 | 460,960| 419,783| 445,834|

Where:
- `v_drop_harmful` = drop 38 HARMFUL pair instances; original caps.
- `v_drop_harmful_unstable` = also drop pairs with β-shift >50% (12 pairs at
  idx≥39); original caps.
- `v_conservative` = + tightened caps PANEL_1X4 (10→5), UV_VISOR_YELLOW (10→5),
  OXYGEN_SHAKE_CHOCOLATE (10→4).

Key findings:
- `v_drop_harmful` is the **best risk-adjusted variant**: -44K total,
  fold_min only -4.3K, **Sharpe 13→20**, max-DD reduced 27.2K→24.8K. Joint
  drop is far gentler than the LOO-sum predicted.
- Adding UNSTABLE drops (β>50%) HURTS — those pairs were doing useful work
  via short-window mean-reversion, even with parameter drift between days.
- Adding caps HURTS hard — the tighter caps cost 45-65K PnL with no fold_min
  benefit. The "fragility" products are noisy but net positive.

Mission ship rule for v_conservative: median ≥ tuned_median - 30K AND
Sharpe ≥ 30 AND fold_min ≥ tuned. v_conservative fails on fold_min
(419,783 < 450,479) and Sharpe (21.23 < 30). Decision: **KEEP TUNED**.

---

## 2026-04-29 22:52 — Phase F (re-plateau with stability filter)

Source: `audit/06_plateau_v2/n_sweep_filtered.csv`, `summary.json`, `summary.md`.

Filter: drop pairs with β-shift >30% (Phase C) → 80 of 157 cross-group
pairs survive. Then sweep N ∈ {30, 50, 75, 100, 125, 150} on the survivors
(plus the 9 within-group COINT pairs).

| N_target | N_used | total_pairs | total_3day  | fold_min | sharpe |
|---------:|-------:|------------:|------------:|---------:|-------:|
|       30 |     30 |          39 |     942,355 |  292,522 |  12.08 |
|       50 |     50 |          59 |   1,141,214 |  355,858 |   9.93 |
|       75 |     75 |          84 |   1,238,713 |  377,782 |  10.29 |
|      100 |     80 |          89 |   1,250,154 |  381,333 |  11.99 |
|      125 |     80 |          89 |   1,250,154 |  381,333 |  11.99 |
|      150 |     80 |          89 |   1,250,154 |  381,333 |  11.99 |

Best (by fold_min): N=80 with fold_min 381,333, total 1,250,154, Sharpe 11.99.
This is **69K below v_final** on fold_min and the Sharpe didn't improve.

The β-shift filter is too aggressive: it removes productive pairs whose
parameters drift across days but whose tilt-direction stays correct. Phase F
**fails to find a better N**.

---

## 2026-04-29 22:55 — Phase G (final decision)

Source: `audit/07_final/decision.md`, `algo1_day5.py`, `pnl_projection.md`,
        `candidates.csv`, `pnl_projection.csv`.

Compared 4 candidates (sorted by fold_min, then Sharpe):

| candidate           |  n_pairs | total_3day  | fold_min  | fold_median | sharpe | max_dd  |
|:--------------------|---------:|------------:|----------:|------------:|-------:|--------:|
| v_final             |      166 |   1,436,024 |   450,479 |     465,320 |  13.03 |  27,243 |
| v_drop_harmful_only |      128 |   1,392,280 |   446,200 |     456,258 |  20.32 |  24,766 |
| v_conservative      |      119 |   1,326,576 |   419,783 |     419,783 |  21.23 |  36,775 |
| v_replatueau        |       89 |   1,250,154 |   381,333 |     418,008 |  11.99 |  20,099 |

**Day-5 PnL projection (Normal-fit q05/q50/q95)**:

| candidate           | per-day mean | per-day std | day-5 q05  | day-5 q50  | day-5 q95  | observed floor |
|:--------------------|-------------:|------------:|-----------:|-----------:|-----------:|---------------:|
| v_final             |      478,675 |      29,999 |    429,327 |    478,675 |    528,023 |        450,479 |
| v_drop_harmful_only |      464,094 |      18,651 |    433,413 |    464,094 |    494,775 |        446,200 |
| v_conservative      |      442,192 |      17,007 |    414,217 |    442,192 |    470,168 |        419,783 |
| v_replatueau        |      416,718 |      28,380 |    370,033 |    416,718 |    463,404 |        381,333 |

**WINNER (mission rule, max fold_min): `v_final` (= `algo1_tuned.py`, unchanged).**
- fold_min 450,479 vs runner-up 446,200 (Δ +4,279, +0.95%).
- 3-day total 1,436,024.
- Sharpe 13.03.

**Audit verdict: the +353K uplift over baseline is mostly REAL.**
- 54% of the gain (191K of 353K) comes from 5 products (PEBBLES_XS,
  SNACKPACK_*, MICROCHIP_CIRCLE) that improved on every fold.
- 0 added pairs touch SNACKPACK_RASPBERRY but it gained +36.6K — pure parameter-driven win.
- Aggressive pair set is mostly inert; only 38 of 127 added instances are
  measurable harmful, mapped to 10 unique (a,b) signatures.

**Honourable mention: `v_drop_harmful_only`.**
On day-5 q05 projection (433K), it actually exceeds v_final's 429K despite
losing 4K on fold_min. Sharpe is 56% higher and max-DD 9% lower. If the user
wants tighter tail risk at the cost of 1% fold_min, ship this. Available at
`audit/07_final/algo1_drop_harmful_only.py`.

**Failed variants:**
- v_conservative: -30K below v_final on fold_min. Caps hurt.
- v_replatueau: -69K below v_final on fold_min. β-shift filter is too strict.

**Smoke verification: `algo1_day5.py` re-run via prosperity4btest reproduces
1,436,024 / Sharpe 13.0284 / fold_min 450,479. ✓**

---

## Final summary

The audit successfully decomposed the +353K tuning uplift:
- **Robust gains (~280K)**: cap+skew param tuning on PEBBLES_XS, SNACKPACK_*,
  MICROCHIP_CIRCLE; the 9 within-group COINT pairs and high-rank cross-group
  pairs (ranks 1-30).
- **Marginal/noisy (~50K)**: ~10 unique (a,b) pair signatures with 3-4
  duplicates each that net to +44K but have higher per-day variance.
- **Variance cost**: Sharpe 63→13 is real, concentrated in 10 products
  (90% of variance increase). Cannot be fixed by capping without giving back
  PnL.

**Day-5 floor projection**: 429K (parametric q05) / 450K (observed worst day).
3-day total target: 1.40M ± 0.05M (90% Normal CI).

**Ship `algo1_day5.py` = `algo1_tuned.py` (unchanged).**
