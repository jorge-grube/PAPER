# Python Dependency Map

**Audit date:** 2026-05-12

Per-script inputs/outputs and the active dependency graph.

---

## 1. DAG (active pipeline)

```
        raw xlsx (data/raw, data/investable_assets, data/regime_variables)
                 │
        ┌────────▼──────────────┐
        │ 01_validate_and_build │  ──► metadata.yaml, investable_*_weekly.parquet,
        └───────┬───────────────┘      regime_variables_weekly.parquet,
                │                       regime_features_weekly.parquet
                │
                ├──────────────────────────────────┐
                ▼                                  │
        ┌───────────────────────┐                  │
        │ 02_hmm_walkforward_156│                  │
        └───────┬───────────────┘                  │
                │ regime_labels_wf_156.parquet     │
                │ regime_probs_wf_156.parquet      │
                │                                  │
                ├──────────────┬──────────────┐    │
                ▼              ▼              ▼    ▼
       ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
       │ 06_panel_a  │ │ 07_panel_b  │ │ 09_figure_1 │ │ 10_hicp_lag6│
       └──────┬──────┘ └─────┬───────┘ └─────────────┘ └─────┬───────┘
              │              │                                │
              │              │                                │
       panel_a_returns  panel_b_returns                       │
              │              │                                │
              └──────┬───────┴────────────────────────────────┤
                     ▼                                        │
              ┌─────────────┐                                 │
              │08_stat_tests│                                 │
              └─────────────┘                                 │
                                                              │
                                          regime_features_weekly_hicp_lag6.parquet
                                          regime_labels_wf_156_hicp_lag6.parquet
                                          regime_probs_wf_156_hicp_lag6.parquet
                                          panel_b_regime_oos_*_hicp_lag6.csv/md

       ┌────────── parallel "robustness" branches ────────────┐
       │                                                       │
       │  11_zew_swap (uses regime_variables_weekly +          │
       │              regime_features_weekly)                  │
       │     ↓                                                 │
       │  → regime_features_weekly_zew_swap.parquet            │
       │  → regime_labels_wf_156_zew_swap.parquet              │
       │  → regime_probs_wf_156_zew_swap.parquet               │
       │                                                       │
       │  12_rebalance_freq  (reads zew_swap + baseline labels)│
       │  13_turnover_smooth (reads zew_swap labels)           │
       │  14_tc_aware_cvar   (reads baseline + zew_swap labels)│
       │  15_regime_constr   (reads baseline + zew_swap labels)│
       └───────────────────────────────────────────────────────┘

       ┌────────── FI-expanded branch ────────────────────────┐
       │ 16_fi_expanded_universe (reads raw FTSE bond xlsx +  │
       │   investable_prices_weekly.parquet + investable_     │
       │   returns_weekly.parquet)                            │
       │     ↓                                                 │
       │  → investable_{prices,returns}_weekly_fi_expanded.   │
       │    parquet                                            │
       │                                                       │
       │  17_panel_a_fi_expanded                              │
       │  18_panel_b_fi_expanded (also reads regime_labels_   │
       │                          wf_156.parquet, regime_probs)│
       └───────────────────────────────────────────────────────┘

       ┌────────── figure-generation ─────────────────────────┐
       │ 07_figures/generate_paper_figures.py                 │
       │   reads: panel_a_returns.parquet, panel_b_returns.   │
       │     parquet, panel_b_returns_fi_expanded.parquet,    │
       │     investable_returns_weekly.parquet                │
       │   writes: paper/figures/figure_{2..5}.png,           │
       │     paper/tables/appendix_f_*.csv                    │
       │   ⚠ HARDCODED SESSION PATH (see python_code_audit P1-A)│
       └───────────────────────────────────────────────────────┘

       ┌────────── paper build ───────────────────────────────┐
       │ paper/build_paper_v8.js                              │
       │   reads: paper/figures/figure_{1..5}.png             │
       │   writes: paper/drafts/paper_draft_JF_style_v8_      │
       │     FINAL_FOR_FEEDBACK.docx (and pdf via pandoc)     │
       │   ⚠ HARDCODED SESSION PATH (see python_code_audit P1-B)│
       └───────────────────────────────────────────────────────┘
```

## 2. Per-script inputs and outputs

### 01_validate_and_build_dataset.py
- Reads: raw xlsx (50+ files)
- Writes:
  - `data/processed/metadata.yaml`
  - `data/processed/investable_prices_weekly.parquet`
  - `data/processed/investable_returns_weekly.parquet`
  - `data/processed/regime_variables_weekly.parquet`
  - `data/processed/regime_features_weekly.parquet`
  - `reports/missing_values_report.csv`  *(intended in reports/, exists in reports/archive/)*
  - `reports/series_coverage_report.csv` *(same)*
  - `reports/outlier_report.csv` *(same)*
  - `reports/frequency_report.csv` *(same)*
  - `reports/data_validation_summary.md` *(same — currently in reports/data/ instead)*

### 02_hmm_walkforward_156.py
- Reads: `regime_features_weekly.parquet`
- Writes: `regime_labels_wf_156.parquet`, `regime_probs_wf_156.parquet`, `hmm_wf_checkpoint_156.pkl`

### 06_panel_a_long_horizon.py
- Reads: `investable_returns_weekly.parquet`
- Writes:
  - `data/processed/panel_a_returns.parquet`
  - `reports/panels/panel_a_long_horizon_performance.csv`
  - `reports/panels/panel_a_long_horizon_summary.md`

### 07_panel_b_regime_oos.py
- Reads: `investable_returns_weekly.parquet`, `regime_labels_wf_156.parquet`, `regime_probs_wf_156.parquet`
- Writes:
  - `data/processed/panel_b_returns.parquet`
  - `reports/panels/panel_b_regime_oos_performance.csv`
  - `reports/panels/panel_b_regime_oos_tc_sensitivity.csv`
  - `reports/panels/panel_b_regime_oos_summary.md`

### 08_panel_statistical_tests.py
- Reads: `panel_a_returns.parquet`, `panel_b_returns.parquet`, `investable_returns_weekly.parquet` (for EURIBOR rf)
- Writes:
  - `reports/panels/panel_a_statistical_tests.csv` / `.md`
  - `reports/panels/panel_b_statistical_tests.csv` / `.md`

### 09_regime_timeline_figure.py
- Reads: `regime_labels_full.parquet` (⚠ orphan — no active producer), `investable_returns_weekly.parquet`
- Writes: `reports/figures/full_sample_regime_timeline.png`
- (Then manually copied to `paper/figures/figure_1_regime_timeline.png` — binary-identical)

### 10_hicp_lag6_robustness.py
- Reads: `regime_features_weekly.parquet`, `investable_returns_weekly.parquet`, baseline `panel_b_regime_oos_performance.csv`, baseline `panel_b_regime_oos_tc_sensitivity.csv`
- Writes:
  - `data/processed/regime_features_weekly_hicp_lag6.parquet`
  - `data/processed/regime_labels_wf_156_hicp_lag6.parquet`
  - `data/processed/regime_probs_wf_156_hicp_lag6.parquet`
  - `data/processed/hmm_wf_checkpoint_156_hicp_lag6.pkl`
  - `reports/panels/panel_b_regime_oos_performance_hicp_lag6.csv`
  - `reports/panels/panel_b_regime_oos_tc_sensitivity_hicp_lag6.csv`
  - `reports/panels/panel_b_regime_oos_summary_hicp_lag6.md`
  - `reports/regimes/hicp_lag6_robustness.md`

### 11_zew_swap_experiment.py
- Reads: `regime_variables_weekly.parquet`, `regime_features_weekly.parquet`, `investable_returns_weekly.parquet`, baseline panel CSVs
- Writes (under `data/processed/model_improvement/` and `reports/model_improvement/`):
  - `regime_features_weekly_zew_swap.parquet`
  - `regime_labels_wf_156_zew_swap.parquet`
  - `regime_probs_wf_156_zew_swap.parquet`
  - `hmm_wf_checkpoint_156_zew_swap.pkl`
  - `panel_b_returns_zew_swap.parquet`
  - `reports/model_improvement/panel_b_performance_zew_swap.csv`, `panel_b_tc_sensitivity_zew_swap.csv`
  - `reports/model_improvement/panel_b_summary_zew_swap.md`
  - `reports/model_improvement/zew_swap_comparison.md`
  - `reports/model_improvement/zew_swap_statistical_tests.md`

### 12_rebalance_frequency_experiment.py
- Reads: baseline labels + ZEW-swap labels + investable returns
- Writes: `reports/model_improvement/rebalance_frequency/*` (md, csvs)
  and `data/processed/model_improvement/rebalance_frequency/perf_*.csv`, `crisis_*.csv`

### 13_turnover_smoothing_experiment.py
- Reads: ZEW-swap labels and probs, investable returns, baseline panel B perf CSV, RF perf CSV
- Writes: `reports/model_improvement/turnover_smoothing/*.csv`, `*_summary.md`, `*_recommendation.md`

### 14_tc_aware_cvar_experiment.py
- Reads: baseline + ZEW-swap labels/probs, investable returns
- Writes:
  - `data/processed/model_improvement/tc_aware_cvar/weights_{strategy}_{slug}.parquet` × 30+ files
  - `reports/model_improvement/tc_aware_cvar/performance.csv`
  - `reports/model_improvement/tc_aware_cvar/tc_sensitivity.csv`
  - `reports/model_improvement/tc_aware_cvar/turnover_summary.csv`
  - `reports/model_improvement/tc_aware_cvar/tc_aware_cvar_summary.md`

### 15_regime_constraints_experiment.py
- Reads: baseline + ZEW-swap labels, investable returns
- Writes:
  - `data/processed/model_improvement/regime_constraints/weights_rc_baseline.parquet`, `weights_rc_zew.parquet`
  - (Also reuses older `weights_regime_cvar_A.parquet`, `weights_weighted_cvar.parquet`, `weights_zew_*.parquet` from an earlier generation — see archive_contamination_audit.md)
  - `reports/model_improvement/regime_constraints/performance.csv`
  - `reports/model_improvement/regime_constraints/tc_sensitivity.csv`
  - `reports/model_improvement/regime_constraints/regime_average_weights.csv`
  - `reports/model_improvement/regime_constraints/crisis_window_performance.csv`
  - `reports/model_improvement/regime_constraints/regime_constraints_summary.md`

### 16_fi_expanded_universe.py
- Reads: `data/raw/fixed_income/*.xlsx`, baseline prices/returns parquets
- Writes:
  - `data/processed/investable_prices_weekly_fi_expanded.parquet`
  - `data/processed/investable_returns_weekly_fi_expanded.parquet`
  - `reports/fi_expanded/data_validation_fi_expanded.md`
  - `reports/fi_expanded/series_coverage_fi_expanded.csv`
  - `reports/fi_expanded/return_summary_fi_expanded.csv`
  - `reports/fi_expanded/correlation_matrix_fi_expanded.csv`
  - `reports/fi_expanded/fixed_income_file_validation.md`

### 17_panel_a_fi_expanded.py
- Reads: `investable_returns_weekly_fi_expanded.parquet`
- Writes:
  - `data/processed/panel_a_returns_fi_expanded.parquet`
  - `reports/fi_expanded/panel_a_performance_fi_expanded.csv`
  - `reports/fi_expanded/panel_a_summary_fi_expanded.md`

### 18_panel_b_fi_expanded.py
- Reads: `investable_returns_weekly_fi_expanded.parquet`, `regime_labels_wf_156.parquet`, `regime_probs_wf_156.parquet`
- Writes:
  - `data/processed/panel_b_returns_fi_expanded.parquet`
  - `reports/fi_expanded/panel_b_performance_fi_expanded.csv`
  - `reports/fi_expanded/panel_b_tc_sensitivity_fi_expanded.csv`
  - `reports/fi_expanded/panel_b_summary_fi_expanded.md`

### 07_figures/generate_paper_figures.py
- Reads (under hard-coded path):
  - `panel_b_returns.parquet`
  - `panel_b_returns_fi_expanded.parquet`
  - `investable_returns_weekly.parquet`
- Writes:
  - `paper/figures/figure_2_cumulative_wealth_panel_b.png`
  - `paper/figures/figure_3_turnover_vs_net_sharpe.png`
  - `paper/figures/figure_4_static_cvar_weights_baseline_vs_fi.png`
  - `paper/figures/figure_5_drawdown_baseline_vs_fi.png`
  - `paper/tables/appendix_f_descriptive_stats.csv`
  - `paper/tables/appendix_f_correlations.csv`

### paper/build_paper_v8.js
- Reads (under hard-coded path):
  - `paper/figures/figure_{1..5}.png`
  - Hard-coded numerical literals throughout the JS source.
- Writes: `paper/drafts/paper_draft_JF_style_v8_FINAL_FOR_FEEDBACK.docx` (and PDF via pandoc post-step).

## 3. Orphans (files in `data/processed/` not produced by any active script)

| File | Mtime | Likely producer | Active consumer | Verdict |
|------|-------|-----------------|-----------------|---------|
| `regime_dataset.parquet` (102 KB) | 2026-05-07 | archived `02_fit_hmm.py` via `src/models/hmm.run_hmm_pipeline` | None | Orphan; safe to archive. Used to be Stage-2 dump combining features + labels. |
| `regime_labels_full.parquet` (12 KB) | 2026-05-07 | same | `scripts/09_regime_timeline_figure.py` | ACTIVE consumer for Figure 1 (P1-C). Must be regenerated by an active script OR documented as static input. |
| `regime_variables_weekly.parquet` (180 KB) | 2026-05-08 | `01_validate_and_build_dataset.py` (via `build_regime_panel`) | `11_zew_swap_experiment.stage_features` (looks up ZEW column) | Active — used as **source for ZEW raw series**. |
