# European Multi-Asset Regime-Aware CVaR Allocation

A reproducible empirical study of CVaR-based tail-risk control and HMM regime
conditioning in European multi-asset portfolios.

---

## Research Question

Does a regime-aware CVaR allocation framework improve downside protection and
out-of-sample risk-adjusted performance versus equal-weight, market-index, and
static CVaR benchmarks in European multi-asset portfolios over the period
2003–2026?

---

## Supported Conclusion

**Static CVaR provides robust European multi-asset tail-risk control** versus
equal-weight and market benchmarks over a 23-year evaluation window (Panel A,
2003–2026).

**HMM regime conditioning adds interpretable market-state structure** but does
**not** deliver statistically significant out-of-sample outperformance over
Static CVaR (Panel B, 2010–2026). Naive regime-filtered CVaR strategies exhibit
substantially higher turnover (~225% annually), while implementation-aware
variants reduce turnover materially but still do not overturn Static CVaR as
the most robust benchmark.

## Unsupported Conclusion

Regime-aware CVaR **beats** Static CVaR or generates robust, statistically
significant alpha. Bootstrap confidence intervals for Sharpe differentials span
±0.3–0.5 units; no pairwise difference is significant at the 95% level.

---

## Investable Universe

Eleven assets — ten risky, one risk-free:

- **European equities (6):** CAC 40, DAX, EuroStoxx 50, FTSE MIB, IBEX 35, STOXX Europe 600
- **Listed real estate (1):** FTSE EPRA/NAREIT Europe
- **Commodities (1):** Bloomberg Commodity Index
- **Energy (1):** Brent crude oil
- **Precious metals (1):** Gold
- **Risk-free / cash proxy:** EURIBOR 3M (annualised rate → weekly simple return)

Returns are **weekly simple (arithmetic)** throughout. EURIBOR is converted to
a weekly simple return via $(1+r_{ann})^{1/52} - 1$ and treated as a cash
holding, not an investable risky asset.

**Robustness appendix:** a 14-asset FI-expanded universe adds Germany, Spain, and
Italy government bond total return indices (FTSE Russell, EUR). See `reports/fi_expanded/`.

---

## Panel Architecture

### Panel A — Long-horizon non-regime evidence

| Parameter | Value |
| --- | --- |
| Strategies | Equal-Weight Risky (1/N), STOXX Europe 600, Static CVaR, Markowitz (Min-Var) |
| Evaluation window | 2003-01-10 → 2026-04-03 (1,213 weeks, 23.3 yr) |
| HMM used? | No |
| Script | `scripts/06_panel_a_long_horizon.py` |

Panel A establishes long-horizon evidence for CVaR-based risk reduction across
the GFC, Eurozone debt crisis, COVID crash, and 2022 inflation shock.

### Panel B — Fully OOS regime-aware evidence

| Parameter | Value |
| --- | --- |
| Strategies | Panel A strategies + Regime CVaR-A + Weighted CVaR |
| Evaluation window | 2010-10-15 → 2026-04-03 (808 weeks, 15.5 yr) |
| HMM states | 4 (ordered by ascending z52\_VIX mean) |
| HMM features | 8 z-score macro-financial features |
| HMM MIN\_TRAIN\_OBS | 156 weeks (3 yr) — walk-forward, strictly OOS |
| Script | `scripts/07_panel_b_regime_oos.py` |

All HMM market-state labels in Panel B are strictly out-of-sample (walk-forward
expanding window, no look-ahead). HMM states are statistical classifications
interpreted ex post from feature means — not asserted true economic regimes.
Heuristic labels: **Risk-on / Expansion**, **Low-vol / Subdued**, **Neutral / Moderate**,
**Elevated-risk / Stress** (and **Acute-stress / Flight-to-quality** in extreme episodes).

> **Full-sample HMM warning:** `data/processed/regime_labels_full.parquet`
> contains in-sample HMM labels fit to the entire dataset. These are used
> **only** for the descriptive regime timeline figure (Figure 1) and are
> **never** used in any OOS performance calculation.

---

## HICP Lag-6 Robustness Check

HICP inflation data is published ~17 days after the reference month ends.
If LSEG timestamps reflect the reference period rather than the release date,
the HMM sees up to 5–7 weeks of look-ahead in the `hicp_headline_core_gap`
feature.

`scripts/10_hicp_lag6_robustness.py` applies a conservative 6-week lag to
this feature before HMM fitting and reruns Panel B. Results use the
`_hicp_lag6` suffix and never overwrite baseline Panel B outputs.

Key finding: label agreement between baseline and lag-6 is ~55%, confirming
HICP timing is a meaningful assumption. Regime CVaR-A Sharpe changes by up to
+0.068 (within bootstrap noise), but the central conclusion is unchanged.

See `reports/regimes/hicp_lag6_robustness.md` and `reports/regimes/macro_release_date_risk_audit.md`.

---

## Canonical Run Order

See **[`docs/RUN_ORDER.md`](docs/RUN_ORDER.md)** for the complete stage-by-stage
run order with declared inputs, outputs, and notes.

Quick summary:

```bash
# Stage 1 — data pipeline
python scripts/01_validate_and_build_dataset.py

# Stage 2 — walk-forward HMM (canonical regime labels)
python scripts/02_hmm_walkforward_156.py

# Stage 3 — Panel A
python scripts/06_panel_a_long_horizon.py

# Stage 4 — Panel B
python scripts/07_panel_b_regime_oos.py

# Stage 5 — statistical tests
python scripts/08_panel_statistical_tests.py

# Stage 6 — descriptive figure
python scripts/09_regime_timeline_figure.py

# Stage 7 — robustness (independent, any order)
python scripts/10_hicp_lag6_robustness.py
python scripts/11_zew_swap_experiment.py
# ... scripts 12–15

# Stage 8 — FI-expanded universe (appendix)
python scripts/16_fi_expanded_universe.py
python scripts/17_panel_a_fi_expanded.py
python scripts/18_panel_b_fi_expanded.py
```

---

## Active Outputs

### Main paper tables and figures

| File | Stage | Description |
| --- | --- | --- |
| `reports/panels/panel_a_long_horizon_performance.csv` | 3 | Panel A full metrics |
| `reports/panels/panel_a_long_horizon_summary.md` | 3 | Panel A summary |
| `reports/panels/panel_a_statistical_tests.csv/.md` | 5 | Panel A HAC/NW tests + block-bootstrap Sharpe CIs |
| `reports/panels/panel_b_regime_oos_performance.csv` | 4 | Panel B full metrics |
| `reports/panels/panel_b_regime_oos_summary.md` | 4 | Panel B summary |
| `reports/panels/panel_b_regime_oos_tc_sensitivity.csv` | 4 | Panel B TC table |
| `reports/panels/panel_b_statistical_tests.csv/.md` | 5 | Panel B HAC/NW tests + block-bootstrap Sharpe CIs |
| `reports/figures/full_sample_regime_timeline.png` | 6 | Figure 1 (descriptive) |

### Robustness and supporting reports

| File | Description |
| --- | --- |
| `reports/panels/panel_b_regime_oos_summary_hicp_lag6.md` | Panel B HICP-lag6 robustness |
| `reports/regimes/hicp_lag6_robustness.md` | HICP lag-6 comparison |
| `reports/regimes/macro_release_date_risk_audit.md` | Look-ahead risk classification |
| `reports/final/model_backtest_summary.md` | Unified two-panel narrative |
| `reports/fi_expanded/fi_expanded_comparison.md` | FI-expanded robustness analysis |

### Documentation

| File | Description |
| --- | --- |
| `docs/RUN_ORDER.md` | Authoritative execution sequence |
| `docs/METHODOLOGY.md` | Model and data methodology reference |
| `docs/REPO_STRUCTURE.md` | Directory map |
| `docs/ACTIVE_OUTPUTS.md` | Live vs. archived file index |
| `data/README_DATA.md` | Data dictionary |

---

## Proprietary Data Notice

Raw source files under `data/raw/` are sourced from LSEG Refinitiv
Eikon/Workspace. They are subject to LSEG's standard data licensing terms and
are **not public-shareable** without explicit license verification. Do not
commit raw LSEG files to public repositories.

Processed parquets in `data/processed/` are derived outputs and should be
treated with equivalent care.

---

## Archive

Legacy Gen 1 scripts (PASO 3–4 prototypes), superseded intermediate outputs,
and stale reports have been moved to `scripts/archive/`, `reports/archive/`,
`data/processed/archive/`, and `docs/archive/`. Do not use these files for
paper writing. See `docs/ACTIVE_OUTPUTS.md` for the full classification.

---

## Environment

```bash
pip install -r requirements.txt
```

Python 3.10+. Key dependencies: `pandas`, `numpy`, `scipy`, `hmmlearn`,
`scikit-learn`, `matplotlib`, `openpyxl`, `pyarrow`.
