# Methodological Consistency Audit

**Audit date:** 2026-05-12
**Scope:** Every active script, doc, report, and data dictionary scanned for the 12 known-stale methodology concepts and 6 known-correct anchor values.

---

## 1. Result summary

| Concept | Status across project |
|---------|----------------------|
| **Log returns for investable assets** | ✓ NOT USED. Only `src/data/transformations.py:compute_log_returns()` is defined, with explicit "DEPRECATED for investable returns panel" docstring. `compute_log_returns` is called only in `src/data/feature_engineering.py:189` for volatility-index z-scores (rolling realised vol from log-differences of vol indices), which is the correct usage. |
| **Simple (arithmetic) returns for portfolios** | ✓ EVERYWHERE — `compute_simple_returns` is used in `build_panels.build_investable_panels`. METHODOLOGY.md, README.md, data/README_DATA.md all state simple returns. |
| **2-state HMM / Bull-Bear binary** | ✓ NOT USED in any active code or doc. The only mentions are inside `reports/final/documentation_consistency_audit.md` and `reports/final/full_project_submission_audit.md` (prior audit reports) where they describe the pre-correction state. |
| **3-state HMM** | ✓ NOT USED. `src/models/hmm.select_n_states` still has `candidates=[2,3,4]` as a default, but the active script `02_hmm_walkforward_156.py` hard-codes `N_STATES=4`. |
| **5 features** | ✓ NOT USED. The only mention is in `reports/regimes/date_pipeline_audit.md` as a historical description ("the matrix starts 2003-05-09 (6 features) or 2000-06-30 (5 features)"). The active 8-feature set is in `src/models/hmm.REGIME_FEATURES`. |
| **4-state HMM with 8 features** | ✓ ACTIVE — `02_hmm_walkforward_156.py`, METHODOLOGY.md §3, README.md, paper Section II.D. |
| **Diebold-Mariano / DM-test** | ✓ NOT USED. `requirements.txt` has stale comment "statsmodels — optional: Diebold-Mariano, etc." Active scripts use HAC/Newey-West t-tests on mean excess-return differentials (script 08). |
| **HAC/Newey-West + block-bootstrap** | ✓ ACTIVE — `scripts/08_panel_statistical_tests.py` (HAC_LAG=13, BLOCK_LEN=13, N_BOOT=5000, SEED=42). |
| **6-month HICP lag** | ✓ NOT USED. All references are "6-week" or "HICP_LAG_WEEKS=6". |
| **6-week HICP lag** | ✓ ACTIVE — `scripts/10_hicp_lag6_robustness.py:HICP_LAG_WEEKS=6`. Verified in `regime_features_weekly_hicp_lag6.parquet`. |
| **EURIBOR as risky asset** | ✓ NOT USED. Every active script excludes `CASH_COL = "EURIBOR_3M"` from the risky universe via `risky = [c for c in ret.columns if c != CASH_COL]`. EURIBOR is correctly treated as the risk-free / cash proxy. |
| **Equal-weight including cash** | ✓ NOT USED. `_eq_drift_to` operates on `ret_r` (risky-only). EW strategy excludes EURIBOR. |
| **Native EUR Italy claim** | ✓ NOT MADE. Files explicitly note "FTSE Russell, EUR" but the user-known fact "no native EUR RIC exists" is acknowledged in v8 notes / fi_expanded comparison. |
| **Static CVaR beats Regime CVaR (correct conclusion)** | ✓ Asserted in paper, model_backtest_summary.md, METHODOLOGY.md, README.md. |
| **Regime CVaR beats Static CVaR (WRONG conclusion)** | ✓ NOT CLAIMED anywhere. README's "Unsupported Conclusion" section explicitly says this is unsupported. |
| **Full-sample HMM for OOS** | ✓ NOT USED. `regime_labels_full.parquet` is documented and used **only** for the descriptive Figure 1; all OOS uses `regime_labels_wf_156.parquet`. The descriptive use is correctly disclosed in `model_backtest_summary.md` and the figure caption. |
| **MIN_TRAIN_OBS=260 for Panel B** | ⚠ Historical references remain in `reports/regimes/date_pipeline_audit.md` and `reports/regimes/window_recovery_options.md` (older audit docs from before the change to 156). These are historical analyses that documented WHY the team switched from 260 to 156. Not active methodology. **P3.** |
| **MAX_WEIGHT=0.25** | ✓ EVERYWHERE in active scripts (06, 07, 10, 11, 14, 15, 17, 18). `src/optimization/cvar.CVaRConfig.max_weight` default is 0.35 (P1-E from code audit), but every active call overrides to 0.25. |
| **MAX_WEIGHT=0.35** | ⚠ Default in `src/optimization/cvar.CVaRConfig`. Could be triggered by future careless calls. P1-E. |

---

## 2. Anchor values cross-check

| Anchor (from user-known facts) | Source | Verified value | Match |
|---|---|---|---|
| HMM is 4-state | scripts/02 `N_STATES=4`, scripts/10, scripts/11 | 4 | ✓ |
| 8 z-score macro-financial features | `src/models/hmm.REGIME_FEATURES` | 8 features ✓ | ✓ |
| States ordered by ascending z52_VIX | `02_hmm_walkforward_156.canonical_permutation` | argsort(argsort(vix_means)) | ✓ |
| HICP robustness lag is 6 weeks | scripts/10 `HICP_LAG_WEEKS=6` | 6 | ✓ |
| HAC/Newey-West + block-bootstrap (not DM) | scripts/08 | HAC_LAG=13, BLOCK_LEN=13, N_BOOT=5000 | ✓ |
| Returns are weekly simple arithmetic | `build_panels.compute_simple_returns` | pct_change | ✓ |
| EURIBOR 3M is RF / cash proxy | every script: `CASH_COL = "EURIBOR_3M"` | excluded from risky | ✓ |
| Static CVaR Panel B Sharpe 0.530 gross, 0.528 net@10bps | `panel_b_regime_oos_performance.csv` | 0.530 / 0.528 | ✓ |
| Static CVaR Panel B TO ~21.4% | same CSV | 21.40% | ✓ |
| Naive Regime CVaR-A Panel B Sharpe 0.365 / 0.346 | same CSV | 0.365 / 0.346 | ✓ |
| Naive Regime CVaR-A Panel B TO 225.8% (≈17.4%/4wk) | same CSV | 225.75% (17.37% per rebal) | ✓ |
| Weighted CVaR Panel B TO 232.5% | same CSV | 232.51% | ✓ |
| ZEW-swap label agreement 47.9339% (47.9%) | parquet recompute | 0.479339 | ✓ |
| ZEW + lambda=0.005 is exploratory | paper Section VII.B + Figure 3 | flagged "exploratory" in MD + JS | ✓ |
| Italy bond TR EUR-converted by LSEG | raw filename "EUR END OF DAY" + paper note | ✓ | ✓ |
| FI-expanded adds Germany, Spain, Italy govt bond TR | scripts/16 + FI parquets | exactly these 3 | ✓ |

---

## 3. Stale references that should be cleaned (P3 unless flagged)

| File | Line / pattern | Recommendation |
|------|----------------|----------------|
| `requirements.txt` | `# optional: statistical tests (Diebold-Mariano, etc.)` | Update comment to "HAC/Newey-West tests"; or remove `statsmodels` entirely since it is not imported |
| `reports/regimes/date_pipeline_audit.md` | references MIN_TRAIN_OBS=260 as the active value | Add a header note that this audit was written under the 260-week regime and 156 is now canonical |
| `reports/regimes/window_recovery_options.md` | same | Same |
| `src/models/hmm.py` docstring line 13-14 | `Usage: python scripts/02_fit_hmm.py` (archived script) | Update to `02_hmm_walkforward_156.py` |
| `src/optimization/cvar.py` | `CVaRConfig.max_weight = 0.35` (P1-E) | Change to `0.25` or document the override pattern |
| `scripts/07_panel_b_regime_oos.py:381-383` (P1-D) | hardcoded `(~100-160%) / (~10%)` narrative | parameterise on CSV values |
| `scripts/09_regime_timeline_figure.py` (P1-C) | non-canonical state labels for `regime_labels_full.parquet` | regenerate parquet with canonical permutation OR document the inversion explicitly |

---

## 4. Cross-document consistency matrix

| Claim | METHODOLOGY.md | README.md | data/README_DATA.md | docs/ACTIVE_OUTPUTS.md | docs/RUN_ORDER.md | model_backtest_summary.md | paper v8 | Consistent? |
|------|----------------|-----------|--------------------|----------------------|------------------|--------------------------|----------|-------------|
| 4-state HMM | ✓ | ✓ | ✓ | (n/a) | (n/a) | ✓ | ✓ | ✓ |
| 8 features (z-score) | ✓ | (high-level) | ✓ | ✓ | (n/a) | (n/a) | ✓ | ✓ |
| Walk-forward MIN_TRAIN_OBS=156 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| HICP-lag6 robustness | ✓ | (n/a) | (n/a) | ✓ | ✓ | (n/a) | ✓ | ✓ |
| Static CVaR best benchmark | ✓ | ✓ | (n/a) | (n/a) | (n/a) | ✓ | ✓ | ✓ |
| Sharpe = excess / std × √52 | ✓ | ✓ | (n/a) | (n/a) | (n/a) | ✓ | ✓ | ✓ |
| Simple weekly returns | ✓ | ✓ | ✓ | (n/a) | (n/a) | ✓ | ✓ | ✓ |
| EURIBOR excluded from risky | ✓ | ✓ | ✓ | (n/a) | (n/a) | ✓ | ✓ | ✓ |
| Max weight 25% | ✓ | ✓ | (n/a) | (n/a) | (n/a) | ✓ | ✓ | ✓ |
| HMM state 0 = lowest VIX | ✓ | (n/a) | (n/a) | (n/a) | (n/a) | ✓ | ✓ | ✓ for WF labels; ✗ for `regime_labels_full.parquet` / Figure 1 — see §1 P1-C |

---

## 5. Verdict

**The active project follows a single, internally consistent methodology** — 4-state HMM, 8 z-score features, walk-forward MIN_TRAIN=156, simple weekly returns, EURIBOR cash, 25% max weight, HAC/Newey-West tests, 5000-block bootstrap, 6-week HICP-lag robustness. No active script or doc contradicts this.

The **only methodological inconsistency** is the state-numbering convention for `regime_labels_full.parquet` / Figure 1 (P1-C), where state 0 = highest VIX, opposite of every other element. The figure caption documents this but the inversion is not robust to a future regeneration.

The remaining "stale" hits are historical audit reports (`reports/final/documentation_consistency_audit.md`, `reports/final/full_project_submission_audit.md`, `reports/regimes/{date_pipeline,window_recovery}.md`) that describe **past** changes from 2-state / 260-week / DM-test to the current methodology. They are not active.
