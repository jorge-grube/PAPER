"""
11_zew_swap_experiment.py
--------------------------
Controlled feature-swap experiment: replace z52_VSTOXX with z52_ZEW_Germany
in the 8-feature HMM regime model.

Motivation:
  z52_VSTOXX and z52_VIX are highly correlated (r≈0.90), making VSTOXX
  largely redundant. ZEW_Germany (forward-looking expectations) is nearly
  orthogonal to all current HMM features (r≈0.02 vs ESI) and provides
  genuine incremental information about the macro regime.

Experimental feature set (ZEW_SWAP_FEATURES):
  z52_VIX, z52_ZEW_Germany, z52_MOVE, z52_germany_10y_2y_slope,
  z52_peripheral_spread_avg, z52_DXY_USD_Index,
  z52_Eurozone_Economic_Sentiment_Indicator, z52_hicp_headline_core_gap

All outputs go to model_improvement/ subdirectories and use the _zew_swap
suffix.  Baseline Panel A/B outputs are NEVER overwritten.

Stages:
  1. Feature engineering — add z52_ZEW_Germany, save experimental parquet
  2. Walk-forward HMM (MIN_TRAIN_OBS=156, checkpoint-resume, batch=10)
  3. Panel B backtest with zew-swap labels/probs
  4. Comparison + statistical tests vs baseline
"""
from __future__ import annotations
import logging, pickle, sys, time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import t as t_dist

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from models.hmm import (
    WALK_FORWARD_STEP, HMMFitResult,
    fit_hmm, decode_regimes, select_and_impute,
)
from optimization.cvar      import solve_cvar, CVaRConfig
from optimization.markowitz import solve_min_variance, MarkowitzConfig

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s | %(levelname)-7s | %(message)s",
                    datefmt="%H:%M:%S")
log = logging.getLogger(__name__)

# ── paths ─────────────────────────────────────────────────────────────────────
PROCESSED  = ROOT / "data" / "processed"
MI_DATA    = PROCESSED / "model_improvement"
MI_REPORTS = ROOT / "reports" / "model_improvement"
REPORTS    = ROOT / "reports"

for _d in [MI_DATA, MI_REPORTS]:
    _d.mkdir(parents=True, exist_ok=True)

FEAT_PATH  = MI_DATA / "regime_features_weekly_zew_swap.parquet"
LAB_PATH   = MI_DATA / "regime_labels_wf_156_zew_swap.parquet"
PRB_PATH   = MI_DATA / "regime_probs_wf_156_zew_swap.parquet"
CKPT_PATH  = MI_DATA / "hmm_wf_checkpoint_156_zew_swap.pkl"
PERF_PATH  = MI_REPORTS / "panel_b_performance_zew_swap.csv"
TC_PATH    = MI_REPORTS / "panel_b_tc_sensitivity_zew_swap.csv"
SUMM_PATH  = MI_REPORTS / "panel_b_summary_zew_swap.md"
CMP_PATH   = MI_REPORTS / "zew_swap_comparison.md"
STAT_PATH  = MI_REPORTS / "zew_swap_statistical_tests.md"

# ── experiment config ─────────────────────────────────────────────────────────
ZEW_SWAP_FEATURES: list[str] = [
    "z52_VIX",
    "z52_ZEW_Germany",               # replaces z52_VSTOXX
    "z52_MOVE",
    "z52_germany_10y_2y_slope",
    "z52_peripheral_spread_avg",
    "z52_DXY_USD_Index",
    "z52_Eurozone_Economic_Sentiment_Indicator",
    "z52_hicp_headline_core_gap",
]

VIX_IDX       = 0      # z52_VIX stays at position 0 → state ordering unaffected
N_STATES      = 4
MIN_TRAIN_OBS = 156
BATCH_SIZE    = 10     # checkpoints per bash call (survives 45s timeout)

# ── portfolio config ───────────────────────────────────────────────────────────
ALPHA        = 0.95
MAX_WEIGHT   = 0.25
REBALANCE    = 4
MIN_HISTORY  = 156
SCENARIO_CAP = 260
MIN_REGIME_SCENARIOS = 30
TC_BPS_LIST  = [0, 5, 10, 25]
CASH_COL     = "EURIBOR_3M"
STOXX_COL    = "StoxxEurope600"
ANN          = 52

STRATEGY_LABELS = {
    "equal_weight_risky": "Equal-Weight Risky (1/N)",
    "stoxx600":           "STOXX Europe 600",
    "static_cvar":        "Static CVaR",
    "markowitz":          "Markowitz (Min-Var)",
    "regime_cvar_A":      "Regime CVaR-A (ZEW)",
    "weighted_cvar":      "Weighted CVaR (ZEW)",
}

CVAR_CFG = CVaRConfig(alpha=ALPHA, max_weight=MAX_WEIGHT)
MKV_CFG  = MarkowitzConfig(max_weight=MAX_WEIGHT, min_scenarios=52, fallback_to_equal=True)

# ── statistical test config ────────────────────────────────────────────────────
HAC_LAG   = 13
BLOCK_LEN = 13
N_BOOT    = 5_000
SEED      = 42


# ══════════════════════════════════════════════════════════════════════════════
# Stage 1 — Feature engineering
# ══════════════════════════════════════════════════════════════════════════════

def stage_features():
    if FEAT_PATH.exists():
        log.info("Stage 1: %s already exists — skipping.", FEAT_PATH.name)
        return

    log.info("Stage 1: Engineering z52_ZEW_Germany...")

    rv = pd.read_parquet(PROCESSED / "regime_variables_weekly.parquet")
    rv.index = pd.to_datetime(rv.index)

    # Identify ZEW column (case-insensitive search)
    zew_col = next(
        (c for c in rv.columns if "zew" in c.lower() and "germany" in c.lower()), None
    )
    if zew_col is None:
        # Fallback: any column with "ZEW"
        zew_col = next((c for c in rv.columns if "zew" in c.lower()), None)
    if zew_col is None:
        raise RuntimeError(
            f"No ZEW_Germany column found in regime_variables_weekly.parquet. "
            f"Available columns: {list(rv.columns)}"
        )
    log.info("  Using ZEW column: '%s'", zew_col)
    log.info("  Non-null obs: %d / %d", rv[zew_col].notna().sum(), len(rv))

    # 52-week rolling z-score (same convention as feature_engineering.py)
    zew_raw = rv[zew_col]
    rolling_mean = zew_raw.rolling(52, min_periods=26).mean()
    rolling_std  = zew_raw.rolling(52, min_periods=26).std(ddof=1)
    z52_zew = (zew_raw - rolling_mean) / rolling_std.replace(0, np.nan)
    z52_zew.name = "z52_ZEW_Germany"

    # Load the baseline feature parquet and add the new column
    feats = pd.read_parquet(PROCESSED / "regime_features_weekly.parquet")
    feats.index = pd.to_datetime(feats.index)

    feats["z52_ZEW_Germany"] = z52_zew.reindex(feats.index)

    non_null = feats["z52_ZEW_Germany"].notna().sum()
    log.info("  z52_ZEW_Germany added: %d non-null rows out of %d", non_null, len(feats))

    feats.to_parquet(FEAT_PATH)
    log.info("Stage 1 complete: %s", FEAT_PATH)


# ══════════════════════════════════════════════════════════════════════════════
# Stage 2 — Walk-forward HMM with ZEW_SWAP_FEATURES
# ══════════════════════════════════════════════════════════════════════════════

def canonical_permutation(result: HMMFitResult) -> np.ndarray:
    """Order states by ascending mean z52_VIX (position 0)."""
    vix_means = result.model.means_[:, VIX_IDX]
    return np.argsort(np.argsort(vix_means))   # inv_perm: old→new label


def stage_hmm(batch_size: int = BATCH_SIZE):
    feats_raw = pd.read_parquet(FEAT_PATH)
    X = select_and_impute(feats_raw, ZEW_SWAP_FEATURES, logger=log)
    n = len(X)
    log.info("Stage 2: Feature matrix %d×%d  %s..%s",
             n, X.shape[1], X.index[0].date(), X.index[-1].date())

    checkpoints = list(range(MIN_TRAIN_OBS, n + 1, WALK_FORWARD_STEP))
    total = len(checkpoints)
    log.info("MIN_TRAIN=%d  STEP=%d  N_STATES=%d  total_ckpts=%d",
             MIN_TRAIN_OBS, WALK_FORWARD_STEP, N_STATES, total)

    # Load or initialise checkpoint
    if CKPT_PATH.exists():
        with open(CKPT_PATH, "rb") as f:
            ckpt = pickle.load(f)
        valid = (
            ckpt.get("n") == n and
            ckpt.get("n_states") == N_STATES and
            ckpt.get("min_train") == MIN_TRAIN_OBS and
            ckpt.get("features") == ZEW_SWAP_FEATURES and
            ckpt.get("label_switched") is True
        )
        if not valid:
            log.warning("Checkpoint invalid (param mismatch) — starting fresh.")
            ckpt = None
        else:
            done = len(ckpt["completed_ends"])
            log.info("Resuming: %d/%d done (%.1f%%)",
                     done, total, 100 * done / total)
    else:
        ckpt = None

    if ckpt is None:
        ckpt = {
            "n":              n,
            "n_states":       N_STATES,
            "min_train":      MIN_TRAIN_OBS,
            "features":       ZEW_SWAP_FEATURES,
            "label_switched": True,
            "labels":         np.full(n, np.nan),
            "posteriors":     np.full((n, N_STATES), np.nan),
            "completed_ends": set(),
            "done":           False,
        }

    if ckpt["done"]:
        log.info("Stage 2: Already complete — writing parquets.")
        _write_hmm_parquets(ckpt, X)
        return

    todo = [e for e in checkpoints if e not in ckpt["completed_ends"]]
    log.info("Stage 2: %d checkpoints remaining", len(todo))

    for end in todo[:batch_size]:
        X_train       = X.iloc[:end]
        result        = fit_hmm(X_train, n_states=N_STATES, logger=log)
        raw_labels    = decode_regimes(result, X_train)
        X_scaled      = result.scaler.transform(X_train.values)
        raw_post      = result.model.predict_proba(X_scaled)

        inv_perm  = canonical_permutation(result)
        perm      = np.argsort(inv_perm)
        can_label = int(inv_perm[int(raw_labels.iloc[-1])])
        can_post  = raw_post[-1][perm]

        ckpt["labels"][end - 1]     = can_label
        ckpt["posteriors"][end - 1] = can_post
        ckpt["completed_ends"].add(end)

    with open(CKPT_PATH, "wb") as f:
        pickle.dump(ckpt, f)

    done = len(ckpt["completed_ends"])
    log.info("Stage 2: Saved %d/%d (%.1f%%) — %d remaining",
             done, total, 100 * done / total, total - done)

    if done >= total:
        ckpt["done"] = True
        with open(CKPT_PATH, "wb") as f:
            pickle.dump(ckpt, f)
        log.info("Stage 2: All checkpoints complete.")

    _write_hmm_parquets(ckpt, X)


def _write_hmm_parquets(ckpt, X):
    lab = pd.Series(ckpt["labels"], index=X.index, name="regime_wf")
    prb = pd.DataFrame(ckpt["posteriors"], index=X.index,
                       columns=[f"prob_state_{k}" for k in range(N_STATES)])
    # Forward-fill between checkpoints so every weekly row has a label.
    # Matches the convention used in regime_labels_wf_156.parquet (baseline).
    lab = lab.ffill()
    prb = prb.ffill()
    n_valid = lab.notna().sum()
    if n_valid > 0:
        log.info("Valid labels: %d  first=%s  last=%s",
                 n_valid, lab.dropna().index.min().date(),
                 lab.dropna().index.max().date())
    lab.to_frame().to_parquet(LAB_PATH)
    prb.to_parquet(PRB_PATH)
    log.info("Stage 2: Parquets written → %s, %s", LAB_PATH.name, PRB_PATH.name)


# ══════════════════════════════════════════════════════════════════════════════
# Stage 3 — Panel B backtest (ZEW-swap labels)
# ══════════════════════════════════════════════════════════════════════════════

def _port(w_df, ret):
    return (w_df.shift(1) * ret.reindex(columns=w_df.columns)).sum(axis=1, min_count=1)

def _weekly_to(w_df):
    return w_df.diff().abs().sum(axis=1) / 2.0

def _eq_drift_to(ret_r):
    n = ret_r.shape[1]; rp = ret_r.mean(axis=1)
    wd = ret_r.apply(lambda r: (1/n)*(1+r)/(1+rp), axis=0)
    return (wd - 1/n).abs().sum(axis=1) / 2.0

def _apply_tc(gross, to, rate):
    return gross - rate * to.shift(1).fillna(0.0).reindex(gross.index).fillna(0.0)

def compute_metrics(r, rf):
    r   = r.dropna()
    rf_a = rf.reindex(r.index).fillna(0.0)
    exc  = r - rf_a
    cagr = (1+r).prod()**(ANN/len(r)) - 1
    vol  = r.std(ddof=1) * np.sqrt(ANN)
    sh   = exc.mean()/exc.std(ddof=1)*np.sqrt(ANN) if exc.std(ddof=1) > 0 else np.nan
    cum  = (1+r).cumprod()
    mdd  = (cum/cum.cummax()-1).min()
    k    = max(1, int(len(r)*(1-ALPHA)))
    cvar_w = float(np.sort(r.values)[:k].mean())
    cal  = cagr/abs(mdd) if mdd else np.nan
    return dict(CAGR_pct=round(cagr*100,2), Vol_pct=round(vol*100,2),
                Sharpe=round(sh,3), MaxDD_pct=round(mdd*100,2),
                CVaR95_weekly_pct=round(cvar_w*100,3),
                Calmar=round(cal,3), N_weeks=len(r),
                RF_ann_pct=round(rf_a.mean()*ANN*100,3))

def _solve_regime_cvar_A(hist, labels_hist, current_label):
    mask = labels_hist == current_label
    regime_hist = hist[mask]
    if len(regime_hist) >= MIN_REGIME_SCENARIOS:
        res = solve_cvar(regime_hist, CVAR_CFG)
        if res and res.get("weights") is not None:
            return res["weights"]
    res = solve_cvar(hist, CVAR_CFG)
    return res["weights"] if res and res.get("weights") is not None else None

def _solve_weighted_cvar(hist, posteriors_hist, current_posterior):
    from scipy.optimize import linprog
    n, m = hist.shape
    w_raw = posteriors_hist @ current_posterior
    w_sum = w_raw.sum()
    if w_sum == 0 or np.isnan(w_sum):
        res = solve_cvar(hist, CVAR_CFG)
        return res["weights"] if res and res.get("weights") is not None else None
    w_norm = w_raw / w_sum

    c = np.zeros(m + 1 + n)
    c[m] = 1.0
    c[m+1:] = w_norm / (1 - ALPHA)

    A_eq = np.zeros((1, m+1+n)); A_eq[0,:m] = 1.0; b_eq = np.array([1.0])
    A_ub = np.zeros((2*n, m+1+n))
    A_ub[:n, :m]   = -hist
    A_ub[:n, m]    = -1.0
    A_ub[:n, m+1:] = -np.eye(n)
    A_ub[n:, m+1:] = -np.eye(n)
    b_ub = np.zeros(2*n)
    bounds = [(0, MAX_WEIGHT)]*m + [(None,None)] + [(0,None)]*n

    res = linprog(c, A_ub=A_ub, b_ub=b_ub, A_eq=A_eq, b_eq=b_eq,
                  bounds=bounds, method="highs")
    return res.x[:m] if res.success else None


def stage_panel_b():
    log.info("Stage 3: Panel B backtest (ZEW-swap regime labels)...")

    ret = pd.read_parquet(PROCESSED / "investable_returns_weekly.parquet")
    ret.index = pd.to_datetime(ret.index)
    lab = pd.read_parquet(LAB_PATH)["regime_wf"]
    lab.index = pd.to_datetime(lab.index)
    prb = pd.read_parquet(PRB_PATH)
    prb.index = pd.to_datetime(prb.index)

    risky = [c for c in ret.columns if c != CASH_COL]
    n_r   = len(risky)
    ret_r = ret[risky].dropna()
    rf    = ret[CASH_COL]
    n_states = prb.shape[1]

    valid_lab = lab.dropna()
    common = ret_r.index.intersection(valid_lab.index).sort_values()
    log.info("Common index: %s → %s  n=%d",
             common.min().date(), common.max().date(), len(common))

    w_s = {}; w_m = {}; w_rA = {}; w_wC = {}
    last_ws = np.ones(n_r)/n_r; last_wm = np.ones(n_r)/n_r
    last_rA = np.ones(n_r)/n_r; last_wC = np.ones(n_r)/n_r
    first_rebal = None; rebal_ctr = 0

    for i, date in enumerate(common):
        if i < MIN_HISTORY:
            continue
        if first_rebal is None:
            first_rebal = date
            log.info("First rebal: %s (i=%d)", date.date(), i)

        if rebal_ctr % REBALANCE == 0:
            s0       = max(0, i - SCENARIO_CAP)
            hist_idx = common[s0:i]
            hist     = ret_r.loc[hist_idx].values
            hist_df  = ret_r.loc[hist_idx]
            lab_hist = valid_lab.loc[hist_idx].values.astype(int)
            prb_hist = prb.loc[hist_idx].values
            cur_lab  = int(valid_lab.loc[date])
            cur_prb  = prb.loc[date].values

            res = solve_cvar(hist, CVAR_CFG)
            if res and res.get("weights") is not None:
                last_ws = res["weights"]
            w_s[date] = last_ws.copy()

            try:
                wm, _ = solve_min_variance(hist_df, MKV_CFG)
                last_wm = wm
            except Exception:
                pass
            w_m[date] = last_wm.copy()

            wA = _solve_regime_cvar_A(hist, lab_hist, cur_lab)
            if wA is not None:
                last_rA = wA
            w_rA[date] = last_rA.copy()

            wW = _solve_weighted_cvar(hist, prb_hist, cur_prb)
            if wW is not None:
                last_wC = wW
            w_wC[date] = last_wC.copy()

        rebal_ctr += 1

    log.info("Walk-forward complete. Building weight frames...")
    def _wdf(d): return pd.DataFrame(d, index=risky).T.reindex(common).ffill()
    w_s_df  = _wdf(w_s);  w_m_df  = _wdf(w_m)
    w_rA_df = _wdf(w_rA); w_wC_df = _wdf(w_wC)
    w_eq    = pd.DataFrame(1.0/n_r, index=common, columns=risky)
    w_st    = pd.DataFrame({STOXX_COL: 1.0}, index=common)

    gross = pd.DataFrame(index=common)
    gross["equal_weight_risky"] = _port(w_eq,    ret_r)
    gross["stoxx600"]           = _port(w_st,    ret[[STOXX_COL]])
    gross["static_cvar"]        = _port(w_s_df,  ret_r)
    gross["markowitz"]          = _port(w_m_df,  ret_r)
    gross["regime_cvar_A"]      = _port(w_rA_df, ret_r)
    gross["weighted_cvar"]      = _port(w_wC_df, ret_r)

    strat  = gross.loc[first_rebal:].dropna(how="all")
    rf_ev  = rf.reindex(strat.index).fillna(0.0)
    log.info("Eval: %s → %s  n=%d",
             strat.index.min().date(), strat.index.max().date(), len(strat))

    to_eq = _eq_drift_to(ret_r.reindex(strat.index))
    to_s  = _weekly_to(w_s_df.reindex(strat.index))
    to_m  = _weekly_to(w_m_df.reindex(strat.index))
    to_rA = _weekly_to(w_rA_df.reindex(strat.index))
    to_wC = _weekly_to(w_wC_df.reindex(strat.index))
    to_st = pd.Series(0.0, index=strat.index)
    to_map = {"equal_weight_risky": to_eq, "stoxx600": to_st,
              "static_cvar": to_s, "markowitz": to_m,
              "regime_cvar_A": to_rA, "weighted_cvar": to_wC}

    cols = [c for c in STRATEGY_LABELS if c in strat.columns]
    net_f = {tc: pd.DataFrame({
        c: _apply_tc(strat[c], to_map[c], tc/10_000) for c in cols})
        for tc in TC_BPS_LIST}

    rows = []
    for tc in TC_BPS_LIST:
        for col in cols:
            m = compute_metrics(net_f[tc][col], rf_ev)
            to_c = to_map[col].reindex(strat.index).fillna(0)
            m.update({"tc_bps": tc, "strategy": col, "label": STRATEGY_LABELS[col],
                      "weekly_to_pct": round(to_c.mean()*100, 4),
                      "ann_to_pct": round(to_c.mean()*ANN*100, 2),
                      "eval_start": str(strat.index.min().date()),
                      "eval_end": str(strat.index.max().date())})
            rows.append(m)

    mdf = pd.DataFrame(rows)
    mdf.to_csv(PERF_PATH, index=False)
    log.info("Wrote %s", PERF_PATH.name)

    # Persist gross strategy returns for Stage 4 statistical tests
    strat_save_path = MI_DATA / "panel_b_returns_zew_swap.parquet"
    strat.to_parquet(strat_save_path)
    log.info("Wrote %s", strat_save_path.name)

    # TC sensitivity
    tc_rows = []
    for col in cols:
        to_c = to_map[col].reindex(strat.index).fillna(0)
        ann_to = to_c.mean()*ANN*100
        for tc in TC_BPS_LIST:
            m = compute_metrics(net_f[tc][col], rf_ev)
            tc_rows.append({"strategy": col, "label": STRATEGY_LABELS[col],
                            "tc_bps": tc, "CAGR_pct": m["CAGR_pct"],
                            "Sharpe": m["Sharpe"], "MaxDD_pct": m["MaxDD_pct"],
                            "Calmar": m["Calmar"],
                            "weekly_to_pct": round(to_c.mean()*100, 4),
                            "ann_to_pct": round(ann_to, 2)})
    pd.DataFrame(tc_rows).to_csv(TC_PATH, index=False)
    log.info("Wrote %s", TC_PATH.name)

    # Summary markdown
    _write_panel_summary(mdf, strat)
    log.info("Stage 3 complete.")

    # Console summary
    g0 = mdf[mdf["tc_bps"]==0].set_index("strategy")
    log.info("%-28s %7s %7s %7s %8s","Strategy","CAGR%","Vol%","Sharpe","MaxDD%")
    for s, m in g0.iterrows():
        log.info("%-28s %+6.2f  %6.2f  %7.3f  %7.2f",
                 s, m.CAGR_pct, m.Vol_pct, m.Sharpe, m.MaxDD_pct)

    return mdf, strat, lab, prb


def _write_panel_summary(mdf, strat):
    g0   = mdf[mdf["tc_bps"]==0].set_index("strategy")
    es   = strat.index.min().date(); ee = strat.index.max().date(); nw = len(strat)
    cols = [c for c in STRATEGY_LABELS if c in g0.index]

    sh_static = g0.loc["static_cvar","Sharpe"] if "static_cvar" in g0.index else None
    sh_rA     = g0.loc["regime_cvar_A","Sharpe"] if "regime_cvar_A" in g0.index else None
    if sh_static and sh_rA:
        diff = sh_rA - sh_static
        if diff > 0.02:
            verdict = f"Regime CVaR-A (ZEW) achieves a **higher** gross Sharpe ({sh_rA:.3f} vs {sh_static:.3f})."
        elif diff < -0.02:
            verdict = f"Regime CVaR-A (ZEW) achieves a **lower** gross Sharpe ({sh_rA:.3f} vs {sh_static:.3f})."
        else:
            verdict = f"Regime CVaR-A (ZEW) achieves a **similar** gross Sharpe ({sh_rA:.3f} vs {sh_static:.3f})."
    else:
        verdict = "See performance table."

    lines = [
        "# Panel B — ZEW-Swap Experiment",
        "", "*Generated by `11_zew_swap_experiment.py`*", "",
        "> **Experimental variant:** z52_VSTOXX replaced by z52_ZEW_Germany",
        "> in the 8-feature HMM. All other parameters identical to baseline Panel B.",
        "> Walk-forward MIN_TRAIN_OBS=156. All labels strictly out-of-sample.", "",
        "---", "", "## Experimental Feature Set", "",
        "| # | Feature | Role |",
        "| --- | --- | --- |",
        "| 1 | z52_VIX | Equity volatility (US, anchor for state ordering) |",
        "| 2 | **z52_ZEW_Germany** | **NEW — replaces z52_VSTOXX** — forward expectations |",
        "| 3 | z52_MOVE | Fixed income volatility |",
        "| 4 | z52_germany_10y_2y_slope | Yield curve slope |",
        "| 5 | z52_peripheral_spread_avg | Sovereign stress |",
        "| 6 | z52_DXY_USD_Index | Dollar strength |",
        "| 7 | z52_Eurozone_Economic_Sentiment_Indicator | Cyclical sentiment |",
        "| 8 | z52_hicp_headline_core_gap | Inflation surprise |",
        "",
        "---", "", "## Performance (Gross, 0 bps TC)", "",
        f"**Evaluation:** {es} → {ee} ({nw} weeks, {nw/ANN:.1f} yr)", "",
        "| Strategy | CAGR | Vol | Sharpe | MaxDD | CVaR 95% (wkly) | Calmar |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for s in cols:
        m = g0.loc[s]
        lines.append(f"| {m.label} | {m.CAGR_pct:+.2f}% | {m.Vol_pct:.2f}% | "
                     f"{m.Sharpe:.3f} | {m.MaxDD_pct:.2f}% | "
                     f"{m.CVaR95_weekly_pct:.3f}% | {m.Calmar:.3f} |")

    tc_p = mdf[["strategy","tc_bps","Sharpe"]].pivot(
        index="strategy", columns="tc_bps", values="Sharpe")
    lines += ["", "---", "", "## TC Sensitivity (Sharpe)", "",
              "| Strategy | 0 bps | 5 bps | 10 bps | 25 bps |",
              "| --- | ---: | ---: | ---: | ---: |"]
    for s in cols:
        v = tc_p.loc[s] if s in tc_p.index else {}
        lines.append(f"| {STRATEGY_LABELS[s]} | {v.get(0,float('nan')):.3f} | "
                     f"{v.get(5,float('nan')):.3f} | {v.get(10,float('nan')):.3f} | "
                     f"{v.get(25,float('nan')):.3f} |")

    tob = mdf[mdf["tc_bps"]==0][["strategy","label","weekly_to_pct","ann_to_pct"]]
    lines += ["", "---", "", "## Turnover", "",
              "| Strategy | Weekly | Annualised |", "| --- | ---: | ---: |"]
    for _, r in tob.iterrows():
        if r["strategy"] not in cols: continue
        lines.append(f"| {r['label']} | {r['weekly_to_pct']:.3f}% | {r['ann_to_pct']:.2f}% |")

    lines += ["", "---", "", "## Key Findings", "",
              f"- **Verdict:** {verdict}",
              f"- **Turnover:** See table above. Compare vs baseline Regime CVaR-A ~225% annually.",
              "- **Statistical caution:** Bootstrap CIs span ±0.3–0.5 units. See zew_swap_statistical_tests.md."]
    SUMM_PATH.write_text("\n".join(lines))
    log.info("Wrote %s", SUMM_PATH.name)


# ══════════════════════════════════════════════════════════════════════════════
# Stage 4 — Comparison + statistical tests vs baseline
# ══════════════════════════════════════════════════════════════════════════════

def newey_west_se(x: np.ndarray, lag: int) -> float:
    n = len(x)
    x_dm = x - x.mean()
    nw_var = np.dot(x_dm, x_dm) / n
    for k in range(1, lag + 1):
        gamma_k = np.dot(x_dm[k:], x_dm[:-k]) / n
        nw_var += 2.0 * (1.0 - k / (lag + 1.0)) * gamma_k
    return float(np.sqrt(max(nw_var, 0.0) / n))

def hac_nw_test(strat_excess, bench_excess, lag=HAC_LAG):
    d = np.asarray(strat_excess) - np.asarray(bench_excess)
    mean_d = d.mean()
    se = newey_west_se(d, lag)
    if se == 0.0:
        return float(mean_d), np.nan, np.nan
    t_stat = mean_d / se
    p_one  = float(t_dist.sf(t_stat, df=len(d)-1))
    return float(mean_d), float(t_stat), p_one

def block_bootstrap_sharpe(excess, block=BLOCK_LEN, n_boot=N_BOOT, seed=SEED):
    rng   = np.random.default_rng(seed)
    n     = len(excess)
    ann   = np.sqrt(ANN)
    sd    = excess.std(ddof=1)
    point = excess.mean() / sd * ann if sd > 0 else np.nan
    n_blocks = int(np.ceil(n / block))
    boot_sharpes = []
    for _ in range(n_boot):
        starts = rng.integers(0, n, size=n_blocks)
        idx    = np.concatenate([np.arange(s, s+block) % n for s in starts])[:n]
        sample = excess[idx]
        sd_b   = sample.std(ddof=1)
        if sd_b > 0:
            boot_sharpes.append(sample.mean() / sd_b * ann)
    boot_arr = np.array(boot_sharpes)
    return float(point), float(np.percentile(boot_arr, 2.5)), float(np.percentile(boot_arr, 97.5))


def stage_comparison(mdf_zew, strat_zew):
    log.info("Stage 4: Comparison + statistical tests...")

    # Load baseline Panel B
    base_path = REPORTS / "panels" / "panel_b_regime_oos_performance.csv"
    if not base_path.exists():
        log.error("Baseline not found: %s", base_path)
        return
    mdf_base = pd.read_csv(base_path)

    g0_zew  = mdf_zew[mdf_zew["tc_bps"]==0].set_index("strategy")
    g0_base = mdf_base[mdf_base["tc_bps"]==0].set_index("strategy")

    COMPARE_COLS = ["equal_weight_risky","stoxx600","static_cvar","markowitz",
                    "regime_cvar_A","weighted_cvar"]

    # ── comparison markdown ───────────────────────────────────────────────────
    lines = [
        "# ZEW-Swap Experiment — Comparison vs Baseline Panel B",
        "", "*Generated by `11_zew_swap_experiment.py`*", "",
        "**Baseline:** z52_VSTOXX as feature 2 (r≈0.90 with z52_VIX)",
        "**ZEW-swap:** z52_ZEW_Germany as feature 2 (r≈0.02 with z52_ESI)", "",
        "---", "", "## Gross Performance Comparison (0 bps TC)", "",
        "| Strategy | Base Sharpe | ZEW Sharpe | Δ Sharpe | Base MaxDD | ZEW MaxDD | Base TO% | ZEW TO% |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for col in COMPARE_COLS:
        if col not in g0_base.index or col not in g0_zew.index:
            continue
        bs = g0_base.loc[col, "Sharpe"]
        zs = g0_zew.loc[col, "Sharpe"]
        bd = g0_base.loc[col, "MaxDD_pct"]
        zd = g0_zew.loc[col, "MaxDD_pct"]
        bt = g0_base.loc[col, "ann_to_pct"]
        zt = g0_zew.loc[col, "ann_to_pct"]
        label = STRATEGY_LABELS.get(col, col)
        lines.append(f"| {label} | {bs:.3f} | {zs:.3f} | {zs-bs:+.3f} | "
                     f"{bd:.2f}% | {zd:.2f}% | {bt:.1f}% | {zt:.1f}% |")

    # TC sensitivity comparison
    def _get_tc_sharpe(mdf, col, tc):
        row = mdf[(mdf["strategy"]==col) & (mdf["tc_bps"]==tc)]
        return row["Sharpe"].iloc[0] if len(row) > 0 else np.nan

    lines += ["", "---", "", "## Net Sharpe at 10 bps TC", "",
              "| Strategy | Baseline | ZEW-swap | Δ |",
              "| --- | ---: | ---: | ---: |"]
    for col in COMPARE_COLS:
        bs = _get_tc_sharpe(mdf_base, col, 10)
        zs = _get_tc_sharpe(mdf_zew, col, 10)
        label = STRATEGY_LABELS.get(col, col)
        lines.append(f"| {label} | {bs:.3f} | {zs:.3f} | {zs-bs:+.3f} |")

    # Regime frequency in ZEW-swap labels
    lab_zew = pd.read_parquet(LAB_PATH)["regime_wf"].dropna()
    vc = lab_zew.value_counts().sort_index()
    total = vc.sum()
    lines += ["", "---", "", "## ZEW-Swap Regime Frequency", "",
              "| State | Weeks | % |", "| --- | ---: | ---: |"]
    for s, cnt in vc.items():
        lines.append(f"| State {int(s)} | {int(cnt)} | {100*cnt/total:.1f}% |")

    # Label agreement between baseline and ZEW-swap
    lab_base_path = PROCESSED / "regime_labels_wf_156.parquet"
    if lab_base_path.exists():
        lab_base = pd.read_parquet(lab_base_path)["regime_wf"].dropna()
        common_idx = lab_base.index.intersection(lab_zew.index)
        agree = (lab_base.loc[common_idx].values.astype(int) ==
                 lab_zew.loc[common_idx].values.astype(int))
        pct_agree = 100 * agree.mean()
        lines += ["", "---", "",
                  f"## Label Agreement: Baseline vs ZEW-Swap", "",
                  f"- **Common dates:** {len(common_idx)}",
                  f"- **Agreement:** {pct_agree:.1f}% of dates assigned identical state",
                  f"- **Disagreement:** {100-pct_agree:.1f}% — these are the dates where",
                  "  the VSTOXX→ZEW swap materially changes the regime classification."]

    CMP_PATH.write_text("\n".join(lines))
    log.info("Wrote %s", CMP_PATH.name)

    # ── statistical tests ─────────────────────────────────────────────────────
    ret = pd.read_parquet(PROCESSED / "investable_returns_weekly.parquet")
    ret.index = pd.to_datetime(ret.index)
    rf = ret[CASH_COL]

    strat_zew.index = pd.to_datetime(strat_zew.index)
    cols = [c for c in STRATEGY_LABELS if c in strat_zew.columns]
    rf_ev = rf.reindex(strat_zew.index).fillna(0.0)
    bench_col = "static_cvar"
    bench_exc = (strat_zew[bench_col] - rf_ev).dropna().values

    stat_lines = [
        "# Statistical Tests — ZEW-Swap Experiment",
        "", "*Generated by `11_zew_swap_experiment.py`*", "",
        f"Tests strategy returns against **Static CVaR** benchmark.",
        f"HAC/NW lag={HAC_LAG}, block-bootstrap block={BLOCK_LEN}, n_boot={N_BOOT}, seed={SEED}.", "",
        "---", "", "## 1  HAC/Newey-West Tests vs Static CVaR", "",
        "One-sided H₁: strategy mean excess return > Static CVaR.",
        "Significance: \\* p<0.10 &nbsp; \\*\\* p<0.05 &nbsp; \\*\\*\\* p<0.01", "",
        "| Strategy | Ann. Diff | t-stat | p (one-sided) | Sig |",
        "| --- | ---: | ---: | ---: | --- |",
    ]
    for col in cols:
        if col == bench_col:
            stat_lines.append(f"| {STRATEGY_LABELS[col]} | 0.000% | — | — | — |")
            continue
        s   = strat_zew[col].dropna()
        rf_s = rf_ev.reindex(s.index).fillna(0.0)
        se  = (s - rf_s).values
        n   = min(len(se), len(bench_exc))
        mean_d, t_stat, p_val = hac_nw_test(se[-n:], bench_exc[-n:])
        ann_diff = mean_d * ANN * 100
        sig = ("***" if (not np.isnan(p_val) and p_val < 0.01) else
               "**"  if (not np.isnan(p_val) and p_val < 0.05) else
               "*"   if (not np.isnan(p_val) and p_val < 0.10) else "")
        t_str = f"{t_stat:.3f}" if not np.isnan(t_stat) else "—"
        p_str = f"{p_val:.4f}"  if not np.isnan(p_val)  else "—"
        stat_lines.append(f"| {STRATEGY_LABELS[col]} | {ann_diff:+.3f}% | {t_str} | {p_str} | {sig} |")

    stat_lines += ["", "---", "", "## 2  Block-Bootstrap 95% Sharpe CIs", "",
                   "Circular block-bootstrap Sharpe ratio confidence intervals.", "",
                   "| Strategy | Point Sharpe | 95% CI Lo | 95% CI Hi | CI Width |",
                   "| --- | ---: | ---: | ---: | ---: |"]
    for col in cols:
        s   = strat_zew[col].dropna()
        rf_s = rf_ev.reindex(s.index).fillna(0.0)
        exc = (s - rf_s).values
        pt, lo, hi = block_bootstrap_sharpe(exc)
        stat_lines.append(f"| {STRATEGY_LABELS[col]} | {pt:.3f} | {lo:.3f} | {hi:.3f} | {hi-lo:.3f} |")

    # ZEW-swap vs baseline regime strategies comparison
    stat_lines += ["", "---", "", "## 3  ZEW-Swap vs Baseline Regime Strategies", "",
                   "Direct Sharpe comparison (gross, 0 bps TC):", ""]
    for col in ["regime_cvar_A", "weighted_cvar"]:
        if col not in g0_zew.index or col not in g0_base.index:
            continue
        zs = g0_zew.loc[col, "Sharpe"]
        bs = g0_base.loc[col, "Sharpe"]
        zt = g0_zew.loc[col, "ann_to_pct"]
        bt = g0_base.loc[col, "ann_to_pct"]
        stat_lines += [
            f"**{STRATEGY_LABELS[col]}:**",
            f"  - Baseline Sharpe: {bs:.3f} | ZEW-swap Sharpe: {zs:.3f} | Δ: {zs-bs:+.3f}",
            f"  - Baseline TO: {bt:.1f}% ann. | ZEW-swap TO: {zt:.1f}% ann.",
            "",
        ]

    stat_lines += ["---", "",
                   "## Recommendation", "",
                   "See zew_swap_comparison.md for the complete comparison table.",
                   "The ZEW-swap constitutes a meaningful feature improvement if:",
                   "  (A) Regime CVaR-A gross Sharpe improves vs baseline, AND",
                   "  (B) Turnover does not increase substantially, AND",
                   "  (C) Label agreement is not so low as to suggest overfitting.",
                   "  (D) Net Sharpe at 10+ bps TC remains competitive with Static CVaR.",
                   "None of these conditions alone is sufficient; all four must be satisfied."]

    STAT_PATH.write_text("\n".join(stat_lines))
    log.info("Wrote %s", STAT_PATH.name)
    log.info("Stage 4 complete.")


# ══════════════════════════════════════════════════════════════════════════════
# Entry point
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", type=int, default=0,
                    help="Run only a specific stage (1-4). 0 = all stages.")
    ap.add_argument("--batch-size", type=int, default=BATCH_SIZE,
                    help="HMM checkpoints per run (Stage 2 only).")
    args = ap.parse_args()

    t_start = time.time()
    log.info("=== ZEW-Swap Experiment ===")

    if args.stage in (0, 1):
        stage_features()
    if args.stage in (0, 2):
        stage_hmm(batch_size=args.batch_size)
    if args.stage in (0, 3):
        mdf_zew, strat_zew, lab, prb = stage_panel_b()
    if args.stage in (0, 4):
        if args.stage == 4:
            # Load outputs written by Stage 3
            mdf_zew   = pd.read_csv(PERF_PATH)
            strat_zew = pd.read_parquet(MI_DATA / "panel_b_returns_zew_swap.parquet")
            strat_zew.index = pd.to_datetime(strat_zew.index)
        stage_comparison(mdf_zew, strat_zew)

    log.info("=== All stages complete in %.0fs ===", time.time() - t_start)
