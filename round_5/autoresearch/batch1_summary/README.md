# ROUND_5 batch1_summary

Total synthesis of all prior R5 research (autoresearch + EDA/eda_full) into one merged summary and one final algo.

## Layout
- `00_inventory/` — 781-artefact walk of source trees with stats.
- `01_cards/` — one ≤2KB JSON card per artefact (781 cards).
- `02_index/` — flattened `findings_index.jsonl` (1,583 atomic findings) + product/tag pivots.
- `03_reconciliation/` — conflicts.jsonl + reverify scripts/results + checkpoint.
- `04_per_product/` — 50 product files with reconciled findings + recommendation.
- `05_per_group/` — 10 group files.
- `06_themes/` — 11 theme files.
- `07_strategy_design/` — per_product_decision.csv + alternatives + conflict_resolution.
- `08_final_algo/` — `strategy_final.py`, `distilled_params.py`, `ablation.csv`, walk-forward + stress.
- `09_findings_master/` — `headline.md`, `exhaustive_findings.md`, `what_was_dropped.md`.

## Headline
- v3 baseline (round-3 strategy): **733,320 / 3 days** / Sharpe 8.34. Reverified.
- Final algo = v3 with one within-group cointegration pair (OXYGEN_SHAKE_CHOCOLATE/GARLIC) **dropped** after reverify ADF=0.918 (claimed 0.030).
- Final 3-day PnL: see `08_final_algo/ablation.csv` final row.

## Reproducing the final algo
```bash
imcp/bin/prosperity4btest cli \
    ROUND_5/batch1_summary/08_final_algo/strategy_final.py \
    5-2 5-3 5-4 \
    --merge-pnl --match-trades worse --no-progress \
    --data ROUND_5/autoresearch/10_backtesting/data \
    $(cat ROUND_5/autoresearch/utils/limit_flags.txt)
```
