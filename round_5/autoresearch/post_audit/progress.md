# post_audit progress log

Mission: three targeted alpha extractions on top of `algo1_drop_harmful_only.py`.

Baseline file: `ROUND_5/autoresearch/parameter_tuning/audit/07_final/algo1_drop_harmful_only.py`

5-fold protocol (FOLDS in `_pa_lib.py`):
- F1=day3, F2=day4, F3=day3, F4=day2, F5=day3 (test-day PnL).

Match mode: `worse` (mission rule for headline).

- 2026-04-30 00:01:40 — Phase 0 START — locking baseline algo1_drop_harmful_only.py
- 2026-04-30 00:02:03 — Phase 0 — baseline locked. fold_min=446200, max_pct_diff=0.00%
- 2026-04-30 00:05:09 — Phase 1 Step 1a — ROBOT_DISHES diagnostic
- 2026-04-30 00:05:10 — Phase 1 Step 1a — diagnostic written: dishes baseline 3d=26,201, AR1 pooled φ=-0.2317, log-pair isolated sum=61,983
- 2026-04-30 00:09:11 — Phase 1 — starting dedicated handler sweep
- 2026-04-30 00:09:11 — Phase 1 — 116 cells (1b=80, 1c=16, 1d=20)
- 2026-04-30 00:09:50 — Phase 2 Step 2a — AR(1) per priority product per day
- 2026-04-30 00:10:08 — Phase 2 Step 2a — 3/7 priority products survive cross-day stability
- 2026-04-30 00:16:26 — Phase 1 — 10/116 done
- 2026-04-30 00:19:05 — Phase 1 — 20/116 done
- 2026-04-30 00:20:56 — Phase 1 — 30/116 done
- 2026-04-30 00:23:37 — Phase 1 — 40/116 done
- 2026-04-30 00:25:26 — Phase 1 — 50/116 done
- 2026-04-30 00:27:47 — Phase 1 — 60/116 done
- 2026-04-30 00:30:12 — Phase 1 — 70/116 done
- 2026-04-30 00:31:47 — Phase 1 — 80/116 done
- 2026-04-30 00:33:57 — Phase 1 — 90/116 done
- 2026-04-30 00:36:15 — Phase 1 — 100/116 done
- 2026-04-30 00:37:55 — Phase 1 — 110/116 done
- 2026-04-30 00:39:02 — Phase 1 — sweep complete; ablation.csv has 116 rows
- 2026-04-30 00:40:43 — Phase 2 Step 2b — per-product α sweep
- 2026-04-30 00:40:43 — Phase 2 — 3 survivors: OXYGEN_SHAKE_EVENING_BREATH(-0.115), ROBOT_IRONING(-0.118), OXYGEN_SHAKE_CHOCOLATE(-0.080)
- 2026-04-30 00:44:18 — Phase 2 Step 2b — per-product α sweep
- 2026-04-30 00:44:18 — Phase 2 — 3 survivors: OXYGEN_SHAKE_EVENING_BREATH(-0.115), ROBOT_IRONING(-0.118), OXYGEN_SHAKE_CHOCOLATE(-0.080)
- 2026-04-30 00:46:55 — Phase 2 Step 2b — wrote per_product_alpha_sweep.csv (12 rows)
- 2026-04-30 00:46:55 — Phase 2 — per-product decisions written
- 2026-04-30 00:46:55 — Phase 2 Step 2c — no products retained; combined run skipped
- 2026-04-30 00:47:59 — Phase 3 Step 3b — per-product β sweep
- 2026-04-30 00:47:59 — Phase 3 — 70 cells
- 2026-04-30 00:50:54 — Phase 3 — 10/70 done
- 2026-04-30 00:53:02 — Phase 3 — 20/70 done
- 2026-04-30 00:55:41 — Phase 3 — 30/70 done
- 2026-04-30 00:59:19 — Phase 3 — 40/70 done
- 2026-04-30 01:01:19 — Phase 3 — 50/70 done
- 2026-04-30 01:03:10 — Phase 3 — 60/70 done
- 2026-04-30 01:04:53 — Phase 3 — 70/70 done
- 2026-04-30 01:04:53 — Phase 3 Step 3b — per_product_beta_sweep.csv saved
- 2026-04-30 01:04:53 — Phase 3 — decisions: retained 9 products
- 2026-04-30 01:05:14 — Phase 3 Step 3d — combined fold_min=449,084 (Δ=+2,884)
- 2026-04-30 01:08:01 — Phase 4 — combined assembly + ablation v00..v04
- 2026-04-30 01:08:01 — Phase 4 — running v00
- 2026-04-30 01:08:24 — Phase 4 — running v01
- 2026-04-30 01:08:46 — Phase 4 — running v03
- 2026-04-30 01:09:09 — Phase 4 — combined assembly + ablation v00..v04
- 2026-04-30 01:09:09 — Phase 4 — running v00
- 2026-04-30 01:09:32 — Phase 4 — running v01
- 2026-04-30 01:09:55 — Phase 4 — running v03
- 2026-04-30 01:10:17 — Phase 4 — running v04
- 2026-04-30 01:10:41 — Phase 4 — shipped variant v04 as algo1_post_audit.py
- 2026-04-30 01:12:26 — Phase 5 — stress battery START
- 2026-04-30 01:12:26 — Phase 5 — match_mode test
- 2026-04-30 01:13:33 — Phase 5 — limit=8
- 2026-04-30 01:13:56 — Phase 5 — day-removal (per-day runs)
- 2026-04-30 01:14:18 — Phase 5 — perturbation (50 LHS samples)
- 2026-04-30 01:17:20 — Phase 5 perturb 10/50
- 2026-04-30 01:19:02 — Phase 5 perturb 20/50
- 2026-04-30 01:21:06 — Phase 5 perturb 30/50
- 2026-04-30 01:23:22 — Phase 5 perturb 40/50
- 2026-04-30 01:24:49 — Phase 5 perturb 50/50
- 2026-04-30 01:24:49 — Phase 5 perturbation complete
- 2026-04-30 01:31:27 — Phase 6 — final ship-check: fold_min=459,226, total=1,420,758, sharpe=22.8122
- 2026-04-30 01:31:32 — Phase 6 — findings written: headline.md, decisions.md, what_was_dropped.md
- 2026-04-30 01:31:32 — SHIP TARGET: ROUND_5/autoresearch/post_audit/04_combined_assembly/algo1_post_audit.py (= v04)
- 2026-04-30 01:31:32 — Final fold_min=459,226 (+13,026 vs baseline 446,200); 3-day total=1,420,758; Sharpe=22.81
