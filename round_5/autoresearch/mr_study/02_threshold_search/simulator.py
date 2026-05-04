"""Fast in-process MR simulator (taker only) — numba JIT.

Same matching semantics as the prosperity4btest engine for *aggressive*
(cross-spread) orders. Inside-spread MM is evaluated via real backtests later.

Per tick t:
    1. Read book L1+L2+L3.
    2. Compute z(t) = (mid(t) - FV(t)) / sigma.
    3. Decide target_position.
    4. Cross-spread orders sized to (target - position), capped by:
         - position-limit
         - L1+L2+L3 visible depth
    5. Apply fills, update cash, position. PnL = cash + position * mid.

Returns: total_pnl, n_trades, gross_volume, sharpe, max_drawdown_abs.

`run_grid` evaluates a list of configs against a single test slice — the
JIT'd kernel makes this orders-of-magnitude faster than the per-config
Python loop.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Sequence

import numpy as np
from numba import njit


LIM = 10


# --- numba kernel ---------------------------------------------------------
# sizing_kind: 0=fixed, 1=linear, 2=step

@njit(cache=True, fastmath=True)
def _simulate_one(
    mid, fv, sigma_arr,
    bp1, ap1, bv1, av1,
    bp2, ap2, bv2, av2,
    bp3, ap3, bv3, av3,
    z_in, z_out, sizing_kind, sizing_gamma,
    z_stop, time_stop,
):
    """Returns (total_pnl, n_trades, gross_vol, max_dd, final_pos, sharpe)."""
    n = len(mid)
    pos = 0
    cash = 0.0
    trades = 0
    gross = 0
    last_entry = -1
    max_pnl = 0.0
    max_dd = 0.0
    last_mid = 0.0
    # bucketed PnL for sharpe
    bucket = 100
    n_marks = n // bucket
    marks = np.zeros(n_marks)
    mark_idx = 0

    for t in range(n):
        f = fv[t]
        s = sigma_arr[t]
        m = mid[t]
        if not (np.isfinite(m) and np.isfinite(f) and np.isfinite(s) and s > 0.0):
            if (t + 1) % bucket == 0 and mark_idx < n_marks:
                marks[mark_idx] = cash + pos * (m if np.isfinite(m) else last_mid)
                mark_idx += 1
            if np.isfinite(m):
                last_mid = m
            continue
        last_mid = m

        z = (m - f) / s

        # decide target
        if sizing_kind == 0:  # fixed
            if pos == 0:
                if z >= z_in:
                    target = -LIM
                elif z <= -z_in:
                    target = LIM
                else:
                    target = 0
            else:
                if pos > 0 and z >= -z_out:
                    target = 0
                elif pos < 0 and z <= z_out:
                    target = 0
                else:
                    target = LIM if pos > 0 else -LIM
        elif sizing_kind == 1:  # linear
            tgt = -sizing_gamma * z
            if tgt > LIM:
                tgt = LIM
            elif tgt < -LIM:
                tgt = -LIM
            target = int(round(tgt))
        else:  # step
            absz = z if z > 0 else -z
            sign = -1 if z > 0 else 1
            if absz >= 2.5:
                target = sign * LIM
            elif absz >= 1.5:
                target = sign * 5
            elif absz >= 0.8:
                target = sign * 2
            else:
                target = 0
            if pos != 0 and absz <= z_out:
                target = 0

        # stops
        if z_stop > 0.0 and pos != 0:
            if (pos > 0 and z >= z_stop) or (pos < 0 and z <= -z_stop):
                target = 0
        if time_stop > 0 and pos != 0 and last_entry >= 0:
            if t - last_entry >= time_stop:
                target = 0

        delta = target - pos
        if delta != 0:
            if delta > 0:
                need = delta
                cap = LIM - pos
                if need > cap:
                    need = cap
                if need > 0:
                    # L1
                    if np.isfinite(ap1[t]) and av1[t] > 0:
                        f1 = need
                        if f1 > av1[t]:
                            f1 = int(av1[t])
                        if f1 > 0:
                            cash -= ap1[t] * f1
                            pos += f1
                            trades += 1
                            gross += f1
                            need -= f1
                    if need > 0 and np.isfinite(ap2[t]) and av2[t] > 0:
                        f2 = need
                        if f2 > av2[t]:
                            f2 = int(av2[t])
                        if f2 > 0:
                            cash -= ap2[t] * f2
                            pos += f2
                            trades += 1
                            gross += f2
                            need -= f2
                    if need > 0 and np.isfinite(ap3[t]) and av3[t] > 0:
                        f3 = need
                        if f3 > av3[t]:
                            f3 = int(av3[t])
                        if f3 > 0:
                            cash -= ap3[t] * f3
                            pos += f3
                            trades += 1
                            gross += f3
                            need -= f3
            else:
                need = -delta
                cap = LIM + pos
                if need > cap:
                    need = cap
                if need > 0:
                    if np.isfinite(bp1[t]) and bv1[t] > 0:
                        f1 = need
                        if f1 > bv1[t]:
                            f1 = int(bv1[t])
                        if f1 > 0:
                            cash += bp1[t] * f1
                            pos -= f1
                            trades += 1
                            gross += f1
                            need -= f1
                    if need > 0 and np.isfinite(bp2[t]) and bv2[t] > 0:
                        f2 = need
                        if f2 > bv2[t]:
                            f2 = int(bv2[t])
                        if f2 > 0:
                            cash += bp2[t] * f2
                            pos -= f2
                            trades += 1
                            gross += f2
                            need -= f2
                    if need > 0 and np.isfinite(bp3[t]) and bv3[t] > 0:
                        f3 = need
                        if f3 > bv3[t]:
                            f3 = int(bv3[t])
                        if f3 > 0:
                            cash += bp3[t] * f3
                            pos -= f3
                            trades += 1
                            gross += f3
                            need -= f3

        if pos != 0 and last_entry < 0:
            last_entry = t
        if pos == 0:
            last_entry = -1

        cur_pnl = cash + pos * m
        if cur_pnl > max_pnl:
            max_pnl = cur_pnl
        dd = max_pnl - cur_pnl
        if dd > max_dd:
            max_dd = dd

        if (t + 1) % bucket == 0 and mark_idx < n_marks:
            marks[mark_idx] = cur_pnl
            mark_idx += 1

    final_pnl = cash + pos * last_mid

    # Sharpe over bucket diffs
    sharpe = 0.0
    if n_marks > 2:
        diffs = np.diff(marks[:n_marks])
        sd = np.std(diffs)
        if sd > 0.0:
            sharpe = (np.mean(diffs) / sd) * np.sqrt(len(diffs))

    return final_pnl, trades, gross, max_dd, pos, sharpe


@dataclass
class Cfg:
    z_in: float
    z_out: float
    sizing: str   # "fixed"/"linear"/"step"
    sizing_gamma: float = 0.0
    z_stop: float = -1.0
    time_stop: int = -1


def _kind(sizing: str) -> int:
    return {"fixed": 0, "linear": 1, "step": 2}[sizing]


def run_grid(
    *,
    mid, fv, sigma,
    bp1, ap1, bv1, av1,
    bp2, ap2, bv2, av2,
    bp3, ap3, bv3, av3,
    cfgs: Sequence[Cfg],
):
    """Run all configs against a single test slice. Returns numpy structured arr."""
    out = np.zeros(len(cfgs), dtype=[
        ("total_pnl", "f8"), ("n_trades", "i8"), ("gross", "i8"),
        ("max_dd", "f8"), ("final_pos", "i8"), ("sharpe", "f8")])
    for i, c in enumerate(cfgs):
        zs = c.z_stop if c.z_stop is not None and c.z_stop > 0 else 0.0
        ts = c.time_stop if c.time_stop is not None and c.time_stop > 0 else 0
        pnl, nt, gv, dd, fp, sr = _simulate_one(
            mid, fv, sigma,
            bp1, ap1, bv1, av1,
            bp2, ap2, bv2, av2,
            bp3, ap3, bv3, av3,
            c.z_in, c.z_out, _kind(c.sizing), c.sizing_gamma,
            zs, ts,
        )
        out[i] = (pnl, nt, gv, dd, fp, sr)
    return out
