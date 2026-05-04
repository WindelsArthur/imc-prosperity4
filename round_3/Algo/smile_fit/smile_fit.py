"""
Volatility Smile Fitting Pipeline for IMC Prosperity 4 Round 3
"""
import os
import sys
import json
import warnings
import numpy as np
import pandas as pd
from scipy.stats import norm
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.linear_model import HuberRegressor

warnings.filterwarnings('ignore')

# ── Constants ──────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "ROUND_3", "data")
OUT_DIR  = os.path.join(BASE_DIR, "smile_fit")
PLOT_DIR = os.path.join(OUT_DIR, "plots")
os.makedirs(PLOT_DIR, exist_ok=True)

UNDERLYING = "VELVETFRUIT_EXTRACT"
VOUCHERS   = ["VEV_4000", "VEV_4500", "VEV_5000", "VEV_5100", "VEV_5200",
               "VEV_5300", "VEV_5400", "VEV_5500", "VEV_6000", "VEV_6500"]
STRIKES    = {v: int(v.split("_")[1]) for v in VOUCHERS}

# ── Helpers ────────────────────────────────────────────────────────────────────

def tte_years(day, ts):
    """TTE_days = (8 - day) - ts/1_000_000, then /365"""
    tte_d = (8 - day) - ts / 1_000_000
    return tte_d / 365.0

def bs_call(S, K, T, sigma, r=0.0):
    """Black-Scholes call price."""
    if T <= 0 or sigma <= 0 or S <= 0:
        return max(S - K, 0.0)
    d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    return S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)

def bs_vega(S, K, T, sigma, r=0.0):
    """BS vega (dC/dsigma)."""
    if T <= 0 or sigma <= 0 or S <= 0:
        return 0.0
    d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
    return S * norm.pdf(d1) * np.sqrt(T)

def implied_vol_nr(price, S, K, T, seed=0.24, n_iter=30, tol=1e-6):
    """Newton-Raphson implied vol."""
    intrinsic = max(S - K, 0.0)
    if price <= intrinsic + 1e-6:
        return np.nan
    sigma = seed
    for _ in range(n_iter):
        c = bs_call(S, K, T, sigma)
        v = bs_vega(S, K, T, sigma)
        if v < 1e-10:
            return np.nan
        sigma = sigma - (c - price) / v
        sigma = np.clip(sigma, 0.01, 3.0)
        if abs(c - price) < tol:
            break
    if not (0.05 < sigma < 2.0):
        return np.nan
    return sigma

def wall_mid_row(row, pfx_bid, pfx_ask):
    """
    Compute wall_bid and wall_ask for a row.
    pfx_bid = 'bid', pfx_ask = 'ask', levels 1-3.
    Returns (wall_bid, wall_ask, wall_vol_bid, wall_vol_ask) or NaN if missing.
    """
    def best_wall(price_pfx, vol_pfx):
        best_price = np.nan
        best_vol   = np.nan
        for lvl in [1, 2, 3]:
            p = row.get(f"{price_pfx}_price_{lvl}", np.nan)
            v = row.get(f"{vol_pfx}_volume_{lvl}", np.nan)
            if pd.notna(p) and pd.notna(v):
                if pd.isna(best_vol) or v > best_vol:
                    best_vol   = v
                    best_price = p
        return best_price, best_vol

    wb, wbv = best_wall(pfx_bid, pfx_bid)
    wa, wav = best_wall(pfx_ask, pfx_ask)
    return wb, wa, wbv, wav

# ── Step 1 — Load & clean ──────────────────────────────────────────────────────
print("=== Step 1: Loading data ===")

numeric_cols = [
    "bid_price_1","bid_volume_1","bid_price_2","bid_volume_2",
    "bid_price_3","bid_volume_3",
    "ask_price_1","ask_volume_1","ask_price_2","ask_volume_2",
    "ask_price_3","ask_volume_3","mid_price","profit_and_loss"
]

dfs = []
for day in [0, 1, 2]:
    fname = os.path.join(DATA_DIR, f"prices_round_3_day_{day}.csv")
    df = pd.read_csv(fname, sep=";", dtype=str)
    df["day"] = day
    for c in numeric_cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c].str.strip(), errors="coerce")
    dfs.append(df)

raw = pd.concat(dfs, ignore_index=True)
raw["timestamp"] = pd.to_numeric(raw["timestamp"], errors="coerce")
raw["t_global"]  = raw["day"] * 1_000_000 + raw["timestamp"]

# Compute wall_mid for all products
print("Computing wall_mid...")

def compute_wall(df):
    results = []
    for _, row in df.iterrows():
        wb, wa, wbv, wav = wall_mid_row(row, "bid", "ask")
        results.append((wb, wa, wbv, wav))
    return results

all_products = [UNDERLYING] + VOUCHERS
# Vectorized wall computation
def compute_wall_vec(df):
    bid_prices  = df[["bid_price_1","bid_price_2","bid_price_3"]].values
    bid_vols    = df[["bid_volume_1","bid_volume_2","bid_volume_3"]].values
    ask_prices  = df[["ask_price_1","ask_price_2","ask_price_3"]].values
    ask_vols    = df[["ask_volume_1","ask_volume_2","ask_volume_3"]].values

    def wall_side(prices, vols):
        # mask NaN volumes to -inf so argmax ignores them
        v = np.where(np.isnan(vols), -np.inf, vols)
        idx = np.argmax(v, axis=1)
        n   = len(idx)
        best_vol   = vols[np.arange(n), idx]
        best_price = prices[np.arange(n), idx]
        # if all NaN, best_vol will be NaN (argmax of all-inf gives 0 index but vol is nan)
        all_nan = np.all(np.isnan(vols), axis=1)
        best_vol[all_nan]   = np.nan
        best_price[all_nan] = np.nan
        return best_price, best_vol

    wb, wbv = wall_side(bid_prices, bid_vols)
    wa, wav = wall_side(ask_prices, ask_vols)
    return wb, wa, wbv, wav

# Split by product and compute
und_df     = raw[raw["product"] == UNDERLYING].copy()
wb, wa, wbv, wav = compute_wall_vec(und_df)
und_df["wall_bid"] = wb
und_df["wall_ask"] = wa
und_df["wall_vol_bid"] = wbv
und_df["wall_vol_ask"] = wav
und_df["wall_mid"]  = (und_df["wall_bid"] + und_df["wall_ask"]) / 2
und_df = und_df[und_df["wall_mid"].notna()].copy()
und_df = und_df[["day","timestamp","t_global","wall_mid"]].rename(columns={"wall_mid":"S"})

vou_dfs = []
for v in VOUCHERS:
    vdf = raw[raw["product"] == v].copy()
    if vdf.empty:
        print(f"  WARNING: no data for {v}")
        continue
    wb, wa, wbv, wav = compute_wall_vec(vdf)
    vdf["wall_bid"]     = wb
    vdf["wall_ask"]     = wa
    vdf["wall_vol_bid"] = wbv
    vdf["wall_vol_ask"] = wav
    vdf["wall_mid"]     = (vdf["wall_bid"] + vdf["wall_ask"]) / 2
    vdf["voucher"]      = v
    vou_dfs.append(vdf)

vou = pd.concat(vou_dfs, ignore_index=True)
vou = vou[vou["wall_mid"].notna() & vou["wall_bid"].notna() & vou["wall_ask"].notna()].copy()

# Merge with underlying
vou = vou.merge(und_df, on=["day","timestamp","t_global"], how="inner")

# ── Step 2 — TTE ───────────────────────────────────────────────────────────────
print("=== Step 2: TTE ===")
vou["T"] = tte_years(vou["day"], vou["timestamp"])
vou = vou[vou["T"] > 0].copy()
print(f"  After TTE filter: {len(vou)} rows")

# ── Step 3 — Implied vol ────────────────────────────────────────────────────────
print("=== Step 3: Implied vol ===")
vou["K"] = vou["voucher"].map(STRIKES)

iv_list   = []
vega_list = []
for _, row in vou.iterrows():
    S  = row["S"]
    K  = row["K"]
    T  = row["T"]
    C  = row["wall_mid"]
    iv = implied_vol_nr(C, S, K, T)
    if pd.notna(iv):
        vg = bs_vega(S, K, T, iv)
        if vg < 0.5:
            iv = np.nan
            vg = np.nan
    else:
        vg = np.nan
    iv_list.append(iv)
    vega_list.append(vg)

vou["IV"]   = iv_list
vou["vega"] = vega_list
before = len(vou)
vou = vou[vou["IV"].notna()].copy()
print(f"  IV computed: kept {len(vou)}/{before}")

# ── Step 4 — Liquidity filters ─────────────────────────────────────────────────
print("=== Step 4: Liquidity filters ===")

vou["spread"]     = vou["wall_ask"] - vou["wall_bid"]
vou["spread_rel"] = vou["spread"] / vou["wall_mid"]

keep_mask = pd.Series(True, index=vou.index)

# Spread filter
for idx in vou.index:
    v = vou.at[idx, "voucher"]
    if v == "VEV_6500":
        if vou.at[idx, "spread"] > 3:
            keep_mask[idx] = False
    else:
        if vou.at[idx, "spread_rel"] > 0.05:
            keep_mask[idx] = False

# Wall volume filter
keep_mask &= (vou["wall_vol_bid"] >= 5) & (vou["wall_vol_ask"] >= 5)

# Vega filter
keep_mask &= (vou["vega"] >= 0.5)

vou = vou[keep_mask].copy()

# IV jump filter (per voucher, sorted by ts)
vou = vou.sort_values(["voucher", "t_global"]).reset_index(drop=True)
prev_iv   = vou.groupby("voucher")["IV"].shift(1)
iv_jump   = (vou["IV"] - prev_iv).abs()
jump_mask = iv_jump.isna() | (iv_jump <= 0.10)
vou = vou[jump_mask].copy()

# Log kept/total
print("  Per-voucher kept/total after liquidity filters:")
for v in VOUCHERS:
    total_v = len(raw[raw["product"]==v])
    kept_v  = len(vou[vou["voucher"]==v])
    print(f"    {v}: {kept_v}/{total_v}")

print(f"  Total after filters: {len(vou)}")

# ── Step 5 — Pooled smile fit ──────────────────────────────────────────────────
print("=== Step 5: Pooled smile fit ===")

vou["m"] = np.log(vou["K"] / vou["S"]) / np.sqrt(vou["T"])

X = np.column_stack([vou["m"]**2, vou["m"], np.ones(len(vou))])
y = vou["IV"].values
w = vou["vega"].values

# Huber fit
huber = HuberRegressor(epsilon=1.35, max_iter=300)
huber.fit(X, y, sample_weight=w)
a_h, b_h, c_h = huber.coef_[0], huber.coef_[1], huber.intercept_

# WLS fit using sqrt(vega) weighting
w_wls = np.sqrt(w)
Xw = X * w_wls[:, None]
yw = y * w_wls
coef_wls, _, _, _ = np.linalg.lstsq(Xw, yw, rcond=None)
a_w, b_w, c_w = coef_wls

# Compare
iv_pred_h = X @ np.array([a_h, b_h, c_h])
iv_pred_w = X @ coef_wls

rmse_h = np.sqrt(np.mean((y - iv_pred_h)**2))
rmse_w = np.sqrt(np.mean((y - iv_pred_w)**2))
maxres_h = np.max(np.abs(y - iv_pred_h))
maxres_w = np.max(np.abs(y - iv_pred_w))

if rmse_h <= rmse_w * 1.05 and maxres_h < maxres_w:
    a, b, c = a_h, b_h, c_h
    method  = "huber"
    iv_pred = iv_pred_h
else:
    a, b, c = a_w, b_w, c_w
    method  = "wls"
    iv_pred = iv_pred_w

print(f"  Huber RMSE={rmse_h:.5f}, WLS RMSE={rmse_w:.5f}")
print(f"  Chosen: {method}")
print(f"  a={a:.6f}, b={b:.6f}, c={c:.6f}")

vou["IV_fit"]   = iv_pred if method == "huber" else X @ np.array([a, b, c])
vou["residual"] = vou["IV"] - vou["IV_fit"]

# ── Step 6 — Time-split CV ──────────────────────────────────────────────────────
print("=== Step 6: Time-split CV ===")

train = vou[vou["day"] < 2].copy()
test  = vou[vou["day"] == 2].copy()

# Re-fit on train
X_tr = np.column_stack([train["m"]**2, train["m"], np.ones(len(train))])
y_tr = train["IV"].values
w_tr = train["vega"].values

huber_tr = HuberRegressor(epsilon=1.35, max_iter=300)
huber_tr.fit(X_tr, y_tr, sample_weight=w_tr)
a_tr_h, b_tr_h, c_tr_h = huber_tr.coef_[0], huber_tr.coef_[1], huber_tr.intercept_

w_wls_tr = np.sqrt(w_tr)
Xw_tr    = X_tr * w_wls_tr[:, None]
yw_tr    = y_tr * w_wls_tr
coef_wls_tr, _, _, _ = np.linalg.lstsq(Xw_tr, yw_tr, rcond=None)
a_tr_w, b_tr_w, c_tr_w = coef_wls_tr

if method == "huber":
    a_tr, b_tr, c_tr = a_tr_h, b_tr_h, c_tr_h
else:
    a_tr, b_tr, c_tr = a_tr_w, b_tr_w, c_tr_w

X_te = np.column_stack([test["m"]**2, test["m"], np.ones(len(test))])
y_te = test["IV"].values

iv_pred_tr = X_tr @ np.array([a_tr, b_tr, c_tr])
iv_pred_te = X_te @ np.array([a_tr, b_tr, c_tr])

train_rmse_iv = np.sqrt(np.mean((y_tr - iv_pred_tr)**2))
test_rmse_iv  = np.sqrt(np.mean((y_te - iv_pred_te)**2))

# $ space test RMSE
dollar_residuals = []
for _, row in test.iterrows():
    iv_f = a_tr * row["m"]**2 + b_tr * row["m"] + c_tr
    price_f = bs_call(row["S"], row["K"], row["T"], iv_f)
    dollar_residuals.append(abs(row["wall_mid"] - price_f))
test_rmse_dollar = np.sqrt(np.mean(np.array(dollar_residuals)**2))

print(f"  Train RMSE IV: {train_rmse_iv:.5f}")
print(f"  Test  RMSE IV: {test_rmse_iv:.5f}")
print(f"  Test  RMSE $:  {test_rmse_dollar:.5f}")

# Per-strike test RMSE
print("  Per-strike test RMSE (IV):")
per_strike_test_rmse = {}
for v in VOUCHERS:
    sub = test[test["voucher"]==v]
    if len(sub) == 0:
        continue
    iv_s = X_te[test["voucher"].values == v] @ np.array([a_tr, b_tr, c_tr])
    rmse_s = np.sqrt(np.mean((sub["IV"].values - iv_s)**2))
    per_strike_test_rmse[v] = float(rmse_s)
    print(f"    {v}: {rmse_s:.5f} ({len(sub)} pts)")

# ── Step 7 — Per-strike priors (day 2) ─────────────────────────────────────────
print("=== Step 7: Per-strike priors (day 2) ===")

day2 = vou[vou["day"]==2].copy()
day2["IV_smile"] = a * day2["m"]**2 + b * day2["m"] + c
day2["resid_dollar"] = day2.apply(
    lambda r: r["wall_mid"] - bs_call(r["S"], r["K"], r["T"], r["IV_smile"]), axis=1
)

priors = {}
for v in VOUCHERS:
    sub = day2[day2["voucher"]==v]
    if len(sub) == 0:
        priors[v] = {"mu": 0.0, "sigma": 0.0, "n_obs": 0,
                     "median_vega": np.nan, "mu_iv": np.nan, "sigma_iv": np.nan,
                     "median_spread": np.nan}
        continue
    mu_v      = float(sub["resid_dollar"].mean())
    sigma_v   = float(sub["resid_dollar"].std(ddof=1)) if len(sub) > 1 else 0.0
    med_vega  = float(sub["vega"].median())
    mu_iv_v   = mu_v / med_vega if med_vega != 0 else np.nan
    sigma_iv_v= sigma_v / med_vega if med_vega != 0 else np.nan
    n_obs     = int(len(sub))
    med_spread= float(sub["spread"].median())
    priors[v] = {
        "mu": mu_v, "sigma": sigma_v, "n_obs": n_obs,
        "median_vega": med_vega, "mu_iv": mu_iv_v, "sigma_iv": sigma_iv_v,
        "median_spread": med_spread
    }
    print(f"  {v}: n={n_obs}, mu={mu_v:.4f}, sigma={sigma_v:.4f}, mu_iv={mu_iv_v:.5f}, sigma_iv={sigma_iv_v:.5f}")

# ── Step 8 — Sanity checks ─────────────────────────────────────────────────────
print("=== Step 8: Sanity checks ===")

def chk(cond, msg):
    status = "PASS" if cond else "FAIL"
    print(f"  [{status}] {msg}")
    return cond

chk(abs(a) < 5, f"|a|={abs(a):.4f} < 5")
chk(abs(b) < 2, f"|b|={abs(b):.4f} < 2")
chk(0.05 < c < 0.5, f"c={c:.4f} in (0.05, 0.5)")

# Per-day coefficients
for d in [0, 1, 2]:
    sub_d = vou[vou["day"]==d]
    if len(sub_d) < 10:
        continue
    Xd = np.column_stack([sub_d["m"]**2, sub_d["m"], np.ones(len(sub_d))])
    yd = sub_d["IV"].values
    wd = sub_d["vega"].values
    try:
        if method == "huber":
            h = HuberRegressor(epsilon=1.35, max_iter=300)
            h.fit(Xd, yd, sample_weight=wd)
            ad, bd, cd = h.coef_[0], h.coef_[1], h.intercept_
        else:
            wdd = np.sqrt(wd)
            Xdw = Xd * wdd[:, None]
            ydw = yd * wdd
            coef_d, _, _, _ = np.linalg.lstsq(Xdw, ydw, rcond=None)
            ad, bd, cd = coef_d
        chk(abs(ad-a)/max(abs(a),1e-6) < 0.20, f"Day {d} a={ad:.4f} within 20% of pooled a={a:.4f}")
        chk(abs(bd-b)/max(abs(b),1e-6) < 0.20, f"Day {d} b={bd:.4f} within 20% of pooled b={b:.4f}")
        chk(abs(cd-c)/max(abs(c),1e-6) < 0.20, f"Day {d} c={cd:.4f} within 20% of pooled c={c:.4f}")
    except Exception as e:
        print(f"  [SKIP] Day {d} fit failed: {e}")

n_obs_gt1000 = sum(1 for v in VOUCHERS if priors[v]["n_obs"] > 1000)
chk(n_obs_gt1000 >= 6, f"{n_obs_gt1000}/10 strikes have n_obs > 1000")
chk(test_rmse_iv < 0.03, f"Test RMSE IV = {test_rmse_iv:.5f} < 0.03")

# ── Step 9 — Outputs ───────────────────────────────────────────────────────────
print("=== Step 9: Writing outputs ===")

# Per-day per-strike test RMSE for dollar space
per_strike_dollar_rmse = {}
for v in VOUCHERS:
    sub = test[test["voucher"]==v]
    if len(sub) == 0:
        per_strike_dollar_rmse[v] = np.nan
        continue
    dr = []
    for _, row in sub.iterrows():
        iv_f = a_tr * row["m"]**2 + b_tr * row["m"] + c_tr
        pf   = bs_call(row["S"], row["K"], row["T"], iv_f)
        dr.append(abs(row["wall_mid"] - pf))
    per_strike_dollar_rmse[v] = float(np.sqrt(np.mean(np.array(dr)**2)))

# smile_coeffs.json
strike_priors_snippet = {
    v: {"mu_iv": priors[v]["mu_iv"], "sigma_iv": priors[v]["sigma_iv"]}
    for v in VOUCHERS
}
snippet = (
    f"SMILE_COEFFS = ({a:.8f}, {b:.8f}, {c:.8f})\n"
    f"STRIKE_PRIORS = {json.dumps(strike_priors_snippet)}"
)
smile_coeffs = {
    "a": float(a), "b": float(b), "c": float(c),
    "method": method,
    "fit_meta": {
        "train_rmse_iv": float(train_rmse_iv),
        "test_rmse_iv":  float(test_rmse_iv),
        "n_points_total": int(len(vou))
    },
    "python_snippet": snippet
}
with open(os.path.join(OUT_DIR, "smile_coeffs.json"), "w") as f:
    json.dump(smile_coeffs, f, indent=2)
print("  Written: smile_coeffs.json")

# strike_priors.json
with open(os.path.join(OUT_DIR, "strike_priors.json"), "w") as f:
    json.dump(priors, f, indent=2)
print("  Written: strike_priors.json")

# ── Plots ───────────────────────────────────────────────────────────────────────

colors_day = {0: "#1f77b4", 1: "#ff7f0e", 2: "#2ca02c"}
m_range    = np.linspace(vou["m"].min(), vou["m"].max(), 300)
iv_smile   = a * m_range**2 + b * m_range + c

# Plot 1: iv_smile_pooled.png
fig, ax = plt.subplots(figsize=(10, 6))
for d in [0, 1, 2]:
    sub = vou[vou["day"]==d]
    ax.scatter(sub["m"], sub["IV"], s=3, alpha=0.4, color=colors_day[d], label=f"Day {d}")
ax.plot(m_range, iv_smile, "k-", lw=2, label=f"Fit: {a:.4f}m²+{b:.4f}m+{c:.4f}")
ax.set_xlabel("Moneyness m = log(K/S)/√T")
ax.set_ylabel("Implied Volatility")
ax.set_title("Pooled IV Smile Fit")
ax.legend()
fig.tight_layout()
fig.savefig(os.path.join(PLOT_DIR, "iv_smile_pooled.png"), dpi=150)
plt.close(fig)
print("  Saved: iv_smile_pooled.png")

# Plot 2: iv_smile_per_day.png
fig, axes = plt.subplots(1, 3, figsize=(18, 5), sharey=True)
for i, d in enumerate([0, 1, 2]):
    ax = axes[i]
    sub = vou[vou["day"]==d]
    ax.scatter(sub["m"], sub["IV"], s=3, alpha=0.5, color=colors_day[d])
    ax.plot(m_range, iv_smile, "k-", lw=1.5, label="Pooled fit")
    ax.set_title(f"Day {d}")
    ax.set_xlabel("m")
    if i == 0:
        ax.set_ylabel("IV")
    ax.legend()
fig.suptitle("IV Smile Per Day with Pooled Fit")
fig.tight_layout()
fig.savefig(os.path.join(PLOT_DIR, "iv_smile_per_day.png"), dpi=150)
plt.close(fig)
print("  Saved: iv_smile_per_day.png")

# Plot 3: residuals_vs_m.png
cmap   = plt.cm.tab10
v_list = VOUCHERS
fig, ax = plt.subplots(figsize=(10, 6))
for i, v in enumerate(v_list):
    sub = vou[vou["voucher"]==v]
    ax.scatter(sub["m"], sub["residual"], s=3, alpha=0.4,
               color=cmap(i/len(v_list)), label=v)
ax.axhline(0, color="k", lw=0.8)
ax.set_xlabel("Moneyness m")
ax.set_ylabel("IV Residual")
ax.set_title("Residuals vs Moneyness (by Strike)")
ax.legend(markerscale=3, fontsize=7)
fig.tight_layout()
fig.savefig(os.path.join(PLOT_DIR, "residuals_vs_m.png"), dpi=150)
plt.close(fig)
print("  Saved: residuals_vs_m.png")

# Plot 4: residuals_ts_grid.png
fig, axes = plt.subplots(2, 5, figsize=(20, 8))
axes = axes.flatten()
for i, v in enumerate(VOUCHERS):
    ax  = axes[i]
    sub = day2[day2["voucher"]==v]
    pr  = priors[v]
    ax.scatter(sub["t_global"], sub["resid_dollar"], s=2, alpha=0.5, color=cmap(i/len(VOUCHERS)))
    if not np.isnan(pr["mu"]):
        ax.axhline(pr["mu"],                      color="r", lw=1.5, label=f"μ={pr['mu']:.2f}")
        ax.axhline(pr["mu"] + pr["sigma"],        color="r", lw=0.8, ls="--")
        ax.axhline(pr["mu"] - pr["sigma"],        color="r", lw=0.8, ls="--")
    ax.set_title(v, fontsize=8)
    ax.set_xlabel("t_global", fontsize=7)
    ax.set_ylabel("$ Residual", fontsize=7)
    ax.legend(fontsize=6)
fig.suptitle("Day 2 $ Residuals vs t_global per Strike")
fig.tight_layout()
fig.savefig(os.path.join(PLOT_DIR, "residuals_ts_grid.png"), dpi=150)
plt.close(fig)
print("  Saved: residuals_ts_grid.png")

# ── report.md ──────────────────────────────────────────────────────────────────
scalping_rec = []
for v in VOUCHERS:
    pr = priors[v]
    if pr["n_obs"] == 0:
        continue
    enable = (pr["sigma_iv"] is not None and not np.isnan(pr["sigma_iv"]) and
              pr["sigma_iv"] > 0.005 and
              pr["median_spread"] / max(pr["median_vega"], 1e-9) < 0.5)
    scalping_rec.append((v, enable, pr["sigma_iv"], pr["median_spread"], pr["median_vega"]))

table_rows = []
for v in VOUCHERS:
    pr = priors[v]
    mu_iv_str     = f"{pr['mu_iv']:.5f}"     if pr['mu_iv'] is not None and not np.isnan(pr['mu_iv'])     else "N/A"
    sigma_iv_str  = f"{pr['sigma_iv']:.5f}"  if pr['sigma_iv'] is not None and not np.isnan(pr['sigma_iv']) else "N/A"
    med_sp_str    = f"{pr['median_spread']:.3f}" if pr['median_spread'] is not None and not np.isnan(pr['median_spread']) else "N/A"
    row = (f"| {v} | {pr['n_obs']} | {pr['mu']:.4f} | {pr['sigma']:.4f} | "
           f"{mu_iv_str} | {sigma_iv_str} | {med_sp_str} |")
    table_rows.append(row)

reliable = [v for v in VOUCHERS if priors[v]["n_obs"] > 1000]
unreliable = [v for v in VOUCHERS if priors[v]["n_obs"] <= 100]

scalping_lines = []
for v, en, sig_iv, med_sp, med_vg in scalping_rec:
    rec = "ENABLE" if en else "DISABLE"
    scalping_lines.append(f"- {v}: {rec} (sigma_iv={sig_iv:.5f}, spread/vega={med_sp/max(med_vg,1e-9):.3f})")

report_md = f"""# Volatility Smile Fitting Report

## Final Coefficients

| Coefficient | Value |
|---|---|
| a | {a:.8f} |
| b | {b:.8f} |
| c | {c:.8f} |
| Method | {method} |

IV smile: IV(m) = {a:.6f}·m² + {b:.6f}·m + {c:.6f}

## Model Performance

| Metric | Value |
|---|---|
| Train RMSE (IV) | {train_rmse_iv:.5f} |
| Test RMSE (IV) | {test_rmse_iv:.5f} |
| Test RMSE ($) | {test_rmse_dollar:.5f} |
| Total filtered points | {len(vou)} |

### Per-Strike Test RMSE (IV space, day 2)

| Strike | RMSE IV | RMSE $ |
|---|---|---|
{"".join(f"| {v} | {per_strike_test_rmse.get(v,float('nan')):.5f} | {per_strike_dollar_rmse.get(v,float('nan')):.4f} |{chr(10)}" for v in VOUCHERS)}

## Per-Strike Priors (Day 2)

| Voucher | n_obs | mu_v | sigma_v | mu_iv | sigma_iv | median_spread |
|---|---|---|---|---|---|---|
{"".join(r+chr(10) for r in table_rows)}

### Reliability Commentary

**Reliable strikes** (n_obs > 1000): {", ".join(reliable) if reliable else "none"}

**Unreliable strikes** (n_obs ≤ 100): {", ".join(unreliable) if unreliable else "none"}

VEV_4000 and VEV_6500 are deep OTM and may have sparse data, making IV estimation noisy.
Strikes near ATM (VEV_5000–VEV_5300) have the most reliable estimates.

## IV-Scalping Recommendation

sigma_iv > 0.005 AND median_spread/median_vega < 0.5 → ENABLE scalping:

{chr(10).join(scalping_lines)}

## Note on T: 6→5d Regime Shift

Between day 2 (6d TTE) and live trading (5d TTE), the option gamma and vega accelerate.
The pooled fit is trained on 8→6d data; the smile shape (a,b,c) is generally stable,
but the ATM IV level (c) may shift as expiry approaches and market makers reprice
time value more aggressively. Monitor the ATM IV on live day and update c if the
test-day bias shows systematic drift.
"""

with open(os.path.join(OUT_DIR, "report.md"), "w") as f:
    f.write(report_md)
print("  Written: report.md")

# ── Final summary ───────────────────────────────────────────────────────────────
print("\n" + "="*60)
print("PIPELINE COMPLETE")
print("="*60)
print(f"  a = {a:.8f}")
print(f"  b = {b:.8f}")
print(f"  c = {c:.8f}")
print(f"  method = {method}")
print(f"  train_rmse_iv = {train_rmse_iv:.5f}")
print(f"  test_rmse_iv  = {test_rmse_iv:.5f}")
print(f"  test_rmse_$   = {test_rmse_dollar:.5f}")
print(f"  n_points_total = {len(vou)}")
print(f"\nOutputs in: {OUT_DIR}")
print(f"  smile_coeffs.json, strike_priors.json, report.md")
print(f"  plots/: iv_smile_pooled.png, iv_smile_per_day.png,")
print(f"          residuals_vs_m.png, residuals_ts_grid.png")
