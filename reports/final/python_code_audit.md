# Python Code Audit

**Audit date:** 2026-05-12  •  **Mode:** READ-ONLY  •  **Files inspected:** 39 .py (16 active + 8 archived + 15 src/ library), plus 1 .js paper build script

The companion `python_dependency_map.md` lists per-script inputs/outputs.

---

## 1. Top-level findings

| Severity | Count |
|---:|---:|
| P1 | 6 |
| P2 | 11 |
| P3 | 9 |
| P4 | 5 |

Top 6 P1 issues, ordered by impact:

| # | File | Issue |
|---:|------|-------|
| P1-A | `scripts/07_figures/generate_paper_figures.py:16` | `PAPER = '/sessions/friendly-keen-curie/mnt/PAPER'` — hard-coded ephemeral session path. Script will not re-run on the user machine or in any new session. The current session is `trusting-adoring-brahmagupta`. |
| P1-B | `paper/build_paper_v8.js:28` | Same hard-coded path: `const FIG_DIR = '/sessions/friendly-keen-curie/mnt/PAPER/paper/figures/';`. v8 paper can only be rebuilt under that exact (no longer existing) session id. |
| P1-C | `data/processed/regime_labels_full.parquet` (consumed by `scripts/09_regime_timeline_figure.py`) | The full-sample labels are not produced by any active script and follow a NON-canonical state ordering. Measured `mean(z52_VIX)` by state: 0=+1.85, 1=−0.59, 2=+0.05, 3=−0.96. This is the OPPOSITE convention from the canonical walk-forward labels (0 → lowest VIX, 3 → highest). Figure 1's hard-coded `REGIME_LABELS` dict (`0→High-Stress, 3→Bull/Low-Vol`) happens to be consistent with this non-canonical parquet, but no script re-generates the parquet, so any rerun against the canonical convention would silently invert the figure. The methodology document and Tables IV–VII use the canonical convention. |
| P1-D | `scripts/07_panel_b_regime_oos.py:381-383` | Auto-generated summary text contains stale narrative: *"Regime CVaR strategies have substantially higher turnover (~100–160% annually) vs static CVaR (~10%)."* Actual measured values are 225.75% / 232.51% / 21.40%. Each rerun of script 07 will overwrite `panel_b_regime_oos_summary.md` with these wrong figures. |
| P1-E | `src/optimization/cvar.py:39` | `CVaRConfig.max_weight = 0.35` default, while the documented methodology and every active script use `0.25`. Any module that calls `solve_cvar(scenarios)` without an explicit config (currently none in active scripts, but `weighted_cvar_weights` and `solve_cvar_constrained` library helpers can be called this way) will silently relax the cap to 35%. |
| P1-F | `src/optimization/cvar.py:218-331` | `run_cvar_backtest()` is dead code that still encodes the OLD pipeline: 2-state and 3-state HMM not assumed, but `min_history_weeks=156` and full-history equal-weight fallback differ from the active Panel B convention. It is not called by any active script, but `from optimization.cvar import …` is `*`-friendly and a future caller would re-introduce stale logic. |

---

## 2. Per-file audit

### 2.1 `scripts/01_validate_and_build_dataset.py`
- **Role:** Entry point for the data pipeline; orchestrates `src/data/*` modules.
- **Inputs:** raw xlsx under `data/raw/`, `data/investable_assets/`, `data/regime_variables/`.
- **Outputs:** `data/processed/investable_prices_weekly.parquet`, `investable_returns_weekly.parquet`, `regime_variables_weekly.parquet`, `regime_features_weekly.parquet`, `metadata.yaml`, and the four legacy validation CSVs under `reports/archive/` (`missing_values_report.csv`, etc.).
- **Findings:**
  - **P2** — `src/data/reporting.write_validation_reports` writes `missing_values_report.csv`, `series_coverage_report.csv`, `outlier_report.csv`, `frequency_report.csv` and `data_validation_summary.md` to `config.reports_dir = ROOT/"reports"` (i.e. directly into `reports/`, not `reports/archive/`). Today these files live only under `reports/archive/`; if a future user reruns script 01, four fresh CSVs and one fresh MD will land at the top of `reports/`, polluting the active directory.
  - **P3** — `src/data/loaders.discover_data_files` returns ALL non-processed files; the catalogue includes the `data/raw/fixed_income/*.xlsx` and the rejected `BBG / ECB` files. Validate-step will run on them and silently log them as data series, which may include them in the metadata.yaml.

### 2.2 `scripts/02_hmm_walkforward_156.py`
- **Role:** Canonical walk-forward HMM (4-state, MIN_TRAIN=156, step=4) with VIX-z-score state ordering.
- **Inputs:** `regime_features_weekly.parquet`.
- **Outputs:** `regime_labels_wf_156.parquet`, `regime_probs_wf_156.parquet`, `hmm_wf_checkpoint_156.pkl`.
- **Findings:**
  - Correctly uses 4 states, 8 features (via `REGIME_FEATURES`), 52-week z-score features, walk-forward with no look-ahead.
  - Canonical permutation applies `np.argsort(np.argsort(vix_means))` ⇒ state 0 = lowest VIX, state 3 = highest. ✓
  - Forward-fills labels between checkpoints — documented in source as conservative. ✓
  - **P3** — Magic constants `MIN_TRAIN_OBS=156`, `N_STATES=4`, `VIX_IDX=0`, `WALK_FORWARD_STEP=4` are duplicated across this script, `10_hicp_lag6_robustness.py`, `11_zew_swap_experiment.py`. A common config module would prevent drift if any of these changes.
  - **P3** — Resume logic requires `ckpt.get("label_switched") is True` but the script writes `"label_switched": True` unconditionally; the guard never triggers a mismatch. Cosmetic safety only.

### 2.3 `scripts/06_panel_a_long_horizon.py`
- **Role:** Panel A long-horizon backtest (11-asset baseline, 4 strategies).
- **Inputs:** `investable_returns_weekly.parquet`.
- **Outputs:** `panel_a_returns.parquet`, `panel_a_long_horizon_performance.csv`, `panel_a_long_horizon_summary.md`.
- **Findings:**
  - Simple-return arithmetic ✓. EURIBOR 3M used as time-varying RF, excluded from the risky universe ✓. 25% weight cap ✓. 4-week rebalance ✓. 156-week burn-in ✓. 260-week scenario cap ✓.
  - `_port` uses `w_df.shift(1) * ret` — implementation lag is correct.
  - `_weekly_to(w_df) = w_df.diff().abs().sum(axis=1) / 2.0` — one-way turnover convention (sum of absolute changes divided by 2). ✓ Standard.
  - `ann_to_pct = weekly_to.mean() * 52 * 100` — see Section 3 (turnover audit). Mathematically equivalent to per-rebalance turnover × 13 for 4-weekly rebalancing.
  - `_apply_tc(gross, to, rate) = gross − rate * to.shift(1)` — TC is charged in the week AFTER the rebalance, consistent with the 1-week implementation lag. ✓
  - **P3** — `MAX_WEIGHT = 0.25` is hard-coded here AND passed to `CVaRConfig(alpha=ALPHA, max_weight=MAX_WEIGHT)`. The fact that this override is needed only because the `CVaRConfig` default is 0.35 is a smell (see P1-E).

### 2.4 `scripts/07_panel_b_regime_oos.py`
- **Role:** Panel B regime-aware OOS backtest.
- **Inputs:** `investable_returns_weekly.parquet`, `regime_labels_wf_156.parquet`, `regime_probs_wf_156.parquet`.
- **Outputs:** `panel_b_returns.parquet`, `panel_b_regime_oos_performance.csv`, `panel_b_regime_oos_tc_sensitivity.csv`, `panel_b_regime_oos_summary.md`.
- **Findings:**
  - Regime CVaR-A: hard-filter mask `labels_hist == cur_lab`, falls back to static if `<30` scenarios. ✓
  - Weighted CVaR (importance-weighted) is implemented INLINE in this script (with its own LP) and ALSO in `src/optimization/cvar.weighted_cvar_weights`. The inline version is what runs. The library version is dead in the active pipeline.
  - **P1-D** — Hard-coded summary narrative quotes wrong turnover numbers; see Section 1.
  - **P2** — `regime_claim` text generated at line 316: "Regime CVaR-A achieves a **lower** gross Sharpe ratio than Static CVaR ... regime signal adds conditioning complexity without improving …" — content is correct, but the *threshold* uses `± 0.02` so a +0.165 swing (e.g. ZEW-swap variant rerun by mistake) could flip the narrative without a guard.
  - **P3** — Inline weighted-CVaR LP differs subtly from `src/optimization/cvar.weighted_cvar_weights`: inline uses `c[m+1:] = w_norm/(1-α)` (unnormalised by sample count) versus the library's `c[n+1:] = w_t/((1-α))`. Both forms re-weight z-coefficients; the produced `cvar` value scales differently but optimal `w` is unaffected. Worth de-duplicating.

### 2.5 `scripts/08_panel_statistical_tests.py`
- **Role:** HAC/Newey-West tests and block-bootstrap Sharpe CIs for Panel A and B.
- **Inputs:** `panel_a_returns.parquet`, `panel_b_returns.parquet`, EURIBOR column of returns parquet.
- **Outputs:** `panel_{a,b}_statistical_tests.{csv,md}`.
- **Findings:**
  - Uses `HAC_LAG=13` weeks, `BLOCK_LEN=13`, `N_BOOT=5_000`, `SEED=42`. ✓ Matches Methodology section 5.
  - Newey-West SE: `nw_var = γ0 + 2 Σ_k (1-k/(L+1)) γk` then `SE = sqrt(nw_var / n)`. ✓ Correct Bartlett-kernel formula.
  - Circular block bootstrap uses `(idx % n)` wrapping, `n_blocks = ceil(n/block)`, trimmed to `n` — standard CBB. ✓
  - **P3** — `t_dist.sf(t_stat, df=len(d)-1)` uses Student-t with one-sided tail; with `n>>30` and HAC SE this is conservative but a small-sample correction. Asymptotic normal would give nearly identical p-values for n≈800.
  - **P3** — Tests are computed against `equal_weight_risky` (benchmark) and one-sided H1: strategy > benchmark. Static CVaR's reported HAC t-stat is `−0.059` ⇒ p=0.5235 (one-sided). The negative t-stat appears because **arithmetic** mean excess return of Static CVaR (lower, by Jensen's inequality) is below EW although geometric/CAGR is higher. This is documented in `paper/notes/.../v8_FINAL_FOR_FEEDBACK_notes.md` as P2.8 (Known Remaining Issue). Acceptable for now.

### 2.6 `scripts/09_regime_timeline_figure.py`
- **Role:** Figure 1, full-sample HMM regime timeline.
- **Inputs:** `regime_labels_full.parquet` (in-sample, not regenerated by any active script — see P1-C), `investable_returns_weekly.parquet`.
- **Outputs:** `reports/figures/full_sample_regime_timeline.png`.
- **Findings:**
  - **P1-C** — Reads stale, non-canonical labels (see Section 1). Hard-coded `REGIME_LABELS` dict matches the current parquet by coincidence, not by design. There is no test or assertion to detect a future regeneration that would silently invert the colours.
  - **P2** — Source comment at line 31-36 contradicts the methodology document: *"4 states ordered by ascending stress (regime 3 = lowest VIX, regime 0 = highest)"*. Methodology says ascending VIX → state 0 lowest. The comment is technically correct for `regime_labels_full.parquet` but is reverse of every other script.
  - **P3** — The 4 fixed `EVENTS` are hard-coded; future re-use should pull from a shared `crisis_windows.yaml` or similar.

### 2.7 `scripts/10_hicp_lag6_robustness.py`
- **Role:** HICP-lag6 robustness (4 stages in one script).
- **Inputs:** `regime_features_weekly.parquet`, baseline CSV `panel_b_regime_oos_performance.csv` (for comparison).
- **Outputs:** 4 parquets, 1 pickle, 4 csv/md under `reports/panels/` and `reports/regimes/`.
- **Findings:**
  - Stage 1 lags both raw `hicp_headline_core_gap` AND recomputes `z52_hicp_headline_core_gap`. ✓ Correctly recomputes the z-score after the shift.
  - **6-week** lag throughout (constants, log messages, narrative). ✓
  - Stage 3 includes Equal-Weight TO using `_eq_drift_to` ✓.
  - **P3** — Stage 4's STATE_LABELS dict (0=Bull/Low-Vol, 3=Stress) uses the canonical convention — INCONSISTENT with Figure 1 (script 09). This works because Stage 4 operates on `regime_labels_wf_156_hicp_lag6.parquet` which is canonically ordered.
  - **P3** — `conclusion_stable = max_regime_diff < 0.02`. The actual `max_regime_diff` for regime strategies (regime_cvar_A: 0.365→0.433 in HICP-lag6 CSV) is ~ 0.068, so the script will write the *unstable* conclusion path. Verified by reading the produced file `reports/regimes/hicp_lag6_robustness.md`. This contradicts the paper text in `build_paper_v8.js:1149-1150`: *"Regime CVaR-A Sharpe changes by up to +0.068 relative to baseline, within the bootstrap confidence band of approximately +/-0.480. The main conclusion is unchanged."* The script's conclusion would recommend promoting the lag6 variant. Paper text and script narrative diverge.

### 2.8 `scripts/11_zew_swap_experiment.py`
- **Role:** ZEW feature-swap experiment.
- **Inputs:** `regime_variables_weekly.parquet`, `regime_features_weekly.parquet`, `investable_returns_weekly.parquet`.
- **Outputs:** `model_improvement/regime_features_weekly_zew_swap.parquet`, label/prob/checkpoint parquets, performance CSVs, statistical-test MD.
- **Findings:**
  - Correctly recomputes z52_ZEW_Germany with the same 52-week window. ✓
  - Replaces `z52_VSTOXX` with `z52_ZEW_Germany` in the 8-feature set. ✓ VIX_IDX still 0 (z52_VIX kept first) so state ordering still by VIX. ✓
  - **P3** — Statistical-test routines (Newey-West, block bootstrap) are DUPLICATED inline; should call into `src/optimization` or a new `src/evaluation` module.
  - **P3** — Script 11 generates `panel_b_summary_zew_swap.md` containing the auto-generated regime-claim narrative (same pattern as script 07, P1-D); when ZEW-swap Sharpe ≈ 0.483 > 0.530-0.02 boundary, the narrative may say "higher" or "similar" depending on data run; check actual file.

### 2.9 `scripts/12_rebalance_frequency_experiment.py`
- **Role:** Rebalance frequency sensitivity (1, 2, 4, 8 wk).
- **Findings:**
  - Docstring acknowledges freq=1 takes ~52 s and exceeds the 45 s sandbox limit; freq=1 is excluded from automated runs. ✓ Documented.
  - **P3** — Frequencies of 1, 2 lag the regime label by up to 3 weeks because the source labels are produced every 4 weeks and forward-filled. This is the *correct* "no look-ahead" treatment but it weakens the experiment's interpretation: the test isn't really a regime-update-frequency test — it's a portfolio-update frequency test against a stale 4-week regime signal. This is acknowledged in the docstring (lines 7-19).

### 2.10 `scripts/13_turnover_smoothing_experiment.py`
- **Role:** Exponential weight-averaging (EWA, γ=0.5) smoothing.
- **Findings:**
  - Mathematical claim that the 25% cap is preserved under convex combination is correct (assertion in script).
  - **P3** — Only γ=0.5 is tested (line 86: `GAMMA = 0.50`). The two-frequency × two-strategy × γ=0.5 grid is sparse but adequate for a robustness check.

### 2.11 `scripts/14_tc_aware_cvar_experiment.py`
- **Role:** TC-aware CVaR (L1 turnover term inside LP).
- **Findings:**
  - LP variable layout `[w(n), zeta, z(T), d(n)]` — d_i linearises |w_i − w_prev,i|. ✓ Correct standard formulation.
  - **P3** — Constants `EVAL_START = pd.Timestamp("2010-10-15")` is hard-coded. Mismatched if `regime_labels_wf_156.parquet` starts later (e.g. a different HMM warm-up) the script would fail silently. Should anchor to the first valid label date dynamically.

### 2.12 `scripts/15_regime_constraints_experiment.py`
- **Role:** Group-level regime-conditional weight constraints.
- **Findings:**
  - Mapping fixed 2026-05-12 (see source comment line 75-79) — State 2/3 inversion bug corrected; produces RC-CVaR Sharpe 0.522/0.519 baseline, 0.519/0.517 ZEW. ✓ Matches user-known values and paper.
  - State labels (0 = Low-vol/Subdued, ... 3 = Elevated-risk/Stress) match canonical convention. ✓
  - **P3** — Asset universe is hard-coded by string equality (`"CAC_40"`, etc.). If `investable_returns_weekly.parquet` ever renames a column, the script silently treats the asset as "neither equity nor defensive" and the constraint set is corrupted.

### 2.13 `scripts/16_fi_expanded_universe.py`
- **Role:** Append Germany/Spain/Italy government bond TR to the 11-asset universe.
- **Inputs:** `data/raw/fixed_income/*.xlsx`, `investable_prices_weekly.parquet`, `investable_returns_weekly.parquet`.
- **Outputs:** `investable_prices_weekly_fi_expanded.parquet`, `investable_returns_weekly_fi_expanded.parquet`, validation reports.
- **Findings:**
  - **VERIFIED** that the 11 baseline columns in `investable_returns_weekly_fi_expanded.parquet` are byte-identical to the baseline parquet (all 11 column equalities hold; no NaN-introduced divergence).
  - **VERIFIED** Italy/Spain/Germany are EUR-converted by LSEG (file names end with `EUR END OF DAY.xlsx`). ✓ Matches user-known fact that no native EUR Italy RIC exists.
  - Annualised return / vol from raw bond returns:  Germany 2.85% / 4.52%,  Spain 3.88% / 5.66%,  Italy 4.25% / 7.33%. Plausible for sovereign TR over 2000-2026.
  - Italy weekly extremes ±11.27%/11.40% occur in 2011-2012 (Eurozone crisis). Plausible.
  - **P3** — `FI_FILES` dict and `FI_RENAMES` dict are duplicative; can be collapsed.

### 2.14 `scripts/17_panel_a_fi_expanded.py` and `scripts/18_panel_b_fi_expanded.py`
- **Role:** Re-run Panel A and Panel B on the 14-asset universe.
- **Findings:**
  - All parameters identical to scripts 06 / 07. ✓
  - Reuse the SAME `regime_labels_wf_156.parquet` — does NOT refit the HMM. ✓ Documented.
  - **P3** — Strategy labels carry `"(FI-Exp)"` suffix in the strategy column, which is good for disambiguation, but means CSVs cannot be concatenated trivially with baseline CSVs without renaming.

### 2.15 `scripts/07_figures/generate_paper_figures.py`
- **Role:** Generates Figure 2 (cumulative wealth Panel B), Figure 3 (turnover vs net Sharpe scatter), Figure 4 (average weights baseline vs FI), Figure 5 (drawdown baseline vs FI), and Appendix F descriptive stats + correlations.
- **Findings:**
  - **P1-A** — Hard-coded `PAPER = '/sessions/friendly-keen-curie/mnt/PAPER'` on line 16; all `fig{2..5}` and `descriptive_stats` reference this prefix.
  - **P1-G** — Figure 3 datapoints are HARD-CODED in the script (lines 123-139) rather than read from `panel_b_regime_oos_tc_sensitivity.csv` / `tc_aware_cvar/tc_sensitivity.csv` / `regime_constraints/tc_sensitivity.csv`. As of v8 the hard-coded values match the corresponding CSVs (verified) but any future rerun of the underlying experiment will silently desynchronise Figure 3 from the source data.
  - **P1-H** — Figure 4 bar heights `baseline_w = [39.3, 9.7, 25.0, 25.0, 1.1, 0.0]` and `fi_exp_w = [3.0, 0.0, 10.0, 13.5, 0.0, 73.5]` are HARD-CODED (lines 196-197) from `fi_expanded_comparison.md`. Same desync risk.
  - **P2** — `fig5` recomputes drawdowns from parquets — correct and parquet-sourced. Good model for fig2-4 to follow.
  - **P3** — `axhline(static_y, ...)` highlights the 0.528 line on Figure 3 but the title says "Panel B (2010 to 2026)". OK.

### 2.16 `src/data/cleaning.py`
- **Findings:**
  - Date detection is robust (Excel-serial detection, DD/MM vs MM/DD auto-detection, quarter-year fallback). ✓
  - **P2** — `parse_euro_number` removes 'EUR', 'USD', 'GBP' but not e.g. '€', '$' or 'BPS'. Not currently a problem given LSEG files, but worth noting.
  - **P3** — `DATE_NAME_PATTERN = r"date|period|time"` does not match the German 'Datum'. Not an issue for current xlsx headers (English).

### 2.17 `src/data/transformations.py`
- **Findings:**
  - **VERIFIED** `compute_simple_returns` is used in `build_panels.build_investable_panels` for all non-cash assets, and `annualized_rate_to_weekly_return` for EURIBOR. ✓
  - `compute_log_returns` is retained but DOCUMENTED as "DEPRECATED for investable returns panel — use compute_simple_returns instead". ✓
  - `compute_log_returns` is still called in `src/data/feature_engineering.py:189` for *volatility-index* z-scores (rolling realised vol). This is appropriate (log-differences of vol indices) but only feeds the regime panel, not the investable return panel.
  - **P3** — `annualized_rate_to_weekly_return` heuristic: `if median > 1.0: r/=100.0`. Robust for EURIBOR, but is brittle on any policy rate near 100 bps.

### 2.18 `src/data/feature_engineering.py`
- Implements 46 features in `regime_features_weekly.parquet`; HMM uses 8 of them via `REGIME_FEATURES` filter.
- **P3** — Germany 2Y "outstanding bonds" series detection is well-guarded with documented fallback to ECB Deposit Facility Rate.
- **P3** — `regime_features_weekly.parquet` columns include lots of `delta_*_1w` and `rv_*_4w/12w` features that are computed but never used (the active 8-feature HMM uses only 8 of 46). Computational waste but not an error.

### 2.19 `src/models/hmm.py`
- **Findings:**
  - **P1-E (related)** — Defaults: `MIN_TRAIN_OBS = 260` (5 years), `WALK_FORWARD_STEP = 4`, `N_INIT = 15`, `N_ITER = 500`, `COVARIANCE_TYPE = "diag"`, `RANDOM_STATE = 42`. Active script `02_hmm_walkforward_156.py` overrides only `MIN_TRAIN_OBS=156` and `N_STATES=4`.
  - **P2** — Module docstring (line 13-14) says "Usage:  python scripts/02_fit_hmm.py" which is the ARCHIVED script. Should be `02_hmm_walkforward_156.py`.
  - **P2** — `run_hmm_pipeline()` writes `regime_labels_full.parquet`, `regime_labels_wf.parquet`, `regime_probs_wf.parquet`, `regime_dataset.parquet`, `hmm_diagnostics.json`. None of these are produced by an *active* script. The `regime_labels_full.parquet` and `regime_dataset.parquet` files currently in `data/processed/` are last-modified 2026-05-07 from a previous run of this function (the archived `scripts/archive/02_fit_hmm.py`). Their continued use by `scripts/09_regime_timeline_figure.py` ties Figure 1 to a non-canonical, no-longer-produced artefact (P1-C).
  - **P3** — `characterise_regimes` heuristic for `ACUTE_STRESS / FLIGHT_TO_QUALITY` uses `us10y_d` (i.e. `delta_US_10Y_Yield_1w`) which is NOT in the active 8-feature set; the lookup will return 0 (the default) and the branch is unreachable in production.

### 2.20 `src/optimization/cvar.py`
- **P1-E** — `CVaRConfig.max_weight = 0.35` default vs methodology 0.25.
- **P1-F** — `run_cvar_backtest()` (lines 218-331) is dead; the active pipeline uses inline LP code in scripts 07, 10, 11, 14, 18.
- **P2** — Two implementations of weighted-CVaR: the library `weighted_cvar_weights` and inline copies in scripts 07, 10, 11, 14. Need de-duplication.
- **P2** — `RegimeConstraints` / `REGIME_CONSTRAINTS_BY_LABEL` (lines 432-442) are dead: script 15 implements its own regime-constraint mapping. Kept-but-unused code.
- **P3** — `compute_metrics` (lines 338-410) is also dead in active pipeline; each script defines its own version. Inconsistent rounding policies.

### 2.21 `src/optimization/markowitz.py`
- **Findings:** Uses Ledoit-Wolf shrinkage with `fallback_to_equal=True`. Pattern used by scripts 06/07/10/11/17/18. ✓

### 2.22 Archive scripts (`scripts/archive/*`)
- 8 files: `02_fit_hmm.py`, `03_cvar_optimization.py`, `04_canonical_backtest.py`, `05_statistical_tests.py`, `hmm_walkforward_checkpoint.py`, `generate_data_inventory_yaml*.py`, `write_data_inventory_yaml_static.py`.
- **P2** — Three inventory-generator scripts contain `ROOT = Path(r"c:/Users/Jorge/OneDrive - UFV/BAINF/PAPER")` — Windows-personalised absolute paths. They are archived so this is informational, but the archive should ideally be `.gitignore`d or renamed `*.archived` so a future `pip install`+ `python -m runpy scripts/archive/...` cannot be misconfigured.
- **P2** — `04_canonical_backtest.py` (last modified 2026-05-09) is large (32 KB) and probably contains the older 2-state or 5-feature HMM logic. Confirmed it ARCHIVED but its presence next to active scripts is confusing.

### 2.23 `paper/build_paper_v8.js`
- **Role:** Generates the v8 docx + pdf using the `docx` JS library (Node).
- **P1-B** — Hardcoded `FIG_DIR = '/sessions/friendly-keen-curie/mnt/PAPER/paper/figures/'` (line 28). Will fail in any other session.
- **P2** — All tables and text are HARD-CODED. There is no pipeline that pulls Sharpe/CAGR/turnover from CSV. Any rerun of scripts 06/07/14/15 will desync from the paper unless the JS values are edited by hand.
- **P3** — File is 1715 lines, no helpers split out. Maintainability concern.

---

## 3. Cross-cutting issues

- **Duplicated helpers** — `_port`, `_weekly_to`, `_eq_drift_to`, `_apply_tc`, `compute_metrics`, `_solve_regime_cvar_A`, `_solve_weighted_cvar`, and the inline weighted-CVaR LP exist in 6-7 scripts each. A `src/evaluation/portfolio.py` would centralise.
- **Magic constants** — `ALPHA=0.95`, `MAX_WEIGHT=0.25`, `REBALANCE=4`, `MIN_HISTORY=156`, `SCENARIO_CAP=260`, `MIN_REGIME_SCENARIOS=30`, `ANN=52`, `CASH_COL="EURIBOR_3M"`, `STOXX_COL="StoxxEurope600"`, `TC_BPS_LIST=[0,5,10,25]` are each copied into 7-9 scripts. Drift risk on future edits.
- **Random seeds** — `RANDOM_STATE=42` in HMM; `SEED=42` for bootstrap. Documented, reproducible. ✓
- **NumPy / Pandas RNG** — only `np.random.default_rng(seed)` used in bootstrap; otherwise no random calls. ✓
- **Dead code** — `run_cvar_backtest`, `weighted_cvar_weights`, `RegimeConstraints`, `REGIME_CONSTRAINTS_BY_LABEL`, `compute_metrics` in `src/optimization/cvar.py`.

---

## 4. Issue counts by file (active scripts only)

| File | P1 | P2 | P3 | P4 |
|------|---:|---:|---:|---:|
| `scripts/07_figures/generate_paper_figures.py` | 3 | 1 | 1 | 0 |
| `paper/build_paper_v8.js` | 1 | 1 | 1 | 0 |
| `scripts/07_panel_b_regime_oos.py` | 1 | 1 | 1 | 0 |
| `scripts/09_regime_timeline_figure.py` | 1 | 1 | 1 | 0 |
| `src/optimization/cvar.py` | 2 | 2 | 1 | 0 |
| `src/models/hmm.py` | 0 | 2 | 1 | 0 |
| `scripts/02_hmm_walkforward_156.py` | 0 | 0 | 2 | 0 |
| `scripts/10_hicp_lag6_robustness.py` | 0 | 0 | 2 | 0 |
| `scripts/11_zew_swap_experiment.py` | 0 | 0 | 2 | 0 |
| `scripts/12_rebalance_frequency_experiment.py` | 0 | 0 | 1 | 0 |
| `scripts/13_turnover_smoothing_experiment.py` | 0 | 0 | 1 | 0 |
| `scripts/14_tc_aware_cvar_experiment.py` | 0 | 0 | 1 | 0 |
| `scripts/15_regime_constraints_experiment.py` | 0 | 0 | 1 | 0 |
| `scripts/16_fi_expanded_universe.py` | 0 | 0 | 1 | 0 |
| `scripts/17_panel_a_fi_expanded.py` | 0 | 0 | 1 | 0 |
| `scripts/18_panel_b_fi_expanded.py` | 0 | 0 | 1 | 0 |
| `scripts/01_validate_and_build_dataset.py` | 0 | 1 | 1 | 0 |
| `scripts/06_panel_a_long_horizon.py` | 0 | 0 | 1 | 0 |
| `scripts/08_panel_statistical_tests.py` | 0 | 0 | 2 | 0 |
| Archive scripts | 0 | 2 | 0 | 0 |
| `src/data/*` | 0 | 1 | 4 | 0 |

(Totals: 6 P1, 11 P2, 27 P3 — note many P3 items are sub-counted under cross-cutting.)

Detailed per-issue list is centralised in `master_project_issue_list.csv`.
