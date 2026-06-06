"""
Script 18 — Panel B (FI-Expanded Universe)
==========================================
Replicates Panel B (Static CVaR, Markowitz, Regime CVaR-A, Weighted CVaR)
on the 14-asset FI-expanded universe.
Uses existing HMM walk-forward labels (regime_labels_wf_156.parquet) — does NOT
refit the HMM.  Identical parameters to 07_panel_b_regime_oos.py.

Outputs → reports/fi_expanded/
  panel_b_performance_fi_expanded.csv
  panel_b_tc_sensitivity_fi_expanded.csv
  panel_b_summary_fi_expanded.md
  data/processed/panel_b_returns_fi_expanded.parquet
"""
from __future__ import annotations
import logging, sys
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

# ── Parameters (identical to 07_panel_b_regime_oos.py) ───────────────────────
ALPHA                = 0.95
MAX_WEIGHT           = 0.25
REBALANCE            = 4
MIN_HISTORY          = 156
SCENARIO_CAP         = 260
MIN_REGIME_SCENARIOS = 30
TC_BPS_LIST          = [0, 5, 10, 25]
CASH_COL             = "EURIBOR_3M"
STOXX_COL            = "StoxxEurope600"
ANN                  = 52

CVAR_CFG = CVaRConfig(alpha=ALPHA, max_weight=MAX_WEIGHT)
MKV_CFG  = MarkowitzConfig(max_weight=MAX_WEIGHT, min_scenarios=52, fallback_to_equal=True)

STRATEGY_LABELS = {
    "equal_weight_risky": "Equal-Weight Risky (1/N)",
    "stoxx600":           "STOXX Europe 600",
    "static_cvar":        "Static CVaR (FI-Exp)",
    "markowitz":          "Markowitz (FI-Exp)",
    "regime_cvar_A":      "Regime CVaR-A (FI-Exp)",
    "weighted_cvar":      "Weighted CVaR (FI-Exp)",
}

# ── Helpers ───────────────────────────────────────────────────────────────────
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
    r    = r.dropna()
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

    A_eq = np.zeros((1, m+1+n)); A_eq[0, :m] = 1.0; b_eq = np.array([1.0])
    A_ub = np.zeros((2*n, m+1+n))
    A_ub[:n, :m]   = -hist
    A_ub[:n, m]    = -1.0
    A_ub[:n, m+1:] = -np.eye(n)
    A_ub[n:, m+1:] = -np.eye(n)
    b_ub = np.zeros(2*n)
    bounds = [(0, MAX_WEIGHT)]*m + [(None, None)] + [(0, None)]*n

    res = linprog(c, A_ub=A_ub, b_ub=b_ub, A_eq=A_eq, b_eq=b_eq,
                  bounds=bounds, method="highs")
    return res.x[:m] if res.success else None


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    processed = ROOT / "data" / "processed"
    out_dir   = ROOT / "reports" / "fi_expanded"
    out_dir.mkdir(parents=True, exist_ok=True)

    ret = pd.read_parquet(processed / "investable_returns_weekly_fi_expanded.parquet")
    ret.index = pd.to_datetime(ret.index)

    # Load existing HMM labels (do NOT refit)
    lab = pd.read_parquet(processed / "regime_labels_wf_156.parquet")["regime_wf"]
    lab.index = pd.to_datetime(lab.index)
    prb = pd.read_parquet(processed / "regime_probs_wf_156.parquet")
    prb.index = pd.to_datetime(prb.index)

    risky   = [c for c in ret.columns if c != CASH_COL]
    n_r     = len(risky)
    ret_r   = ret[risky].dropna()
    rf      = ret[CASH_COL]
    n_states = prb.shape[1]

    # Common index: dates that have both returns and regime labels
    valid_lab = lab.dropna()
    common    = ret_r.index.intersection(valid_lab.index).sort_values()
    log.info("Common index: %s → %s  n=%d  risky=%d",
             common.min().date(), common.max().date(), len(common), n_r)
    log.info("Risky assets: %s", risky)

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

            # Regime CVaR-A (hard filter to current regime)
            wA = _solve_regime_cvar_A(hist, lab_hist, cur_lab)
            if wA is not None:
                last_rA = wA
            w_rA[date] = last_rA.copy()

            # Weighted CVaR (importance-weighted by HMM posterior)
            wW = _solve_weighted_cvar(hist, prb_hist, cur_prb)
            if wW is not None:
                last_wC = wW
            w_wC[date] = last_wC.copy()

        rebal_ctr += 1

    log.info("Walk-forward complete. Building weight frames...")

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
    to_map = {"equal_weight_risky": to_eq, "stoxx600": to_st,
              "static_cvar": to_s, "markowitz": to_m,
              "regime_cvar_A": to_rA, "weighted_cvar": to_wC}

    cols  = [c for c in STRATEGY_LABELS if c in strat.columns]
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
                      "ann_to_pct":    round(to_c.mean()*ANN*100, 2),
                      "eval_start":    str(strat.index.min().date()),
                      "eval_end":      str(strat.index.max().date()),
                      "universe":      "fi_expanded"})
            rows.append(m)

    mdf = pd.DataFrame(rows)

    # TC sensitivity table (strategy × tc_bps Sharpe grid)
    tc_rows = []
    for col in cols:
        row = {"strategy": col, "label": STRATEGY_LABELS[col],
               "ann_to_pct": round(to_map[col].reindex(strat.index).mean()*ANN*100, 2)}
        for tc in TC_BPS_LIST:
            g = mdf[mdf["tc_bps"] == tc].set_index("strategy")
            row[f"sharpe_{tc}bps"] = g.loc[col, "Sharpe"]
        tc_rows.append(row)

    strat.to_parquet(processed / "panel_b_returns_fi_expanded.parquet")
    mdf.to_csv(out_dir / "panel_b_performance_fi_expanded.csv", index=False)
    pd.DataFrame(tc_rows).to_csv(out_dir / "panel_b_tc_sensitivity_fi_expanded.csv", index=False)
    _write_summary(mdf, strat, out_dir)
    log.info("Panel B (FI-expanded) outputs written.")

    g0 = mdf[mdf["tc_bps"] == 0].set_index("strategy")
    log.info("\n%s", "="*72)
    log.info("%-30s %7s %7s %7s %8s", "Strategy", "CAGR%", "Vol%", "Sharpe", "MaxDD%")
    log.info("-"*72)
    for s, m in g0.iterrows():
        log.info("%-30s %+6.2f  %6.2f  %7.3f  %7.2f",
                 s, m.CAGR_pct, m.Vol_pct, m.Sharpe, m.MaxDD_pct)


def _write_summary(mdf, strat, out_dir):
    g0  = mdf[mdf["tc_bps"] == 0].set_index("strategy")
    g10 = mdf[mdf["tc_bps"] == 10].set_index("strategy")
    es  = strat.index.min().date()
    ee  = strat.index.max().date()
    nw  = len(strat)
    cols = [c for c in STRATEGY_LABELS if c in g0.index]

    lines = [
        "# Panel B — FI-Expanded Universe (Regime-Aware)",
        "",
        f"*Generated by `18_panel_b_fi_expanded.py`*",
        "",
        "> **Universe:** 14 assets (11 baseline + Germany/Spain/Italy Govt Bond TR)",
        f"> **Eval period:** {es} → {ee}  ({nw} weeks)",
        f"> **HMM labels:** existing walk-forward labels (regime_labels_wf_156.parquet) — "
        "NOT refit on FI-expanded data",
        f"> **Parameters:** identical to baseline Panel B (α=0.95, max_w=25%, rebal=4w, "
        "scenario_cap=260w, min_regime_scenarios=30)",
        "",
        "---",
        "",
        "## Performance Summary (gross, TC=0 bps)",
        "",
        "| Strategy | CAGR% | Vol% | Sharpe | MaxDD% | CVaR95w% | Calmar |",
        "|----------|-------|------|--------|--------|----------|--------|",
    ]
    for col in cols:
        m = g0.loc[col]
        lines.append(f"| {STRATEGY_LABELS[col]} | {m.CAGR_pct:.2f}% | {m.Vol_pct:.2f}% | "
                     f"{m.Sharpe:.3f} | {m.MaxDD_pct:.2f}% | {m.CVaR95_weekly_pct:.3f}% | "
                     f"{m.Calmar:.3f} |")

    lines += [
        "",
        "## Performance Summary (net, TC=10 bps)",
        "",
        "| Strategy | CAGR% | Vol% | Sharpe | MaxDD% | Ann. Turnover% |",
        "|----------|-------|------|--------|--------|----------------|",
    ]
    for col in cols:
        m = g10.loc[col]
        lines.append(f"| {STRATEGY_LABELS[col]} | {m.CAGR_pct:.2f}% | {m.Vol_pct:.2f}% | "
                     f"{m.Sharpe:.3f} | {m.MaxDD_pct:.2f}% | {m.ann_to_pct:.1f}% |")

    lines += [
        "",
        "## TC Sensitivity (Sharpe by cost assumption)",
        "",
        "| Strategy | Ann. TO% | Sharpe@0bps | Sharpe@5bps | Sharpe@10bps | Sharpe@25bps |",
        "|----------|----------|-------------|-------------|--------------|--------------|",
    ]
    for col in cols:
        to_c = mdf[mdf["tc_bps"] == 0].set_index("strategy").loc[col, "ann_to_pct"]
        sharpes = []
        for tc in [0, 5, 10, 25]:
            g = mdf[mdf["tc_bps"] == tc].set_index("strategy")
            sharpes.append(f"{g.loc[col, 'Sharpe']:.3f}")
        lines.append(f"| {STRATEGY_LABELS[col]} | {to_c:.1f}% | {' | '.join(sharpes)} |")

    lines += [
        "",
        "## Notes",
        "",
        "- Italy_GovtBond uses RIC `.FTIT_TSYUSDT` — denomination ambiguous; "
        "included after cross-validation against Germany vol ratio (1.62×) and "
        "2011 Eurozone crisis behaviour. Verify before paper submission.",
        "- HMM walk-forward labels are identical to baseline Panel B — the FI-expanded "
        "universe introduces new portfolio opportunities without changing regime detection.",
        "- Regime CVaR-A hard-filters scenarios to the current regime; Weighted CVaR "
        "applies HMM posterior importance weights across all scenarios.",
        "",
    ]

    (out_dir / "panel_b_summary_fi_expanded.md").write_text("\n".join(lines), encoding="utf-8")
    log.info("Wrote panel_b_summary_fi_expanded.md")


if __name__ == "__main__":
    main()
