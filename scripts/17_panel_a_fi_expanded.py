"""
Script 17 — Panel A (FI-Expanded Universe)
==========================================
Replicates Panel A (Equal-Weight, STOXX600, Static CVaR, Markowitz) on the
14-asset FI-expanded universe. Identical parameters to 06_panel_a_long_horizon.py.
Does NOT overwrite baseline Panel A outputs.

Outputs → reports/fi_expanded/
  panel_a_performance_fi_expanded.csv
  panel_a_summary_fi_expanded.md
  data/processed/panel_a_returns_fi_expanded.parquet
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

# ── Parameters (identical to 06_panel_a_long_horizon.py) ─────────────────────
ALPHA        = 0.95
MAX_WEIGHT   = 0.25
REBALANCE    = 4
MIN_HISTORY  = 156
SCENARIO_CAP = 260
TC_BPS_LIST  = [0, 5, 10, 25]
CASH_COL     = "EURIBOR_3M"
STOXX_COL    = "StoxxEurope600"
ANN          = 52

CVAR_CFG = CVaRConfig(alpha=ALPHA, max_weight=MAX_WEIGHT)
MKV_CFG  = MarkowitzConfig(max_weight=MAX_WEIGHT, min_scenarios=52, fallback_to_equal=True)

STRATEGY_LABELS = {
    "equal_weight_risky": "Equal-Weight Risky (1/N)",
    "stoxx600":           "STOXX Europe 600",
    "static_cvar":        "Static CVaR (FI-Exp)",
    "markowitz":          "Markowitz (FI-Exp)",
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
    r   = r.dropna()
    rf_a = rf.reindex(r.index).fillna(0.0)
    exc  = r - rf_a
    cagr = (1 + r).prod() ** (ANN / len(r)) - 1
    vol  = r.std(ddof=1) * np.sqrt(ANN)
    sh   = exc.mean() / exc.std(ddof=1) * np.sqrt(ANN) if exc.std(ddof=1) > 0 else np.nan
    cum  = (1 + r).cumprod()
    mdd  = (cum / cum.cummax() - 1).min()
    k    = max(1, int(len(r) * (1 - ALPHA)))
    cvar = -np.sort(r.values)[:k].mean()
    cal  = cagr / abs(mdd) if mdd != 0 else np.nan
    return dict(CAGR_pct=round(cagr*100,3), Vol_pct=round(vol*100,3),
                Sharpe=round(sh,4), MaxDD_pct=round(mdd*100,3),
                CVaR95_weekly_pct=round(cvar*100,4), Calmar=round(cal,3),
                N_weeks=len(r), RF_ann_pct=round(rf_a.mean()*ANN*100,3))


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    processed = ROOT / "data" / "processed"
    out_dir   = ROOT / "reports" / "fi_expanded"
    out_dir.mkdir(parents=True, exist_ok=True)

    ret = pd.read_parquet(processed / "investable_returns_weekly_fi_expanded.parquet")
    ret.index = pd.to_datetime(ret.index)

    risky = [c for c in ret.columns if c != CASH_COL]
    n_r   = len(risky)
    ret_r = ret[risky].dropna()
    rf    = ret[CASH_COL]
    idx   = ret_r.index

    log.info("FI-expanded returns: %s → %s  n=%d  risky=%d",
             idx.min().date(), idx.max().date(), len(idx), n_r)
    log.info("Risky assets: %s", risky)

    w_s = {}; w_m = {}
    last_ws = np.ones(n_r)/n_r; last_wm = np.ones(n_r)/n_r
    first_rebal = None; rebal_ctr = 0; ns = 0; nf = 0

    for i, date in enumerate(idx):
        if i < MIN_HISTORY:
            continue
        if first_rebal is None:
            first_rebal = date
            log.info("First rebal: %s", date.date())

        if rebal_ctr % REBALANCE == 0:
            s0      = max(0, i - SCENARIO_CAP)
            hist    = ret_r.iloc[s0:i].values
            hist_df = ret_r.iloc[s0:i]

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
    gross["equal_weight_risky"] = _port(w_eq,   ret_r)
    gross["stoxx600"]           = _port(w_st,   ret[[STOXX_COL]])
    gross["static_cvar"]        = _port(w_s_df, ret_r)
    gross["markowitz"]          = _port(w_m_df, ret_r)

    strat  = gross.loc[first_rebal:].dropna(how="all")
    rf_ev  = rf.reindex(strat.index).fillna(0.0)
    log.info("Eval: %s → %s  n=%d",
             strat.index.min().date(), strat.index.max().date(), len(strat))

    to_eq = _eq_drift_to(ret_r.reindex(strat.index))
    to_s  = _weekly_to(w_s_df.reindex(strat.index))
    to_m  = _weekly_to(w_m_df.reindex(strat.index))
    to_st = pd.Series(0.0, index=strat.index)
    to_map = {"equal_weight_risky": to_eq, "stoxx600": to_st,
              "static_cvar": to_s, "markowitz": to_m}

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
    strat.to_parquet(processed / "panel_a_returns_fi_expanded.parquet")
    mdf.to_csv(out_dir / "panel_a_performance_fi_expanded.csv", index=False)
    _write_summary(mdf, strat, out_dir, risky)
    log.info("Panel A (FI-expanded) outputs written.")

    g0 = mdf[mdf["tc_bps"] == 0].set_index("strategy")
    log.info("\n%s", "="*72)
    log.info("%-28s %7s %7s %7s %8s", "Strategy", "CAGR%", "Vol%", "Sharpe", "MaxDD%")
    log.info("-"*72)
    for s, m in g0.iterrows():
        log.info("%-28s %+6.2f  %6.2f  %7.3f  %7.2f",
                 s, m.CAGR_pct, m.Vol_pct, m.Sharpe, m.MaxDD_pct)


def _write_summary(mdf, strat, out_dir, risky):
    g0   = mdf[mdf["tc_bps"] == 0].set_index("strategy")
    g10  = mdf[mdf["tc_bps"] == 10].set_index("strategy")
    es   = strat.index.min().date()
    ee   = strat.index.max().date()
    nw   = len(strat)
    cols = [c for c in STRATEGY_LABELS if c in g0.index]

    new_fi = ["Germany_GovtBond", "Spain_GovtBond", "Italy_GovtBond"]
    fi_in_risky = [c for c in new_fi if c in risky]

    lines = [
        "# Panel A — FI-Expanded Universe",
        "",
        f"*Generated by `17_panel_a_fi_expanded.py`*",
        "",
        f"> **Universe:** 14 assets (11 baseline + {len(fi_in_risky)} government bond TR: "
        + ", ".join(fi_in_risky) + ")",
        f"> **Eval period:** {es} → {ee}  ({nw} weeks)",
        f"> **Parameters:** identical to baseline Panel A (α=0.95, max_w=25%, rebal=4w, "
        f"scenario_cap=260w)",
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
        "## TC Sensitivity",
        "",
        "| Strategy | Sharpe@0bps | Sharpe@5bps | Sharpe@10bps | Sharpe@25bps |",
        "|----------|-------------|-------------|--------------|--------------|",
    ]
    for col in cols:
        sharpes = []
        for tc in [0, 5, 10, 25]:
            g = mdf[mdf["tc_bps"] == tc].set_index("strategy")
            sharpes.append(f"{g.loc[col, 'Sharpe']:.3f}")
        lines.append(f"| {STRATEGY_LABELS[col]} | {' | '.join(sharpes)} |")

    lines += [
        "",
        "## Italy Currency Note",
        "",
        "Italy_GovtBond uses RIC `.FTIT_TSYUSDT` — denomination may be USD. "
        "Cross-validation against Germany vol ratio (1.62×, within EUR periphery range) "
        "and 2011 Eurozone crisis behaviour suggests EUR-equivalent; included with caveat.",
        "",
    ]

    (out_dir / "panel_a_summary_fi_expanded.md").write_text("\n".join(lines), encoding="utf-8")
    log.info("Wrote panel_a_summary_fi_expanded.md")


if __name__ == "__main__":
    main()
