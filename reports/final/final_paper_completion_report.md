# Final Paper Completion Report
**Paper:** When Regimes Do Not Pay: Tail-Risk Allocation, Sovereign Bonds, and Implementation Frictions in European Multi-Asset Portfolios  
**Author:** Jorge Grube  
**Report date:** 2026-05-13  
**Status:** READY FOR FEEDBACK

---

## Deliverables

| File | Size | Status |
|---|---|---|
| `paper/drafts/paper_draft_FINAL.docx` | 1,427 KB | ✓ Built, clean |
| `paper/drafts/paper_draft_FINAL.pdf` | 1,591 KB | ✓ Exported, 47 pages |
| `paper/drafts/When Regimes Do Not Pay - FINAL FOR FEEDBACK.pdf` | 1,591 KB | ✓ Named copy |
| `paper/build_paper_FINAL.js` | ~100 KB | ✓ Reproducible |
| `paper/notes/paper_draft_FINAL_notes.md` | — | ✓ Editor notes |
| `reports/final/final_paper_reframe_report.md` | — | ✓ Reframe rationale |

---

## Work Log (Sessions)

### Pre-FINAL (Tasks 58–66)

| Task | Description | Outcome |
|---|---|---|
| 58 | Regenerate Figures 1–5 without banned symbols | All 5 PNGs clean |
| 59 | Fix script 15 regime constraint inversion (States 2/3 swapped) | RC values corrected: baseline 0.522/0.519/29.2% |
| 60 | Reconcile Static CVaR 0.530 vs. 0.553 discrepancy | Root cause identified; scope note added to Table VII |
| 61 | Fix stale paths and labels in model_backtest_summary.md | 7 paths corrected; state labels updated |
| 62 | Build v8 DOCX: all P1+P2+P3 fixes | v8 DOCX/PDF produced; CLEAN |
| 63 | Verify Frazzini 2015; move gen_figures.py | SSRN note added; script moved to scripts/07_figures/ |
| 64 | Write v8 notes and correction report | v8_correction_report.md, notes file |
| 65 | P1 quick fixes: hardcoded paths, CVaRConfig default, stale turnover, dead code, HICP conclusion, old PDF | All 10 P1 issues resolved |
| 66 | Read all audit files and build script to plan FINAL | Planning complete |

### FINAL build (Tasks 67–68)

| Task | Description | Outcome |
|---|---|---|
| 67 | Build paper_draft_FINAL.docx with intellectual reframe | DOCX 1427 KB, PDF 1591 KB, 47 pages, CLEAN |
| 68 | Write FINAL notes, completion report, named PDF | All files produced |

---

## All Issues Resolved

### P1 Issues (blocking)

| Issue | Status |
|---|---|
| P1.1 — Banned symbols in figures | Resolved (Task 58) |
| P1.2 — Bootstrap count 10,000 → 5,000 (3 locations) | Resolved (Task 62) |
| P1.3 — Script 15 regime constraint inversion | Resolved (Task 59) |
| P1.4 — Static CVaR 0.530 vs. 0.553 discrepancy | Resolved (Task 60/62) |
| P1.5 — Stale paths and labels in model_backtest_summary.md | Resolved (Task 61) |
| P1-01 — Hardcoded session path in generate_paper_figures.py | Resolved (Task 65) |
| P1-02 — Hardcoded session path in build scripts | Resolved (Task 65) |
| P1-03 — Figure 1 state ordering | Documented (Task 65) |
| P1-04 — Stale turnover narrative in script 07 | Resolved (Task 65) |
| P1-05 — CVaRConfig.max_weight default 0.35 vs. 0.25 | Resolved (Task 65) |
| P1-06 — HICP-lag6 auto-conclusion contradicts paper | Resolved (Task 65) |
| P1-07 — Misleading named PDF | Resolved (Task 65/68) |
| P1-08/09 — Figure 3/4 datapoints hard-coded | Documented (Task 65) |
| P1-10 — Dead run_cvar_backtest() | Deprecation warning added (Task 65) |

### P2 Issues (quality)

| Issue | Status |
|---|---|
| P2.1/P2.10 — Table I TR note (Brent/gold not TR indices) | Resolved (Task 62) |
| P2.3 — Frazzini 2015 citation | SSRN note added (Task 63) |
| P2.4 — gen_figures.py location | Moved to scripts/07_figures/ (Task 63) |
| P2.5 — Introduction trimmed ~30% | Resolved (Task 62) |
| P2.6 — Nontechnical closing sentence | Added (Task 62) |
| P2.7 — Data licensing notice in Section I.B | Added (Task 62) |
| P2.8 — HAC t-stat arithmetic/geometric explanation | Deferred (low priority for feedback round) |
| P2.9 — Section V.A 0.528 reference | Resolved (Task 62) |
| P2.11 — Fig 3 reference line | Deferred (Fig 3 caption note needed) |

### P3 Issues (minor)

| Issue | Status |
|---|---|
| P3.7 — ESI correlation precision | Resolved (Task 62) |
| P3.8 — Newey-West inline citation | Resolved (Task 62) |

### FINAL-specific additions

| Addition | Status |
|---|---|
| Abstract rewritten (<100 words, detection-vs-implementation) | Done (Task 67) |
| Introduction rewritten (8 paragraphs, detection succeeds/translation fails) | Done (Task 67) |
| TABLE X mechanism summary (6 rows × 5 columns, Section VIII) | Done (Task 67) |
| Limitations subsection expanded (HMM labels, feature sensitivity, release timing, TC, data) | Done (Task 67) |

---

## Empirical Integrity

**No empirical results were changed in Tasks 67–68.** All canonical Panel B numbers (Tables IV, V, VI) are identical to v8, which are identical to the corrected v8 values (RC corrected in Task 59, all others unchanged from v7).

Specific values confirmed unchanged:
- Static CVaR: 0.530 gross Sharpe, 0.528 net@10bps, 21.4% Ann.TO
- Regime CVaR-A: 0.365 gross Sharpe, 0.346 net@10bps, 225.8% Ann.TO
- RC-CVaR baseline: 0.522 gross, 0.519 net@10bps, 29.2% Ann.TO
- RC-CVaR ZEW-swap: 0.519 gross, 0.517 net@10bps, 27.0% Ann.TO
- TC-aware penalized (λ=0.005): net Sharpe 0.486, ~60% Ann.TO

---

## Pre-Submission Remaining Work

For journal submission (not required for this feedback round):

1. Resolve P2.8 (arithmetic vs. geometric HAC t-stat, Section IV.B)
2. Add Fig 3 caption note clarifying the dashed reference line (0.553 = Table VII experiment Static CVaR)
3. Verify institutional affiliation and acknowledgments
4. Native-English final proofread
5. Confirm JF submission portal format requirements (page limits, supplementary materials policy)
6. Consider corporate credit extension (not pursued in current universe)
