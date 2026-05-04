"""Phase 4 — assemble combined algo, run v00..v04 ablation.

  v00: baseline (algo1_drop_harmful_only.py)
  v01: + Phase 1 winner (ROBOT_DISHES dedicated handler, log-pair-only, β=0.6)
  v02: + Phase 2 (= v01; nothing to add)
  v03: + Phase 3 near-misses (MICROCHIP_OVAL=0.40 + SLEEP_POD_POLYESTER=0.40)
  v04: full combined (v01 + v03)

For each variant: full 5-fold + per-product attribution + strict gate eval.
Pick the SMALLEST variant that passes the strict gate as the ship target.
"""
import csv
import importlib.util
import json
import sys
import time
from pathlib import Path

_PA = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_PA))
sys.path.insert(0, str(_PA / "01_robot_dishes_specialised"))
from _pa_lib import run_algo_text, run_algo, FOLDS, progress_log, write_csv

OUT = _PA / "04_combined_assembly"
OUT.mkdir(exist_ok=True)
BASELINE_PATH = (_PA.parent / "parameter_tuning" / "audit" / "07_final"
                 / "algo1_drop_harmful_only.py")
BASELINE_SRC = BASELINE_PATH.read_text()
BASELINE_JSON = json.loads((_PA / "00_baseline_lock" / "baseline.json").read_text())

# Load Phase 1 winner src
P1_WINNER_PATH = _PA / "01_robot_dishes_specialised" / "04_combined_handler.py"
P1_WINNER_SRC = P1_WINNER_PATH.read_text()


def add_other_beta_map(src: str, beta_map: dict) -> str:
    """Inject `OTHER_BETA_MAP = {...}` and modify `_fair` to use it for
    products other than ROBOT_DISHES.

    Works on either the baseline or the Phase-1 winner source.
    """
    if not beta_map:
        return src

    map_lit = "{" + ", ".join(f'"{p}": {b}' for p, b in beta_map.items()) + "}"
    inject = f"\n# Phase-3 per-product inv_skew β override (non-DISHES)\nOTHER_BETA_MAP = {map_lit}\n"
    src = src.replace("INV_SKEW_BETA = 0.2",
                      "INV_SKEW_BETA = 0.2" + inject, 1)

    # Detect Phase-1 template (it has ROBOT_DISHES branch with `DISHES_INV_BETA`)
    is_p1_template = "DISHES_INV_BETA" in src
    if is_p1_template:
        # Replace the else-branch beta_inv assignment in template
        old = "        beta_inv = INV_SKEW_BETA"
        new = "        beta_inv = OTHER_BETA_MAP.get(prod, INV_SKEW_BETA)"
        if old not in src:
            raise RuntimeError("could not patch P1 template's else-branch beta_inv")
        src = src.replace(old, new, 1)
    else:
        # baseline-style _fair (no ROBOT_DISHES split, single inv line)
        old = "    inv = -pos * INV_SKEW_BETA"
        new = "    inv = -pos * OTHER_BETA_MAP.get(prod, INV_SKEW_BETA)"
        if old not in src:
            raise RuntimeError("could not patch baseline inv = -pos * INV_SKEW_BETA")
        src = src.replace(old, new, 1)
    return src


def assemble(variant: str) -> str:
    if variant == "v00":
        return BASELINE_SRC
    if variant == "v01":
        return P1_WINNER_SRC
    if variant == "v02":
        # Phase 2 contributes nothing
        return P1_WINNER_SRC
    if variant == "v03":
        # Baseline + Phase-3 near-miss β overrides only
        return add_other_beta_map(
            BASELINE_SRC,
            {"MICROCHIP_OVAL": 0.40, "SLEEP_POD_POLYESTER": 0.40},
        )
    if variant == "v04":
        # Phase 1 winner + Phase 3 near-miss β overrides
        return add_other_beta_map(
            P1_WINNER_SRC,
            {"MICROCHIP_OVAL": 0.40, "SLEEP_POD_POLYESTER": 0.40},
        )
    raise ValueError(f"unknown variant: {variant}")


def evaluate(res, base):
    base_folds = base["fold_pnls"]
    deltas = [res.fold_pnls[f"F{i}"] - base_folds[f"F{i}"] for i in range(1, 6)]
    a = res.fold_mean >= base["fold_mean"] + 2000
    b = res.fold_median >= base["fold_median"]
    c = all(d > 0 for d in deltas)
    d = res.fold_min >= base["fold_min"]
    e = (res.max_dd_3day is None or base["max_dd_3day"] is None
         or res.max_dd_3day <= 1.20 * base["max_dd_3day"])
    return {
        "gate_a_mean_2K": a, "gate_b_median": b, "gate_c_all_folds": c,
        "gate_d_fold_min": d, "gate_e_maxdd": e,
        "passed_strict": bool(a and b and c and d and e),
        "deltas": deltas,
    }


def run_variant(label: str) -> dict:
    src = assemble(label)
    src_path = OUT / f"algo1_post_audit_{label}.py"
    src_path.write_text(src)
    t0 = time.time()
    res = run_algo(src_path, save_log_as=f"phase4_{label}")
    elapsed = time.time() - t0
    ev = evaluate(res, BASELINE_JSON)
    return {
        "variant": label,
        "elapsed_s": round(elapsed, 1),
        "F1_pnl": res.fold_pnls["F1"], "F2_pnl": res.fold_pnls["F2"],
        "F3_pnl": res.fold_pnls["F3"], "F4_pnl": res.fold_pnls["F4"],
        "F5_pnl": res.fold_pnls["F5"],
        "fold_min": res.fold_min,
        "fold_median": res.fold_median,
        "fold_mean": round(res.fold_mean, 1),
        "total_3day": res.total_3day,
        "sharpe_3day": res.sharpe_3day,
        "max_dd_3day": res.max_dd_3day,
        "delta_fold_min": res.fold_min - BASELINE_JSON["fold_min"],
        "delta_fold_mean": round(res.fold_mean - BASELINE_JSON["fold_mean"], 1),
        "delta_fold_median": res.fold_median - BASELINE_JSON["fold_median"],
        "delta_max_dd": (res.max_dd_3day - BASELINE_JSON["max_dd_3day"])
                        if (res.max_dd_3day and BASELINE_JSON["max_dd_3day"]) else None,
        "max_dd_ratio": (res.max_dd_3day / BASELINE_JSON["max_dd_3day"])
                        if (res.max_dd_3day and BASELINE_JSON["max_dd_3day"]) else None,
        **{f"deltas_F{i}": ev["deltas"][i-1] for i in range(1, 6)},
        **{k: v for k, v in ev.items() if k.startswith("gate_") or k == "passed_strict"},
    }


def main():
    progress_log("Phase 4 — combined assembly + ablation v00..v04")

    rows = []
    for v in ["v00", "v01", "v03", "v04"]:  # skip v02 (== v01)
        progress_log(f"Phase 4 — running {v}")
        rows.append(run_variant(v))

    # add v02 as a copy of v01 (different label, same numbers)
    v01 = next(r for r in rows if r["variant"] == "v01")
    v02 = dict(v01); v02["variant"] = "v02"; v02["elapsed_s"] = 0.0
    rows.insert(2, v02)

    write_csv(rows, OUT / "full_ablation.csv")

    # pick winner: smallest passing variant by fold_min, with safety margin
    base_fm = BASELINE_JSON["fold_min"]
    print(f"\nBaseline fold_min={base_fm}\n")
    print("Ablation v00..v04:")
    for r in rows:
        flag = "✓" if r["passed_strict"] else "✗"
        print(f"  {r['variant']} {flag} fold_min={r['fold_min']:>6}  "
              f"median={r['fold_median']:>7}  mean={r['fold_mean']:>10}  "
              f"sharpe={r['sharpe_3day']:.2f}  Δfm={r['delta_fold_min']:+,}  "
              f"Δmean={r['delta_fold_mean']:+,.0f}  "
              f"gates: a={r['gate_a_mean_2K']} b={r['gate_b_median']} "
              f"c={r['gate_c_all_folds']} d={r['gate_d_fold_min']} e={r['gate_e_maxdd']}")

    # Decision rule from mission: highest fold_min, tie-break Sharpe
    candidates = [r for r in rows if r["passed_strict"]]
    if candidates:
        winner = max(candidates,
                     key=lambda r: (r["fold_min"], r["sharpe_3day"] or 0))
        print(f"\n=== WINNER: {winner['variant']} ===")
        with (OUT / "winner.json").open("w") as f:
            json.dump(winner, f, indent=2, default=str)
    else:
        print("\nNo variant passes strict gate. Shipping v00 (baseline).")
        winner = next(r for r in rows if r["variant"] == "v00")
        with (OUT / "winner.json").open("w") as f:
            json.dump(winner, f, indent=2, default=str)

    # Save shipped algo path
    ship_var = winner["variant"]
    ship_src = OUT / f"algo1_post_audit_{ship_var}.py"
    if ship_var == "v02":
        ship_src = OUT / "algo1_post_audit_v01.py"
    if ship_var == "v00":
        # ship the baseline; copy the original
        (OUT / "algo1_post_audit.py").write_text(BASELINE_SRC)
    else:
        (OUT / "algo1_post_audit.py").write_text(ship_src.read_text())
    progress_log(f"Phase 4 — shipped variant {ship_var} as algo1_post_audit.py")


if __name__ == "__main__":
    main()
