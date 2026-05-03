# IMC Prosperity 4 — Team BelmonteHunters

This repository contains our algorithmic-trading work for **IMC Prosperity 4** (April 2026), the global online trading challenge run by IMC.  Only the *algorithmic* side of the competition is documented here — manual-trading submissions are excluded by design.

> **Final result.**  Team **BelmonteHunters** finished round-5 with **X XIRECs** and ranked **X / X** overall (algorithmic).

---

## The challenge

Prosperity 4 runs over 16 days split into **5 rounds** (R1 & R2 last 72 h, R3–R5 last 48 h).  Each round introduces new tradable goods on a closed exchange where every team's algorithm trades **independently** against a fixed set of bots — there is no team-vs-team interaction in the algo channel.  At the end of each round teams lock in their final `Trader` class; that class is run for **10 000 ticks** on a held-out trading day, and the resulting PnL feeds the leaderboard.

The technical primitives are deliberately spartan: at every tick the algorithm receives a `TradingState` (level-2 order books, recent trades, current positions, observations), and must return a dict of `Order` objects together with a `traderData` string (≤ 50 000 chars) used to persist state across the stateless Lambda calls.  Position limits are enforced per-product; orders that would breach the aggregate buy/sell limit on a tick are rejected wholesale.

The simulation environment is the official `prosperity4btest` package, run identically against locally-released sample days and (on submission) against the unseen evaluation day.

For the official rules and the full datamodel see <https://imc-prosperity.notion.site/Prosperity-4>.

---

## Repository layout

```
imc-prosperity4/
├── README.md
├── round_1/
│   ├── Data/      ← raw prices_round_1_day_*.csv  +  trades_round_1_day_*.csv
│   ├── Algo/      ← submitted Trader (single .py) + ablation scripts
│   └── EDA/       ← notebooks / figures used to design the algo
├── round_2/   …  (same layout)
├── round_3/   …
├── round_4/   …
└── round_5/
    ├── Data/
    ├── Algo/
    ├── EDA/
    └── AutoResearch/   ← multi-phase research pipeline used only for R5
```

Each round folder is self-contained: open it, read the `Algo/` source, the `EDA/` notebooks, and you have the full provenance of that round's submission.

---

## Round-by-round summary

Each section below links into the corresponding round folder and presents the strategy, the EDA that motivated it, and the final result.  Sections are filled in incrementally as each round is finalised.

### Round 1 — ASH_COATED_OSMIUM & INTARIAN_PEPPER_ROOT

> Final PnL: **X XIRECs** · rank **X / X**

📁 [`round_1/`](round_1/) — submitted file: [`round_1/Algo/algo_r1.py`](round_1/Algo/algo_r1.py)

Round 1 introduced two products with position limit 80: **ASH_COATED_OSMIUM** (mean-reverting around ~10 000) and **INTARIAN_PEPPER_ROOT** (drifting upward almost deterministically).  Our EDA notebook is at [`round_1/EDA/data_exploration.ipynb`](round_1/EDA/data_exploration.ipynb).

#### Reverse-engineering the hidden fair value

Both products behave as if there is a *true* fair price hidden inside the order book — bots quote noisily around it, but cross it as soon as you do.  To recover that fair price empirically we used a small trick: submit an algorithm that simply holds a **fixed position of 1** in the asset, and read the per-tick PnL series that the platform writes to the submission log.  Since PnL = position · Δfair, those logs gave us a near-perfect reconstruction of the hidden fair price tick by tick, which we could then fit offline.

- **ASH** — the recovered fair price is well approximated by an EMA of the **microprice**, `mp = (bb·av + ba·bv) / (bv + av)`, with smoothing factor `α = 0.215`.  See [`algo_r1.py:23-41`](round_1/Algo/algo_r1.py#L23-L41).
- **INT** — the recovered fair price is essentially **linear in time**.  We fitted the closed-form expression
  ```
  fair(t) = base + round((t/100) · 102.4) / 1024
  ```
  where `base` is snapped to the nearest 1 000 from the current quotes.  This formula reproduces the published PnL series almost exactly.  See [`algo_r1.py:107-114`](round_1/Algo/algo_r1.py#L107-L114).  Because INT drifts up monotonically, **just being long was already a positive-expectancy strategy** — much of our daily PnL on this asset comes from a structural long bias built into the asymmetric quoting thresholds.

#### Premium logic (why we still keep it)

Around each fair value we maintain a **premium**: instead of crossing the spread the moment another quote ticks past fair, we only trade when the counter-quote is at least `M` cents through fair (`M2 = 8` ticks for buys, `M1 = 12` ticks for sells on INT — note the asymmetry that biases us long).  The same idea applies on ASH via the `floor`/`ceil` rounding of the fair.  Practically this means **the algo does nothing during the very first ticks** when the EMA hasn't converged yet, and it abstains during normal market regimes where edge is too thin.  We kept the premium logic in even though most of the PnL comes from quoting, because it's the only mechanism that protects us against regime changes and lets us **catch big opportunities** (a fast move through fair value) without re-tuning anything.

#### Wide-quote opportunism on missing-side ticks

Inspecting the level-2 books we noticed that on a small fraction of ticks for **INT**, one side of the book disappears entirely (no bid OR no ask present).  When that happens, an aggressive bot will sometimes lift / hit a quote we leave **up to ~100 ticks away from fair**, which is an enormous mark-to-market profit on a single fill.  The current submission therefore plants a quote at `fair − LIMIT_BOTS` (or `fair + LIMIT_BOTS`) on missing-side ticks via the `if bb is None …` / `if ba is None …` branches in `ash_makes` and `int_makes`.

We also tested the inverse hypothesis — proactively **clearing our resting orders close to the fair when book depth was low**, hoping to leave the book one-sided ourselves and thereby *create* the missing-side condition — but in backtests this consistently lost money.  The wide-edge fills only happen when the book is *organically* one-sided; manufacturing it via cancellations only forfeits the closer-to-fair queue position.  We kept only the passive "quote far when nothing else is there" version.

---

### Round 2 — TBD

> Final PnL: **X XIRECs** · rank **X / X**

*To be filled in.*

📁 [`round_2/`](round_2/)

---

### Round 3 — TBD

> Final PnL: **X XIRECs** · rank **X / X**

*To be filled in.*

📁 [`round_3/`](round_3/)

---

### Round 4 — TBD

> Final PnL: **X XIRECs** · rank **X / X**

*To be filled in.*

📁 [`round_4/`](round_4/)

---

### Round 5 — TBD

> Final PnL: **X XIRECs** · rank **X / X**

*To be filled in.*  Round 5 was the only round where we ran a structured multi-phase research pipeline; it lives under [`round_5/AutoResearch/`](round_5/AutoResearch/).

📁 [`round_5/`](round_5/)

---

## Reproducing a round

Each round's `Algo/` directory contains the single `.py` file submitted on the platform.  To replay it locally against the sample days released by IMC:

```bash
pip install prosperity4btest
prosperity4btest cli round_X/Algo/<file>.py X-2 X-3 X-4 --no-progress
```

(Replace `X` by the round number; trading days are `<round>-<day_index>`.)

The `Data/` folder mirrors the raw CSVs that IMC provided each round, so the backtester can be pointed at it offline.

---

## License

Code in this repository is published under the MIT license.  IMC Prosperity is the property of IMC Trading; this repo is an unofficial student archive of our team's work on the 2026 edition.
