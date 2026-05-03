# IMC Prosperity 4 — Team Belmonte

This repository contains our algorithmic-trading work for **IMC Prosperity 4** (April 2026), the global online trading challenge run by IMC.  Only the *algorithmic* side of the competition is documented here — manual-trading submissions are excluded by design.

> **Final result.**  Team **Belmonte** finished round-5 with **X XIRECs** and ranked **X / X** overall (algorithmic).

---

## Team

**Belmonte** — five ETH Zurich students.

| Member | Profile |
|---|---|
| Arthur Windels | <https://www.linkedin.com/in/arthurwindels> |
| Arthur Vianna | — |
| Dmitry Sereda | — |
| Nicolaj Thomsen | — |
| Yanis Fallet | — |

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

### Round 1 — TBD

> Final PnL: **X XIRECs** · rank **X / X**

*To be filled in.*

📁 [`round_1/`](round_1/)

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
