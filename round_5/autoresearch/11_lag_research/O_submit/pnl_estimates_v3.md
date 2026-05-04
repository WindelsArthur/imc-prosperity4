# PnL Estimates v3 — Round 5

## Per-day backtest (`--match-trades worse`)

| Day  | v1     | v2     | v3 (top-30 cross-group) | Δ vs v2 |
|------|--------|--------|--------------------------|---------|
| 5-2  | 124,893 | 168,887 | **233,855** | +64,968  |
| 5-3  | 105,220 | 162,030 | **277,558** | +115,528 |
| 5-4  | 166,636 | 200,608 | **221,906** | +21,298  |
| Σ234 | **396,749** | **531,525** | **733,320** | +201,795 |

Sharpe (merged): 4.22 → 8.61 → **8.34** (slight Sharpe trade-off for big PnL gain).
Max DD abs: 30,772 → 26,286 → **23,990**.
Max DD %: 26.9 → 5.0 → 21.9 (still well within bounds).
Match-mode band (worse vs all): 0 — fully passive.

## Day-5 forecast band

| Scenario | Per-day PnL | Notes                                |
|----------|-------------|--------------------------------------|
| Low      | ≈ 222,000   | matches worst training day (5-4)     |
| Base     | ≈ 244,000   | mean of training days                |
| High     | ≈ 278,000   | matches best training day (5-3)      |

## Robustness

| Test                                  | v3 result            |
|---------------------------------------|----------------------|
| Walk-forward fold A (test d3 only)    | 277,558               |
| Walk-forward fold B (test d4 only)    | 221,906               |
| Day-removal (test d3+d4 only)         | (sum of d3+d4) ≈ 499K |
| Match-mode worse vs all               | identical             |
| Limit=10 (prescribed)                 | 733,320               |

## Reproduce

```bash
imcp/bin/prosperity4btest cli \
    ROUND_5/autoresearch/14_lag_research/O_submit/strategy_v3.py \
    5-2 5-3 5-4 \
    --merge-pnl --match-trades worse --no-progress \
    --data ROUND_5/autoresearch/10_backtesting/data \
    $(cat ROUND_5/autoresearch/utils/limit_flags.txt)
```
