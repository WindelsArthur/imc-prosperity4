# Theme: Intraday seasonality

## Definition
Mod-K time-of-day patterns in returns, vol, or trade activity.

## Reconciled findings (negative result)
- **Round 1 Phase 4** computed 100-bin mod-day patterns: max cross-day correlation was **0.13**, all below 0.30 threshold.  
- **Round 2 Phase G (Intraday seasonality)**: same conclusion — 100-bin patterns have insufficient cross-day stability for any positive-Sharpe overlay.  
  *Source:* `ROUND_5/autoresearch/13_round2_research/G_intraday/`.

## What about specific products?
- **GALAXY_SOUNDS_SOLAR_FLAMES** had highest mod-K R² in its group (0.89 at K=20,000) — but this is just the sine artefact (period = 2/3 of stitched length), not a real intraday pattern.
- 50 per-product `intraday/{prod}.csv` files exist (`ROUND_5/autoresearch/04_statistical_patterns/intraday/`); none have a mod-K signal that survived OOS.

## Decision for final algo
- **No intraday overlay.** No time-of-day-conditional pricing.
- **No am/pm cycle.** R5 timestamps are sequential 0..1M ticks per day; no calendar structure.

## Expected PnL contribution
0 (excluded).
