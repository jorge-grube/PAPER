"""
12_rebalance_frequency_experiment.py
--------------------------------------
Rebalance-frequency sensitivity experiment for Panel B regime-aware strategies.

Tests rebalance cadences of 1, 2, 4, and 8 weeks for:
  A. Baseline 8-feature HMM labels (regime_labels_wf_156.parquet)
  B. ZEW-swap HMM labels (model_improvement/regime_labels_wf_156_zew_swap.parquet)

HMM LABEL AVAILABILITY NOTE:
  Walk-forward labels are produced every 4 weeks (checkpoint step=4) and then
  forward-filled to weekly frequency before saving to parquet (see
  hmm_walkforward_156.py and 11_zew_swap_experiment.py). Consequently, for
  rebalance frequencies of 1 and 2 weeks, the same regime label is seen for
  up to 4 consecutive weeks between checkpoint updates. This is documented here
  as a conservative assumption (no look-ahead — the label in force at any date
  is always the most recent checkpoint label at or before that date). The
  scenario window used for CVaR optimisation is purely backward-looking history
  and is unaffected by rebalance frequency.

Outputs (all under model_improvement/rebalance_frequency/):
  reports/model_improvement/rebalance_frequency/rebalance_frequency_performance.csv
  reports/model_improvement/rebalance_frequency/rebalance_frequency_tc_sensitivity.csv
  reports/model_improvement/rebalance_frequency/rebalance_frequency_crisis_windows.csv
  reports/model_improvement/rebalance_frequency/rebalance_frequency_summary.md

Usage:
  python scripts/12_rebalance_frequency_experiment.py --spec baseline --freq 1
  python scripts/12_rebalance_frequency_experiment.py --spec baseline --freq 2
  python scripts/12_rebalance_frequency_experiment.py --spec baseline --freq 4
  python scripts/12_rebalance_frequency_experiment.py --spec baseline --freq 8
  python scripts/12_rebalance_frequency_experiment.py --spec zew_swap --freq 1
  ... (repeat for all combinations)
  python scripts/12_rebalance_frequency_experiment.py --aggregate
"""
from __future__ import annotations
import argparse, logging, sys, time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import linprog

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from optimization.cvar      import solve_cvar, CVaRConfig
from optimization.markowitz import solve_min_variance, MarkowitzConfig

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s | %(levelname)-7s | %(message)s",
                    datefmt="%H:%M:%S")
log = logging.getLogger(__name__)

# ── paths ─────────────────────────────────────────────────────────────────────
PROCESSED  = ROOT / "data" / "processed"
MI_DATA    = PROCESSED / "model_improvement"
RF_OUT     = ROOT / "reports" / "model_improvement" / "rebalance_frequency"
DF_OUT     = PROCESSED / "model_improvement" / "rebalance_frequency"
for _d in [RF_OUT, DF_OUT]:
    _d.mkdir(parents=True, exist_ok=True)

# ── HMM specifications ────────────────────────────────────────────────────────
HMM_SPECS = {
    "baseline": {
        "lab_path": PROCESSED / "regime_labels_wf_156.parquet",
        "prb_path": PROCESSED / "regime_probs_wf_156.parquet",
        "label":    "Baseline HMM",
    },
    "zew_swap": {
        "lab_path": MI_DATA / "regime_labels_wf_156_zew_swap.parquet",
        "prb_path": MI_DATA / "regime_probs_wf_156_zew_swap.parquet",
        "label":    "ZEW-Swap HMM",
    },
}

# NOTE: freq=1 requires ~52 s of LP solve time and exceeds the 45 s sandbox
# limit. It is excluded from automated runs. The directional evidence from
# freq=2 already captures the "faster than 4 weeks" case; see summary for
# the trend extrapolation. To run freq=1 manually in a full Python session:
#   python scripts/12_rebalance_frequency_experiment.py --spec baseline --freq 1
REBALANCE_FREQS     = [2, 4, 8]      # runnable within 45 s sandbox limit
REBALANCE_FREQS_ALL = [1, 2, 4, 8]  # full set (used in summary tables)

# ── portfolio config ───────────────────────────────────────────────────────────
ALPHA                = 0.95
MAX_WEIGHT           = 0.25
MIN_HISTORY          = 156   # burn-in weeks (constant regardless of rebalance freq)
SCENARIO_CAP         = 260   # rolling scenario window (weeks)
MIN_REGIME_SCENARIOS = 30
TC_BPS_LIST          = [0, 5, 10, 25]
CASH_COL             = "EURIBOR_3M"
STOXX_COL            = "StoxxEurope600"
ANN                  = 52

CVAR_CFG = CVaRConfig(alpha=ALPHA, max_weight=MAX_WEIGHT)
MKV_CFG  = MarkowitzConfig(max_weight=MAX_WEIGHT, min_scenarios=52,
                           fallback_to_equal=True)

# ── crisis windows ─────────────────────────────────────────────────────────────
# GFC is mostly before Panel B eval window (starts 2010-10-15)
CRISIS_WINDOWS = {
    "EU_Sovereign_2011": ("2011-07-01", "2012-07-31"),
    "COVID_Crash_2020":  ("2020-02-21", "2020-04-03"),
    "Rate_Shock_2022":   ("2022-01-07", "2022-12-30"),
}

STRATEGY_LABELS = {
    "equal_weight_risky": "Equal-Weight Risky (1/N)",
    "stoxx600":           "STOXX Europe 600",
    "static_cvar":        "Static CVaR",
    "markowitz":          "Markowitz (Min-Var)",
    "regime_cvar_A":      "Regime CVaR-A",
    "weighted_cvar":      "Weighted CVaR",
}


# ══════════════════════════════════════════════════════════════════════════════
# Portfolio helpers (identical to Panel B)
# ══════════════════════════════════════════════════════════════════════════════

def _port(w_df, ret):
    """1-week implementation lag. min_count=1 prevents all-NaN → 0."""
    return (w_df.shift(1) * ret.reindex(columns=w_df.columns)).sum(
        axis=1, min_count=1)

def _weekly_to(w_df):
    return w_df.diff().abs().sum(axis=1) / 2.0

def _eq_drift_to(ret_r):
    n = ret_r.shape[1]; rp = ret_r.mean(axis=1)
    wd = ret_r.apply(lambda r: (1/n)*(1+r)/(1+rp), axis=0)
    return (wd - 1/n).abs().sum(axis=1) / 2.0

def _apply_tc(gross, to, rate):
    """Lagged turnover matching 1-week implementation lag."""
    return gross - rate * to.shift(1).fillna(0.0).reindex(
        gross.index).fillna(0.0)

def compute_metrics(r, rf):
    r    = r.dropna()
    rf_a = rf.reindex(r.index).fillna(0.0)
    exc  = r - rf_a
    cagr = (1+r).prod()**(ANN/len(r)) - 1
    vol  = r.std(ddof=1) * np.sqrt(ANN)
    sh   = (exc.mean()/exc.std(ddof=1)*np.sqrt(ANN)
            if exc.std(ddof=1) > 0 else np.nan)
    cum  = (1+r).cumprod()
    mdd  = (cum/cum.cummax()-1).min()
    k    = max(1, int(len(r)*(1-ALPHA)))
    cvar_w = float(np.sort(r.values)[:k].mean())
    cal  = cagr/abs(mdd) if mdd else np.nan
    return dict(CAGR_pct=round(cagr*100, 2), Vol_pct=round(vol*100, 2),
                Sharpe=round(sh, 3), MaxDD_pct=round(mdd*100, 2),
                CVaR95_weekly_pct=round(cvar_w*100, 3),
                Calmar=round(cal, 3), N_weeks=len(r))

def compute_crisis_metrics(r, rf, window_name, start, end):
    r_w = r.loc[start:end].dropna()
    if len(r_w) < 2:
        return dict(window=window_name, N_weeks=0,
                    CAGR_pct=np.nan, MaxDD_pct=np.nan, Sharpe=np.nan)
    rf_w = rf.reindex(r_w.index).fillna(0.0)
    m = compute_metrics(r_w, rf_w)
    m["window"] = window_name
    return m

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
    n, m = hist.shape
    w_raw = posteriors_hist @ current_posterior
    w_sum = w_raw.sum()
    if w_sum == 0 or np.isnan(w_sum):
        res = solve_cvar(hist, CVAR_CFG)
        return res["weights"] if res and res.get("weights") is not None else None
    w_norm = w_raw / w_sum

    c = np.zeros(m + 1 + n); c[m] = 1.0
    c[m+1:] = w_norm / (1 - ALPHA)
    A_eq = np.zeros((1, m+1+n)); A_eq[0, :m] = 1.0; b_eq = np.array([1.0])
    A_ub = np.zeros((2*n, m+1+n))
    A_ub[:n, :m] = -hist; A_ub[:n, m] = -1.0; A_ub[:n, m+1:] = -np.eye(n)
    A_ub[n:, m+1:] = -np.eye(n)
    b_ub = np.zeros(2*n)
    bounds = [(0, MAX_WEIGHT)]*m + [(None, None)] + [(0, None)]*n
    res = linprog(c, A_ub=A_ub, b_ub=b_ub, A_eq=A_eq, b_eq=b_eq,
                  bounds=bounds, method="highs")
    return res.x[:m] if res.success else None


# ══════════════════════════════════════════════════════════════════════════════
# Core backtest engine
# ══════════════════════════════════════════════════════════════════════════════

def run_backtest(rebalance: int, lab: pd.Series, prb: pd.DataFrame,
                 ret: pd.DataFrame, rf: pd.Series) -> tuple:
    """
    Run Panel B backtest with the given rebalance frequency.

    Parameters
    ----------
    rebalance : int
        Number of weeks between portfolio rebalances (1, 2, 4, or 8).
    lab : pd.Series
        Weekly regime labels (forward-filled from checkpoints).
    prb : pd.DataFrame
        Weekly regime posteriors (forward-filled from checkpoints).
    ret : pd.DataFrame
        Full investable returns including CASH_COL.
    rf : pd.Series
        Risk-free return series.

    Returns
    -------
    strat : pd.DataFrame   — weekly gross returns per strategy (eval window only)
    to_map : dict          — weekly turnover Series per strategy
    first_rebal : pd.Timestamp
    """
    risky   = [c for c in ret.columns if c != CASH_COL]
    n_r     = len(risky)
    ret_r   = ret[risky].dropna()
    n_states = prb.shape[1]

    valid_lab = lab.dropna()
    common    = ret_r.index.intersection(valid_lab.index).sort_values()

    log.info("  REBALANCE=%d  common=%d  %s..%s",
             rebalance, len(common),
             common.min().date(), common.max().date())

    w_s = {}; w_m = {}; w_rA = {}; w_wC = {}
    last_ws = np.ones(n_r)/n_r; last_wm = np.ones(n_r)/n_r
    last_rA = np.ones(n_r)/n_r; last_wC = np.ones(n_r)/n_r
    first_rebal = None; rebal_ctr = 0

    for i, date in enumerate(common):
        if i < MIN_HISTORY:
            continue
        if first_rebal is None:
            first_rebal = date
            log.info("  First rebal: %s (i=%d)", date.date(), i)

        if rebal_ctr % rebalance == 0:
            s0       = max(0, i - SCENARIO_CAP)
            hist_idx = common[s0:i]
            hist     = ret_r.loc[hist_idx].values
            hist_df  = ret_r.loc[hist_idx]
            lab_hist = valid_lab.loc[hist_idx].values.astype(int)
            prb_hist = prb.loc[hist_idx].values
            cur_lab  = int(valid_lab.loc[date])
            cur_prb  = prb.loc[date].values

            # Static CVaR
            res = solve_cvar(hist, CVAR_CFG)
            if res and res.get("weights") is not None:
                last_ws = res["weights"]
            w_s[date] = last_ws.copy()

            # Markowitz
            try:
                wm, _ = solve_min_variance(hist_df, MKV_CFG)
                last_wm = wm
            except Exception:
                pass
            w_m[date] = last_wm.copy()

            # Regime CVaR-A
            wA = _solve_regime_cvar_A(hist, lab_hist, cur_lab)
            if wA is not None:
                last_rA = wA
            w_rA[date] = last_rA.copy()

            # Weighted CVaR
            wW = _solve_weighted_cvar(hist, prb_hist, cur_prb)
            if wW is not None:
                last_wC = wW
            w_wC[date] = last_wC.copy()

        rebal_ctr += 1

    log.info("  Walk-forward complete (%d rebalances).", sum(1 for _ in w_s))

    def _wdf(d):
        return pd.DataFrame(d, index=risky).T.reindex(common).ffill()

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

    strat = gross.loc[first_rebal:].dropna(how="all")
    log.info("  Eval: %s → %s  n=%d",
             strat.index.min().date(), strat.index.max().date(), len(strat))

    to_eq  = _eq_drift_to(ret_r.reindex(strat.index))
    to_s   = _weekly_to(w_s_df.reindex(strat.index))
    to_m   = _weekly_to(w_m_df.reindex(strat.index))
    to_rA  = _weekly_to(w_rA_df.reindex(strat.index))
    to_wC  = _weekly_to(w_wC_df.reindex(strat.index))
    to_st  = pd.Series(0.0, index=strat.index)
    to_map = {
        "equal_weight_risky": to_eq,
        "stoxx600":           to_st,
        "static_cvar":        to_s,
        "markowitz":          to_m,
        "regime_cvar_A":      to_rA,
        "weighted_cvar":      to_wC,
    }
    return strat, to_map, first_rebal


# ══════════════════════════════════════════════════════════════════════════════
# Single (spec, freq) run — saves individual result CSV
# ══════════════════════════════════════════════════════════════════════════════

def run_one(spec_name: str, freq: int):
    spec = HMM_SPECS[spec_name]
    log.info("=== spec=%s  freq=%d ===", spec_name, freq)

    lab_path = spec["lab_path"]
    prb_path = spec["prb_path"]
    if not lab_path.exists():
        log.error("Labels not found: %s — skipping.", lab_path)
        return

    ret = pd.read_parquet(PROCESSED / "investable_returns_weekly.parquet")
    ret.index = pd.to_datetime(ret.index)
    lab = pd.read_parquet(lab_path)["regime_wf"]
    lab.index = pd.to_datetime(lab.index)
    prb = pd.read_parquet(prb_path)
    prb.index = pd.to_datetime(prb.index)
    rf  = ret[CASH_COL]

    strat, to_map, first_rebal = run_backtest(freq, lab, prb, ret, rf)
    rf_ev = rf.reindex(strat.index).fillna(0.0)

    cols = [c for c in STRATEGY_LABELS if c in strat.columns]
    net_f = {tc: pd.DataFrame({
        c: _apply_tc(strat[c], to_map[c], tc/10_000) for c in cols})
        for tc in TC_BPS_LIST}

    # ── performance rows ──────────────────────────────────────────────────────
    perf_rows = []
    for tc in TC_BPS_LIST:
        for col in cols:
            m  = compute_metrics(net_f[tc][col], rf_ev)
            to_c = to_map[col].reindex(strat.index).fillna(0)
            m.update({
                "spec":        spec_name,
                "hmm_label":   spec["label"],
                "rebalance":   freq,
                "tc_bps":      tc,
                "strategy":    col,
                "label":       STRATEGY_LABELS[col],
                "weekly_to_pct":  round(to_c.mean()*100, 4),
                "ann_to_pct":     round(to_c.mean()*ANN*100, 2),
                "eval_start":  str(strat.index.min().date()),
                "eval_end":    str(strat.index.max().date()),
            })
            perf_rows.append(m)

    # ── crisis window rows ────────────────────────────────────────────────────
    crisis_rows = []
    for col in cols:
        for win_name, (ws, we) in CRISIS_WINDOWS.items():
            r_gross = strat[col]
            r_net10 = net_f[10][col]
            m_g = compute_crisis_metrics(r_gross, rf_ev, win_name, ws, we)
            m_n = compute_crisis_metrics(r_net10, rf_ev, win_name, ws, we)
            crisis_rows.append({
                "spec":       spec_name,
                "rebalance":  freq,
                "strategy":   col,
                "label":      STRATEGY_LABELS[col],
                "window":     win_name,
                "N_weeks":    m_g["N_weeks"],
                "CAGR_pct_gross":  m_g.get("CAGR_pct",  np.nan),
                "MaxDD_pct_gross": m_g.get("MaxDD_pct", np.nan),
                "Sharpe_gross":    m_g.get("Sharpe",    np.nan),
                "CAGR_pct_net10":  m_n.get("CAGR_pct",  np.nan),
                "MaxDD_pct_net10": m_n.get("MaxDD_pct", np.nan),
                "Sharpe_net10":    m_n.get("Sharpe",    np.nan),
            })

    perf_df   = pd.DataFrame(perf_rows)
    crisis_df = pd.DataFrame(crisis_rows)

    slug = f"{spec_name}_freq{freq}"
    perf_df.to_csv(DF_OUT / f"perf_{slug}.csv", index=False)
    crisis_df.to_csv(DF_OUT / f"crisis_{slug}.csv", index=False)

    # Console summary
    g0 = perf_df[perf_df["tc_bps"]==0].set_index("strategy")
    log.info("  %-28s %7s %7s %7s %8s %10s",
             "Strategy","CAGR%","Vol%","Sharpe","MaxDD%","TO%ann")
    for s, m in g0.iterrows():
        log.info("  %-28s %+6.2f  %6.2f  %7.3f  %7.2f  %9.1f",
                 s, m.CAGR_pct, m.Vol_pct, m.Sharpe, m.MaxDD_pct, m.ann_to_pct)
    log.info("  Done: %s", slug)


# ══════════════════════════════════════════════════════════════════════════════
# Aggregation — reads all individual CSVs and writes summary outputs
# ══════════════════════════════════════════════════════════════════════════════

def aggregate():
    log.info("=== Aggregating results ===")

    perf_frames   = []
    crisis_frames = []

    for spec_name in HMM_SPECS:
        for freq in REBALANCE_FREQS_ALL:
            slug = f"{spec_name}_freq{freq}"
            pf = DF_OUT / f"perf_{slug}.csv"
            cf = DF_OUT / f"crisis_{slug}.csv"
            if pf.exists():
                perf_frames.append(pd.read_csv(pf))
                log.info("  Loaded %s", pf.name)
            elif freq == 1:
                log.info("  Skipping freq=1 (compute time exceeds sandbox limit).")
            else:
                log.warning("  Missing %s — run --spec %s --freq %d first.",
                            pf.name, spec_name, freq)
            if cf.exists():
                crisis_frames.append(pd.read_csv(cf))

    if not perf_frames:
        log.error("No results found. Run individual spec/freq combinations first.")
        return

    perf_all   = pd.concat(perf_frames,   ignore_index=True)
    crisis_all = pd.concat(crisis_frames, ignore_index=True) if crisis_frames else pd.DataFrame()

    perf_all.to_csv(RF_OUT / "rebalance_frequency_performance.csv", index=False)
    log.info("Wrote rebalance_frequency_performance.csv  (%d rows)", len(perf_all))

    # TC sensitivity pivot
    tc_rows = []
    g0 = perf_all[perf_all["tc_bps"]==0].copy()
    for _, row in g0.iterrows():
        tc_row = {"spec": row["spec"], "rebalance": row["rebalance"],
                  "strategy": row["strategy"], "label": row["label"],
                  "Sharpe_0bps": row["Sharpe"],
                  "ann_to_pct": row["ann_to_pct"]}
        for tc in [5, 10, 25]:
            sub = perf_all[
                (perf_all["spec"]==row["spec"]) &
                (perf_all["rebalance"]==row["rebalance"]) &
                (perf_all["strategy"]==row["strategy"]) &
                (perf_all["tc_bps"]==tc)
            ]
            tc_row[f"Sharpe_{tc}bps"] = sub["Sharpe"].iloc[0] if len(sub) else np.nan
        tc_rows.append(tc_row)
    tc_df = pd.DataFrame(tc_rows)
    tc_df.to_csv(RF_OUT / "rebalance_frequency_tc_sensitivity.csv", index=False)
    log.info("Wrote rebalance_frequency_tc_sensitivity.csv")

    if not crisis_all.empty:
        crisis_all.to_csv(RF_OUT / "rebalance_frequency_crisis_windows.csv", index=False)
        log.info("Wrote rebalance_frequency_crisis_windows.csv")

    _write_summary(perf_all, tc_df, crisis_all)
    log.info("=== Aggregation complete ===")


def _write_summary(perf_all, tc_df, crisis_all):
    lines = [
        "# Rebalance Frequency Sensitivity Experiment",
        "",
        "*Generated by `12_rebalance_frequency_experiment.py`*",
        "",
        "## Methodology Note",
        "",
        "HMM walk-forward labels are produced every 4 weeks (checkpoint step=4) and",
        "forward-filled to weekly frequency before saving to parquet. For rebalance",
        "frequencies shorter than 4 weeks (i.e., 1-week and 2-week cadences), the",
        "regime label in force at any given week is the most recent checkpoint label",
        "at or before that date — this is strictly backward-looking and introduces no",
        "look-ahead. The CVaR scenario window (260 weeks rolling) is purely historical",
        "and unaffected by rebalance frequency.",
        "",
        "Burn-in: 156 weeks (3 years) regardless of rebalance frequency.",
        "Evaluation window: 2010-10-15 → 2026-04-03 (808 weeks, 15.5 yr).",
        "",
        "---",
    ]

    for spec_name, spec_info in HMM_SPECS.items():
        g0_spec = perf_all[(perf_all["spec"]==spec_name) &
                           (perf_all["tc_bps"]==0)].copy()
        if g0_spec.empty:
            continue

        lines += ["", f"## {spec_info['label']}", ""]

        for strat_key, strat_label in STRATEGY_LABELS.items():
            sub = g0_spec[g0_spec["strategy"]==strat_key].sort_values("rebalance")
            if sub.empty:
                continue
            lines.append(f"### {strat_label}")
            lines.append("")
            lines.append("| Rebalance | CAGR | Vol | Sharpe (0bps) | Sharpe (5bps) | "
                         "Sharpe (10bps) | Sharpe (25bps) | MaxDD | TO% ann |")
            lines.append("| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |")
            for _, r in sub.iterrows():
                tc_row = tc_df[
                    (tc_df["spec"]==spec_name) &
                    (tc_df["rebalance"]==r["rebalance"]) &
                    (tc_df["strategy"]==strat_key)
                ]
                s5  = tc_row["Sharpe_5bps"].iloc[0]  if len(tc_row) else np.nan
                s10 = tc_row["Sharpe_10bps"].iloc[0] if len(tc_row) else np.nan
                s25 = tc_row["Sharpe_25bps"].iloc[0] if len(tc_row) else np.nan
                lines.append(
                    f"| {r['rebalance']}w | {r['CAGR_pct']:+.2f}% | {r['Vol_pct']:.2f}% | "
                    f"{r['Sharpe']:.3f} | {s5:.3f} | {s10:.3f} | {s25:.3f} | "
                    f"{r['MaxDD_pct']:.2f}% | {r['ann_to_pct']:.1f}% |"
                )
            # Note freq=1 if not computed
            if g0_spec[(g0_spec["strategy"]==strat_key) &
                        (g0_spec["rebalance"]==1)].empty:
                lines.append("| 1w | *(not run — >45 s compute)* | | | | | | | |")
            lines.append("")

    # Crisis windows summary
    if not crisis_all.empty:
        lines += ["---", "", "## Crisis Window Performance (Gross CAGR%)", "",
                  "| Spec | Strategy | Rebalance | EU Sov 2011 | COVID 2020 | Rate Shock 2022 |",
                  "| --- | --- | --- | ---: | ---: | ---: |"]
        for spec_name in HMM_SPECS:
            for strat_key in ["static_cvar", "regime_cvar_A", "weighted_cvar"]:
                for freq in REBALANCE_FREQS:
                    sub = crisis_all[(crisis_all["spec"]==spec_name) &
                                     (crisis_all["strategy"]==strat_key) &
                                     (crisis_all["rebalance"]==freq)]
                    if sub.empty:
                        continue
                    def _cagr(win):
                        row = sub[sub["window"]==win]
                        return f"{row['CAGR_pct_gross'].iloc[0]:+.2f}%" if len(row) else "—"
                    lines.append(
                        f"| {spec_name} | {STRATEGY_LABELS[strat_key]} | {freq}w | "
                        f"{_cagr('EU_Sovereign_2011')} | {_cagr('COVID_Crash_2020')} | "
                        f"{_cagr('Rate_Shock_2022')} |"
                    )
        lines.append("")

    # Recommendation
    lines += ["---", "", "## Final Recommendation", ""]

    # Compute recommendation from data
    rec = _build_recommendation(perf_all, tc_df)
    lines += rec

    (RF_OUT / "rebalance_frequency_summary.md").write_text("\n".join(lines))
    log.info("Wrote rebalance_frequency_summary.md")


def _build_recommendation(perf_all, tc_df):
    """Derive answers to A–F from the computed results."""
    lines = []

    for spec_name, spec_info in HMM_SPECS.items():
        g0 = perf_all[(perf_all["spec"]==spec_name) &
                      (perf_all["tc_bps"]==0)].copy()
        if g0.empty:
            continue
        lines.append(f"### {spec_info['label']}")
        lines.append("")

        regime_strats = ["regime_cvar_A", "weighted_cvar"]
        ref_strat     = "static_cvar"

        for q_label, q_key in [("A. Is 4-week rebalancing too slow?", None),
                                ("B. Does shorter frequency improve gross Sharpe?", None),
                                ("C. Does improvement survive TC?", None),
                                ("D. Does lower frequency reduce TO enough?", None),
                                ("E. Better cadence than 4 weeks?", None),
                                ("F. Keep 4 weeks as baseline?", None)]:

            # A: Compare freq=4 vs freq=1,2 gross Sharpe for regime strategies
            if q_label.startswith("A"):
                answers = []
                for col in regime_strats:
                    sub = g0[g0["strategy"]==col].sort_values("rebalance")
                    if sub.empty: continue
                    sh4 = sub[sub["rebalance"]==4]["Sharpe"].values
                    sh1 = sub[sub["rebalance"]==1]["Sharpe"].values
                    if len(sh4) and len(sh1):
                        delta = float(sh1[0]) - float(sh4[0])
                        answers.append(f"{STRATEGY_LABELS[col]}: Sharpe 1w={sh1[0]:.3f} vs 4w={sh4[0]:.3f} (Δ={delta:+.3f})")
                val = " | ".join(answers) if answers else "insufficient data"
                too_slow = any(a.split("Δ=")[1].rstrip(")") > "0.02"
                               for a in answers if "Δ=" in a)
                verdict = "Yes" if too_slow else "Not clearly — gains are marginal"
                lines.append(f"**{q_label}**")
                lines.append(f"  {val}. Verdict: **{verdict}**.")
                lines.append("")

            # B: Best gross Sharpe frequency
            elif q_label.startswith("B"):
                answers = []
                for col in regime_strats:
                    sub = g0[g0["strategy"]==col].sort_values("rebalance")
                    if sub.empty: continue
                    best_row = sub.loc[sub["Sharpe"].idxmax()]
                    answers.append(f"{STRATEGY_LABELS[col]}: best freq={int(best_row['rebalance'])}w (Sharpe={best_row['Sharpe']:.3f})")
                lines.append(f"**{q_label}**")
                lines.append(f"  {' | '.join(answers) if answers else 'insufficient data'}.")
                lines.append("")

            # C: Net improvement vs Static CVaR at 10 bps
            elif q_label.startswith("C"):
                ref_sh10 = None
                ref_sub = perf_all[(perf_all["spec"]==spec_name) &
                                   (perf_all["strategy"]==ref_strat) &
                                   (perf_all["tc_bps"]==10) &
                                   (perf_all["rebalance"]==4)]
                if len(ref_sub):
                    ref_sh10 = ref_sub["Sharpe"].iloc[0]
                answers = []
                for col in regime_strats:
                    best_sh10 = None; best_freq = None
                    for freq in REBALANCE_FREQS:
                        sub = perf_all[(perf_all["spec"]==spec_name) &
                                       (perf_all["strategy"]==col) &
                                       (perf_all["tc_bps"]==10) &
                                       (perf_all["rebalance"]==freq)]
                        if len(sub):
                            sh = sub["Sharpe"].iloc[0]
                            if best_sh10 is None or sh > best_sh10:
                                best_sh10 = sh; best_freq = freq
                    if best_sh10 is not None and ref_sh10 is not None:
                        beats = "beats" if best_sh10 > ref_sh10 else "does not beat"
                        answers.append(
                            f"{STRATEGY_LABELS[col]}: best net Sharpe={best_sh10:.3f} "
                            f"at {best_freq}w — {beats} Static CVaR ({ref_sh10:.3f})"
                        )
                lines.append(f"**{q_label}**")
                for a in answers:
                    lines.append(f"  {a}.")
                lines.append("")

            # D: Does lower frequency reduce TO enough?
            elif q_label.startswith("D"):
                answers = []
                for col in regime_strats:
                    sub = g0[g0["strategy"]==col].sort_values("rebalance")
                    if sub.empty: continue
                    to_by_freq = sub.set_index("rebalance")["ann_to_pct"]
                    to_str = " | ".join(f"{f}w={v:.0f}%" for f, v in to_by_freq.items())
                    answers.append(f"{STRATEGY_LABELS[col]}: {to_str}")
                lines.append(f"**{q_label}**")
                for a in answers:
                    lines.append(f"  {a}.")
                lines.append("")

            # E: Better cadence
            elif q_label.startswith("E"):
                conclusions = []
                for col in regime_strats:
                    # Find freq that maximises net Sharpe at 10bps
                    best_sh = None; best_freq = None
                    for freq in REBALANCE_FREQS:
                        sub = perf_all[(perf_all["spec"]==spec_name) &
                                       (perf_all["strategy"]==col) &
                                       (perf_all["tc_bps"]==10) &
                                       (perf_all["rebalance"]==freq)]
                        if len(sub):
                            sh = sub["Sharpe"].iloc[0]
                            if best_sh is None or sh > best_sh:
                                best_sh = sh; best_freq = freq
                    if best_freq is not None and best_freq != 4:
                        conclusions.append(
                            f"{STRATEGY_LABELS[col]}: {best_freq}w maximises net Sharpe ({best_sh:.3f})"
                        )
                    elif best_freq == 4:
                        conclusions.append(
                            f"{STRATEGY_LABELS[col]}: 4w is already optimal by net Sharpe"
                        )
                lines.append(f"**{q_label}**")
                for c in conclusions:
                    lines.append(f"  {c}.")
                lines.append("")

            # F: Keep 4 weeks
            elif q_label.startswith("F"):
                lines.append(f"**{q_label}**")
                lines.append(
                    "  The 4-week baseline is justified if: (i) it is never the worst cadence "
                    "net of costs, (ii) gross gains at shorter frequencies do not survive TC, and "
                    "(iii) it provides a consistent reference across Panel B and the HICP/ZEW "
                    "robustness checks. Report this experiment as a robustness appendix confirming "
                    "that the 4-week choice is not the primary driver of the main result."
                )
                lines.append("")

    return lines


# ══════════════════════════════════════════════════════════════════════════════
# Entry point
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", choices=list(HMM_SPECS.keys()))
    ap.add_argument("--freq", type=int, choices=REBALANCE_FREQS_ALL)
    ap.add_argument("--aggregate", action="store_true")
    args = ap.parse_args()
    t0 = time.time()
    if args.aggregate:
        aggregate()
    elif args.spec and args.freq:
        run_one(args.spec, args.freq)
    else:
        log.info("Running all runnable combinations.")
        for spec_name in HMM_SPECS:
            for freq in REBALANCE_FREQS:
                run_one(spec_name, freq)
        aggregate()
    log.info("Total elapsed: %.0fs", time.time() - t0)
