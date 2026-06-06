# Parquet Data Audit

**Audit date:** 2026-05-12
**Files inspected:** 27 active parquets + 2 archive samples
**Companion CSV:** `parquet_schema_inventory.csv` (shape, dates, NaN, duplicates).

---

## 1. Canonical baseline parquets

| File | Rows | Cols | Date range | NaN | Verdict |
|------|----:|----:|---|----:|--------|
| `data/processed/investable_prices_weekly.parquet` | 1370 | 11 | 2000-01-07 → 2026-04-03 | 0 | ✓ Clean |
| `data/processed/investable_returns_weekly.parquet` | 1370 | 11 | 2000-01-07 → 2026-04-03 | 10 | ✓ Clean (NaNs in opening rows due to pct_change initial) |

**Verified columns** (matches METHODOLOGY.md):
```
['EURIBOR_3M', 'Bloomberg_Commodity', 'Brent', 'Gold', 'CAC_40', 'DAX',
 'EuroStoxx50', 'FTSE_MIB', 'IBEX35', 'StoxxEurope600', 'FTSE_EPRA_NAREIT_Europe']
```

**EURIBOR_3M is correctly a weekly return series** (not a raw annualised rate). Mean ≈ 0.0006 per week (~3% annual when rates were high), and median ≈ 0.00028 per week (~1.5% annual). The first 3 values are 0.000628–0.000629, consistent with annualised ~3.3% in early 2000 → weekly simple return = `(1.033)^(1/52)-1 ≈ 0.000625`. ✓

## 2. FI-expanded parquets

| File | Rows | Cols | Date range | NaN |
|------|----:|----:|---|----:|
| `investable_prices_weekly_fi_expanded.parquet` | 1370 | 14 | 2000-01-07 → 2026-04-03 | 0 |
| `investable_returns_weekly_fi_expanded.parquet` | 1370 | 14 | 2000-01-07 → 2026-04-03 | 14 |

**Verified:**
- All 11 baseline columns are **byte-identical** to the baseline parquet (no rounding drift, no NaN drift).
- 3 new columns: `Germany_GovtBond`, `Spain_GovtBond`, `Italy_GovtBond`. ✓
- Sovereign bond return summary stats:
  | Series | n | mean annual % | vol annual % | min weekly | max weekly |
  |---|---:|---:|---:|---:|---:|
  | Germany_GovtBond | 1369 | 2.85% | 4.52% | −2.94% | +2.93% |
  | Spain_GovtBond | 1369 | 3.88% | 5.66% | −3.59% | +6.21% |
  | Italy_GovtBond | 1369 | 4.25% | 7.33% | −11.40% | +11.27% |

  Italy's extreme tails (±11%) occur in the 2011–2012 Eurozone sovereign crisis. Plausible.

- File-naming confirms LSEG **EUR-converted** sources (e.g. `FTSE ITALIAN GOVERNMENT BOND TOTAL RETURN INDEX EUR END OF DAY.xlsx`). ✓ Matches user-known fact that no native EUR Italy RIC exists.

## 3. Regime feature / variable parquets

| File | Rows | Cols | Date range | NaN |
|------|----:|----:|---|----:|
| `regime_features_weekly.parquet` | 3457 | 46 | 1960-02-05 → 2026-05-01 | 66,786 |
| `regime_features_weekly_hicp_lag6.parquet` | 3457 | 46 | 1960-02-05 → 2026-05-01 | 66,786 |
| `regime_variables_weekly.parquet` | 3462 | 35 | 1960-02-05 → 2026-06-05 | 60,593 |
| `regime_features_weekly_zew_swap.parquet` | 3457 | 47 | 1960-02-05 → 2026-05-01 | 69,124 |

**Verified:** the only difference between baseline and `hicp_lag6` is the `hicp_headline_core_gap` and `z52_hicp_headline_core_gap` columns (raw and z-scored both lagged 6 weeks).
**Verified:** zew_swap variant has +1 column `z52_ZEW_Germany`. ✓

**Caveat:** these files span 1960-2026 because some macro series start in the 1960s (HICP). The HMM training only begins once `select_and_impute` drops residual-NaN rows, which truncates to roughly 1999–2026. The 46-column count includes many derived features unused by the 8-feature HMM. Documentation accurately notes "regime_features_weekly.parquet — 46 engineered columns; HMM selects 8 z-score features" (`docs/ACTIVE_OUTPUTS.md` line 25).

`regime_variables_weekly.parquet` has 35 columns and ends 2026-06-05 (further than other parquets). This file is read **only** by script 11 to look up the raw ZEW_Germany column. Acceptable.

## 4. HMM label / probability parquets

| File | Rows | Cols | Valid label range | NaN |
|------|----:|----:|---|----:|
| `regime_labels_wf_156.parquet` | 1123 | 1 | first valid 2007-10-19 → last 2026-05-01 | 155 (burn-in) |
| `regime_probs_wf_156.parquet` | 1123 | 4 | same | 620 (155 NaN × 4 cols) |
| `regime_labels_wf_156_hicp_lag6.parquet` | 1122 | 1 | first valid 2007-10-26 → 2026-05-01 | 155 |
| `regime_probs_wf_156_hicp_lag6.parquet` | 1122 | 4 | same | 620 |
| `regime_labels_full.parquet` | 1123 | 1 | 2004-10-29 → 2026-05-01 | 0 |
| `regime_dataset.parquet` | 1123 | 10 | 2004-10-29 → 2026-05-01 | 0 |
| model_improvement: zew_swap labels / probs | 1123 / 1123 | 1 / 4 | same as baseline | 155 / 620 |

**Verified:**
- Posterior probabilities sum to 1 (min, max, mean all = 1.000000). ✓
- Burn-in NaN count: 155 rows (the first 156 rows minus 1 to align with `end - 1` indexing). ✓
- Labels use {0, 1, 2, 3} integer states. ✓
- Distributions (canonical WF):

  | State | Frequency |
  |------|----------:|
  | 0 | 23.1% (224 weeks) |
  | 1 | 30.2% (292 weeks) |
  | 2 | 25.6% (248 weeks) |
  | 3 | 21.1% (204 weeks) |

  Mean z52_VIX by state: 0 = −0.71, 1 = −0.40, 2 = +0.17, 3 = +1.02. **Canonical ordering verified.** ✓
- ZEW-swap label distribution: {0: 25.6, 1: 21.1, 2: 26.9, 3: 26.4}. Different from baseline distribution (as expected since label agreement is only 47.93%).

### 4.1 ⚠ `regime_labels_full.parquet` uses NON-canonical state ordering

Mean z52_VIX by state for `regime_labels_full.parquet`:

| State | n | mean(z52_VIX) | Caller's REGIME_LABELS dict |
|---|---:|---:|---|
| 0 | 222 | **+1.849** (HIGHEST) | "High-Stress / Crisis" ✓ for THIS file |
| 1 | 320 | −0.591 | "Recovery / Growth" |
| 2 | 302 | +0.048 | "Moderate" |
| 3 | 279 | **−0.959** (LOWEST) | "Bull / Low-Vol" ✓ for THIS file |

This is the OPPOSITE convention from `regime_labels_wf_156.parquet`. Script 09 / Figure 1 hard-codes labels to match THIS non-canonical ordering. No active script regenerates `regime_labels_full.parquet`; the file is from a previous run of the archived `02_fit_hmm.py`. (See `python_code_audit.md` issue P1-C.)

### 4.2 Label-agreement verification

- **ZEW-swap vs baseline:** 0.479339 = **47.9339%** ≈ 47.9% ✓ (matches user)
- **HICP-lag6 vs baseline:** 0.5512 = **55.12%** ≈ 55% ✓ (matches paper text)

## 5. Panel return parquets

| File | Rows | Cols | Date range | NaN |
|------|----:|----:|---|----:|
| `panel_a_returns.parquet` | 1213 | 4 | 2003-01-10 → 2026-04-03 | 2 |
| `panel_b_returns.parquet` | 808 | 6 | 2010-10-15 → 2026-04-03 | 4 |
| `panel_a_returns_fi_expanded.parquet` | 1213 | 4 | 2003-01-10 → 2026-04-03 | 2 |
| `panel_b_returns_fi_expanded.parquet` | 808 | 6 | 2010-10-15 → 2026-04-03 | 4 |
| `model_improvement/panel_b_returns_zew_swap.parquet` | 808 | 6 | same | 4 |

**Verified Sharpe ratios re-computed from parquets** (against EURIBOR rf, ×√52):

| Strategy | Sharpe (parquet) | Sharpe (CSV) | Match |
|---|---:|---:|---|
| equal_weight_risky | 0.409 | 0.409 | ✓ |
| stoxx600 | 0.363 | 0.363 | ✓ |
| static_cvar | **0.530** | 0.530 | ✓ |
| markowitz | 0.447 | 0.447 | ✓ |
| regime_cvar_A | **0.365** | 0.365 | ✓ |
| weighted_cvar | 0.369 | 0.368 (rounding) | ✓ |

NaN distribution: Panel A `static_cvar` and `markowitz` have first-row NaN (no `i-1` weight to apply); same in Panel B. Standard 1-week implementation lag artefact. ✓ Documented in `_port` via `min_count=1`.

## 6. Weight parquets (regime_constraints, tc_aware)

| File | Rows | Cols | Notes |
|------|----:|----:|-------|
| `weights_rc_baseline.parquet` | 808 | 10 | 10 risky columns; max weight 0.250 ✓; row sums = 1 ✓ |
| `weights_rc_zew.parquet` | 808 | 10 | same |
| `tc_aware_cvar/weights_*.parquet` | varies | 10 | 30+ files (baseline + tau×3 + lambda×3) × 4 base strategies |
| `regime_constraints/weights_regime_cvar_A.parquet` | (older gen, 2026-05-10) | 10 | **GENERATION 1** — see below |
| `regime_constraints/weights_rc_baseline.parquet` | (newer gen, 2026-05-12) | 10 | **GENERATION 2** — currently active |
| `fi_expanded/weights_regime_constrained_fi_expanded.parquet` | 964 | 13 | Spans 2007-10-19 → 2026-04-03; first 13 risky cols include 3 govt bonds |

### 6.1 ⚠ Two generations of regime-constraint weights coexist

`data/processed/model_improvement/regime_constraints/` contains:

- Older (2026-05-10): `weights_regime_cvar_A.parquet`, `weights_weighted_cvar.parquet`, `weights_zew_regime_cvar_A.parquet`, `weights_zew_weighted_cvar.parquet`, `weights_static_cvar.parquet`. These are the **pre-correction** regime-constrained weights from the incorrect State 2/3 mapping.
- Newer (2026-05-12): `weights_rc_baseline.parquet`, `weights_rc_zew.parquet`. These are produced by the CURRENT script 15 with the corrected mapping.

Script 15 currently only WRITES `weights_rc_baseline.parquet` and `weights_rc_zew.parquet`. The older files are no longer regenerated but are not archived; their presence is potentially confusing (P2). See `archive_contamination_audit.md`.

## 7. Archive parquets

Inspected `data/processed/archive/regime_labels_wf.parquet` (12 KB, 2026-05-08): 1123 rows, 1 col, 259 NaN. This is from the older `02_fit_hmm.py` walk-forward; the higher NaN count (259 vs canonical 155) indicates a different `MIN_TRAIN_OBS`. **Confirmed archived; not consumed by active scripts.**

`data/processed/archive/canonical_backtest_returns.parquet` (57 KB, 2026-05-08): 704 rows, 7 cols, dates 2012-10-12 → 2026-04-03. This is from the OLD archive script 04_canonical_backtest.py. Distinct strategies (likely includes old regime_B and 5-feature variants). **Confirmed archived.**

## 8. Suspicious observations / outlier checks

- **No suspicious zeros** in any active parquet (zero values only appear in burn-in NaN rows or the rebalance-week=0 turnover, which is expected).
- **No duplicate rows or indices** in any active parquet (`dup=0` across the board).
- **Italy bond extreme weekly returns (±11%)** are concentrated in the Eurozone crisis (Nov 2011 – Sep 2012). Spot-check: 2011-12-09 week (Mario Monti government) and 2012-08-03 (Draghi "whatever it takes") both visible. Plausible.
- **HICP gap z-scores** in `regime_features_weekly_hicp_lag6.parquet`: the lag operation correctly recomputes the z-score on the lagged feature.
- **The `select_and_impute` function in src/models/hmm.py** drops rows with residual NaN in any of the 8 HMM features. This correctly truncates the dataset to the earliest week with all 8 features observable; result: WF labels start 2007-10-19 (after 156-week burn-in from the first usable feature row ~2004-10).

## 9. Date alignment audit

All active parquets use **Friday close (`W-FRI`)** index. Median step = 7.0 days. ✓

Date-range cross-check:
- Investable returns: 2000-01-07 → 2026-04-03 (1370 wk)
- Panel A starts: 2003-01-10 (= 2000-01-07 + 156 wk ≈ 3 yr burn-in) ✓
- Panel B starts: 2010-10-15 (= first WF label date 2007-10-19 + 156 wk = 2010-10-08; actual 2010-10-15 has one extra week due to label burn-in offset) ✓

## 10. Documentation alignment

`docs/ACTIVE_OUTPUTS.md` lists 14 active parquet files; **all are present**. Two extra parquets exist in `data/processed/` (`regime_dataset.parquet`, `regime_labels_full.parquet`) that are NOT listed as active but are consumed by `scripts/09_regime_timeline_figure.py`. Documentation update needed (see `markdown_report_audit.md`).

`data/README_DATA.md` accurately describes the data dictionary, but does not list the FI-expanded parquets explicitly. The metadata.yaml (auto-generated by `01_validate_and_build_dataset.py`) is comprehensive for raw inputs.

## 11. Summary verdict

- **All active parquets schema/date/format check pass.** ✓
- **Returns are simple arithmetic, EURIBOR converted to weekly simple return.** ✓
- **Labels in canonical wf_156 follow the canonical ascending-VIX ordering.** ✓
- **Posterior probabilities sum to 1, no NaN where expected to be data, NaN preserved in burn-in.** ✓
- **NO contamination of FI-expanded existing 11 columns by raw bond data.** ✓
- **Italy/Spain/Germany sovereign bond TR series are EUR-converted by LSEG.** ✓
- **ZEW label agreement is exactly 47.9339% (rounds to 47.9%).** ✓
- **One material concern (P1-C):** `regime_labels_full.parquet` is orphaned and uses a non-canonical state ordering; consumed only by Figure 1.
- **One material concern (P2):** two generations of regime-constraint weight parquets coexist under `data/processed/model_improvement/regime_constraints/`.
