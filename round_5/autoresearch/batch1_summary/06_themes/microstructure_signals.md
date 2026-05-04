# Theme: Microstructure signals

## Definition
Order-book level signals: bid-ask spread, depth at multiple levels, OFI (order-flow imbalance), microprice, queue position, signed flow.

## Reconciled findings
- **Spread distribution per product** is captured in `ROUND_5/autoresearch/02_microstructure/`. Tight-spread products (≤5 ticks): MICROCHIP_CIRCLE, OVAL, RECTANGLE, TRIANGLE, ROBOT_IRONING. Wide-spread (≥10 ticks): MICROCHIP_SQUARE, all PEBBLES (~13).
- **Round 2 Phase D (microstructure):** Multi-level OFI IC peaks at **0.10** (max). Negative on lattice products (i.e. flow against price = contra-signal). Tight-spread regime has **negative realised spread** on most products — informs PROD_CAP for spread/vol < 0.6 bleeders.  
  *Source:* `ROUND_5/autoresearch/13_round2_research/D_micro/`.
- **Aggregate signed-flow IC ≈ 0.01** — flow is essentially uninformed.  
  *Source:* `ROUND_5/autoresearch/03_trade_flow/`, `ROUND_5/autoresearch/11_findings/findings.md`.
- **Counterparty fields (buyer, seller) are EMPTY** in every R5 trades CSV. Per-counterparty bot fingerprinting is impossible.  
  *Source:* `ROUND_5/autoresearch/00_data_inventory/inventory.md`.
- **Lagged OFI / cross-flow (Phase F round 3):** Top |IC| = 0.090 at k=1 (own ROBOT_IRONING). This is just AR(1) restated.

## What survives → PROD_CAP
Phase B of round 2 ("Bleeder forensics") found that 9 of 11 v1 bleeders had spread/vol < 0.6 → MM was being adversely selected by informed flow. Reducing each product's max position to ±3..±5 cuts the bleed without removing the spread-capture floor.

| Product | Cap | v1 PnL | v2 PnL | Δ |
|---|---:|---:|---:|---:|
| SLEEP_POD_LAMB_WOOL | 3 | −24,199 | −2,310 | +21,889 |
| UV_VISOR_MAGENTA | 4 | −7,001 | −2,880 | +4,121 |
| PANEL_1X2 | 3 | −18,729 | +509 | +19,238 |
| TRANSLATOR_SPACE_GRAY | 4 | −4,820 | −5,039 | −219 |
| ROBOT_MOPPING | 4 | −17,174 | +994 | +18,168 |
| PANEL_4X4 | 4 | −4,391 | +3,116 | +7,507 |
| GALAXY_SOUNDS_SOLAR_FLAMES | 4 | −8,237 | +2,060 | +10,297 |
| SNACKPACK_RASPBERRY | 5 | −31,946 | +4,179 | +36,125 |
| SNACKPACK_CHOCOLATE | 5 | −16,417 | +4,776 | +21,193 |

**Total Phase B uplift = +134,776** (the entire v1→v2 delta).

## Decision for final algo
- **Keep PROD_CAP exactly as v3** — Phase B is the single largest ablation contributor in the entire research history.
- **Phase H test:** does adding cap on PEBBLES_L (chronic v3 loser, −12K) help? v2 found +92 PnL but Sharpe 8.6→7.2.

## Expected PnL contribution
+134K over 3 days from PROD_CAP. Embedded in v3 baseline.
