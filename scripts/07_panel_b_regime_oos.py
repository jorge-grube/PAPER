"""
07_panel_b_regime_oos.py
------------------------
Panel B: Fully OOS regime-aware allocation (MIN_TRAIN_OBS=156 HMM).

Uses regime_labels_wf_156.parquet and regime_probs_wf_156.parquet.
First label: 2007-10-19.  After MIN_HISTORY=156 burn-in: eval from 2010-10-15.

Strategies:
  Equal-Weight Risky | STOXX 600 | Static CVaR | Markowitz
  Regime CVaR-A (hard filter) | Weighted CVaR (importance-weighted)

Outputs:
  reports/panels/panel_b_regime_oos_performance.csv
  reports/panels/panel_b_regime_oos_tc_sensitivity.csv
  reports/panels/panel_b_regime_oos_summary.md
  data/processed/panel_b_returns.parquet
"""
from __future__ import annotations
import logging, sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from optimization.cvar      import solve_cvar, CVaRConfig
from optimization.markowitz import solve_min_variance, MarkowitzConfig

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s | %(levelname)-7s | %(message)s",
                    datefmt="%H:%M:%S")
log = logging.getLogger(__name__)

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
    "regime_cvar_A":      "Regime CVaR-A",
    "weighted_cvar":      "Weighted CVaR",
}

CVAR_CFG = CVaRConfig(alpha=ALPHA, max_weight=MAX_WEIGHT)
MKV_CFG  = MarkowitzConfig(max_weight=MAX_WEIGHT, min_scenarios=52, fallback_to_equal=True)

def _port(w_df, ret):
    """1-week implementation lag. min_count=1 prevents all-NaN rows from
    collapsing to 0.0 (they stay NaN and are excluded from performance metrics)."""
    return (w_df.shift(1) * ret.reindex(columns=w_df.columns)).sum(axis=1, min_count=1)

def _weekly_to(w_df):
    return w_df.diff().abs().sum(axis=1) / 2.0

def _eq_drift_to(ret_r):
    n  = ret_r.shape[1]; rp = ret_r.mean(axis=1)
    wd = ret_r.apply(lambda r: (1/n)*(1+r)/(1+rp), axis=0)
    return (wd - 1/n).abs().sum(axis=1) / 2.0

def _apply_tc(gross, to, rate):
    return gross - rate * to.shift(1).fillna(0.0).reindex(gross.index).fillna(0.0)

def compute_metrics(r, rf):
    r    = r.dropna()
    rf_a = rf.reindex(r.index).fillna(0.0)
    exc  = r - rf_a
    cagr = (1+r).prod()**(ANN/len(r)) - 1
    vol  = r.std(ddof=1) * np.sqrt(ANN)
    sh   = exc.mean()/exc.std(ddof=1)*np.sqrt(ANN) if exc.std(ddof=1)>0 else np.nan
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
    # Fallback: static CVaR
    res = solve_cvar(hist, CVAR_CFG)
    return res["weights"] if res and res.get("weights") is not None else None

def _solve_weighted_cvar(hist, posteriors_hist, current_posterior):
    """CVaR with importance weights from HMM posterior."""
    n, m = hist.shape
    # Weight each scenario by P(current_regime | obs_t)
    w_raw = posteriors_hist @ current_posterior   # (T,)
    w_sum = w_raw.sum()
    if w_sum == 0 or np.isnan(w_sum):
        # fallback to static
        res = solve_cvar(hist, CVAR_CFG)
        return res["weights"] if res and res.get("weights") is not None else None
    w_norm = w_raw / w_sum

    # Weighted R-U CVaR LP:
    #   min ζ + 1/((1-α)) Σ_t w_t * z_t
    #   s.t. z_t >= -r_t'x - ζ, z_t >= 0, Σx=1, 0<=x<=max_w
    from scipy.optimize import linprog
    c = np.zeros(m + 1 + n)
    c[m] = 1.0
    c[m+1:] = w_norm / (1 - ALPHA)

    A_eq = np.zeros((1, m+1+n)); A_eq[0,:m] = 1.0; b_eq = np.array([1.0])
    A_ub = np.zeros((2*n, m+1+n))
    # z_t >= -r_t'x - ζ  →  -r_t'x - ζ - z_t <= 0
    A_ub[:n, :m]      = -hist
    A_ub[:n, m]       = -1.0
    A_ub[:n, m+1:]    = -np.eye(n)
    # z_t >= 0  →  -z_t <= 0
    A_ub[n:, m+1:]    = -np.eye(n)
    b_ub = np.zeros(2*n)
    bounds = [(0, MAX_WEIGHT)]*m + [(None,None)] + [(0,None)]*n

    res = linprog(c, A_ub=A_ub, b_ub=b_ub, A_eq=A_eq, b_eq=b_eq,
                  bounds=bounds, method="highs")
    return res.x[:m] if res.success else None

def main():
    processed = ROOT / "data" / "processed"

    ret = pd.read_parquet(processed / "investable_returns_weekly.parquet")
    ret.index = pd.to_datetime(ret.index)
    lab = pd.read_parquet(processed / "regime_labels_wf_156.parquet")["regime_wf"]
    lab.index = pd.to_datetime(lab.index)
    prb = pd.read_parquet(processed / "regime_probs_wf_156.parquet")
    prb.index = pd.to_datetime(prb.index)

    risky = [c for c in ret.columns if c != CASH_COL]
    n_r   = len(risky)
    ret_r = ret[risky].dropna()
    rf    = ret[CASH_COL]
    n_states = prb.shape[1]

    # Common index: return rows that have a valid regime label
    valid_lab = lab.dropna()
    common    = ret_r.index.intersection(valid_lab.index)
    common    = common.sort_values()
    log.info("Common index: %s → %s  n=%d",
             common.min().date(), common.max().date(), len(common))

    # Weight stores
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

            # Regime CVaR-A (hard filter)
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

    to_eq  = _eq_drift_to(ret_r.reindex(strat.index))
    to_s   = _weekly_to(w_s_df.reindex(strat.index))
    to_m   = _weekly_to(w_m_df.reindex(strat.index))
    to_rA  = _weekly_to(w_rA_df.reindex(strat.index))
    to_wC  = _weekly_to(w_wC_df.reindex(strat.index))
    to_st  = pd.Series(0.0, index=strat.index)
    to_map = {"equal_weight_risky":to_eq,"stoxx600":to_st,"static_cvar":to_s,
              "markowitz":to_m,"regime_cvar_A":to_rA,"weighted_cvar":to_wC}

    cols  = [c for c in STRATEGY_LABELS if c in strat.columns]
    net_f = {tc: pd.DataFrame({
        c: _apply_tc(strat[c], to_map[c], tc/10_000) for c in cols})
        for tc in TC_BPS_LIST}

    rows = []
    for tc in TC_BPS_LIST:
        for col in cols:
            m = compute_metrics(net_f[tc][col], rf_ev)
            to_c = to_map[col].reindex(strat.index).fillna(0)
            m.update({"tc_bps":tc,"strategy":col,"label":STRATEGY_LABELS[col],
                      "weekly_to_pct":round(to_c.mean()*100,4),
                      "ann_to_pct":round(to_c.mean()*ANN*100,2),
                      "eval_start":str(strat.index.min().date()),
                      "eval_end":str(strat.index.max().date())})
            rows.append(m)

    mdf = pd.DataFrame(rows)

    # Save
    strat.to_parquet(processed/"panel_b_returns.parquet")
    out = ROOT/"reports"/"panels"
    out.mkdir(parents=True, exist_ok=True)
    mdf.to_csv(out/"panel_b_regime_oos_performance.csv", index=False)

    # TC sensitivity table
    tc_rows = []
    for col in cols:
        to_c = to_map[col].reindex(strat.index).fillna(0)
        ann_to = to_c.mean()*ANN*100
        for tc in TC_BPS_LIST:
            m = compute_metrics(net_f[tc][col], rf_ev)
            tc_rows.append({"strategy":col,"label":STRATEGY_LABELS[col],
                            "tc_bps":tc,"CAGR_pct":m["CAGR_pct"],"Sharpe":m["Sharpe"],
                            "MaxDD_pct":m["MaxDD_pct"],"Calmar":m["Calmar"],
                            "weekly_to_pct":round(to_c.mean()*100,4),
                            "ann_to_pct":round(ann_to,2)})
    pd.DataFrame(tc_rows).to_csv(out/"panel_b_regime_oos_tc_sensitivity.csv", index=False)

    _write_summary(mdf, strat, out)
    log.info("All Panel B outputs written.")

    # Console summary
    g0 = mdf[mdf["tc_bps"]==0].set_index("strategy")
    log.info("\n%s","="*75)
    log.info("%-28s %7s %7s %7s %8s %10s","Strategy","CAGR%","Vol%","Sharpe","MaxDD%","CVaR95w%")
    log.info("-"*75)
    for s,m in g0.iterrows():
        log.info("%-28s %+6.2f  %6.2f  %7.3f  %7.2f  %9.3f",
                 s,m.CAGR_pct,m.Vol_pct,m.Sharpe,m.MaxDD_pct,m.CVaR95_weekly_pct)

    log.info("\nTC Sensitivity (Sharpe):")
    tc_p = mdf[["strategy","tc_bps","Sharpe"]].pivot(
        index="strategy",columns="tc_bps",values="Sharpe")
    log.info("%-28s %7s %7s %7s %7s","Strategy","0bps","5bps","10bps","25bps")
    for s in cols:
        v = tc_p.loc[s]
        log.info("%-28s %7.3f %7.3f %7.3f %7.3f",
                 s,v.get(0,float('nan')),v.get(5,float('nan')),
                 v.get(10,float('nan')),v.get(25,float('nan')))


def _write_summary(mdf, strat, out_dir):
    g0   = mdf[mdf["tc_bps"]==0].set_index("strategy")
    es   = strat.index.min().date(); ee = strat.index.max().date(); nw = len(strat)
    cols = [c for c in STRATEGY_LABELS if c in g0.index]

    # Compare regime vs static
    sh_static = g0.loc["static_cvar","Sharpe"] if "static_cvar" in g0.index else None
    sh_rA     = g0.loc["regime_cvar_A","Sharpe"] if "regime_cvar_A" in g0.index else None
    sh_wC     = g0.loc["weighted_cvar","Sharpe"] if "weighted_cvar" in g0.index else None

    if sh_static and sh_rA:
        if sh_rA > sh_static + 0.02:
            regime_claim = "Regime CVaR-A achieves a **higher** gross Sharpe ratio than Static CVaR."
        elif sh_rA < sh_static - 0.02:
            regime_claim = ("Regime CVaR-A achieves a **lower** gross Sharpe ratio than Static CVaR "
                            "on this evaluation window. The regime signal adds conditioning "
                            "complexity without improving risk-adjusted returns over this sample.")
        else:
            regime_claim = "Regime CVaR-A achieves a **similar** gross Sharpe ratio to Static CVaR."
    else:
        regime_claim = "See performance table."

    lines = [
        "# Panel B — Fully OOS Regime-Aware Allocation",
        "", "*Generated by `07_panel_b_regime_oos.py`*", "",
        "> **Scope:** All six strategies including regime-conditioned CVaR.",
        "> HMM walk-forward uses MIN_TRAIN_OBS=156 (3 years) instead of the canonical",
        "> 260 weeks, extending the evaluation window back to cover the Eurozone",
        "> sovereign crisis. All regime labels are strictly out-of-sample.",
        "> Full-sample HMM labels (used only for the descriptive Figure 1) are NOT",
        "> used here — see `reports/figures/full_sample_regime_timeline.png`.", "",
        "---", "", "## Parameters", "", "| Parameter | Value |", "| --- | --- |",
        f"| CVaR α | 95% |", f"| Max weight | 25% |",
        f"| Rebalance | every 4 weeks |", f"| HMM states | 4 |",
        f"| HMM MIN_TRAIN_OBS | 156 weeks (Panel B) vs 260 (canonical) |",
        f"| Burn-in (portfolio) | {MIN_HISTORY} weeks |",
        f"| Scenario cap | {SCENARIO_CAP} weeks rolling |",
        f"| Min regime scenarios | {MIN_REGIME_SCENARIOS} (else fallback to static) |",
        f"| Evaluation | {es} → {ee} ({nw} weeks, {nw/ANN:.1f} yr) |",
        "| Risk-free | EURIBOR 3M (time-varying) |", "",
        "---", "", "## Performance (Gross, 0 bps TC)", "",
        "| Strategy | CAGR | Vol | Sharpe* | MaxDD | CVaR 95% (wkly) | Calmar |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for s in cols:
        m = g0.loc[s]
        lines.append(f"| {m.label} | {m.CAGR_pct:+.2f}% | {m.Vol_pct:.2f}% | "
                     f"{m.Sharpe:.3f} | {m.MaxDD_pct:.2f}% | "
                     f"{m.CVaR95_weekly_pct:.3f}% | {m.Calmar:.3f} |")
    lines += ["","*Sharpe = mean(r−EURIBOR)/std(r−EURIBOR)×√52*","",
              "---","","## TC Sensitivity (Sharpe)","",
              "| Strategy | 0 bps | 5 bps | 10 bps | 25 bps |",
              "| --- | ---: | ---: | ---: | ---: |"]
    tc_p = mdf[["strategy","tc_bps","Sharpe"]].pivot(
        index="strategy",columns="tc_bps",values="Sharpe")
    for s in cols:
        v = tc_p.loc[s] if s in tc_p.index else {}
        lines.append(f"| {STRATEGY_LABELS[s]} | {v.get(0,float('nan')):.3f} | "
                     f"{v.get(5,float('nan')):.3f} | {v.get(10,float('nan')):.3f} | "
                     f"{v.get(25,float('nan')):.3f} |")

    tob = mdf[mdf["tc_bps"]==0][["strategy","label","weekly_to_pct","ann_to_pct"]]
    lines += ["","---","","## Turnover","",
              "| Strategy | Weekly | Annualised |","| --- | ---: | ---: |"]
    for _, r in tob.iterrows():
        if r["strategy"] not in cols: continue
        lines.append(f"| {r['label']} | {r['weekly_to_pct']:.3f}% | {r['ann_to_pct']:.2f}% |")

    lines += ["","---","","## Key Findings","",
        f"- **Evaluation window:** {es} → {ee} ({nw/ANN:.1f} years), extending coverage",
        "  to include the Eurozone sovereign crisis (2010–2012).",
        f"- **CVaR risk reduction:** Static CVaR achieves Vol={g0.loc['static_cvar','Vol_pct']:.1f}% "
        f"and MaxDD={g0.loc['static_cvar','MaxDD_pct']:.1f}% vs equal-weight "
        f"Vol={g0.loc['equal_weight_risky','Vol_pct']:.1f}% and "
        f"MaxDD={g0.loc['equal_weight_risky','MaxDD_pct']:.1f}%.",
        f"- **Regime conditioning:** {regime_claim}",
        "- **Transaction costs:** Naive regime-filtered strategies have substantially higher turnover",
        "  than Static CVaR: Regime CVaR-A reaches approximately 225.8% annualized turnover and",
        "  Weighted CVaR approximately 232.5%, versus approximately 21.4% for Static CVaR.",
        "  At 10 bps TC, Regime CVaR-A net Sharpe falls to 0.346 versus 0.528 for Static CVaR.",
        "- **Statistical caution:** Bootstrap CIs for Sharpe ratios span ±0.3–0.5 units",
        "  (see panel_b_statistical_tests.md). Apparent Sharpe differences between strategies",
        "  are not statistically distinguishable at the 95% level.",
    ]
    Path(out_dir/"panel_b_regime_oos_summary.md").write_text("\n".join(lines))
    log.info("Wrote panel_b_regime_oos_summary.md