# Reproducibility Audit

**Audit date:** 2026-05-12
**Question:** Can a clean user reproduce the project from raw data, processed parquets, or scripts alone?

---

## 1. Top-line verdict

| From | Feasible? | Confidence |
|------|-----------|------------|
| **Raw xlsx + active scripts** | ⚠ Partial — pipeline runs but cannot rebuild paper/figures in a new session due to hardcoded paths | Medium |
| **Processed parquets + active scripts** | ⚠ Partial — Stages 3-8 run cleanly; figure regeneration is broken | Medium |
| **Processed parquets only (no rerun)** | ✓ All published numbers can be VERIFIED from the existing CSVs | High |
| **Paper rebuild from JS** | ✗ Hardcoded `/sessions/friendly-keen-curie/...` path; build fails | Low |

---

## 2. Environment

### 2.1 `requirements.txt` (32 lines)
- Python 3.11.x specified.
- Core stack pinned exactly: `pandas==3.0.2`, `numpy==2.4.4`, `pyarrow==24.0.0`, `openpyxl==3.1.5`, `python-calamine==0.6.2`, `PyYAML==6.0.3`, `python-dateutil==2.9.0.post0`, `tzdata==2026.1`.
- Modelling stack pinned with ranges: `scipy>=1.13,<2`, `scikit-learn>=1.5,<2`, **`hmmlearn>=0.3,<1`** ✓ flexible, but **HMM RNG behaviour can change between minor versions of hmmlearn**.
- `matplotlib>=3.9,<4`, `seaborn>=0.13,<1`.
- Notebook deps included (optional).
- Dev tools commented out.
- **NOTE:** `statsmodels>=0.14,<1` is listed but **not imported** by any active script (verified via `grep -rE "import statsmodels|from statsmodels" scripts/ src/` returns nothing in active code). Comment says "optional: statistical tests (Diebold-Mariano, etc.)" — that's stale (DM removed from the methodology). **P3** — unused dependency.

### 2.2 No `pyproject.toml`, no `setup.py`, no `setup.cfg`
There is no package metadata. The project relies on `sys.path.insert(0, str(ROOT/"src"))` in every script. ✓ Works, but means the project is not pip-installable as a package.

### 2.3 No `package.json` for the JS paper build
`paper/build_paper_v8.js` requires `./node_modules/docx`. The repo does not include `node_modules/` or a `package.json`. A new user must `npm install docx` manually and hope the major version matches what the JS code was written against. **P2.**

### 2.4 No `Dockerfile`, no `conda environment.yml`, no `Makefile`
**P3** — environment provisioning is documented only narratively in README.

---

## 3. Raw data availability

| Source | Files | Pages |
|--------|-------|-------|
| LSEG Workspace (Refinitiv) | 51 .xlsx files | Most under `data/investable_assets/` and `data/regime_variables/` |
| ECB Data Portal | 1 xlsx (rejected for FI candidate analysis) | `data/raw/fixed_income/` |
| FTSE Russell (via LSEG) | 5 govt bond TR xlsx (active 3 + 2 rejected) | `data/raw/fixed_income/` |
| Bloomberg Index Services (via xls) | 1 (rejected) | `data/raw/fixed_income/BBG Euro Aggregate ...xls` |

**Proprietary data caveat:** LSEG content is subject to data-licensing restrictions (acknowledged in paper Section I.B per v8 P2.7 fix). Raw xlsx **cannot be redistributed publicly.** The processed parquet files (which contain only derived numerical series, not LSEG metadata or tickers) MAY be redistributable — this should be confirmed against the LSEG license terms. **P3** — license terms should be cited.

---

## 4. Run order (per `docs/RUN_ORDER.md`)

1. `scripts/01_validate_and_build_dataset.py` — Stage 1 (data pipeline)
2. `scripts/02_hmm_walkforward_156.py` — Stage 2 (HMM walk-forward)
3. `scripts/06_panel_a_long_horizon.py` — Stage 3 (Panel A baseline)
4. `scripts/07_panel_b_regime_oos.py` — Stage 4 (Panel B baseline)
5. `scripts/08_panel_statistical_tests.py` — Stage 5 (statistical tests)
6. `scripts/09_regime_timeline_figure.py` + `scripts/07_figures/generate_paper_figures.py` — Stage 6 (figures)
7. `scripts/10_hicp_lag6_robustness.py`, `11_zew_swap_experiment.py`, `12_rebalance_frequency_experiment.py`, `13_turnover_smoothing_experiment.py`, `14_tc_aware_cvar_experiment.py`, `15_regime_constraints_experiment.py` — Stage 7 (robustness)
8. `scripts/16_fi_expanded_universe.py`, `17_panel_a_fi_expanded.py`, `18_panel_b_fi_expanded.py` — Stage 8 (FI-expanded)

**Missing from RUN_ORDER:** none — every active script is listed. ✓

**Implicit dependencies:**
- Script 09 depends on `regime_labels_full.parquet` which is **NOT produced by any active script** (P1-C). Currently it exists from a 2026-05-07 run of the archived `02_fit_hmm.py`. A fresh user starting from raw data cannot regenerate Figure 1 by following RUN_ORDER alone.
- Script 12 depends on both baseline and ZEW-swap label parquets (RUN_ORDER specifies "Stage 7 scripts can be run in any order after Stages 1-5" but script 12 actually requires script 11 first).
- Script 13 depends on script 11 (ZEW-swap labels) AND script 12 (rebalance-frequency CSV for comparison context).
- Scripts 14/15 depend on both baseline (script 02) and ZEW-swap (script 11) labels.

These cross-dependencies inside Stage 7 are not explicitly documented in RUN_ORDER but are easy to infer from each script's docstring.

---

## 5. Runtime expectations

| Script | Approx runtime | Notes |
|--------|---------------|-------|
| 01_validate_and_build_dataset.py | 1-2 min | Reads ~50 xlsx files |
| 02_hmm_walkforward_156.py | ~5-10 min/full | Checkpointed; configurable `--batch-size` for 45 s sandbox |
| 06_panel_a_long_horizon.py | 2-5 min | 303 LP solves |
| 07_panel_b_regime_oos.py | 5-10 min | 808 LP solves |
| 08_panel_statistical_tests.py | 1 min | 5,000-block bootstrap × 10 strategies |
| 09_regime_timeline_figure.py | < 30 sec | |
| 10_hicp_lag6_robustness.py | ~10-15 min | Re-runs walk-forward HMM |
| 11_zew_swap_experiment.py | ~10-15 min | Re-runs walk-forward HMM |
| 12_rebalance_frequency_experiment.py | ~10-60 min | freq=1 exceeds sandbox timeout (~52 s per checkpoint); documented |
| 13_turnover_smoothing_experiment.py | ~5-10 min | |
| 14_tc_aware_cvar_experiment.py | ~15-30 min | Larger LPs (extra L1 vars) |
| 15_regime_constraints_experiment.py | ~10-15 min | |
| 16_fi_expanded_universe.py | < 1 min | Just reads xlsx |
| 17_panel_a_fi_expanded.py | 2-5 min | |
| 18_panel_b_fi_expanded.py | 5-10 min | |
| 07_figures/generate_paper_figures.py | < 1 min | |
| paper/build_paper_v8.js | < 1 min | |

**Total clean-rerun estimate:** 2-3 hours of CPU time. Acceptable.

---

## 6. Random seeds

| Source | Seed | Reproducible? |
|--------|------|---------------|
| `src/models/hmm.py:RANDOM_STATE = 42` | 42 | ✓ |
| HMM walk-forward `_fit_one` iterates `range(random_state, random_state + n_init)` | 42-56 (15 restarts) | ✓ |
| `scripts/08_panel_statistical_tests.py:SEED = 42` | 42 | ✓ |
| `np.random.default_rng(42)` used | 42 | ✓ |

No `np.random.seed()` style global state. ✓ Best-practice.

**hmmlearn version** is bounded to `>=0.3,<1`. The internal RNG behaviour of hmmlearn's EM algorithm can change with patch versions. **P3** — pin exact `hmmlearn` version to guarantee bit-exact reproducibility.

---

## 7. Hardcoded paths and platform dependencies

### 7.1 Critical (P1)
- `scripts/07_figures/generate_paper_figures.py:16` — `PAPER = '/sessions/friendly-keen-curie/mnt/PAPER'`. Will fail outside this session id.
- `paper/build_paper_v8.js:28` — `FIG_DIR = '/sessions/friendly-keen-curie/mnt/PAPER/paper/figures/'`. Same.

### 7.2 Archive-only (P2 informational)
- `scripts/archive/generate_data_inventory_yaml.py:7` — `ROOT = Path(r"c:/Users/Jorge/OneDrive - UFV/BAINF/PAPER")`
- `scripts/archive/generate_data_inventory_yaml_fast.py:6` — same
- `scripts/archive/write_data_inventory_yaml_static.py:5` — same

Archive scripts are correctly archived but their Windows-personalised paths would expose the author's local file system if the archive ever leaks. Cosmetic since they are not on the run path.

### 7.3 Active scripts — clean ✓
Every active script (01, 02, 06-18 except 07_figures) uses `ROOT = Path(__file__).resolve().parent.parent` for relative resolution. ✓

---

## 8. Reproducibility scenarios

### 8.1 Reviewer wants to verify the headline numbers without rerunning anything
**Outcome:** ✓ Possible. All numbers in the paper can be looked up in:
- `reports/panels/panel_{a,b}_regime_oos_*.csv` for Tables II-VI
- `reports/model_improvement/{tc_aware_cvar,regime_constraints,...}/*.csv` for Table VII
- `reports/fi_expanded/*.csv` for Table VIII
- `reports/regimes/hicp_lag6_robustness.md` for HICP robustness
- `reports/model_improvement/panel_b_*_zew_swap.csv` for ZEW row

### 8.2 Reviewer wants to rerun the full pipeline from raw xlsx
**Outcome:** ⚠ Mostly works:
- Scripts 01, 02, 06, 07, 08, 10, 11, 12, 13, 14, 15, 16, 17, 18 run cleanly.
- Script 09 will fail unless `regime_labels_full.parquet` already exists (no active producer).
- `07_figures/generate_paper_figures.py` will fail (hardcoded path).
- `paper/build_paper_v8.js` will fail (hardcoded path; needs `npm install docx`).

### 8.3 Reviewer wants to fork the public processed parquets and run only the model-improvement experiments
**Outcome:** ✓ Stages 7-8 run cleanly with just `data/processed/*.parquet` + `data/processed/model_improvement/regime_features_weekly_zew_swap.parquet` already present.

### 8.4 Reviewer wants to rebuild the paper docx from scratch
**Outcome:** ✗ The hardcoded `friendly-keen-curie` path makes this impossible without source-editing `build_paper_v8.js` and `generate_paper_figures.py`.

---

## 9. Required fixes for full reproducibility

| Priority | Fix |
|---------:|-----|
| P1 | Replace `PAPER = '/sessions/friendly-keen-curie/mnt/PAPER'` with `PAPER = str(Path(__file__).resolve().parents[2])` (or an env-var) in `generate_paper_figures.py` |
| P1 | Same for `FIG_DIR` in `build_paper_v8.js`: use `path.resolve(__dirname, 'figures')` |
| P1 | Either (a) add `regime_labels_full.parquet` regeneration to RUN_ORDER (e.g. via a small wrapper script around `src/models/hmm.run_hmm_pipeline`), OR (b) move the file to `data/static/` and mark it as a fixed published artefact |
| P2 | Add a `package.json` for the JS paper build, pinning `docx` version |
| P2 | Add a `paper/figures/.gitkeep` or pre-built fallback so build_paper_v8.js works without rerunning fig scripts |
| P2 | Consolidate `_port`, `_weekly_to`, `compute_metrics` into a shared `src/evaluation` module to prevent drift |
| P3 | Pin exact `hmmlearn` version |
| P3 | Remove `statsmodels` from requirements.txt (unused) |
| P3 | Add a Dockerfile or `environment.yml` |

---

## 10. Verdict

**The pipeline is reproducible at the data and CSV level**, but **paper assembly is broken outside the original session**. For an external reviewer, the practical workflow is:
1. Read parquets + CSVs to verify all reported numbers (works today),
2. Rerun Stage 7-8 robustness experiments (works today),
3. Rerun Stage 1-5 baseline (works today),
4. **Cannot** rerun the paper build or Figure 2-5 generation without source-editing two paths.

The P1 path fixes are 2 single-character edits each and could be applied in minutes.
