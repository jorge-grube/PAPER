# CSV Output Audit

**Audit date:** 2026-05-12
**Files inspected:** 58 active CSVs (excluding archive).

The companion file `csv_table_source_map.md` maps every paper Table/Figure to its source CSV.

---

## 1. Active CSV inventory by directory

### 1.1 `reports/panels/` (canonical Panel A/B)
| File | Rows × Cols | Verdict |
|------|------------:|---------|
| `panel_a_long_horizon_performance.csv` | 16 × 15 (4 strategies × 4 TC levels) | ✓ |
| `panel_b_regime_oos_performance.csv` | 24 × 15 (6 × 4) | ✓ |
| `panel_b_regime_oos_tc_sensitivity.csv` | 24 × 9 | ✓ |
| `panel_a_statistical_tests.csv` | 4 × 10 | ✓ |
| `panel_b_statistical_tests.csv` | 6 × 10 | ✓ |
| `panel_b_regime_oos_performance_hicp_lag6.csv` | 24 × 14 (no RF_ann_pct col) | ✓ |
| `panel_b_regime_oos_tc_sensitivity_hicp_lag6.csv` | 6 × 6 | ✓ |

### 1.2 `reports/fi_expanded/`
| File | Notes |
|------|-------|
| `panel_a_performance_fi_expanded.csv` | 16 rows; adds `universe=fi_expanded` column |
| `panel_b_performance_fi_expanded.csv` | 28 rows (6 standard strategies × 4 TCs + 4 rows for `regime_constrained`) |
| `panel_b_tc_sensitivity_fi_expanded.csv` | 7 rows |
| `return_summary_fi_expanded.csv` | 14 rows |
| `series_coverage_fi_expanded.csv` | 14 rows |
| `correlation_matrix_fi_expanded.csv` | 14×14 correlation |

### 1.3 `reports/model_improvement/` family
| File | Verdict |
|------|---------|
| `panel_b_performance_zew_swap.csv` | ✓ 24 rows |
| `panel_b_tc_sensitivity_zew_swap.csv` | ✓ |
| `rebalance_frequency/rebalance_frequency_performance.csv` | ✓ (2/4/8 wk × 2 specs × 6 strat × 4 TC) |
| `rebalance_frequency/rebalance_frequency_tc_sensitivity.csv` | ✓ |
| `rebalance_frequency/rebalance_frequency_crisis_windows.csv` | ✓ |
| `turnover_smoothing/zew_smooth50_performance.csv` | ✓ |
| `turnover_smoothing/zew_smooth50_tc_sensitivity.csv` | ✓ |
| `tc_aware_cvar/performance.csv` | ✓ (5 strat × 7 variant × 4 TC = 140 rows) |
| `tc_aware_cvar/tc_sensitivity.csv` | ✓ |
| `tc_aware_cvar/turnover_summary.csv` | ✓ |
| `regime_constraints/performance.csv` | ✓ Includes `rc_baseline`, `rc_zew` rows |
| `regime_constraints/tc_sensitivity.csv` | ✓ |
| `regime_constraints/regime_average_weights.csv` | ✓ |
| `regime_constraints/crisis_window_performance.csv` | ✓ |

### 1.4 `paper/tables/`
| File | Verdict |
|------|---------|
| `appendix_f_descriptive_stats.csv` | ✓ 10 risky assets; mean, vol, skew, kurt, MaxDD, start, end |
| `appendix_f_correlations.csv` | ✓ 10×10 |

---

## 2. Value-level consistency checks

### 2.1 Headline values — paper vs CSV
*(See `headline_number_audit.md` for the full check.) All headline numbers in the paper match the CSV source values to the published precision.*

### 2.2 Decimal vs percentage convention
- All Sharpe ratios are stored as DECIMALS (e.g., 0.530, not 53.0).
- All CAGR / Vol / MaxDD / CVaR / turnover are stored as PERCENTAGES (e.g., 6.03 = 6.03%). Suffix `_pct` is universally used. ✓ Consistent.
- TC bps are integers (0, 5, 10, 25). ✓

### 2.3 Negative-sign character
Spot-checked CSVs for the U+2212 math-minus character; **none found** in any active CSV. All negative values use ASCII hyphen-minus (U+002D). ✓ Clean.

### 2.4 No duplicate strategy keys in any single CSV
Verified: each `(tc_bps, strategy)` pair is unique per CSV. ✓

### 2.5 Units verification
- All `weekly_to_pct` values are weekly TURNOVER in percent (not absolute). e.g. `0.4116` for Static CVaR is 0.41% per week. ✓
- All `ann_to_pct` values are `weekly_to_pct × 52`. ✓ (See `turnover_transaction_cost_audit.md`.)

### 2.6 NaN / missing values in CSVs
- `panel_a_statistical_tests.csv` line 1: equal_weight_risky row has empty `t_stat` and `p_value_one_sided`, which is correct (benchmark vs itself). ✓
- No other unexpected NaNs.

---

## 3. CSV-pair consistency

| CSV A | CSV B | Check | Result |
|-------|-------|-------|--------|
| `panel_b_regime_oos_performance.csv` | `panel_b_regime_oos_tc_sensitivity.csv` | Same Sharpe at each (strategy, tc_bps) | ✓ |
| `panel_b_regime_oos_performance.csv` | `panel_b_statistical_tests.csv` | Same gross Sharpe (0 bps) per strategy | ✓ |
| `panel_a_long_horizon_performance.csv` | `panel_a_statistical_tests.csv` | Same gross Sharpe per strategy | ✓ |
| `tc_aware_cvar/performance.csv` | `tc_aware_cvar/tc_sensitivity.csv` | Same Sharpe per (strategy, variant, tc) | ✓ |
| `regime_constraints/performance.csv` | `regime_constraints/tc_sensitivity.csv` | Same Sharpe per strategy and tc | ✓ |
| `panel_b_performance_zew_swap.csv` | `panel_b_tc_sensitivity_zew_swap.csv` | Same Sharpe per (strategy, tc) | ✓ |

---

## 4. Issues found

### P2 — `tc_aware_cvar/performance.csv` contains five strategies; the `static_cvar` rows are FULL-history-evaluated (n_weeks=807 versus Panel B's n=808). Same for `regime_constraints/performance.csv` (n_weeks=807). This is exactly the P1.4 scope difference documented in v8_correction_report.md and Table VII caption. Acceptable but should be flagged in column comments — currently CSVs have no scope tag distinguishing "label-intersected" from "full-history" Static CVaR.

### P2 — `regime_constraints/regime_average_weights.csv` has only 4 strategies (`rc_baseline`, `rc_zew`, `static_cvar`). Missing: the unconstrained naive `regime_cvar_A` and `weighted_cvar` average weights. If the paper or report ever wants to show "weights per regime for the naive variants", the data is not in this CSV.

### P3 — `fi_expanded/series_coverage_fi_expanded.csv` `Missing_pct` is fractional (e.g. 0.073 for 0.073%) but is unlabelled; the same column in `panel_*` CSVs uses different units. Cosmetic.

### P3 — `appendix_f_descriptive_stats.csv` uses string-formatted percentages (`"6.42"` rather than numeric `6.42`); makes downstream processing awkward.

### P3 — `panel_b_regime_oos_performance_hicp_lag6.csv` lacks an `RF_ann_pct` column. Other panel-B CSVs include it. Inconsistent schema.

---

## 5. Archive CSVs (should NOT be consumed by active scripts)

All under `reports/archive/`:
- `inventory.csv`, `inventory.md`, `missing_values_report.csv`, `frequency_report.csv`, `outlier_report.csv`, `series_coverage_report.csv`, `statistical_tests.csv/.md`, `cvar_backtest_summary.md`, `sample_coverage_table.csv`, `performance_gross_net.csv`, `transaction_cost_sensitivity.csv`, and `quality/*.csv` (7 files).

`reports/archive/statistical_tests.{csv,md}` is **STALE** and contains the OLD DM-test results referenced under the old methodology — it must not be consulted; `reports/panels/panel_{a,b}_statistical_tests.{csv,md}` are the active equivalents. The archive file is correctly archived but its existence is a contamination risk if a future glob picks it up (see `archive_contamination_audit.md`).
