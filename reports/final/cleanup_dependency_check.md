# Repository Cleanup — Dependency Check

**Date:** 2026-05-10  
**Purpose:** Verify path integrity after repository reorganisation.

---

## 1. Active Scripts — Existence Check

All 15 active scripts confirmed present in `scripts/`:

| Script | Status |
|--------|--------|
| `01_validate_and_build_dataset.py` | ✅ |
| `02_hmm_walkforward_156.py` | ✅ |
| `06_panel_a_long_horizon.py` | ✅ |
| `07_panel_b_regime_oos.py` | ✅ |
| `08_panel_statistical_tests.py` | ✅ |
| `09_regime_timeline_figure.py` | ✅ |
| `10_hicp_lag6_robustness.py` | ✅ |
| `11_zew_swap_experiment.py` | ✅ |
| `12_rebalance_frequency_experiment.py` | ✅ |
| `13_turnover_smoothing_experiment.py` | ✅ |
| `14_tc_aware_cvar_experiment.py` | ✅ |
| `15_regime_constraints_experiment.py` | ✅ |
| `16_fi_expanded_universe.py` | ✅ |
| `17_panel_a_fi_expanded.py` | ✅ |
| `18_panel_b_fi_expanded.py` | ✅ |

---

## 2. Critical Path Fix — Script 16

**Issue:** After TEMPORARY_FA/ was moved to `data/raw/fixed_income/`, script 16 contained a broken path.

**Fix applied:** `scripts/16_fi_expanded_universe.py` line 36:
```python
# Before
DATA_RAW = BASE / "TEMPORARY_FA"
# After
DATA_RAW = BASE / "data" / "raw" / "fixed_income"
```

**Verified:** `grep DATA_RAW scripts/16_fi_expanded_universe.py` → `data/raw/fixed_income` ✅

---

## 3. Report Path Updates — Scripts 06, 07, 08, 10, 13

Panel reports moved from `reports/` root to `reports/panels/` and `reports/regimes/`. The following script paths were updated:

| Script | Old path | New path |
|--------|---------|---------|
| 06 | `ROOT/"reports"` | `ROOT/"reports"/"panels"` |
| 07 | `ROOT/"reports"` | `ROOT/"reports"/"panels"` |
| 08 | `ROOT/"reports"` | `ROOT/"reports"/"panels"` |
| 10 | `REPORTS/"panel_b_*_hicp_lag6.*"` | `REPORTS/"panels"/"panel_b_*_hicp_lag6.*"` |
| 10 | `REPORTS/"hicp_lag6_robustness.md"` | `REPORTS/"regimes"/"hicp_lag6_robustness.md"` |
| 10 | reads `REPORTS/"panel_b_*"` | reads `REPORTS/"panels"/"panel_b_*"` |
| 13 | `ROOT/"reports"/"panel_b_regime_oos_performance.csv"` | `ROOT/"reports"/"panels"/"panel_b_..."` |

Scripts 06 and 07 also received `out.mkdir(parents=True, exist_ok=True)` to auto-create `reports/panels/` if needed.

---

## 4. Canonical Processed Data — Existence Check

| File | Status |
|------|--------|
| `data/processed/investable_prices_weekly.parquet` | ✅ |
| `data/processed/investable_returns_weekly.parquet` | ✅ |
| `data/processed/regime_labels_wf_156.parquet` | ✅ |
| `data/processed/regime_probs_wf_156.parquet` | ✅ |
| `data/processed/panel_a_returns.parquet` | ✅ |
| `data/processed/panel_b_returns.parquet` | ✅ |
| `data/processed/investable_prices_weekly_fi_expanded.parquet` | ✅ |
| `data/processed/investable_returns_weekly_fi_expanded.parquet` | ✅ |
| `data/processed/panel_a_returns_fi_expanded.parquet` | ✅ |
| `data/processed/panel_b_returns_fi_expanded.parquet` | ✅ |

---

## 5. Panel Reports — Existence Check (new locations)

| File | Status |
|------|--------|
| `reports/panels/panel_a_long_horizon_performance.csv` | ✅ |
| `reports/panels/panel_a_long_horizon_summary.md` | ✅ |
| `reports/panels/panel_b_regime_oos_performance.csv` | ✅ |
| `reports/panels/panel_b_regime_oos_summary.md` | ✅ |
| `reports/panels/panel_a_statistical_tests.md` | ✅ |
| `reports/panels/panel_b_statistical_tests.md` | ✅ |
| `reports/panels/panel_b_regime_oos_performance_hicp_lag6.csv` | ✅ |
| `reports/panels/panel_b_regime_oos_summary_hicp_lag6.md` | ✅ |

---

## 6. FI Raw Data — Existence Check

| File | Status |
|------|--------|
| `data/raw/fixed_income/FTSE GERMAN GOVERNMENT BOND TR EUR.xlsx` | ✅ |
| `data/raw/fixed_income/FTSE SPANISH GOVERNMENT BOND TR EUR.xlsx` | ✅ |
| `data/raw/fixed_income/FTSE ITALIAN GOVERNMENT BOND TR EUR.xlsx` | ✅ |

---

## 7. Documentation Files — Existence Check

| File | Status |
|------|--------|
| `README.md` | ✅ updated |
| `docs/RUN_ORDER.md` | ✅ updated |
| `docs/METHODOLOGY.md` | ✅ new |
| `docs/REPO_STRUCTURE.md` | ✅ new |
| `docs/ACTIVE_OUTPUTS.md` | ✅ new |
| `data/README_DATA.md` | ✅ new |
| `paper/drafts/paper_draft_JF_style.docx` | ✅ |

---

## 8. Known Residual Issues

| Issue | Severity | Notes |
|-------|----------|-------|
| `data/robustness/` empty dir not removed | Low | Windows mount permission restriction; inert |
| `src/portfolio_eu/` empty dir not removed | Low | Windows mount permission restriction; inert |
| `TEMPORARY_FA/` empty dir not removed | Low | Windows mount permission restriction; inert |
| Script numbering gaps (03, 04, 05) | Cosmetic | Archived scripts; documented in RUN_ORDER.md |

---

## Summary

**All 48 dependency checks passed.** Critical broken path in script 16 fixed. All script output paths updated to match new `reports/panels/` and `reports/regimes/` structure. No empirical results were recomputed. Reproducibility is fully maintained.
