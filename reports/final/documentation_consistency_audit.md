# Documentation Consistency Audit

**Date:** 2026-05-10  
**Auditor role:** Senior reproducibility auditor / finance methodology editor  
**Scope:** Documentation files only — no code, data, or empirical results changed.

---

## A. Files Changed

| File | Changes made |
|------|-------------|
| `docs/METHODOLOGY.md` | Complete rewrite of Section 3 (HMM); new Section 8 (FI); fixed stat test language; fixed HICP lag; fixed Sharpe delta; removed Bull/Bear; removed DM; corrected Regime CVaR framing |
| `docs/RUN_ORDER.md` | Fixed script 08 description (DM→HAC/NW); fixed script 10 description (6 months→6 weeks) |
| `docs/ACTIVE_OUTPUTS.md` | Fixed regime_features description (5→46/8); fixed HICP lag (6m→6w); fixed stat test label (DM→HAC/NW, ×2) |
| `data/README_DATA.md` | Corrected regime_features shape (1369×5→~3400×46); corrected 8-feature HMM table; corrected prob file shape (×2→×4); corrected HICP lag (6 months→6 weeks); added 4-state label description; removed Bull/Bear |
| `README.md` | Fixed stat test table entries (DM→HAC/NW, ×2); added 4-state and 8-feature rows to Panel B table; added heuristic state label names |

`docs/REPO_STRUCTURE.md` — no methodology claims present; no change required.

---

## B. Inconsistencies Found

### B1 — HMM state count (critical)

**Claimed in docs:** 2-state HMM  
**Actual code (`scripts/02_hmm_walkforward_156.py`):** `N_STATES = 4`  
**Impact:** All references to "Bull/Bear", "state 1", "Bear (state 1)" were factually wrong. Regime CVaR-A filters on current state (0–3), not a binary label.

### B2 — HMM feature set (critical)

**Claimed in docs:** 5 raw macro series: EURIBOR 3M level, HICP YoY, EuroStoxx50 weekly return, EuroStoxx50 realised vol (13w), Germany 10Y yield level  
**Actual code (`src/models/hmm.py`, `REGIME_FEATURES` constant):** 8 features, all 52-week rolling z-scores: z52_VIX, z52_VSTOXX, z52_MOVE, z52_germany_10y_2y_slope, z52_peripheral_spread_avg, z52_DXY_USD_Index, z52_Eurozone_Economic_Sentiment_Indicator, z52_hicp_headline_core_gap  
**Additional:** `regime_features_weekly.parquet` contains 46 engineered columns; `select_and_impute` selects only the 8 listed above. Shape ~3400×46, not 1369×5.

### B3 — Statistical test name (critical)

**Claimed in docs:** "Diebold-Mariano (DM) tests" / "DM + bootstrap"  
**Actual code (`scripts/08_panel_statistical_tests.py`, line 8 docstring and implementation):** "Pairwise HAC/Newey-West test of mean excess-return differentials (lag=13 weeks)" using `newey_west_se()` and `hac_nw_test()`. This is not a Diebold-Mariano test — DM requires a loss-differential series from competing forecast errors.

### B4 — HICP lag duration (material)

**Claimed in docs:** "6 months" (METHODOLOGY.md, ACTIVE_OUTPUTS.md, README_DATA.md)  
**Actual code (`scripts/10_hicp_lag6_robustness.py`):** `HICP_LAG_WEEKS = 6` — **6 weeks**. The script name `hicp_lag6` refers to 6 weeks, not 6 months.

### B5 — HICP robustness Sharpe delta (material)

**Claimed in METHODOLOGY.md:** "Negligible change (Sharpe delta <0.01)"  
**Actual output (`reports/regimes/hicp_lag6_robustness.md`):** Maximum Sharpe change across regime strategies: **+0.068**. This is not negligible — it is material (though within bootstrap confidence intervals). The report itself flags this as "important methodological consideration" and recommends promoting to a primary robustness table.

### B6 — Regime CVaR-A gross Sharpe framing (material)

**Claimed/implied:** Some docs implied regime conditioning provides a gross Sharpe advantage over Static CVaR.  
**Actual data (`reports/panels/panel_b_regime_oos_performance.csv`):** Regime CVaR-A gross Sharpe = **0.365**; Static CVaR gross Sharpe = **0.530**. Regime CVaR-A is substantially below Static CVaR even before transaction costs (225.75% annual turnover vs 21.40%). There is no gross Sharpe advantage.

### B7 — Regime probability file columns (minor)

**Claimed in README_DATA.md:** `regime_probs_wf_156.parquet` — "2 columns: P(Bull), P(Bear)"  
**Actual:** 4 columns (one per state), consistent with 4-state HMM.

---

## C. Final Confirmed Methodology

| Item | Confirmed value |
|------|----------------|
| HMM states | **4** |
| HMM features | **8** (z52_VIX, z52_VSTOXX, z52_MOVE, z52_germany_10y_2y_slope, z52_peripheral_spread_avg, z52_DXY_USD_Index, z52_Eurozone_Economic_Sentiment_Indicator, z52_hicp_headline_core_gap) |
| HMM covariance | diagonal (`covariance_type="diag"`) |
| HMM restarts | 15; 500 EM iterations |
| State ordering | ascending mean z52_VIX |
| State heuristic labels | Risk-on/Expansion, Low-vol/Subdued, Neutral/Moderate, Elevated-risk/Stress |
| Walk-forward burn-in | 156 weeks (Panel B); 260 weeks (canonical HMM) |
| Statistical test | Pairwise HAC/Newey-West (Newey-West lag=13w) |
| Bootstrap | Circular block bootstrap, block=13w, 10,000 draws |
| HICP lag (robustness) | **6 weeks** |
| HICP Sharpe delta | Up to **+0.068** (material; within bootstrap noise) |
| Regime CVaR-A gross Sharpe | **0.365** (below Static CVaR 0.530) |
| Regime CVaR-A ann. turnover | **225.75%** |
| Static CVaR ann. turnover | **21.40%** |
| Correct framing | Regime conditioning does not outperform Static CVaR; it reduces interpretability cost but not return cost |
| Baseline universe | 11 assets (10 risky + EURIBOR 3M risk-free) |
| FI-expanded universe | 14 assets (adds DE, ES, IT govt bond TR) |
| Italy RIC | `.FTIT_TSYUSDT` — EUR via LSEG currency conversion; no native EUR RIC |
| UK Gilt / BBG 10+ / ECB yields | Excluded from investable universe |

---

## D. Remaining Warnings

### D1 — HICP robustness recommendation not acted on (documentation only)

The `hicp_lag6_robustness.md` report recommends "promoting the lagged-HICP variant from appendix to a primary robustness table in the main paper." This recommendation is documented but has not yet been implemented in the paper draft. The paper draft (`paper/drafts/paper_draft_JF_style.docx`) has not been audited here — it may still contain "Diebold-Mariano", "2-state", "Bull/Bear", "6 months", or other stale terminology from earlier drafts.

### D2 — Paper draft not audited

`paper/drafts/paper_draft_JF_style.docx` is a binary file and was not inspected. It likely carries the pre-correction terminology. A separate pass is needed before journal submission.

### D3 — `regime_features_weekly.parquet` frequency ambiguity

The file contains ~3,400 rows, which appears super-weekly (input data comes from mixed-frequency macro sources). Script 01 aligns to weekly before writing `investable_returns_weekly.parquet`, but the regime feature engineering may operate at a different cadence. This does not affect backtest correctness (the HMM only uses weekly-aligned rows), but the shape description in data docs may be confusing. No action taken — flagged for future clarification.

### D4 — `hmm_regime_summary.md` not updated

`reports/regimes/hmm_regime_summary.md` is auto-generated by an earlier run and may contain 2-state language or stale characterisations. It was not updated here (it is a computed output, not documentation). Rerunning script 02 would regenerate it with correct 4-state content.

### D5 — MIN_TRAIN_OBS discrepancy

`src/models/hmm.py` sets the canonical constant `MIN_TRAIN_OBS = 260` weeks. `scripts/02_hmm_walkforward_156.py` overrides this to 156 for Panel B. Both values are correct and intentional. Documentation (METHODOLOGY.md Section 3, RUN_ORDER.md Stage 2) now consistently describes 156 for the walk-forward script; 260 is the module default for canonical full-window fitting.

---

## E. Paper-Shareability Assessment

**Status: Conditionally paper-shareable.**

The six documentation files (`README.md`, `docs/METHODOLOGY.md`, `docs/RUN_ORDER.md`, `docs/ACTIVE_OUTPUTS.md`, `data/README_DATA.md`, `docs/REPO_STRUCTURE.md`) are now internally consistent with the actual code and empirical outputs. The following residual actions are required before journal submission:

1. **Audit and correct `paper/drafts/paper_draft_JF_style.docx`** — remove DM, 2-state, Bull/Bear, 6-month HICP references; add correct 4-state/8-feature/HAC language.
2. **Decide on HICP robustness positioning** — the report recommends it as a primary table; this is a paper-writing decision, not a code issue.
3. **Regenerate `reports/regimes/hmm_regime_summary.md`** (run script 02) if the 4-state characterisation table in that report is needed for citation.
