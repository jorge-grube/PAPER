# Repository Cleanup Report

**Date:** 2026-05-10  
**Scope:** Full repository reorganisation following completion of Task #50 (FI-expanded universe).  
**Principle:** Archive before delete; no model reruns; no empirical results altered.

---

## Summary of Changes

### Phase 1 — Directory Creation

Created new directories:
- `paper/` (with `drafts/`, `notes/`, `tables/`, `figures/`)
- `docs/archive/`
- `reports/final/`, `reports/data/`, `reports/regimes/`, `reports/panels/`
- `data/raw/fixed_income/`

### Phase 2 — Pycache Deletion

Deleted all `__pycache__/` and `.pyc` files from `scripts/`, `src/`, and subdirectories.

### Phase 3 — Script Archiving

| Action | File |
|--------|------|
| Archived | `scripts/04_canonical_backtest.py` → `scripts/archive/` |
| Archived | `scripts/05_statistical_tests.py` → `scripts/archive/` |

### Phase 4 — Script Rename

| Old name | New name | Notes |
|----------|----------|-------|
| `scripts/hmm_walkforward_156.py` | `scripts/02_hmm_walkforward_156.py` | Safe: stays in scripts/, ROOT pattern unaffected |

### Phase 5 — FI Raw Data Organisation

Moved 7 files from `TEMPORARY_FA/` → `data/raw/fixed_income/`:
- 5 FTSE government bond TR xlsx files (Germany, Spain, Italy, Eurozone, UK)
- BBG Euro Aggregate .xls
- ECB Data Portal .xlsx

**Critical fix:** Updated `scripts/16_fi_expanded_universe.py` path from `BASE / "TEMPORARY_FA"` to `BASE / "data" / "raw" / "fixed_income"`.

Note: `TEMPORARY_FA/` directory itself could not be removed (Windows filesystem mount permission restriction). It is now empty.

### Phase 6 — Canonical Backtest Data Archive

Moved 9 files from `data/processed/` → `data/processed/archive/`:
- `canonical_backtest_diagnostics.json`
- `canonical_backtest_returns.parquet`
- 5 `canonical_backtest_weights_*.parquet` files
- `canonical_crisis_windows.parquet`
- `canonical_metrics.parquet`

These are outputs of the superseded `04_canonical_backtest.py` and are replaced by scripts 06/07.

### Phase 7 — Paper Files

| Action | File |
|--------|------|
| Moved | `paper_draft_JF_style.docx` → `paper/drafts/` |
| Moved | `paper_draft_JF_style_notes.md` → `paper/notes/` |

### Phase 8 — Stale Root Docs Archived

| Action | File |
|--------|------|
| Archived | `MIGRATION.md` → `docs/archive/` |
| Archived | `NEXT_EXECUTION.md` → `docs/archive/` |
| Archived | `reports/repo_cleanup_plan.md` → `docs/archive/` |

### Phase 9 — Misplaced Scripts Archived

| Action | File |
|--------|------|
| Archived | `reports/generate_data_inventory_yaml.py` → `scripts/archive/` |
| Archived | `reports/generate_data_inventory_yaml_fast.py` → `scripts/archive/` |
| Archived | `reports/write_data_inventory_yaml_static.py` → `scripts/archive/` |

### Phase 10 — Stale Reports Archived

Moved from `reports/` root to `reports/archive/`:
- `frequency_report.csv`
- `inventory.csv`, `inventory.md`
- `missing_values_report.csv`
- `outlier_report.csv`
- `sample_coverage_table.csv`
- `series_coverage_report.csv`
- `statistical_tests.csv`, `statistical_tests.md` (from `04_canonical_backtest.py` era)

Also moved `reports/quality/` → `reports/archive/quality/`.

### Phase 11 — Report Reorganisation

**→ `reports/data/`:**
`data_inventory.yml`, `data_validation_summary.md`, `final_dataset_summary.md`, `fixed_income_candidate_audit.md`, `fixed_income_data_audit.md`

**→ `reports/regimes/`:**
`date_pipeline_audit.md`, `hmm_regime_summary.md`, `macro_release_date_risk_audit.md`, `window_recovery_options.md`, `hicp_lag6_robustness.md`

**→ `reports/final/`:**
`model_backtest_summary.md`

**→ `reports/panels/`:**
All `panel_a_*` and `panel_b_*` performance, summary, and statistical test files (12 files total).

### Phase 12 — Script Output Path Updates

Updated 5 scripts to write to new `reports/panels/` and `reports/regimes/` locations:

| Script | Change |
|--------|--------|
| `06_panel_a_long_horizon.py` | `ROOT/"reports"` → `ROOT/"reports"/"panels"` + mkdir |
| `07_panel_b_regime_oos.py` | `ROOT/"reports"` → `ROOT/"reports"/"panels"` + mkdir |
| `08_panel_statistical_tests.py` | `ROOT/"reports"` → `ROOT/"reports"/"panels"` |
| `10_hicp_lag6_robustness.py` | Individual paths updated to panels/ and regimes/ |
| `13_turnover_smoothing_experiment.py` | Input read path updated to panels/ |

### Phase 13 — Documentation Created / Updated

| File | Action |
|------|--------|
| `README.md` | Updated — correct paths, run order, active outputs table |
| `docs/RUN_ORDER.md` | Updated — includes script 02, correct output paths |
| `docs/METHODOLOGY.md` | Created — full methodology reference |
| `docs/REPO_STRUCTURE.md` | Created — annotated directory tree |
| `docs/ACTIVE_OUTPUTS.md` | Created — live vs. archived file index |
| `data/README_DATA.md` | Created — data dictionary with RICs, shapes, notes |

### Phase 14 — Empty Directory Cleanup

| Directory | Outcome |
|-----------|---------|
| `data/robustness/` | Could not remove (Windows mount permission) — inert, empty |
| `src/portfolio_eu/` | Could not remove (Windows mount permission) — inert, empty |
| `TEMPORARY_FA/` | Could not remove (Windows mount permission) — inert, empty |

---

## Invariants Confirmed

- No empirical results were recomputed.
- No parquet files were overwritten or modified.
- No script logic was changed — only output/input path strings updated.
- All archived files remain recoverable from their archive locations.
- 48/48 dependency checks pass (see `cleanup_dependency_check.md`).

---

## Final Repository State

```
scripts/          15 active scripts (01, 02, 06–18)
scripts/archive/  8 superseded scripts
src/              Library modules (data, models, optimization)
data/raw/         LSEG xlsx files + data/raw/fixed_income/ (7 FI files)
data/processed/   10 active parquet files + archive/
reports/panels/   12 Panel A/B output files
reports/final/    3 consolidated summaries
reports/fi_expanded/  11 FI-expanded outputs
reports/regimes/  5 regime/macro audit files
reports/data/     5 data validation files
reports/model_improvement/  Robustness experiment outputs
reports/figures/  1 figure
reports/archive/  Stale historical outputs
paper/drafts/     paper_draft_JF_style.docx
docs/             5 documentation files + archive/
data/README_DATA.md
README.md
requirements.txt
```
