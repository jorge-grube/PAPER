# CSV Table → Paper Source Map

**Audit date:** 2026-05-12

Maps every active CSV to the paper Table / Figure that consumes it (if any).

| CSV | Producer script | Consumed by paper element |
|-----|-----------------|---------------------------|
| `reports/panels/panel_a_long_horizon_performance.csv` | scripts/06 | Table II (Panel A performance) |
| `reports/panels/panel_a_statistical_tests.csv` | scripts/08 | Table III (Panel A statistical tests) |
| `reports/panels/panel_b_regime_oos_performance.csv` | scripts/07 | Table IV (Panel B performance), Table V (turnover table) |
| `reports/panels/panel_b_regime_oos_tc_sensitivity.csv` | scripts/07 | Table V/VI (TC sensitivity), Figure 3 |
| `reports/panels/panel_b_statistical_tests.csv` | scripts/08 | Table VI (Panel B statistical tests) |
| `reports/panels/panel_b_regime_oos_performance_hicp_lag6.csv` | scripts/10 | Table IX row 1 (HICP-lag6 robustness) |
| `reports/panels/panel_b_regime_oos_tc_sensitivity_hicp_lag6.csv` | scripts/10 | Table IX row 1 |
| `reports/model_improvement/panel_b_performance_zew_swap.csv` | scripts/11 | Table IX row 2 (ZEW-swap) |
| `reports/model_improvement/panel_b_tc_sensitivity_zew_swap.csv` | scripts/11 | Table IX row 2 |
| `reports/model_improvement/zew_swap_statistical_tests.md` (no CSV) | scripts/11 | Section VII.B (text) |
| `reports/model_improvement/rebalance_frequency/rebalance_frequency_performance.csv` | scripts/12 | Section VII.C (text) |
| `reports/model_improvement/rebalance_frequency/rebalance_frequency_tc_sensitivity.csv` | scripts/12 | Section VII.C |
| `reports/model_improvement/rebalance_frequency/rebalance_frequency_crisis_windows.csv` | scripts/12 | Section VII.C |
| `reports/model_improvement/turnover_smoothing/zew_smooth50_performance.csv` | scripts/13 | Section VII.D (text) |
| `reports/model_improvement/turnover_smoothing/zew_smooth50_tc_sensitivity.csv` | scripts/13 | Section VII.D |
| `reports/model_improvement/tc_aware_cvar/performance.csv` | scripts/14 | Table VII upper block (TC-aware) |
| `reports/model_improvement/tc_aware_cvar/tc_sensitivity.csv` | scripts/14 | Table VII, Figure 3 (tau=0.10 data points) |
| `reports/model_improvement/tc_aware_cvar/turnover_summary.csv` | scripts/14 | Table VII (turnover column) |
| `reports/model_improvement/regime_constraints/performance.csv` | scripts/15 | Table VII lower block (RC-CVaR) |
| `reports/model_improvement/regime_constraints/tc_sensitivity.csv` | scripts/15 | Table VII |
| `reports/model_improvement/regime_constraints/regime_average_weights.csv` | scripts/15 | Appendix C (regime-conditional weights) |
| `reports/model_improvement/regime_constraints/crisis_window_performance.csv` | scripts/15 | Discussion text |
| `reports/fi_expanded/panel_a_performance_fi_expanded.csv` | scripts/17 | Table VIII upper (FI Panel A) |
| `reports/fi_expanded/panel_b_performance_fi_expanded.csv` | scripts/18 | Table VIII lower (FI Panel B), Figure 4 (avg weights), Figure 5 (drawdowns) |
| `reports/fi_expanded/panel_b_tc_sensitivity_fi_expanded.csv` | scripts/18 | Table VIII |
| `reports/fi_expanded/return_summary_fi_expanded.csv` | scripts/16 | Appendix F (FI summary stats) |
| `reports/fi_expanded/series_coverage_fi_expanded.csv` | scripts/16 | Appendix F |
| `reports/fi_expanded/correlation_matrix_fi_expanded.csv` | scripts/16 | Appendix F (FI correlations) |
| `paper/tables/appendix_f_descriptive_stats.csv` | scripts/07_figures (`descriptive_stats`) | Table F.1 |
| `paper/tables/appendix_f_correlations.csv` | scripts/07_figures (`descriptive_stats`) | Table F.2 |

## Tables NOT auto-generated (hard-coded in build_paper_v8.js)
- **Table I** (Asset universe summary). Values are static metadata. Cross-check `data/README_DATA.md` and METHODOLOGY.md against build_paper_v8.js.
- All TABLE values in `paper/build_paper_v8.js` are HARD-CODED Python-like lists. **There is no automated pipeline from CSV → paper.** Any rerun of any script that changes a number requires the JS source to be edited manually. This is the single largest reproducibility risk (see `reproducibility_audit.md`).
