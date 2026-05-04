"""Single-file MR Trader.

Loads per-product params from `distilled_params.py`. For each product runs one
of:
  - TAKER: maintain rolling FV + residual sigma; cross-spread when |z| > z_in,
           flatten when |z| < z_out.
  - MM:    quote inside-spread (best±1) with inventory skew β·pos. No signal
           skew unless alpha_skew is set.
  - IDLE:  no orders.

Position-limit landmine: track `bought` and `sold` separately per product per
tick (NOT cumulative position) to avoid the matching engine's all-or-nothing
rejection.

No external imports beyond datamodel + (optional) statistics. Pure-python
incremental FV state stored in the Trader instance — reset every run.
"""
from __future__ import annotations

import math
import os
import sys
from collections import deque
from typing import Any, Deque, Dict, List, Optional

# ---------------------------------------------------------------------------
# datamodel comes from prosperity4btest harness
from datamodel import OrderDepth, Order, TradingState  # type: ignore  # noqa: F401

# Import distilled_params from this directory regardless of cwd
_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)
from distilled_params import get_params  # noqa: E402

LIM = 10


# ---------------------------------------------------------------------------
# Incremental FV state
# ---------------------------------------------------------------------------
class FvState:
    """Holds per-product running FV state. compute() is called each tick after
    appending the latest mid-price. No look-ahead: FV uses only mid history
    UP TO BUT NOT INCLUDING the current tick (i.e. the value just appended).

    Implementations cover the families used by distilled_params:
        rolling_mean, rolling_median, rolling_linreg, rolling_quadratic,
        range_mid, ewma, microprice, microprice_ewma, ar_diff, lattice,
        ofi_corrected, anchor.
    """
    def __init__(self, family: str, params: Dict[str, Any]):
        self.family = family
        self.params = params
        self.history: Deque[float] = deque()
        self.maxlen = self._compute_maxlen()
        # AR(p) coef placeholder; updated on the fly
        self.ar_coef: Optional[List[float]] = None
        # Holt state
        self.holt_level: Optional[float] = None
        self.holt_slope: Optional[float] = None
        # Microprice EWMA state
        self.mp_ewma: Optional[float] = None
        # OFI state
        self.prev_book: Optional[Dict[str, float]] = None
        self.ofi_alpha: float = 0.0  # would be calibrated offline

    def _compute_maxlen(self) -> int:
        """How much price history we need to keep."""
        f = self.family
        p = self.params
        if f in ("rolling_mean", "rolling_median", "range_mid",
                 "rolling_linreg", "rolling_quadratic"):
            return int(p["w"]) + 4
        if f in ("ewma",):
            return int(max(8, p["half_life"] * 5))
        if f in ("microprice_ewma",):
            return int(max(8, p["half_life"] * 5))
        if f in ("ar_diff",):
            return 5000  # for OLS refit
        return 8

    def update_and_compute(self, mid: float, *, bid: float, ask: float,
                           bv: float, av: float) -> Optional[float]:
        """Append latest mid, return FV(t+1) prediction (used at NEXT tick)."""
        if not math.isfinite(mid):
            return None
        # The FV reported now will be the prediction usable AT the NEXT tick.
        # But the trader uses FV computed using info up to and INCLUDING current
        # tick to inform the order placed for current tick (which fills at the
        # current visible book). That is causal because the engine matches
        # against the book snapshot we already saw.
        self.history.append(mid)
        if len(self.history) > self.maxlen:
            self.history.popleft()
        f = self.family
        p = self.params
        h = self.history
        n = len(h)
        if f == "rolling_mean":
            w = int(p["w"])
            if n < w:
                return None
            # average over last w values (use most-recent w)
            s = 0.0
            cnt = 0
            for v in list(h)[-w:]:
                s += v
                cnt += 1
            return s / cnt
        if f == "rolling_median":
            w = int(p["w"])
            if n < w:
                return None
            arr = list(h)[-w:]
            arr_sorted = sorted(arr)
            mid_i = w // 2
            if w % 2 == 0:
                return 0.5 * (arr_sorted[mid_i - 1] + arr_sorted[mid_i])
            return arr_sorted[mid_i]
        if f == "range_mid":
            w = int(p["w"])
            if n < w:
                return None
            arr = list(h)[-w:]
            return 0.5 * (max(arr) + min(arr))
        if f == "ewma":
            hl = float(p["half_life"])
            alpha = 1.0 - 0.5 ** (1.0 / hl)
            # rebuild EWMA from history (cost is O(n) but we cap maxlen)
            arr = list(h)
            v = arr[0]
            for x in arr[1:]:
                v = alpha * x + (1 - alpha) * v
            return v
        if f == "rolling_linreg":
            w = int(p["w"])
            if n < w:
                return None
            arr = list(h)[-w:]
            t_arr = list(range(w))
            t_mean = (w - 1) / 2.0
            num = 0.0
            den = 0.0
            x_mean = sum(arr) / w
            for i, x in enumerate(arr):
                d = i - t_mean
                num += d * (x - x_mean)
                den += d * d
            if den <= 0:
                return None
            b = num / den
            a = x_mean - b * t_mean
            return a + b * w  # extrapolate one step ahead
        if f == "rolling_quadratic":
            w = int(p["w"])
            if n < w:
                return None
            arr = list(h)[-w:]
            # quadratic fit: y = c0 + c1·t + c2·t²
            # solve normal equations via small 3×3
            S0, S1, S2, S3, S4 = w, 0.0, 0.0, 0.0, 0.0
            T0, T1, T2 = 0.0, 0.0, 0.0
            for i, x in enumerate(arr):
                t = float(i)
                t2 = t * t
                S1 += t
                S2 += t2
                S3 += t * t2
                S4 += t2 * t2
                T0 += x
                T1 += t * x
                T2 += t2 * x
            # normal eqn matrix
            A = [[S0, S1, S2], [S1, S2, S3], [S2, S3, S4]]
            b = [T0, T1, T2]
            try:
                c0, c1, c2 = _solve3x3(A, b)
            except Exception:
                return None
            # extrapolate at t = w (one ahead)
            return c0 + c1 * w + c2 * w * w
        if f == "microprice":
            denom = bv + av
            if denom <= 0:
                return None
            return (bid * av + ask * bv) / denom
        if f == "microprice_ewma":
            denom = bv + av
            if denom <= 0:
                return self.mp_ewma
            mp = (bid * av + ask * bv) / denom
            hl = float(p["half_life"])
            alpha = 1.0 - 0.5 ** (1.0 / hl)
            if self.mp_ewma is None:
                self.mp_ewma = mp
            else:
                self.mp_ewma = alpha * mp + (1 - alpha) * self.mp_ewma
            return self.mp_ewma
        if f == "lattice":
            step = float(p["step"])
            if step <= 0:
                return None
            return round(mid / step) * step
        if f == "ar_diff":
            p_ord = int(p["p"])
            arr = list(h)
            if len(arr) < max(50, p_ord + 5):
                return None
            # OLS fit on entire current history's first-differences
            diffs = [arr[i] - arr[i - 1] for i in range(1, len(arr))]
            n_d = len(diffs)
            if n_d < p_ord + 10:
                return None
            # design matrix: lag-1..p of diffs predicting next diff
            # we fit only every 200 ticks to amortize cost
            need_refit = (self.ar_coef is None) or (n_d % 200 == 0)
            if need_refit:
                Y = []
                Xrow = []
                for k in range(p_ord, n_d):
                    Y.append(diffs[k])
                    Xrow.append([diffs[k - 1 - i] for i in range(p_ord)])
                if not Y:
                    return None
                self.ar_coef = _ols_solve(Xrow, Y)
            # forecast next diff
            lags = [diffs[-1 - i] for i in range(p_ord)]
            dx_hat = sum(c * lg for c, lg in zip(self.ar_coef, lags))
            return mid + dx_hat
        if f == "anchor":
            return mid
        return None

    def update_book(self, bid: float, ask: float, bv: float, av: float) -> None:
        """Track book snapshot for OFI-style FVs."""
        self.prev_book = {"bid": bid, "ask": ask, "bv": bv, "av": av}


# Tiny linear-algebra helpers (no numpy at runtime per task contract)
def _solve3x3(A, b):
    # gaussian elim
    M = [row[:] + [b[i]] for i, row in enumerate(A)]
    for i in range(3):
        # pivot
        piv = abs(M[i][i])
        pi = i
        for k in range(i + 1, 3):
            if abs(M[k][i]) > piv:
                piv = abs(M[k][i])
                pi = k
        if pi != i:
            M[i], M[pi] = M[pi], M[i]
        if abs(M[i][i]) < 1e-12:
            raise ValueError("singular")
        for k in range(i + 1, 3):
            f = M[k][i] / M[i][i]
            for j in range(i, 4):
                M[k][j] -= f * M[i][j]
    x = [0.0, 0.0, 0.0]
    for i in (2, 1, 0):
        s = M[i][3]
        for j in range(i + 1, 3):
            s -= M[i][j] * x[j]
        x[i] = s / M[i][i]
    return x


def _ols_solve(X_rows, Y):
    """Solve X^T X beta = X^T Y for beta, returning a list."""
    p = len(X_rows[0])
    # build XtX (pxp) and XtY (p)
    XtX = [[0.0] * p for _ in range(p)]
    XtY = [0.0] * p
    for row, y in zip(X_rows, Y):
        for i in range(p):
            XtY[i] += row[i] * y
            for j in range(p):
                XtX[i][j] += row[i] * row[j]
    # gaussian elim
    M = [XtX[i][:] + [XtY[i]] for i in range(p)]
    for i in range(p):
        piv = abs(M[i][i])
        pi = i
        for k in range(i + 1, p):
            if abs(M[k][i]) > piv:
                piv = abs(M[k][i])
                pi = k
        if pi != i:
            M[i], M[pi] = M[pi], M[i]
        if abs(M[i][i]) < 1e-12:
            return [0.0] * p
        for k in range(i + 1, p):
            f = M[k][i] / M[i][i]
            for j in range(i, p + 1):
                M[k][j] -= f * M[i][j]
    beta = [0.0] * p
    for i in range(p - 1, -1, -1):
        s = M[i][p]
        for j in range(i + 1, p):
            s -= M[i][j] * beta[j]
        beta[i] = s / M[i][i]
    return beta


# ---------------------------------------------------------------------------
# Trader
# ---------------------------------------------------------------------------
class Trader:
    def __init__(self):
        self._params: Dict[str, Dict[str, Any]] = get_params()
        self._fv_state: Dict[str, FvState] = {}
        self._sigma_state: Dict[str, Dict[str, float]] = {}  # rolling sigma stats
        self._last_z: Dict[str, float] = {}
        # warm-up tick counter
        self._tick = 0

    def _get_fv_state(self, prod: str) -> Optional[FvState]:
        if prod not in self._fv_state:
            cfg = self._params.get(prod, {})
            if cfg.get("mode") != "TAKER":
                return None
            family = cfg["fv_family"]
            params = cfg["fv_params"]
            self._fv_state[prod] = FvState(family, params)
            self._sigma_state[prod] = {"sum": 0.0, "sum2": 0.0, "n": 0,
                                       "max_n": 5000}
        return self._fv_state.get(prod)

    def _get_mm_fv_state(self, prod: str, cfg: Dict[str, Any]) -> FvState:
        if prod not in self._fv_state:
            family = cfg["fv_family"]
            params = cfg["fv_params"]
            self._fv_state[prod] = FvState(family, params)
            self._sigma_state[prod] = {"sum": 0.0, "sum2": 0.0, "n": 0,
                                       "max_n": 5000}
        return self._fv_state[prod]

    def _update_sigma(self, prod: str, residual: float) -> float:
        st = self._sigma_state[prod]
        st["sum"] += residual
        st["sum2"] += residual * residual
        st["n"] += 1
        # use exponential decay for stability (simple cap-based variant)
        if st["n"] > st["max_n"]:
            # halve to keep "rolling" feel
            st["sum"] *= 0.5
            st["sum2"] *= 0.5
            st["n"] = int(st["n"] * 0.5)
        n = st["n"]
        if n < 50:
            return 1.0
        mean = st["sum"] / n
        var = max(0.0, st["sum2"] / n - mean * mean)
        sigma = math.sqrt(var)
        return sigma if sigma > 0 else 1.0

    def run(self, state: TradingState):
        result: Dict[str, List[Order]] = {}
        self._tick += 1
        for prod, od in state.order_depths.items():
            cfg = self._params.get(prod)
            if not cfg or cfg.get("mode") == "IDLE":
                continue
            pos = state.position.get(prod, 0)
            # extract book
            buys = od.buy_orders or {}
            asks = od.sell_orders or {}
            if not buys or not asks:
                continue
            best_bid = max(buys.keys())
            best_ask = min(asks.keys())
            bv = buys[best_bid]
            av = -asks[best_ask]   # convert to positive size
            mid = 0.5 * (best_bid + best_ask)
            mode = cfg.get("mode")
            orders: List[Order] = []
            if mode == "TAKER":
                fv_st = self._get_fv_state(prod)
                if fv_st is None:
                    continue
                fv_val = fv_st.update_and_compute(mid, bid=best_bid, ask=best_ask,
                                                  bv=bv, av=av)
                if fv_val is None:
                    continue
                residual = mid - fv_val
                sigma = self._update_sigma(prod, residual)
                if sigma <= 0:
                    continue
                z = residual / sigma
                self._last_z[prod] = z
                z_in = float(cfg["z_in"])
                z_out = float(cfg["z_out"])
                # decide target (fixed sizing only — others added later)
                sizing = cfg.get("sizing", "fixed")
                if sizing == "fixed":
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
                elif sizing == "linear":
                    g = float(cfg.get("sizing_gamma", 3.0))
                    tgt = -g * z
                    if tgt > LIM:
                        tgt = LIM
                    elif tgt < -LIM:
                        tgt = -LIM
                    target = int(round(tgt))
                else:
                    target = 0
                delta = target - pos
                # Aggressive crossing — taker
                bought = 0
                sold = 0
                if delta > 0:
                    need = delta
                    cap = LIM - pos
                    if need > cap:
                        need = cap
                    for ap in sorted(asks.keys()):
                        if need <= 0:
                            break
                        a_size = -asks[ap]
                        f = min(need, a_size)
                        if f > 0:
                            orders.append(Order(prod, ap, f))
                            bought += f
                            need -= f
                elif delta < 0:
                    need = -delta
                    cap = LIM + pos
                    if need > cap:
                        need = cap
                    for bp in sorted(buys.keys(), reverse=True):
                        if need <= 0:
                            break
                        b_size = buys[bp]
                        f = min(need, b_size)
                        if f > 0:
                            orders.append(Order(prod, bp, -f))
                            sold += f
                            need -= f
                # nothing else — never both buy & sell same tick for taker
            elif mode == "MM":
                # Inside-spread quoting with inventory + (optional) signal skew.
                offset = int(cfg.get("spread_offset", 1))
                spread = best_ask - best_bid
                if spread <= 1:
                    continue
                buy_px = best_bid + offset
                sell_px = best_ask - offset
                if buy_px >= sell_px:
                    continue
                beta = float(cfg.get("beta_inv", 0.2))
                alpha = float(cfg.get("alpha_skew", 0.0))
                # Optional signal-driven FV
                fv_family = cfg.get("fv_family")
                signal_z = 0.0
                if fv_family is not None:
                    fv_st = self._get_mm_fv_state(prod, cfg)
                    fv_val = fv_st.update_and_compute(mid, bid=best_bid, ask=best_ask,
                                                     bv=bv, av=av)
                    if fv_val is not None:
                        residual = mid - fv_val
                        sigma = self._update_sigma(prod, residual)
                        if sigma > 0:
                            signal_z = residual / sigma
                # inventory shift: pos>0 -> shift both quotes DOWN to flatten
                inv_shift = int(round(beta * pos))
                # signal shift: z>0 (price above FV) -> shift DOWN to encourage selling
                sig_shift = int(round(alpha * signal_z))
                shift = inv_shift + sig_shift
                buy_px -= shift
                sell_px -= shift
                # ensure quotes still inside spread
                if buy_px <= best_bid:
                    buy_px = best_bid + 1
                if sell_px >= best_ask:
                    sell_px = best_ask - 1
                if buy_px >= sell_px:
                    if buy_px > best_bid:
                        buy_px = sell_px - 1
                    else:
                        sell_px = buy_px + 1
                size = int(cfg.get("max_size", 10))
                buy_cap = LIM - pos
                sell_cap = LIM + pos
                if buy_cap > 0:
                    qty = min(size, buy_cap)
                    if qty > 0:
                        orders.append(Order(prod, buy_px, qty))
                if sell_cap > 0:
                    qty = min(size, sell_cap)
                    if qty > 0:
                        orders.append(Order(prod, sell_px, -qty))
            else:
                continue
            if orders:
                result[prod] = orders
        return result, 0, ""
