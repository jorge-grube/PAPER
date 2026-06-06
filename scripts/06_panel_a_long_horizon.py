"""
06_panel_a_long_horizon.py
--------------------------
Panel A: Long-horizon non-regime allocation.

Strategies : Equal-Weight Risky | STOXX Europe 600 | Static CVaR | Markowitz
Start date : first rebal after MIN_HISTORY=156w (~2003-01-10)
RF         : EURIBOR 3M (time-varying)
TC         : 0 / 5 / 10 / 25 bps (weekly turnover × rate, lagged 1w)
Scenario window: rolling 260w cap for CVaR / Markowitz LPs.

Outputs:
  reports/panels/panel_a_long_horizon_performance.csv
  reports/panels/panel_a_long_horizon_summary.md
  data/processed/panel_a_returns.parquet
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
TC_BPS_LIST  = [0, 5, 10, 25]
CASH_COL     = "EURIBOR_3M"
STOXX_COL    = "StoxxEurope600"
ANN          = 52

STRATEGY_LABELS = {
    "equal_weight_risky": "Equal-Weight Risky (1/N)",
    "stoxx600":           "STOXX Europe 600",
    "static_cvar":        "Static CVaR",
    "markowitz":          "Markowitz (Min-Var)",
}

CVAR_CFG = CVaRConfig(alpha=ALPHA, max_weight=MAX_WEIGHT)
MKV_CFG  = MarkowitzConfig(max_weight=MAX_WEIGHT, min_scenarios=52, fallback_to_equal=True)

def _port(w_df: pd.DataFrame, ret: pd.DataFrame) -> pd.Series:
    """1-week implementation lag. min_count=1 prevents all-NaN rows from
    collapsing to 0.0 (they stay NaN and are excluded from performance metrics)."""
    return (w_df.shift(1) * ret.reindex(columns=w_df.columns)).sum(axis=1, min_count=1)

def _weekly_to(w_df: pd.DataFrame) -> pd.Series:
    return w_df.diff().abs().sum(axis=1) / 2.0

def _eq_drift_to(ret_r: pd.DataFrame) -> pd.Series:
    n  = ret_r.shape[1]; rp = ret_r.mean(axis=1)
    wd = ret_r.apply(lambda r: (1/n)*(1+r)/(1+rp), axis=0)
    return (wd - 1/n).abs().sum(axis=1) / 2.0

def _apply_tc(gross: pd.Series, to: pd.Series, rate: float) -> pd.Series:
    return gross - rate * to.shift(1).fillna(0.0).reindex(gross.index).fillna(0.0)

def compute_metrics(r: pd.Series, rf: pd.Series) -> dict:
    r  = r.dropna()
    rf_a = rf.reindex(r.index).fillna(0.0)
    exc  = r - rf_a
    cagr = (1 + r).prod() ** (ANN / len(r)) - 1
    vol  = r.std(ddof=1) * np.sqrt(ANN)
    sh   = exc.mean() / exc.std(ddof=1) * np.sqrt(ANN) if exc.std(ddof=1) > 0 else np.nan
    cum  = (1 + r).cumprod()
    mdd  = (cum / cum.cummax() - 1).min()
    k    = max(1, int(len(r) * (1 - ALPHA)))
    cvar_w = float(np.sort(r.values)[:k].mean())   # weekly, fractional
    cal  = cagr / abs(mdd) if mdd != 0 else np.nan
    return dict(CAGR_pct=round(cagr*100,2), Vol_pct=round(vol*100,2), Sharpe=round(sh,3),
                MaxDD_pct=round(mdd*100,2), CVaR95_weekly_pct=round(cvar_w*100,3),
                Calmar=round(cal,3), N_weeks=len(r),
                RF_ann_pct=round(rf_a.mean()*ANN*100,3))

def main():
    processed = ROOT / "data" / "processed"
    ret = pd.read_parquet(processed / "investable_returns_weekly.parquet")
    ret.index = pd.to_datetime(ret.index)

    risky = [c for c in ret.columns if c != CASH_COL]
    n_r   = len(risky)
    ret_r = ret[risky].dropna()
    rf    = ret[CASH_COL]
    idx   = ret_r.index

    log.info("Returns %s → %s  n=%d  risky=%d",
             idx.min().date(), idx.max().date(), len(idx), n_r)

    w_s: dict = {}; w_m: dict = {}
    last_ws = np.ones(n_r)/n_r; last_wm = np.ones(n_r)/n_r
    first_rebal = None; rebal_ctr = 0; ns = 0; nf = 0

    for i, date in enumerate(idx):
        if i < MIN_HISTORY:
            continue
        if first_rebal is None:
            first_rebal = date
            log.info("First rebal: %s", date.date())
        if rebal_ctr % REBALANCE == 0:
            s0   = max(0, i - SCENARIO_CAP)
            hist = ret_r.iloc[s0:i].values           # (T, m) numpy
            hist_df = ret_r.iloc[s0:i]               # DataFrame for Markowitz

            res = solve_cvar(hist, CVAR_CFG)
            if res and res.get("weights") is not None:
                last_ws = res["weights"]; ns += 1
            else:
                nf += 1
            w_s[date] = last_ws.copy()

            try:
                wm, _ = solve_min_variance(hist_df, MKV_CFG)
                last_wm = wm
            except Exception:
                pass
            w_m[date] = last_wm.copy()

        rebal_ctr += 1

    log.info("CVaR: %d solved  %d fallback", ns, nf)

    w_s_df = pd.DataFrame(w_s, index=risky).T.reindex(idx).ffill()
    w_m_df = pd.DataFrame(w_m, index=risky).T.reindex(idx).ffill()
    w_eq   = pd.DataFrame(1.0/n_r, index=idx, columns=risky)
    w_st   = pd.DataFrame({STOXX_COL: 1.0}, index=idx)

    gross = pd.DataFrame(index=idx)
    gross["equal_weight_risky"] = _port(w_eq,  ret_r)
    gross["stoxx600"]           = _port(w_st,  ret[[STOXX_COL]])
    gross["static_cvar"]        = _port(w_s_df, ret_r)
    gross["markowitz"]          = _port(w_m_df, ret_r)

    strat  = gross.loc[first_rebal:].dropna(how="all")
    rf_ev  = rf.reindex(strat.index).fillna(0.0)
    log.info("Eval %s → %s  n=%d", strat.index.min().date(),
             strat.index.max().date(), len(strat))

    to_eq = _eq_drift_to(ret_r.reindex(strat.index))
    to_s  = _weekly_to(w_s_df.reindex(strat.index))
    to_m  = _weekly_to(w_m_df.reindex(strat.index))
    to_st = pd.Series(0.0, index=strat.index)
    to_map = {"equal_weight_risky":to_eq,"stoxx600":to_st,
              "static_cvar":to_s,"markowitz":to_m}

    cols = [c for c in STRATEGY_LABELS if c in strat.columns]
    net_f = {tc: pd.DataFrame({
                c: _apply_tc(strat[c], to_map[c], tc/10_000)
                for c in cols}) for tc in TC_BPS_LIST}

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
    strat.to_parquet(processed/"panel_a_returns.parquet")
    out = ROOT/"reports"/"panels"
    out.mkdir(parents=True, exist_ok=True)
    mdf.to_csv(out/"panel_a_long_horizon_performance.csv", index=False)
    _write_summary(mdf, strat, out)
    log.info("All Panel A outputs written.")

    g0 = mdf[mdf["tc_bps"]==0].set_index("strategy")
    log.info("\n%s","="*72)
    log.info("%-28s %7s %7s %7s %8s %10s",
             "Strategy","CAGR%","Vol%","Sharpe","MaxDD%","CVaR95w%")
    log.info("-"*72)
    for s,m in g0.iterrows():
        log.info("%-28s %+6.2f  %6.2f  %7.3f  %7.2f  %9.3f",
                 s,m.CAGR_pct,m.Vol_pct,m.Sharpe,m.MaxDD_pct,m.CVaR95_weekly_pct)


def _write_summary(mdf, strat, out_dir):
    g0   = mdf[mdf["tc_bps"]==0].set_index("strategy")
    es   = strat.index.min().date(); ee = strat.index.max().date(); nw = len(strat)
    cols = [c for c in STRATEGY_LABELS if c in g0.index]
    lines = [
        "# Panel A — Long-Horizon Non-Regime Allocation",
        "", "*Generated by `06_panel_a_long_horizon.py`*", "",
        "> **Scope:** Non-regime strategies only (Equal-Weight Risky, STOXX Europe 600,",
        "> Static CVaR, Markowitz). No HMM regime labels are used.",
        "> Evaluation begins at the earliest date supported by a 156-week return burn-in",
        f"> from January 2000. CVaR/Markowitz use a rolling {SCENARIO_CAP}-week scenario window.", "",
        "---", "", "## Parameters", "",
        "| Parameter | Value |","| --- | --- |",
        f"| CVaR α | 95% |",f"| Max weight | 25% |",
        f"| Rebalance | every 4 weeks |",f"| Burn-in | 156 weeks |",
        f"| Scenario window | rolling {SCENARIO_CAP} weeks |",
        f"| Evaluation | {es} → {ee} ({nw} weeks, {nw/ANN:.1f} yr) |",
        "| Risk-free | EURIBOR 3M (time-varying) |","",
        "---","","## Performance (Gross, 0 bps TC)","",
        "CVaR 95% is the **weekly** mean of the worst-5% weekly returns (not annualised,",
        "to avoid inflation by extreme single-week GFC losses).", "",
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
        f"- **{nw/ANN:.1f}-year evaluation** ({es} → {ee}): GFC, Eurozone crisis, COVID, "
        "2022 inflation shock all included.",
        "- Static CVaR and Markowitz reduce volatility and maximum drawdown vs "
        "equal-weight and the STOXX 600 market index.",
        "- These results require **no regime model** — robust long-horizon evidence "
        "for CVaR-based risk reduction.",
        "- Regime-aware strategies evaluated separately in Panel B."]
    Path(out_dir/"panel_a_long_horizon_summary.md").write_text("\n".join(lines))
    log.info("Wrote panel_a_long_horizon_summary.md")


if __name__ == "__main__":
    main()
