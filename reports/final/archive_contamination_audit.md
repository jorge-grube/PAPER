# Archive Contamination Audit

**Audit date:** 2026-05-12

Verifies that no active script, doc, or paper element accidentally loads an archived file or refers to a now-archived path as if it were active.

---

## 1. Findings summary

**No active script reads from any `archive/` directory.**

Specifically verified (grepped `/archive/`, `gen1_wrong`, `canonical_backtest`, `02_fit_hmm`, `03_cvar_optimization`, `04_canonical_backtest`, `05_statistical_tests` across all .py / .md / .csv / .yaml files):

- All `archive` references in active code/docs are EXPLICIT mentions of what NOT to use:
  - `docs/ACTIVE_OUTPUTS.md` lines 85-90 — describes the archive contents (correctly classified).
  - `docs/REPO_STRUCTURE.md` lines 26-30, 84-86, 128, 143 — describes the archive layout.
- **Active scripts:**
  - `scripts/01_validate_and_build_dataset.py` reads under `data/raw/`, `data/investable_assets/`, `data/regime_variables/` — not `archive/`. ✓
  - `scripts/02_hmm_walkforward_156.py` reads `regime_features_weekly.parquet` directly — not from `archive/`. ✓
  - All other active scripts use explicit absolute paths (via `PROCESSED / "<name>.parquet"`). None of these names hit `archive/`. ✓

## 2. Stale reference in source code

- **`src/models/hmm.py:13`** docstring says `Usage: python scripts/02_fit_hmm.py` — this is the ARCHIVED filename. The active script is `scripts/02_hmm_walkforward_156.py`. **P2 stale docstring** (cosmetic — the module is imported, not run directly).

## 3. Glob patterns — risk of accidentally globbing into archive

- `src/data/loaders.py:39` — `data_dir.rglob(f"*{ext}")` then filters via `"processed" not in p.parts`.
  - `processed/archive` is INSIDE `processed`, so the filter excludes ALL processed parquet (active and archived). The function only reads raw xlsx, which lives outside `processed/`. ✓
  - The `data/raw/fixed_income/` directory contains 7 xlsx files including 2 rejected ones (BBG xls, ECB xlsx). When `discover_data_files` runs, it will pick them up. The downstream validation pipeline correctly logs them but does not include them in the investable panel because their `category` is not `investable_assets`. ✓

No glob in any active script reaches into `archive/` or `__pycache__/`.

## 4. Filename collision risk

Same-name files exist in both active and archive locations:
- `regime_labels_wf.parquet` (active: `regime_labels_wf_156.parquet`; archive: `data/processed/archive/regime_labels_wf.parquet`)
- `canonical_backtest_*.parquet` (only archive — no active equivalent)
- `inventory.csv/.md`, `frequency_report.csv`, `outlier_report.csv`, `series_coverage_report.csv`, `statistical_tests.csv/.md`, `missing_values_report.csv` (only archive — no active equivalent at top-level reports/)

The active scripts use the `_156` suffix to disambiguate. No collisions observed in script source.

## 5. Co-existing generations under `data/processed/model_improvement/regime_constraints/`

**P2:** Two generations of weight parquets coexist:

- **Older (2026-05-10, pre-correction):**
  - `weights_regime_cvar_A.parquet`
  - `weights_weighted_cvar.parquet`
  - `weights_zew_regime_cvar_A.parquet`
  - `weights_zew_weighted_cvar.parquet`
  - `weights_static_cvar.parquet`
- **Newer (2026-05-12, post-correction):**
  - `weights_rc_baseline.parquet`
  - `weights_rc_zew.parquet`

Script 15 in its current form writes **only** the newer two files; the older five are residual from a previous run and are no longer regenerated. They are not loaded by any active script (verified by `grep -rE "weights_regime_cvar_A.parquet|weights_weighted_cvar.parquet"` across active code: no hits).

**Verdict:** Not a *contamination* (no active reader), but a **storage/clarity** issue. Should ideally be moved to `data/processed/model_improvement/regime_constraints/_archive/`.

## 6. Stale `paper/drafts/When Regimes Do Not Pay.pdf`

Already documented in `paper_artifact_audit.md`: this file is the v7 PDF under a friendly name. Not consumed by any active script, but a reviewer who picks this file by its title gets v7, not v8. **P2.**

## 7. Active docs that correctly classify archived items

- `docs/ACTIVE_OUTPUTS.md` Section "Archived (do not cite or use)" — correctly lists `data/processed/archive/`, `reports/archive/`, `scripts/archive/`. ✓
- `docs/REPO_STRUCTURE.md` — shows the archive tree but labels every archive folder "do not run / do not use / superseded". ✓
- `reports/final/repository_cleanup_report.md` — documents the cleanup that produced the current archive structure. ✓
- `reports/final/cleanup_dependency_check.md` — verifies that no active path references archive locations. ✓ (Pre-existing audit confirms this independently.)

## 8. Verdict

- **No active path references any archive file.** ✓
- **No glob pattern reaches into archive directories.** ✓
- **One stale docstring reference** (`src/models/hmm.py:13`) to an archived script name. P2.
- **One generational duplicate** under `regime_constraints/`. P2.
- **`When Regimes Do Not Pay.pdf` is the v7 build under a friendly name.** P2.
- **Archived files exist solely as historical record and are correctly classified.** ✓
