"""
08_panel_statistical_tests.py
------------------------------
Formal statistical tests for Panel A (long-horizon, 2003–2026) and
Panel B (regime OOS, 2010–2026) separately.

Tests per panel:
  1. Pairwise HAC/Newey-West test of mean excess-return differentials (lag=13 weeks)
     - All strategies vs equal_weight_risky (one-sided: H1: strat > bench)
  2. Block-bootstrap 95% CI for Sharpe ratios
     - Block = 13 weeks, n_boot = 5_000, seed = 42

Outputs:
  reports/panels/panel_a_statistical_tests.md
  reports/panels/panel_b_statistical_tests.md
  reports/panels/panel_a_statistical_tests.csv
  reports/panels/panel_b_statistical_tests.csv
"""

from __future__ import annotations
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import t as t_dist

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

# ── config ────────────────────────────────────────────────────────────────────
WEEKS_PER_YEAR = 52
HAC_LAG   = 13
BLOCK_LEN = 13
N_BOOT    = 5_000
SEED      = 42
CASH_COL  = "EURIBOR_3M"
BENCHMARK = "equal_weight_risky"

STRATEGY_LABELS = {
    "equal_weight_risky": "Equal-Weight Risky (1/N)",
    "stoxx600":           "STOXX Europe 600",
    "static_cvar":        "Static CVaR",
    "markowitz":          "Markowitz (Min-Var)",
    "regime_cvar_A":      "Regime CVaR-A",
    "weighted_cvar":      "Weighted CVaR",
}

# ── stats helpers ─────────────────────────────────────────────────────────────
def newey_west_se(x: np.ndarray, lag: int) -> float:
    n = len(x)
    x_dm = x - x.mean()
    nw_var = np.dot(x_dm, x_dm) / n
    for k in range(1, lag + 1):
        gamma_k = np.dot(x_dm[k:], x_dm[:-k]) / n
        nw_var += 2.0 * (1.0 - k / (lag + 1.0)) * gamma_k
    return float(np.sqrt(max(nw_var, 0.0) / n))


def hac_nw_test(strat_excess: np.ndarray, bench_excess: np.ndarray, lag: int = HAC_LAG):
    d = strat_excess - bench_excess
    mean_d = d.mean()
    se = newey_west_se(d, lag)
    if se == 0.0:
        return float(mean_d), np.nan, np.nan
    t_stat = mean_d / se
    p_one = float(t_dist.sf(t_stat, df=len(d) - 1))
    return float(mean_d), float(t_stat), p_one


def block_bootstrap_sharpe(
    excess: np.ndarray,
    block: int = BLOCK_LEN,
    n_boot: int = N_BOOT,
    seed: int = SEED,
):
    rng = np.random.default_rng(seed)
    n   = len(excess)
    ann = np.sqrt(WEEKS_PER_YEAR)
    sd  = excess.std(ddof=1)
    point = excess.mean() / sd * ann if sd > 0 else np.nan

    n_blocks = int(np.ceil(n / block))
    boot_sharpes = []
    for _ in range(n_boot):
        starts = rng.integers(0, n, size=n_blocks)
        idx    = np.concatenate([np.arange(s, s + block) % n for s in starts])[:n]
        sample = excess[idx]
        sd_b   = sample.std(ddof=1)
        if sd_b > 0:
            boot_sharpes.append(sample.mean() / sd_b * ann)
    boot_arr = np.array(boot_sharpes)
    return (
        float(point),
        float(np.percentile(boot_arr, 2.5)),
        float(np.percentile(boot_arr, 97.5)),
    )


# ── per-panel runner ──────────────────────────────────────────────────────────
def run_panel(
    panel_name: str,
    ret_path: Path,
    rf_series: pd.Series,
    out_dir: Path,
    panel_desc: str,
):
    if not ret_path.exists():
        log.error("Missing %s", ret_path)
        return

    strat = pd.read_parquet(ret_path)
    strat.index = pd.to_datetime(strat.index)
    n_obs = len(strat)
    date_range = f"{strat.index[0].date()} → {strat.index[-1].date()}"
    years = n_obs / WEEKS_PER_YEAR

    log.info(
        "=== %s | %d obs (%.1f yr) | %s ===",
        panel_name, n_obs, years, date_range
    )

    cols = [c for c in STRATEGY_LABELS if c in strat.columns]
    log.info("Strategies: %s", cols)

    rf = rf_series.reindex(strat.index).fillna(0.0)
    bench_excess = (strat[BENCHMARK] - rf).values

    # ── HAC/NW tests ──────────────────────────────────────────────────────────
    dm_rows = []
    for col in cols:
        if col == BENCHMARK:
            dm_rows.append({
                "strategy": col,
                "label": STRATEGY_LABELS[col],
                "mean_excess_diff_ann_pct": 0.0,
                "t_stat": np.nan,
                "p_value_one_sided": np.nan,
                "significance": "—",
            })
            continue
        s   = strat[col].dropna()
        rf_s = rf.reindex(s.index).fillna(0.0)
        se  = (s - rf_s).values
        n   = min(len(se), len(bench_excess))
        mean_d, t_stat, p_val = hac_nw_test(se[-n:], bench_excess[-n:])
        ann_diff_pct = mean_d * WEEKS_PER_YEAR * 100
        sig = (
            "***" if (not np.isnan(p_val) and p_val < 0.01) else
            "**"  if (not np.isnan(p_val) and p_val < 0.05) else
            "*"   if (not np.isnan(p_val) and p_val < 0.10) else ""
        )
        dm_rows.append({
            "strategy": col,
            "label": STRATEGY_LABELS[col],
            "mean_excess_diff_ann_pct": round(ann_diff_pct, 3),
            "t_stat": round(t_stat, 3) if not np.isnan(t_stat) else np.nan,
            "p_value_one_sided": round(p_val, 4) if not np.isnan(p_val) else np.nan,
            "significance": sig,
        })
        log.info(
            "HAC %-28s  diff=%+.2f%%  t=%6.3f  p=%.4f  %s",
            col, ann_diff_pct,
            t_stat if not np.isnan(t_stat) else 0.0,
            p_val  if not np.isnan(p_val)  else 1.0,
            sig,
        )

    dm_df = pd.DataFrame(dm_rows)

    # ── block-bootstrap Sharpe CIs ────────────────────────────────────────────
    boot_rows = []
    for col in cols:
        s   = strat[col].dropna()
        rf_s = rf.reindex(s.index).fillna(0.0)
        exc = (s - rf_s).values
        pt, lo, hi = block_bootstrap_sharpe(exc)
        boot_rows.append({
            "strategy": col,
            "label": STRATEGY_LABELS[col],
            "sharpe_point": round(pt, 3),
            "ci_lo_95": round(lo, 3),
            "ci_hi_95": round(hi, 3),
            "ci_width":  round(hi - lo, 3),
        })
        log.info(
            "Boot %-28s  Sharpe=%.3f  95%%CI=[%.3f, %.3f]", col, pt, lo, hi
        )

    boot_df = pd.DataFrame(boot_rows)

    # ── merged CSV ────────────────────────────────────────────────────────────
    merged = boot_df.merge(
        dm_df[["strategy", "mean_excess_diff_ann_pct", "t_stat",
               "p_value_one_sided", "significance"]],
        on="strategy",
        how="left",
    )
    slug = panel_name.lower().replace(" ", "_")
    csv_path = out_dir / f"{slug}_statistical_tests.csv"
    merged.to_csv(csv_path, index=False)
    log.info("Wrote %s", csv_path)

    # ── markdown ──────────────────────────────────────────────────────────────
    _write_md(
        panel_name, panel_desc, date_range, n_obs, years,
        dm_df, boot_df, out_dir, slug
    )


def _write_md(
    panel_name: str,
    panel_desc: str,
    date_range: str,
    n_obs: int,
    years: float,
    dm_df: pd.DataFrame,
    boot_df: pd.DataFrame,
    out_dir: Path,
    slug: str,
):
    bench_label = STRATEGY_LABELS[BENCHMARK]
    lines = [
        f"# Statistical Tests — {panel_name}",
        "",
        f"*Generated by `08_panel_statistical_tests.py`*",
        "",
        f"**Evaluation window:** {date_range} ({n_obs} weekly obs, {years:.1f} years)",
        f"**Panel description:** {panel_desc}",
        "",
        "---",
        "",
        "## 1  Pairwise HAC/Newey-West Tests of Mean Excess-Return Differentials",
        "",
        f"One-sided HAC t-test (Newey-West lag = {HAC_LAG} weeks) on weekly "
        f"excess-return differentials (strategy minus benchmark).",
        f"Benchmark: **{bench_label}**.",
        "H₀: mean differential ≤ 0. H₁: strategy mean excess return > benchmark (one-sided).",
        "Significance: \\* p<0.10 &nbsp; \\*\\* p<0.05 &nbsp; \\*\\*\\* p<0.01",
        "",
        "| Strategy | Ann. Diff vs Benchmark | t-stat | p (one-sided) | Sig |",
        "| --- | ---: | ---: | ---: | :---: |",
    ]
    for _, r in dm_df.iterrows():
        if r["strategy"] == BENCHMARK:
            lines.append(f"| {r['label']} *(benchmark)* | — | — | — | — |")
            continue
        t   = r["t_stat"]
        p   = r["p_value_one_sided"]
        sig = r["significance"]
        diff = r["mean_excess_diff_ann_pct"]
        t_str = f"{t:.3f}" if not (isinstance(t, float) and np.isnan(t)) else "—"
        p_str = f"{p:.4f}" if not (isinstance(p, float) and np.isnan(p)) else "—"
        lines.append(
            f"| {r['label']} | {diff:+.2f}% | {t_str} | {p_str} | {sig} |"
        )

    lines += [
        "",
        "---",
        "",
        "## 2  Block-Bootstrap Sharpe Ratio Confidence Intervals",
        "",
        f"Circular block bootstrap: block = {BLOCK_LEN} weeks, "
        f"n_boot = {N_BOOT:,}, seed = {SEED}.",
        "Sharpe = mean(r − EURIBOR) / std(r − EURIBOR) × √52.",
        "",
        "| Strategy | Sharpe | 95% CI lower | 95% CI upper | CI width |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for _, r in boot_df.iterrows():
        lines.append(
            f"| {r['label']} | {r['sharpe_point']:.3f} | "
            f"{r['ci_lo_95']:.3f} | {r['ci_hi_95']:.3f} | {r['ci_width']:.3f} |"
        )

    n_strats = len(boot_df)
    lines += [
        "",
        "---",
        "",
        "## 3  Interpretation",
        "",
        "A strategy whose 95% CI clearly excludes zero provides evidence of a reliably "
        "positive risk-adjusted return over the evaluation window. "
        "When the lower bound is close to (but just above) zero, the evidence is marginal.",
        "Overlapping CIs between two strategies indicate their Sharpe difference "
        "is not statistically distinguishable at the 95% level.",
        "",
        f"**Degrees-of-freedom caveat:** With {n_obs} weekly observations and "
        f"HAC lag = {HAC_LAG}, effective degrees of freedom are substantially "
        "lower than nominal. Results should be interpreted as indicative rather "
        "than conclusive; even multi-year backtests are typically underpowered "
        "to detect realistic alpha differences between portfolio strategies.",
        "",
        "Block-bootstrap CIs account for return autocorrelation and fat tails "
        "automatically without distributional assumptions.",
    ]

    md_path = out_dir / f"{slug}_statistical_tests.md"
    md_path.write_text("\n".join(lines))
    log.info("Wrote %s", md_path)


# ── main ──────────────────────────────────────────────────────────────────────
def main():
    processed = ROOT / "data" / "processed"
    reports   = ROOT / "reports" / "panels"
    reports.mkdir(exist_ok=True)

    # Load RF series
    rf_full = pd.read_parquet(processed / "investable_returns_weekly.parquet")
    rf_full.index = pd.to_datetime(rf_full.index)
    rf_series = rf_full[CASH_COL]

    # Panel A
    run_panel(
        panel_name="Panel A",
        ret_path=processed / "panel_a_returns.parquet",
        rf_series=rf_series,
        out_dir=reports,
        panel_desc=(
            "Long-horizon non-regime strategies (Equal-Weight, STOXX 600, "
            "Static CVaR, Markowitz). No HMM required; starts 2003-01-10."
        ),
    )

    # Panel B
    run_panel(
        panel_name="Panel B",
        ret_path=processed / "panel_b_returns.parquet",
        rf_series=rf_series,
        out_dir=reports,
        panel_desc=(
            "Fully OOS regime-aware strategies including Regime CVaR-A and "
            "Weighted CVaR. HMM trained with MIN_TRAIN_OBS=156; starts 2010-10-15."
        ),
    )

    log.info("All panels done.")


if __name__ == "__main__":
    main()
