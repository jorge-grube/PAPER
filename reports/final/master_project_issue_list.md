# Master Project Issue List

**Audit date:** 2026-05-12
**Companion CSV:** `master_project_issue_list.csv` (sortable per-issue table)

This master list consolidates findings from all 14 audit sub-reports.

---

## 1. Severity definitions

| Severity | Meaning |
|----------|---------|
| **P1** | Must fix before sending to professor / private share |
| **P2** | Should fix before formal journal submission |
| **P3** | Nice to fix if time |
| **P4** | Future work / optional |

## 2. Counts

| Severity | Count | Changes empirical results? | Requires rerun? |
|----------|------:|:--------------------------:|:----------------:|
| P1 | 10 | 0 | 0 |
| P2 | 16 | 0 (one — P2-11 — affects only scope clarity) | 0 |
| P3 | 21 | 0 | 0 (P3-14 partial) |
| P4 | 5 | 0 | 0 |
| **Total** | **52** | **0** | **0** |

**KEY VERDICT: No P1, P2, or P3 issue changes any reported empirical number.** Every issue is about reproducibility, clarity, code hygiene, or descriptive accuracy.

## 3. P1 issues (10) — must address before share

| ID | Category | Headline | Effort (min) |
|----|----------|----------|-------------:|
| P1-01 | reproducibility | `scripts/07_figures/generate_paper_figures.py` hardcoded `/sessions/friendly-keen-curie/...` path | 5 |
| P1-02 | reproducibility | `paper/build_paper_v8.js` hardcoded `/sessions/friendly-keen-curie/...` path | 5 |
| P1-03 | methodology | Figure 1 state-numbering convention inverted vs. every other paper element | 30 |
| P1-04 | reports | Script 07 writes stale `(~100-160%) / (~10%)` turnover narrative into Panel B summary MD | 15 |
| P1-05 | methodology | `CVaRConfig.max_weight` default 0.35 vs documented 0.25 | 2 |
| P1-06 | reports | `hicp_lag6_robustness.md` auto-conclusion contradicts paper text | 15 |
| P1-07 | paper | `When Regimes Do Not Pay.pdf` is byte-identical to v7 (not v8) | 2 |
| P1-08 | reproducibility | Figure 3 datapoints hard-coded in script (not loaded from CSV) | 60 |
| P1-09 | reproducibility | Figure 4 bar heights hard-coded in script | 45 |
| P1-10 | methodology | Dead `run_cvar_backtest()` in `src/optimization/cvar.py` re-introduces stale logic if called | 10 |

**Total P1 effort: ≈ 3 hours.** None requires rerunning any experiment; none changes any numerical result.

## 4. P2 issues (16) — should fix before journal submission

(see CSV for full descriptions; highlights below)

- P2-01: `model_backtest_summary.md` regime VIX z-score table shows wrong WF values
- P2-02: stale paths in `model_backtest_summary.md` File Index
- P2-03: `docs/ACTIVE_OUTPUTS.md` doesn't flag `regime_labels_full.parquet` as orphan
- P2-04: no `package.json` for the JS paper build
- P2-05: `src/models/hmm.py` docstring references archived `02_fit_hmm.py`
- P2-06: `src/data/reporting.py` writes auto-generated CSVs to wrong destination (top-level `reports/`)
- P2-07 / P2-08 / P2-09: pre-public-release housekeeping (Spanish-language archive doc, Windows path in archive scripts, raw data not gitignored)
- P2-10: Two generations of regime-constraint weight parquets coexist
- P2-11: TC-aware/RC performance CSVs lack a "scope" column distinguishing full-history vs label-intersected Static CVaR (Sharpe 0.553 vs 0.530)
- P2-12: `EVAL_START` hardcoded in script 14
- P2-13: Inline weighted-CVaR LP duplicates library `weighted_cvar_weights`
- P2-14: Asset universe hardcoded in script 15 (no assertion)
- P2-15: `regime_average_weights.csv` missing naive-variant rows
- P2-16: Paper build script has no CSV ingestion (all values hand-coded)

**Total P2 effort: ≈ 8-10 hours.**

## 5. P3 issues (21) — nice to fix

Minor code-hygiene, documentation, and convention items. See CSV for details. None blocking.

## 6. P4 issues (5) — future / optional

Documentation polish, alternative kernel choices, license/citation files, etc.

## 7. Top 20 issues ranked by combined impact (severity × reader visibility)

1. **P1-02** — Paper build broken (most visible if anyone tries to rebuild the docx)
2. **P1-01** — Figure-generation broken (most visible if anyone tries to regenerate Figures 2-5)
3. **P1-07** — Misleading "When Regimes Do Not Pay.pdf" is the v7 build
4. **P1-04** — Hard-coded turnover narrative in auto-generated Panel B summary
5. **P1-06** — HICP-lag6 auto-MD contradicts paper text
6. **P1-03** — Figure 1 state-numbering inversion
7. **P1-05** — CVaRConfig.max_weight default 0.35 vs documented 0.25
8. **P1-08** — Figure 3 datapoints hard-coded
9. **P1-09** — Figure 4 bar heights hard-coded
10. **P2-01** — Wrong VIX z-scores in model_backtest_summary state table
11. **P2-02** — Stale paths in model_backtest_summary File Index
12. **P1-10** — Dead `run_cvar_backtest` could re-introduce stale logic
13. **P2-16** — No CSV→docx pipeline (manual sync of every table)
14. **P2-06** — Data pipeline writes auto-CSVs to wrong directory
15. **P2-09** — Raw LSEG data not gitignored (public-release risk)
16. **P2-10** — Pre/post-correction regime-constraint parquets coexist
17. **P2-04** — No package.json pinning docx version
18. **P2-11** — No scope tag for 0.530 vs 0.553 Static CVaR
19. **P2-05** — src/models/hmm.py docstring references archived script
20. **P2-07** — `docs/archive/MIGRATION.md` contains Spanish-language author preferences

## 8. Quick-fix bundle (recommended pre-share)

If only ~30 minutes are available before sharing the v8 paper with the professor, the minimum-viable fix list is:

1. **P1-04** — Edit `scripts/07_panel_b_regime_oos.py:381-383` to use actual CSV values (15 min)
2. **P1-07** — Delete `paper/drafts/When Regimes Do Not Pay.pdf` or regenerate from v8 (2 min)
3. **P1-05** — Change `CVaRConfig.max_weight` default to 0.25 (2 min)
4. **P2-02** — Fix 3 stale paths in `reports/final/model_backtest_summary.md` File Index (5 min)
5. **P2-01** — Fix the 4 WF VIX z-scores in `reports/final/model_backtest_summary.md` (5 min)

**Total: 30 min.** After these, the project is ready to share.

The remaining P1 issues (P1-01, P1-02, P1-03, P1-06, P1-08, P1-09, P1-10) are reproducibility / robustness items that do NOT block sharing the v8 paper for feedback. They DO block third-party reproduction of the figures and paper build.

## 9. Detailed reading list

For full per-issue descriptions, refer to:

- `reports/final/python_code_audit.md` — issues in source code
- `reports/final/turnover_transaction_cost_audit.md` — turnover-specific verifications
- `reports/final/parquet_data_audit.md` — data integrity
- `reports/final/csv_output_audit.md` — CSV integrity
- `reports/final/markdown_report_audit.md` — markdown integrity
- `reports/final/figure_image_audit.md` — figure provenance
- `reports/final/paper_artifact_audit.md` — paper builds and notes
- `reports/final/paper_traceability_audit.md` — paper element → source
- `reports/final/reproducibility_audit.md` — clean-rerun feasibility
- `reports/final/methodology_consistency_audit.md` — stale methodology scan
- `reports/final/headline_number_audit.md` — every published number verified
- `reports/final/archive_contamination_audit.md` — archive-vs-active separation
- `reports/final/sharing_safety_audit.md` — public/private share readiness
