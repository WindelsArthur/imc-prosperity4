# IMC Prosperity 4 — Team BelmonteHunters

This repository contains our algorithmic-trading work for **IMC Prosperity 4** (April 2026), the global online trading challenge run by IMC.  Only the *algorithmic* side of the competition is documented here — manual-trading submissions are excluded by design.

> **Final result.**  Team **BelmonteHunters** finished round-5 with **X XIRECs** and ranked **X / X** overall (algorithmic).

---

## The challenge

Prosperity 4 runs over 16 days split into **5 rounds** (R1 & R2 last 72 h, R3–R5 last 48 h).  Each round introduces new tradable goods on a closed exchange where every team's algorithm trades **independently** against a fixed set of bots — there is no team-vs-team interaction in the algo channel.  At the end of each round teams lock in their final `Trader` class; that class is run for **10 000 ticks** on a held-out trading day, and the resulting PnL feeds the leaderboard.

Each tick of the simulation follows a fixed timeline:

1. We receive the current `TradingState` with the bots' resting quotes (level-2 order book per product) and the trades that occurred since the previous tick.
2. We decide whether to **take** any of those bot quotes — i.e. cross the spread to buy from a bot ask we judge mispriced, or hit a bot bid we judge mispriced.
3. We post our own resting quotes (limit buy / sell orders) for this tick.
4. The bots react: some of them lift or hit our resting quotes, some trade among themselves, and they post new quotes for the next tick.
5. The next `TradingState` is generated and the loop repeats.

This pipeline is the same for all five rounds.

The **official evaluation** happens on the IMC platform: at each round we receive a few days of historical data (typically three) for the products that round introduces, and when we submit a `Trader` class the platform runs it for one full unseen day (10 000 ticks) against the round's bot population — that final-day PnL is what feeds the leaderboard.  Locally, we developed against a third-party backtester we cloned from <https://github.com/nabayansaha/imc-prosperity-4-backtester>, replaying the released sample days; this is **not** the official simulator, just a faithful enough emulator to iterate quickly between submissions.

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

#### High-level strategy

The skeleton is the same for both products and is the template we reuse in every following round:

1. **Compute a fair price** for the product on each tick.
2. **Take any bot quote that is mispriced relative to fair** — buy from any bot ask `≤ fair`, sell into any bot bid `≥ fair`.
3. **Market-make around the best remaining bid / ask** (post a passive bid one tick inside the bid, and a passive ask one tick inside the ask), with the constraint that **our resting quotes never cross our own fair**.

Everything else — premium thresholds, inventory skew, opportunistic wide quotes — are layered modifications of those three steps.

#### Reverse-engineering the fair price

Both products behave as if there is a *true* fair price hidden inside the order book — bots quote noisily around it but cross it as soon as you do.  To recover that fair price empirically we used a small trick: **submit an algorithm that simply holds a fixed position of +1 in the asset, and read the per-tick PnL series that the platform writes to the submission log**.  Since PnL = position · Δfair, those logs give us a near-perfect tick-by-tick reconstruction of the hidden fair, which we could then fit offline.

- **ASH** — the recovered fair price is well approximated by an EMA of the **microprice**, `mp = (bb·av + ba·bv) / (bv + av)`, with smoothing factor `α = 0.215`.  See [`algo_r1.py:23-41`](round_1/Algo/algo_r1.py#L23-L41).
- **INT** — the recovered fair price is essentially **linear in time**.  We fitted the closed-form expression
  ```
  fair(t) = base + round((t/100) · 102.4) / 1024
  ```
  where `base` is snapped to the nearest 1 000 from the current quotes.  This formula reproduces the published PnL series almost exactly.  See [`algo_r1.py:107-114`](round_1/Algo/algo_r1.py#L107-L114).

#### Per-product position bias

The two products have very different price dynamics, so the bias we bake into the quoting differs:

- **INT — premium logic to stay as long as possible.**  Because INT drifts upward almost monotonically, just being long is a positive-expectancy strategy.  We exploit that with **asymmetric premium thresholds** (INT only): we buy as long as the bot ask is `≤ fair + 8`, but only sell when the bot bid is `≥ fair + 12`.  In other words we are willing to buy *above* our estimate of fair, and we refuse to sell unless we get a real markup.  This pushes the position long without us having to predict direction.  As a side effect the premiums also act as a regime-change buffer: while the formula is still warming up at the start of the day, or during sudden moves, the algo simply abstains rather than trading on a stale fair.
- **ASH — inventory skew to stay close to neutral.**  ASH mean-reverts and the source of edge is symmetric two-sided quoting, so the goal is to **avoid accumulating directional inventory**.  We subtract `INV_SKEW · position` (with `INV_SKEW = 0.10`) from the fair value before each take/quote step, which biases the algo to sell when long and buy when short, pulling the position back toward zero.

#### Wide-quote opportunism on missing-side ticks

Inspecting the level-2 books we noticed that on a small fraction of ticks for **INT**, one side of the book disappears entirely (no bid OR no ask present).  When that happens, an aggressive bot will sometimes lift / hit a quote we leave **up to ~95 ticks away from fair**, which is an enormous mark-to-market profit on a single fill.  The current submission therefore plants a quote at `fair − 95` (or `fair + 95`) on missing-side ticks via the `if bb is None …` / `if ba is None …` branches in `ash_makes` and `int_makes`.

We also tested the inverse idea: **proactively *taking* the bots' near-fair quotes ourselves to remove one side of the book**, so that we could then post our own wide quote far from fair and hope an aggressive bot would lift it.  Concretely, sweep the bid side clean and post a new bid at `fair − 95`; if a bot fills it we collect ~95 ticks of edge.  But the cost of clearing the book in the first place — paying `(fair − bid_price) · volume` to take all the resting bids — was always larger than the upside of the speculative wide-fill.  In short: wide-edge fills only pay when the book is *organically* one-sided; manufacturing the condition is a losing trade.  We kept only the passive "quote far when nothing else is there" version.

---

### Round 2 — same products, blind-auction for extra market access

> Final PnL: **X XIRECs** · rank **X / X**

📁 [`round_2/`](round_2/) — submitted file: [`round_2/Algo/algo_r2.py`](round_2/Algo/algo_r2.py)

Round 2 keeps the same two products (`ASH_COATED_OSMIUM`, `INTARIAN_PEPPER_ROOT`, position limit 80 each) but introduces a one-off twist: a **Market Access Fee** auction.  Each team can include a `bid()` method in their `Trader` class returning a one-time fee in XIRECs; the **top 50 % of bids** (i.e. those above the cross-team median) win a **25 % larger order book** for the round — the extra quotes slot perfectly into the existing depth distribution.  The accepted bid is then deducted from R2 PnL; teams in the bottom half pay nothing and trade the unmodified book.  Because bids are revealed only after submissions close, it is effectively a blind auction.

Rounds 1 and 2 jointly serve as a qualifier: a team needs **≥ 200 000 XIRECs** of cumulative algorithmic PnL across the two rounds to advance to rounds 3-5, and the leaderboard is reset for Phase 2 regardless of the surplus we accumulate beyond it.  We had already cleared the threshold in Round 1, so two things were true at submission time: (1) marginal PnL beyond the qualifier had no impact on Phase 2, and (2) any MAF bid we won would directly reduce the comfort cushion we still wanted as a safety margin.  We therefore chose **not to spend further effort on Round 2** — we resubmitted the Round 1 algorithm verbatim, with `bid()` returning **0** (effectively opting out of the auction and trading the unmodified 80 % book).

The submitted file [`algo_r2.py`](round_2/Algo/algo_r2.py) is identical to [`algo_r1.py`](round_1/Algo/algo_r1.py) except for the added `bid()` method.

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

## License

Code in this repository is published under the MIT license.  IMC Prosperity is the property of IMC Trading; this repo is an unofficial student archive of our team's work on the 2026 edition.
