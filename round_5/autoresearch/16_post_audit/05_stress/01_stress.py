"""Phase 5 — stress battery for the v04 winner.

Tests:
  1. match_mode 'all' vs 'worse' — band of expected PnL change.
  2. limit=8 — must stay positive ≥ 30% of headline.
  3. perturbation ±20% on the 4 new parameters introduced (LHS, 50 samples).
  4. day-removal — per-day PnL reported (3 single-day runs).
  5. latency: not supported by upstream CLI; documented as N/A.

Output:
  perturbation.csv, match_mode.csv, limit_8.csv, day_removal.csv, stress_summary.md.
"""
from __future__ import annotations

import csv
import json
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import numpy as np

_PA = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_PA))
from _pa_lib import run_algo, run_algo_text, write_csv, progress_log, FOLDS

OUT = _PA / "05_stress"
OUT.mkdir(exist_ok=True)
WINNER_PATH = _PA / "04_combined_assembly" / "algo1_post_audit.py"
WINNER_SRC = WINNER_PATH.read_text()
BASELINE_JSON = json.loads((_PA / "00_baseline_lock" / "baseline.json").read_text())


def assemble_perturbed(params: dict) -> str:
    """Substitute the four new parameters into the v04 source."""
    src = WINNER_SRC
    # DISHES_LOG_CLIP and DISHES_INV_BETA in the dedicated handler block
    src = re.sub(r"DISHES_LOG_CLIP\s*=\s*[\d.]+",
                 f"DISHES_LOG_CLIP = {params['DISHES_LOG_CLIP']:.4f}", src, count=1)
    src = re.sub(r"DISHES_INV_BETA\s*=\s*[\d.]+",
                 f"DISHES_INV_BETA = {params['DISHES_INV_BETA']:.4f}", src, count=1)
    # OTHER_BETA_MAP overrides
    src = re.sub(
        r'OTHER_BETA_MAP\s*=\s*\{[^}]*\}',
        ('OTHER_BETA_MAP = {"MICROCHIP_OVAL": '
         f'{params["MICROCHIP_OVAL_BETA"]:.4f}, "SLEEP_POD_POLYESTER": '
         f'{params["SLEEP_POD_POLYESTER_BETA"]:.4f}}}'),
        src, count=1
    )
    return src


def lhs(n_samples: int, dim: int, seed: int = 7) -> np.ndarray:
    """Simple LHS sampling in [0,1]^dim."""
    rng = np.random.default_rng(seed)
    cuts = np.linspace(0, 1, n_samples + 1)
    u = rng.uniform(0, 1, size=(n_samples, dim))
    a = cuts[:-1, None]
    pts = a + u * (cuts[1:, None] - cuts[:-1, None])
    for j in range(dim):
        rng.shuffle(pts[:, j])
    return pts


def perturbation(n_samples: int = 50) -> list:
    """50 LHS samples, ±20% on each of 4 parameters."""
    progress_log(f"Phase 5 — perturbation ({n_samples} LHS samples)")
    base = {
        "DISHES_LOG_CLIP": 10.0,
        "DISHES_INV_BETA": 0.60,
        "MICROCHIP_OVAL_BETA": 0.40,
        "SLEEP_POD_POLYESTER_BETA": 0.40,
    }
    keys = list(base.keys())
    samples = lhs(n_samples, dim=4)
    results = []

    def _run_one(i: int, sample: np.ndarray) -> dict:
        params = {}
        for j, k in enumerate(keys):
            v = base[k]
            scaled = v * (0.80 + 0.40 * sample[j])  # ±20%
            params[k] = scaled
        src = assemble_perturbed(params)
        res = run_algo_text(src, save_log_as=f"phase5_perturb_{i:03d}")
        return {
            "i": i,
            **{k: round(params[k], 4) for k in keys},
            "F1_pnl": res.fold_pnls["F1"], "F2_pnl": res.fold_pnls["F2"],
            "F3_pnl": res.fold_pnls["F3"], "F4_pnl": res.fold_pnls["F4"],
            "F5_pnl": res.fold_pnls["F5"],
            "fold_min": res.fold_min,
            "fold_median": res.fold_median,
            "fold_mean": round(res.fold_mean, 1),
            "total_3day": res.total_3day,
            "sharpe_3day": res.sharpe_3day,
            "max_dd_3day": res.max_dd_3day,
        }

    with ThreadPoolExecutor(max_workers=4) as ex:
        futs = {ex.submit(_run_one, i, samples[i]): i for i in range(n_samples)}
        done = 0
        for fut in as_completed(futs):
            try:
                results.append(fut.result())
            except Exception as e:
                progress_log(f"Phase 5 perturb ERROR i={futs[fut]}: {e}")
            done += 1
            if done % 10 == 0:
                progress_log(f"Phase 5 perturb {done}/{n_samples}")

    results.sort(key=lambda r: r["i"])
    write_csv(results, OUT / "perturbation.csv")
    progress_log("Phase 5 perturbation complete")
    return results


def match_mode_test() -> list:
    progress_log("Phase 5 — match_mode test")
    rows = []
    for mode in ("worse", "all", "none"):
        res = run_algo(WINNER_PATH, match_mode=mode,
                        save_log_as=f"phase5_mm_{mode}")
        rows.append({
            "mode": mode,
            "F1_pnl": res.fold_pnls["F1"], "F2_pnl": res.fold_pnls["F2"],
            "F3_pnl": res.fold_pnls["F3"], "F4_pnl": res.fold_pnls["F4"],
            "F5_pnl": res.fold_pnls["F5"],
            "fold_min": res.fold_min,
            "fold_median": res.fold_median,
            "fold_mean": round(res.fold_mean, 1),
            "total_3day": res.total_3day,
            "sharpe_3day": res.sharpe_3day,
            "max_dd_3day": res.max_dd_3day,
        })
    write_csv(rows, OUT / "match_mode.csv")
    return rows


def limit_8_test() -> dict:
    progress_log("Phase 5 — limit=8")
    # build alternate LIMIT_FLAGS with limit=8
    products = [line.split(":")[0].split("=", 1)[1]
                for line in (_PA.parent / "utils" / "limit_flags.txt").read_text().split()]
    extra = [f"--limit={p}:8" for p in products]
    res = run_algo(WINNER_PATH, match_mode="worse",
                   extra_flags=extra, save_log_as="phase5_limit8")
    out = {
        "F1_pnl": res.fold_pnls["F1"], "F2_pnl": res.fold_pnls["F2"],
        "F3_pnl": res.fold_pnls["F3"], "F4_pnl": res.fold_pnls["F4"],
        "F5_pnl": res.fold_pnls["F5"],
        "fold_min": res.fold_min,
        "fold_median": res.fold_median,
        "fold_mean": round(res.fold_mean, 1),
        "total_3day": res.total_3day,
        "sharpe_3day": res.sharpe_3day,
        "max_dd_3day": res.max_dd_3day,
    }
    write_csv([out], OUT / "limit_8.csv")
    return out


def day_removal_test() -> list:
    progress_log("Phase 5 — day-removal (per-day runs)")
    rows = []
    for d in (2, 3, 4):
        res = run_algo(WINNER_PATH, days=(d,), match_mode="worse",
                       save_log_as=f"phase5_dayonly_{d}")
        rows.append({
            "day": d,
            "pnl": res.per_day_pnl.get(d, 0),
            "total_3day_via_single": res.total_3day,
            "sharpe": res.sharpe_3day,
            "max_dd": res.max_dd_3day,
        })
    write_csv(rows, OUT / "day_removal.csv")
    return rows


def main():
    progress_log("Phase 5 — stress battery START")

    # 1. match_mode (3 runs, sequential is fine)
    mm = match_mode_test()
    # 2. limit=8 (1 run)
    lim8 = limit_8_test()
    # 3. day-removal (3 runs)
    dr = day_removal_test()
    # 4. perturbation (50 LHS — biggest)
    pert = perturbation(n_samples=50)

    # Summary
    base_fm = BASELINE_JSON["fold_min"]
    base_fmean = BASELINE_JSON["fold_mean"]
    p_fm = [r["fold_min"] for r in pert]
    p_fmean = [r["fold_mean"] for r in pert]
    head_fm = next(r["fold_min"] for r in mm if r["mode"] == "worse")
    head_fmean = next(r["fold_mean"] for r in mm if r["mode"] == "worse")

    md = []
    md.append("# Phase 5 — stress summary\n")
    md.append("Headline (algo1_post_audit, match_mode='worse'):\n")
    md.append(f"- fold_min: {head_fm:,}")
    md.append(f"- fold_mean: {head_fmean:,.1f}")
    md.append(f"- baseline fold_min: {base_fm:,}")
    md.append(f"- baseline fold_mean: {base_fmean:,.1f}")

    md.append("\n## 1. match_mode band")
    md.append("| mode | fold_min | fold_mean | sharpe |\n|---|---|---|---|")
    for r in mm:
        sh = f"{r['sharpe_3day']:.2f}" if r['sharpe_3day'] is not None else "n/a"
        md.append(f"| {r['mode']} | {r['fold_min']:,} | {r['fold_mean']:,.0f} | {sh} |")
    mm_worse = next(r for r in mm if r["mode"] == "worse")
    mm_all = next(r for r in mm if r["mode"] == "all")
    if mm_all["fold_min"] >= mm_worse["fold_min"]:
        md.append(f"\nmatch_mode='all' fold_min ≥ match_mode='worse' fold_min ✓")
    else:
        md.append(f"\nmatch_mode='all' fold_min < 'worse'! Unexpected.")

    md.append("\n## 2. limit=8 stress (must stay positive, ≥30% headline)")
    md.append(f"- fold_min: {lim8['fold_min']:,} ({lim8['fold_min']/head_fm*100:.1f}% of headline)")
    md.append(f"- fold_mean: {lim8['fold_mean']:,.0f}")
    if lim8['fold_min'] > 0 and lim8['fold_min'] / head_fm >= 0.30:
        md.append("- ✓ passes (positive AND ≥30%)")
    else:
        md.append("- ✗ FAILS")

    md.append("\n## 3. perturbation ±20% (50 LHS samples)")
    md.append(f"- fold_min mean: {np.mean(p_fm):,.0f}")
    md.append(f"- fold_min std:  {np.std(p_fm):,.0f}")
    md.append(f"- fold_min min:  {min(p_fm):,}")
    md.append(f"- fold_min p05:  {np.percentile(p_fm, 5):,.0f}")
    md.append(f"- fold_min p50:  {np.percentile(p_fm, 50):,.0f}")
    md.append(f"- fold_min p95:  {np.percentile(p_fm, 95):,.0f}")
    md.append(f"- fold_min max:  {max(p_fm):,}")
    above_base = sum(1 for v in p_fm if v >= base_fm)
    md.append(f"- samples with fold_min ≥ baseline: {above_base}/{len(p_fm)} "
              f"({above_base/len(p_fm)*100:.1f}%)")

    md.append("\n## 4. day-removal (per-day single-day backtests)")
    md.append("| day | PnL | sharpe | max_dd |\n|---|---|---|---|")
    for r in dr:
        sh = r["sharpe"] if r["sharpe"] is not None else "n/a"
        md.append(f"| {r['day']} | {r['pnl']:,} | {sh} | {r['max_dd']} |")

    md.append("\n## 5. latency stress: not run")
    md.append("The upstream `prosperity4btest` CLI does not expose a latency "
              "flag. To simulate +1 tick latency would require modifying the "
              "algo to defer a tick of `state.position` reads — out of scope "
              "for this study.\n")

    md.append("\n## Verdict")
    pass_band = mm_worse["fold_min"] <= mm_all["fold_min"]
    pass_lim8 = lim8['fold_min'] > 0 and lim8['fold_min']/head_fm >= 0.30
    pass_pert = above_base / len(p_fm) >= 0.70  # ≥70% must beat baseline
    pass_dr = all(r["pnl"] > 0 for r in dr)  # every single day positive
    md.append(f"- match_mode band: {'✓' if pass_band else '✗'}")
    md.append(f"- limit=8 (positive AND ≥30%): {'✓' if pass_lim8 else '✗'}")
    md.append(f"- perturbation (≥70% beat baseline fold_min): {'✓' if pass_pert else '✗'}")
    md.append(f"- day-removal (every day positive): {'✓' if pass_dr else '✗'}")
    md.append(f"- **{'OVERALL PASS' if all([pass_band, pass_lim8, pass_pert, pass_dr]) else 'OVERALL FAIL'}**")

    (OUT / "stress_summary.md").write_text("\n".join(md))
    print("\n".join(md))
    progress_log("Phase 5 — stress complete")


if __name__ == "__main__":
    main()
