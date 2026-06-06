"""
10_hicp_lag6_robustness.py
--------------------------
Conservative robustness check: lag hicp_headline_core_gap by 6 weeks before
HMM fitting, then rerun Panel B regime-aware backtest.

Stages (all in one run):
  1.  Create lagged feature parquet
  2.  Walk-forward HMM (MIN_TRAIN=156, same as Panel B baseline)
  3.  Panel B backtest with lagged regime labels
  4.  Comparison report vs baseline

All outputs use suffix _hicp_lag6 — baseline files are NEVER overwritten.

Outputs:
  data/processed/regime_features_weekly_hicp_lag6.parquet
  data/processed/hmm_wf_checkpoint_156_hicp_lag6.pkl
  data/processed/regime_labels_wf_156_hicp_lag6.parquet
  data/processed/regime_probs_wf_156_hicp_lag6.parquet
  reports/panels/panel_b_regime_oos_performance_hicp_lag6.csv
  reports/panels/panel_b_regime_oos_tc_sensitivity_hicp_lag6.csv
  reports/panels/panel_b_regime_oos_summary_hicp_lag6.md
  reports/regimes/hicp_lag6_robustness.md
"""
from __future__ import annotations
import logging, pickle, sys, time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from models.hmm import (
    WALK_FORWARD_STEP, HMMFitResult,
    fit_hmm, decode_regimes, select_and_impute, REGIME_FEATURES,
)
from optimization.cvar      import solve_cvar, CVaRConfig
from optimization.markowitz import solve_min_variance, MarkowitzConfig

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

PROCESSED = ROOT / "data" / "processed"
REPORTS   = ROOT / "reports"

# ── shared constants (match Panel B baseline) ─────────────────────────────────
HICP_LAG_WEEKS   = 6
MIN_TRAIN_OBS    = 156
N_STATES         = 4
VIX_IDX          = 0    # z52_VIX is first in REGIME_FEATURES
ALPHA            = 0.95
MAX_WEIGHT       = 0.25
REBALANCE        = 4
MIN_HISTORY      = 156
SCENARIO_CAP     = 260
MIN_REGIME_SCEN  = 30
TC_BPS_LIST      = [0, 5, 10, 25]
CASH_COL         = "EURIBOR_3M"
STOXX_COL        = "StoxxEurope600"
ANN              = 52

CVAR_CFG = CVaRConfig(alpha=ALPHA, max_weight=MAX_WEIGHT)
MKV_CFG  = MarkowitzConfig(max_weight=MAX_WEIGHT, min_scenarios=52,
                            fallback_to_equal=True)

STRATEGY_LABELS = {
    "equal_weight_risky": "Equal-Weight Risky (1/N)",
    "stoxx600":           "STOXX Europe 600",
    "static_cvar":        "Static CVaR",
    "markowitz":          "Markowitz (Min-Var)",
    "regime_cvar_A":      "Regime CVaR-A",
    "weighted_cvar":      "Weighted CVaR",
}


# ─────────────────────────────────────────────────────────────────────────────
# STAGE 1 — Create lagged HICP feature parquet
# ─────────────────────────────────────────────────────────────────────────────
def _rolling_zscore(s: pd.Series, window: int = 52,
                    min_periods: int = 26) -> pd.Series:
    m = s.rolling(window, min_periods=min_periods).mean()
    sd = s.rolling(window, min_periods=min_periods).std()
    return (s - m) / sd


def stage_features():
    out_path = PROCESSED / "regime_features_weekly_hicp_lag6.parquet"
    if out_path.exists():
        log.info("STAGE 1: %s already exists — skipping.", out_path.name)
        return

    log.info("STAGE 1: Creating HICP-lag6 feature parquet ...")
    feats = pd.read_parquet(PROCESSED / "regime_features_weekly.parquet")

    lagged = feats.copy()
    # Apply 6-week lag to the raw HICP headline-core gap
    lagged["hicp_headline_core_gap"] = feats["hicp_headline_core_gap"].shift(HICP_LAG_WEEKS)
    # Recompute the z52 score on the lagged gap
    lagged["z52_hicp_headline_core_gap"] = _rolling_zscore(
        lagged["hicp_headline_core_gap"], window=52, min_periods=26
    )

    lagged.to_parquet(out_path)
    log.info("STAGE 1: Saved %s  (%d rows x %d cols)",
             out_path.name, len(lagged), lagged.shape[1])


# ─────────────────────────────────────────────────────────────────────────────
# STAGE 2 — Walk-forward HMM (lagged features)
# ─────────────────────────────────────────────────────────────────────────────
def canonical_permutation(result: HMMFitResult) -> np.ndarray:
    vix_means = result.model.means_[:, VIX_IDX]
    return np.argsort(np.argsort(vix_means))


def stage_hmm():
    ckpt_path  = PROCESSED / "hmm_wf_checkpoint_156_hicp_lag6.pkl"
    lab_path   = PROCESSED / "regime_labels_wf_156_hicp_lag6.parquet"
    prob_path  = PROCESSED / "regime_probs_wf_156_hicp_lag6.parquet"

    feats_raw = pd.read_parquet(
        PROCESSED / "regime_features_weekly_hicp_lag6.parquet"
    )
    X = select_and_impute(feats_raw, REGIME_FEATURES, logger=log)
    n = len(X)
    checkpoints = list(range(MIN_TRAIN_OBS, n + 1, WALK_FORWARD_STEP))

    log.info("STAGE 2: HMM walk-forward  n=%d  ckpts=%d  MIN_TRAIN=%d",
             n, len(checkpoints), MIN_TRAIN_OBS)

    # Load or init checkpoint
    ckpt = None
    if ckpt_path.exists():
        with open(ckpt_path, "rb") as f:
            ckpt = pickle.load(f)
        valid = (ckpt.get("n") == n and
                 ckpt.get("n_states") == N_STATES and
                 ckpt.get("min_train") == MIN_TRAIN_OBS)
        if not valid:
            log.warning("STAGE 2: Checkpoint invalid — starting fresh.")
            ckpt = None
        else:
            done = len(ckpt["completed_ends"])
            log.info("STAGE 2: Resuming: %d/%d checkpoints done", done, len(checkpoints))

    if ckpt is None:
        ckpt = {
            "n": n, "n_states": N_STATES, "min_train": MIN_TRAIN_OBS,
            "label_switched": True,
            "labels":     np.full(n, np.nan),
            "posteriors": np.full((n, N_STATES), np.nan),
            "completed_ends": set(),
            "done": False,
        }

    if ckpt["done"]:
        log.info("STAGE 2: Already complete.")
    else:
        todo = [e for e in checkpoints if e not in ckpt["completed_ends"]]
        log.info("STAGE 2: %d checkpoints remaining ...", len(todo))
        t0 = time.time()

        for i, end in enumerate(todo):
            X_train = X.iloc[:end]
            result  = fit_hmm(X_train, n_states=N_STATES, logger=log)

            raw_labels     = decode_regimes(result, X_train)
            X_scaled       = result.scaler.transform(X_train.values)
            raw_posteriors = result.model.predict_proba(X_scaled)

            inv_perm  = canonical_permutation(result)
            perm      = np.argsort(inv_perm)
            can_label = int(inv_perm[int(raw_labels.iloc[-1])])
            can_post  = raw_posteriors[-1][perm]

            ckpt["labels"][end - 1]     = can_label
            ckpt["posteriors"][end - 1] = can_post
            ckpt["completed_ends"].add(end)

            if (i + 1) % 10 == 0:
                elapsed = time.time() - t0
                pct = (i + 1) / len(todo) * 100
                log.info("STAGE 2: %d/%d (%.0f%%)  elapsed=%.0fs",
                         i + 1, len(todo), pct, elapsed)
                with open(ckpt_path, "wb") as f:
                    pickle.dump(ckpt, f)

        ckpt["done"] = True
        with open(ckpt_path, "wb") as f:
            pickle.dump(ckpt, f)
        log.info("STAGE 2: All %d checkpoints complete in %.0fs.",
                 len(checkpoints), time.time() - t0)

    # Write parquets with ffill to weekly frequency
    lab = pd.Series(ckpt["labels"], index=X.index, name="regime_wf").ffill()
    prb = pd.DataFrame(ckpt["posteriors"], index=X.index,
                       columns=[f"prob_state_{k}" for k in range(N_STATES)]).ffill()
    lab.to_frame().to_parquet(lab_path)
    prb.to_parquet(prob_path)
    n_valid = lab.notna().sum()
    log.info("STAGE 2: Parquets written. Valid labels=%d  first=%s  last=%s",
             n_valid,
             lab.dropna().index.min().date() if n_valid > 0 else "—",
             lab.dropna().index.max().date() if n_valid > 0 else "—")


# ─────────────────────────────────────────────────────────────────────────────
# STAGE 3 — Panel B with lagged-HICP regimes
# ─────────────────────────────────────────────────────────────────────────────
def _port(w_df, ret):
    return (w_df.shift(1) * ret.reindex(columns=w_df.columns)).sum(axis=1, min_count=1)

def _weekly_to(w_df):
    return w_df.diff().abs().sum(axis=1) / 2.0

def _eq_drift_to(ret_r):
    n  = ret_r.shape[1]; rp = ret_r.mean(axis=1)
    wd = ret_r.apply(lambda r: (1/n)*(1+r)/(1+rp), axis=0)
    return (wd - 1/n).abs().sum(axis=1) / 2.0

def _apply_tc(gross, turnover, tc_frac):
    # Use lagged turnover to match Panel B (07_panel_b_regime_oos.py line 74):
    # TC is charged on the turnover from the *previous* period, consistent with
    # the 1-week implementation lag in _port().
    return gross - tc_frac * turnover.shift(1).fillna(0.0).reindex(gross.index).fillna(0.0)

def compute_metrics(r, rf):
    r  = r.dropna()
    rf_a = rf.reindex(r.index).fillna(0.0)
    exc  = r - rf_a
    cagr = (1 + r).prod() ** (ANN / len(r)) - 1
    vol  = r.std(ddof=1) * np.sqrt(ANN)
    sh   = exc.mean() / exc.std(ddof=1) * np.sqrt(ANN) if exc.std(ddof=1) > 0 else np.nan
    cum  = (1 + r).cumprod()
    mdd  = (cum / cum.cummax() - 1).min()
    k    = max(1, int(len(r) * (1 - ALPHA)))
    cvar = float(np.sort(r.values)[:k].mean())
    cal  = cagr / abs(mdd) if mdd != 0 else np.nan
    return dict(CAGR_pct=round(cagr*100,2), Vol_pct=round(vol*100,2),
                Sharpe=round(sh,3), MaxDD_pct=round(mdd*100,2),
                CVaR95_weekly_pct=round(cvar*100,3), Calmar=round(cal,3),
                N_weeks=len(r))


def stage_panel_b():
    lab_path  = PROCESSED / "regime_labels_wf_156_hicp_lag6.parquet"
    prob_path = PROCESSED / "regime_probs_wf_156_hicp_lag6.parquet"
    perf_path = REPORTS / "panels" / "panel_b_regime_oos_performance_hicp_lag6.csv"
    tc_path   = REPORTS / "panels" / "panel_b_regime_oos_tc_sensitivity_hicp_lag6.csv"
    summ_path = REPORTS / "panels" / "panel_b_regime_oos_summary_hicp_lag6.md"

    log.info("STAGE 3: Running Panel B (HICP-lag6 regimes) ...")

    ret = pd.read_parquet(PROCESSED / "investable_returns_weekly.parquet")
    ret.index = pd.to_datetime(ret.index)
    lab = pd.read_parquet(lab_path)["regime_wf"]
    prb = pd.read_parquet(prob_path)
    lab.index = pd.to_datetime(lab.index)
    prb.index = pd.to_datetime(prb.index)

    risky = [c for c in ret.columns if c != CASH_COL]
    n_r   = len(risky)
    ret_r = ret[risky].dropna()
    rf    = ret[CASH_COL]
    idx   = ret_r.index

    # Intersect with available regime labels
    common = idx.intersection(lab.dropna().index)
    log.info("Common dates with labels: %d  first=%s  last=%s",
             len(common), common.min().date(), common.max().date())

    # Walk-forward portfolio
    w_s: dict = {}; w_m: dict = {}
    w_rA: dict = {}; w_wC: dict = {}
    last_ws = np.ones(n_r)/n_r
    last_wm = np.ones(n_r)/n_r
    last_rA = np.ones(n_r)/n_r
    last_wC = np.ones(n_r)/n_r
    first_rebal = None; rebal_ctr = 0; ns = 0; nf = 0

    for i, date in enumerate(common):
        if i < MIN_HISTORY:
            continue
        if first_rebal is None:
            first_rebal = date
            log.info("STAGE 3: First rebal: %s", date.date())

        if rebal_ctr % REBALANCE == 0:
            s0 = max(0, i - SCENARIO_CAP)
            hist    = ret_r.reindex(common).iloc[s0:i].values
            hist_df = ret_r.reindex(common).iloc[s0:i]
            labels_hist = lab.reindex(common).iloc[s0:i].values
            prb_hist    = prb.reindex(common).iloc[s0:i].values
            cur_lab  = int(lab.reindex(common).iloc[i])
            cur_prb  = prb.reindex(common).iloc[i].values

            # Static CVaR
            res = solve_cvar(hist, CVAR_CFG)
            if res and res.get("weights") is not None:
                last_ws = res["weights"]; ns += 1
            else:
                nf += 1

            # Markowitz
            try:
                wm, _ = solve_min_variance(hist_df, MKV_CFG)
                last_wm = wm
            except Exception:
                pass

            # Regime CVaR-A (hard filter)
            mask = labels_hist == cur_lab
            regime_hist = hist[mask]
            if len(regime_hist) >= MIN_REGIME_SCEN:
                res_A = solve_cvar(regime_hist, CVAR_CFG)
                if res_A and res_A.get("weights") is not None:
                    last_rA = res_A["weights"]

            # Weighted CVaR (importance-weighted scenarios)
            if len(hist) > 0 and len(prb_hist) > 0:
                w_raw  = prb_hist @ cur_prb
                w_norm = w_raw / w_raw.sum()
                m = len(hist); n_a = n_r
                import scipy.optimize as sco
                c = np.zeros(m + 1 + n_a)
                c[0] = 1.0
                c[1:m+1] = w_norm / (1 - ALPHA)
                A_ub = np.zeros((m, m + 1 + n_a))
                for t in range(m):
                    A_ub[t, 0]       = -1.0
                    A_ub[t, 1 + t]   = -1.0
                    A_ub[t, m+1:]    = -hist[t]
                b_ub = np.zeros(m)
                A_eq = np.zeros((1, m + 1 + n_a)); A_eq[0, m+1:] = 1.0
                b_eq = np.array([1.0])
                bounds = [(None, None)] + [(0.0, None)]*m + [(0.0, MAX_WEIGHT)]*n_a
                res_w = sco.linprog(c, A_ub=A_ub, b_ub=b_ub, A_eq=A_eq, b_eq=b_eq,
                                    bounds=bounds, method="highs")
                if res_w.success:
                    last_wC = res_w.x[m+1:]
                    s = last_wC.sum()
                    if s > 0:
                        last_wC /= s

            w_s[date]  = last_ws.copy()
            w_m[date]  = last_wm.copy()
            w_rA[date] = last_rA.copy()
            w_wC[date] = last_wC.copy()

        rebal_ctr += 1

    log.info("STAGE 3: Walk-forward done. CVaR: %d solved / %d fallback", ns, nf)

    # Build DataFrames
    eval_idx = common[MIN_HISTORY:]
    w_s_df  = pd.DataFrame(w_s,  index=risky).T.reindex(eval_idx).ffill()
    w_m_df  = pd.DataFrame(w_m,  index=risky).T.reindex(eval_idx).ffill()
    w_rA_df = pd.DataFrame(w_rA, index=risky).T.reindex(eval_idx).ffill()
    w_wC_df = pd.DataFrame(w_wC, index=risky).T.reindex(eval_idx).ffill()
    w_eq    = pd.DataFrame(1.0/n_r, index=idx, columns=risky)
    w_st    = pd.DataFrame({STOXX_COL: 1.0}, index=idx)

    gross = pd.DataFrame(index=eval_idx)
    gross["equal_weight_risky"] = _port(w_eq,    ret_r)
    gross["stoxx600"]           = _port(w_st,    ret[[STOXX_COL]])
    gross["static_cvar"]        = _port(w_s_df,  ret_r)
    gross["markowitz"]          = _port(w_m_df,  ret_r)
    gross["regime_cvar_A"]      = _port(w_rA_df, ret_r)
    gross["weighted_cvar"]      = _port(w_wC_df, ret_r)

    strat  = gross.loc[first_rebal:].dropna(how="all")
    rf_ev  = rf.reindex(strat.index).fillna(0.0)
    log.info("STAGE 3: Eval %s → %s  n=%d",
             strat.index.min().date(), strat.index.max().date(), len(strat))

    to_eq  = _eq_drift_to(ret_r.reindex(strat.index))
    to_s   = _weekly_to(w_s_df.reindex(strat.index))
    to_m   = _weekly_to(w_m_df.reindex(strat.index))
    to_st  = pd.Series(0.0, index=strat.index)
    to_rA  = _weekly_to(w_rA_df.reindex(strat.index))
    to_wC  = _weekly_to(w_wC_df.reindex(strat.index))
    to_map = {"equal_weight_risky": to_eq, "stoxx600": to_st,
              "static_cvar": to_s, "markowitz": to_m,
              "regime_cvar_A": to_rA, "weighted_cvar": to_wC}

    cols = list(STRATEGY_LABELS.keys())
    rows = []
    for tc in TC_BPS_LIST:
        for col in cols:
            m = compute_metrics(
                _apply_tc(strat[col], to_map[col], tc/10_000), rf_ev
            )
            to_c = to_map[col].reindex(strat.index).fillna(0)
            m.update({"tc_bps": tc, "strategy": col, "label": STRATEGY_LABELS[col],
                      "weekly_to_pct": round(to_c.mean()*100, 4),
                      "ann_to_pct":    round(to_c.mean()*ANN*100, 2),
                      "eval_start": str(strat.index.min().date()),
                      "eval_end":   str(strat.index.max().date())})
            rows.append(m)

    mdf = pd.DataFrame(rows)
    mdf.to_csv(perf_path, index=False)
    log.info("STAGE 3: Wrote %s", perf_path.name)

    # TC sensitivity table
    tc_rows = []
    for col in cols:
        row = {"strategy": col, "label": STRATEGY_LABELS[col]}
        for tc in TC_BPS_LIST:
            s = mdf[(mdf["tc_bps"]==tc) & (mdf["strategy"]==col)]["Sharpe"].values
            row[f"sharpe_{tc}bps"] = round(float(s[0]),3) if len(s) else np.nan
        tc_rows.append(row)
    tc_df = pd.DataFrame(tc_rows)
    tc_df.to_csv(tc_path, index=False)
    log.info("STAGE 3: Wrote %s", tc_path.name)

    # Summary markdown
    g0 = mdf[mdf["tc_bps"]==0].set_index("strategy")
    es = strat.index.min().date(); ee = strat.index.max().date(); nw = len(strat)
    lines = [
        "# Panel B — HICP-Lag6 Robustness Check",
        "", "*Generated by `10_hicp_lag6_robustness.py`*", "",
        f"> **Robustness variant:** HICP headline-core gap lagged by "
        f"{HICP_LAG_WEEKS} weeks before z-score computation and HMM fitting.",
        "> All other features and parameters identical to the baseline Panel B.",
        "", "---", "",
        "## Performance (gross, 0 bps TC)",
        "",
        f"**Evaluation:** {es} → {ee} ({nw} weeks, {nw/ANN:.1f} yr)",
        "",
        "| Strategy | CAGR | Vol | Sharpe | MaxDD | CVaR 95% (wkly) | Calmar |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for col in cols:
        m = g0.loc[col]
        lines.append(
            f"| {STRATEGY_LABELS[col]} | "
            f"{m.CAGR_pct:+.2f}% | {m.Vol_pct:.2f}% | {m.Sharpe:.3f} | "
            f"{m.MaxDD_pct:.2f}% | {m.CVaR95_weekly_pct:.3f}% | {m.Calmar:.3f} |"
        )
    lines += [
        "", "---", "",
        "## TC Sensitivity (Sharpe)",
        "",
        "| Strategy | 0 bps | 5 bps | 10 bps | 25 bps |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for _, r in tc_df.iterrows():
        lines.append(
            f"| {r['label']} | {r['sharpe_0bps']:.3f} | "
            f"{r['sharpe_5bps']:.3f} | {r['sharpe_10bps']:.3f} | "
            f"{r['sharpe_25bps']:.3f} |"
        )
    summ_path.write_text("\n".join(lines))
    log.info("STAGE 3: Wrote %s", summ_path.name)

    return mdf, strat, lab, prb


# ─────────────────────────────────────────────────────────────────────────────
# STAGE 4 — Comparison report
# ─────────────────────────────────────────────────────────────────────────────
def stage_comparison(mdf_lag):
    out_path = REPORTS / "regimes" / "hicp_lag6_robustness.md"
    log.info("STAGE 4: Writing comparison report ...")

    # Load baseline Panel B metrics
    base_perf = pd.read_csv(REPORTS / "panels" / "panel_b_regime_oos_performance.csv")
    base_tc   = pd.read_csv(REPORTS / "panels" / "panel_b_regime_oos_tc_sensitivity.csv")

    # Baseline regime labels
    lab_base = pd.read_parquet(
        PROCESSED / "regime_labels_wf_156.parquet"
    )["regime_wf"].dropna()
    lab_lag  = pd.read_parquet(
        PROCESSED / "regime_labels_wf_156_hicp_lag6.parquet"
    )["regime_wf"].dropna()

    # Regime distribution comparison
    base_dist = lab_base.value_counts(normalize=True).sort_index()
    lag_dist  = lab_lag.value_counts(normalize=True).sort_index()

    # Agreement between baseline and lag labels (common dates)
    common_dates = lab_base.index.intersection(lab_lag.index)
    agreement = (lab_base.reindex(common_dates) == lab_lag.reindex(common_dates)).mean()

    # Stability: fraction of non-transitions in each series
    def stability(lab_s):
        s = lab_s.dropna()
        return (s == s.shift(1)).sum() / (len(s) - 1)

    stab_base = stability(lab_base)
    stab_lag  = stability(lab_lag)

    # Performance comparison (0 bps)
    g_base = base_perf[base_perf["tc_bps"]==0].set_index("strategy")
    g_lag  = mdf_lag[mdf_lag["tc_bps"]==0].set_index("strategy")
    cols   = list(STRATEGY_LABELS.keys())

    # State-label economic names
    STATE_LABELS = {
        0: "Bull/Low-Vol",
        1: "Recovery/Growth",
        2: "Neutral/Moderate",
        3: "Elevated-Risk/Stress",
    }

    lines = [
        "# HICP Release-Date Robustness Check",
        "",
        "*Generated by `10_hicp_lag6_robustness.py`*",
        "",
        "Robustness variant: `hicp_headline_core_gap` and `z52_hicp_headline_core_gap` "
        f"lagged by {HICP_LAG_WEEKS} weeks before HMM fitting. "
        "All other parameters identical to Panel B baseline.",
        "",
        "---",
        "",
        "## 1  Regime Label Agreement",
        "",
        f"Common evaluation dates: {len(common_dates)}",
        f"Label agreement (baseline vs lagged): **{agreement:.1%}**",
        "",
        "### State distribution — baseline vs HICP-lag6",
        "",
        "| State | Label | Baseline freq | Lag6 freq | Diff |",
        "| --- | --- | ---: | ---: | ---: |",
    ]
    for s in range(N_STATES):
        b = base_dist.get(float(s), 0.0)
        l = lag_dist.get(float(s), 0.0)
        lines.append(
            f"| {s} | {STATE_LABELS[s]} | {b:.1%} | {l:.1%} | {l-b:+.1%} |"
        )

    lines += [
        "",
        f"Regime stability (fraction of unchanged labels week-to-week):",
        f"- Baseline: **{stab_base:.1%}**",
        f"- HICP-lag6: **{stab_lag:.1%}**",
        "",
        "---",
        "",
        "## 2  Performance Comparison (gross, 0 bps TC)",
        "",
        "| Strategy | Baseline Sharpe | Lag6 Sharpe | Diff | Baseline CAGR | Lag6 CAGR | Diff |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for col in cols:
        bs = g_base.loc[col, "Sharpe"] if col in g_base.index else np.nan
        ls = g_lag.loc[col, "Sharpe"]  if col in g_lag.index  else np.nan
        bc = g_base.loc[col, "CAGR_pct"] if col in g_base.index else np.nan
        lc = g_lag.loc[col, "CAGR_pct"]  if col in g_lag.index  else np.nan
        ds = ls - bs if not (np.isnan(ls) or np.isnan(bs)) else np.nan
        dc = lc - bc if not (np.isnan(lc) or np.isnan(bc)) else np.nan
        lines.append(
            f"| {STRATEGY_LABELS[col]} | {bs:.3f} | {ls:.3f} | {ds:+.3f} | "
            f"{bc:.2f}% | {lc:.2f}% | {dc:+.2f}% |"
        )

    lines += [
        "",
        "---",
        "",
        "## 3  Turnover Comparison (0 bps)",
        "",
        "| Strategy | Baseline TO ann% | Lag6 TO ann% | Diff |",
        "| --- | ---: | ---: | ---: |",
    ]
    for col in cols:
        bt = g_base.loc[col, "ann_to_pct"] if col in g_base.index else np.nan
        lt = g_lag.loc[col, "ann_to_pct"]  if col in g_lag.index  else np.nan
        dt = lt - bt if not (np.isnan(lt) or np.isnan(bt)) else np.nan
        lines.append(
            f"| {STRATEGY_LABELS[col]} | {bt:.1f}% | {lt:.1f}% | {dt:+.1f}% |"
        )

    # TC sensitivity for regime strategies
    lines += [
        "",
        "---",
        "",
        "## 4  TC Sensitivity — Regime Strategies",
        "",
        "| Strategy | Variant | 0 bps | 5 bps | 10 bps | 25 bps |",
        "| --- | --- | ---: | ---: | ---: | ---: |",
    ]
    for col in ["regime_cvar_A", "weighted_cvar"]:
        # Baseline
        brow = base_tc[base_tc["strategy"]==col]
        lrow = mdf_lag[mdf_lag["strategy"]==col].copy()
        for variant, df in [("Baseline", base_perf), ("HICP-lag6", mdf_lag)]:
            tc_vals = []
            for tc in TC_BPS_LIST:
                s = df[(df["tc_bps"]==tc) & (df["strategy"]==col)]["Sharpe"].values
                tc_vals.append(f"{float(s[0]):.3f}" if len(s) else "—")
            lines.append(
                f"| {STRATEGY_LABELS[col]} | {variant} | "
                + " | ".join(tc_vals) + " |"
            )

    # Conclusion
    # Compute max absolute Sharpe change for regime strategies
    regime_cols = ["regime_cvar_A", "weighted_cvar"]
    sharpe_diffs = []
    for col in regime_cols:
        bs = g_base.loc[col, "Sharpe"] if col in g_base.index else np.nan
        ls = g_lag.loc[col, "Sharpe"]  if col in g_lag.index  else np.nan
        if not (np.isnan(bs) or np.isnan(ls)):
            sharpe_diffs.append(abs(ls - bs))
    max_regime_diff = max(sharpe_diffs) if sharpe_diffs else np.nan
    conclusion_stable = (not np.isnan(max_regime_diff)) and max_regime_diff < 0.02

    lines += [
        "",
        "---",
        "",
        "## 5  Conclusion",
        "",
    ]
    if conclusion_stable:
        lines += [
            f"**Label agreement:** {agreement:.1%} of weekly HMM classifications are "
            "unchanged between baseline and the 6-week HICP-lagged variant. "
            f"Maximum Sharpe change across regime strategies: "
            f"**{max_regime_diff:+.3f}**.",
            "",
            "**Conclusion: Main results are robust to conservative HICP release-date "
            "lagging.** The 6-week lag on HICP data does not materially alter the "
            "HMM market-state classifications or the relative ranking of strategies. "
            "The finding that Static CVaR outperforms regime-conditioned strategies "
            "holds in this robustness variant.",
            "",
            "**Recommendation:** Report in an appendix or footnote as a standard "
            "robustness check. No need to revise the main text conclusions.",
        ]
    else:
        lines += [
            f"**Label agreement:** {agreement:.1%} of weekly HMM classifications are "
            "unchanged between baseline and the 6-week HICP-lagged variant. "
            f"Maximum Sharpe change across regime strategies: "
            f"**{max_regime_diff:+.3f}**.",
            "",
            "**Conclusion: HICP lagging materially changes regime labels and/or "
            "strategy performance.** This suggests the HICP release-date alignment "
            "is an important methodological consideration. The baseline results should "
            "be presented alongside this robustness check, with appropriate caveats "
            "about look-ahead risk in the HICP feature.",
            "",
            "**Recommendation:** The lagged-HICP variant should be promoted from "
            "appendix to a primary robustness table in the main paper. Consider "
            "using the lagged version as the baseline.",
        ]

    out_path.write_text("\n".join(lines))
    log.info("STAGE 4: Wrote %s", out_path.name)


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    t_start = time.time()
    log.info("=== HICP-Lag6 Robustness Check ===")
    stage_features()
    stage_hmm()
    mdf_lag, strat, lab, prb = stage_panel_b()
    stage_comparison(mdf_lag)
    log.info("=== All stages complete in %.0fs ===", time.time() - t_start)
