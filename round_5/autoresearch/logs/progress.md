PT: phase 0 | configs_tested=1 configs_passing_gate=baseline mean_fold_pnl=362034 median_fold_pnl=363578 min_fold_pnl=354448 max_fold_pnl=364990 sharpe=63.08 maxDD=24692 bootstrap_q05=943838 q50=1085215 q95=1262435
PT: phase 1 | param_inventory_n=23 tier1=5 tier2=7 tier3=10 tier4=2 budget=~970_configs
PT: phase 2a in_progress | n_cfgs=51 (1 baseline + 50 LHS) workers=2 ETA=~30min started=20:41
PT: phase 2a complete | n_lhs=51 baseline_rank=1/51 best_lhs_median=362930 best_lhs_mean=370642 configs_passing_a=8 configs_passing_b=1 configs_passing_all_gates=0 elapsed=915s avg_per_cfg=17.9s
PT: phase 2b_tpe completed at 21:10:21
PT: phase 2c_plateau completed at 21:14:42
PT: phase 2d_bootstrap completed at 21:14:43
PT: phase 2_checkpoint completed at 21:14:43
PT: phase 2bcd complete | tier1=revert_to_baseline | tpe_best=(div=1.70,clip=11.58,beta=0.12,qbsc=6,gate=0.59) but no_config_passed_gates_(a+b+c+e)
PT: phase 3a_pebbles completed at 21:21:02
PT: phase 3b_snackpack completed at 21:25:25
PT: phase 3c_aggr completed at 21:26:36
PT: phase 4_prod_cap completed at 21:35:44
PT: phase 5_n_pairs completed at 21:37:53
PT: phase 5_checkpoint completed at 21:37:54
PT: phase 7_assembly completed at 21:38:44
PT: phase 6_stress completed at 21:42:28
PT: phase 6_checkpoint completed at 21:42:28
PT: phase 8_findings completed at 21:42:29
PT: phase 3 complete | tier2_pebbles=DIVISOR_5_to_8_CLIP_3_to_5_BIG_1.8_to_3.5 (+16K) | tier2_snackpack=CLIP_5_to_3 (+114K) | tier2_aggr=irrelevant
PT: phase 4 complete | tier3_caps_changed: SLEEP_POD_LAMB_WOOL=3->10 SNACKPACK_RASPBERRY=5->10 SNACKPACK_CHOCOLATE=5->10 ROBOT_MOPPING=4->2
PT: phase 5 complete | n_pairs=157 (full pool) rank=combined_pnl 3day=1436024 +353K_vs_baseline fold_min=450479
PT: phase 6 complete | match_PASS latency=90%_PASS limit8=24%_DEGRADED_but_positive day_only=all_pos perturb_q05=88%_PASS
PT: phase 7 complete | algo1_tuned.py reproduces 1,436,024 exactly | ablation v00->v05 logged
PT: phase 8 complete | headline.md parameter_decisions.md what_was_dropped.md written
PT: FINAL | tuned_3day=1,436,024 baseline_3day=1,083,016 uplift=+353,008 (+32.6%) fold_min=450,479 day5_floor=450K mid=480K high=520K
PT: ALL DONE at 21:48:30
