# v8 Correction Report
**Paper:** When Regimes Do Not Pay: Tail-Risk Allocation, Sovereign Bonds, and Implementation Frictions in European Multi-Asset Portfolios  
**Author:** Jorge Grube  
**Report date:** 2026-05-12  
**Covers:** All P1 and selected P2/P3 issues from `reports/final/full_project_submission_audit.md`

---

## A. P1 Issues — Resolution Summary

### P1.1 — Banned Symbols in Figures (RESOLVED)

**Issue:** Figures 1, 2, 3, 5 contained em dashes (—), en dashes (–), or math minus signs (−) in axis labels, titles, or legend text. Figure 3 also needed updated data points from corrected script 15.

**Fix applied:**
- `scripts/09_regime_timeline_figure.py`: Replaced all banned Unicode characters with ASCII equivalents throughout (title, caption, annotation labels, in-sample notice).
- `outputs/gen_figures.py` (→ now `scripts/07_figures/generate_paper_figures.py`): Replaced em dashes in Figure 2 title, Figure 3 title, and Figure 5 legend text. Updated Figure 3 RC-CVaR data points to corrected values (see P1.3).
- All five figures regenerated and saved to `paper/figures/`.
- DOCX XML post-build scan: **CLEAN** (no banned symbols).

**Impact on conclusions:** None. Visual only.

---

### P1.2 — Bootstrap Count Discrepancy (RESOLVED)

**Issue:** Paper text said "10,000 bootstrap draws" in three locations; `scripts/08_panel_statistical_tests.py` uses `N_BOOT = 5_000`. The CIs in the paper were always computed with 5,000 draws.

**Decision:** Correct the paper text to match the script (do not rerun).

**Fix applied (3 locations):**
1. Section II.F: "10,000 bootstrap draws" → "5,000 bootstrap draws"
2. Table III caption: "block = 13 weeks, 10,000 draws" → "5,000 draws"
3. Table VI caption: "block = 13 weeks, 10,000 draws" → "5,000 draws"

**Impact on conclusions:** None. The CI values themselves are unchanged.

---

### P1.3 — Script 15 Regime Constraint Inversion (RESOLVED)

**Issue:** `REGIME_CONSTRAINTS` dict in `scripts/15_regime_constraints_experiment.py` had States 2 and 3 swapped. State 2 (mean VIX z-score +0.17, Neutral/Moderate) was receiving stress-tier constraints (equity cap 45%, defensive floor 30%), while State 3 (mean VIX z-score +1.02, Elevated-risk/Stress) was receiving neutral-tier constraints (equity cap 60%, defensive floor 15%). This inversion was verified against `data/processed/regime_labels_wf_156.parquet`.

**Fix applied:**
- Corrected `REGIME_CONSTRAINTS` mapping:
  - State 2: `label="Neutral / Moderate", max_equity=0.60, min_defensive=0.15`
  - State 3: `label="Elevated-risk / Stress", max_equity=0.45, min_defensive=0.30`
- Script rerun via `outputs/run_rc_correction.py` (direct computation bypassing checkpoint files that could not be deleted on NTFS mount).

**Corrected results (vs old results):**

| Metric | Old (inverted) | New (correct) |
|---|---|---|
| RC-baseline gross Sharpe | 0.521 | 0.522 |
| RC-baseline net@10bps | 0.518 | 0.519 |
| RC-baseline Ann.TO | 31.1% | 29.2% |
| RC-ZEW gross Sharpe | 0.527 | 0.519 |
| RC-ZEW net@10bps | 0.525 | 0.517 |
| RC-ZEW Ann.TO | 26.3% | 27.0% |

**Paper updates applied:**
- Table VII Panel B: updated RC-CVaR rows
- Table VII caption: scope note added (see P1.4)
- Section V.B prose: all RC value references updated
- Introduction para 6: "0.518 net Sharpe with only 31% turnover" → "0.519 net Sharpe with only 29% turnover"
- Section IX Conclusion: "0.486 to 0.525 at 10 bps" → "0.486 to 0.519 at 10 bps"
- Figure 3 RC data points: updated to corrected values

**Impact on conclusions:** Immaterial. Static CVaR (0.530 gross, 0.528 net@10bps) continues to dominate both RC-CVaR variants by a wide margin. The RC approach still demonstrates substantially reduced turnover versus naive Regime CVaR-A (29.2% vs 225.8%).

---

### P1.4 — Static CVaR Sharpe Inconsistency (RESOLVED)

**Issue:** Main Panel B tables (IV, V, VI) show Static CVaR gross Sharpe = 0.530, net@10bps = 0.528. Table VII (TC-aware and RC-CVaR experiments) shows Static CVaR gross Sharpe = 0.553, net@10bps = 0.551. Section V.A text referenced "0.528" while Table VII showed "0.551" in the same reading context.

**Root cause:** Scripts 14/15 run `static_cvar` with `lab=None`, causing `run_walkforward()` to use the full 2000-origin asset-return index (1,369 dates) as the `common` rebalance grid. Script 07 uses the label-intersected index (964 dates from 2007-10-19). Different rebalance grids produce different 260-week scenario windows and therefore different weights. Neither is wrong; they represent different evaluation conventions. Full analysis in `reports/final/static_cvar_sharpe_reconciliation.md`.

**Fix applied:**
- Table VII caption: added scope note explaining the 0.553 vs 0.530 difference.
- Section V.A: "Static CVaR (net Sharpe 0.528 at 10 bps)" → "Static CVaR (net Sharpe 0.551 at 10 bps in this experiment context; see Table VII note)"

**Impact on conclusions:** None. The comparison between regime strategies and Static CVaR within each table is internally consistent. The main conclusion that Static CVaR dominates holds at both 0.530 and 0.553.

---

### P1.5 — Stale Paths and Labels in model_backtest_summary.md (RESOLVED)

**Issue:** Seven file paths referenced `reports/panel_*` (old location) instead of `reports/panels/panel_*` (correct location). Walk-forward HMM state label table used outdated labels ("Bull/Low-Vol", "Recovery/Growth") and math-minus VIX z-scores.

**Fix applied:**
- Seven paths corrected via batch replacement.
- State label table updated to current ordering: Low-vol/Subdued, Risk-on/Expansion, Neutral/Moderate, Elevated-risk/Stress.
- VIX z-scores: math-minus (U+2212) replaced with hyphen-minus throughout.

---

## B. P2 Issues — Resolution Summary

| Issue | Status | Fix |
|---|---|---|
| P2.1 (Table I TR note) | **Resolved** | Added: "Brent crude oil and gold are price series, not total-return indices..." |
| P2.2 (model_backtest_summary state labels) | **Resolved** | Covered under P1.5 |
| P2.3 (Frazzini 2015 citation) | **Resolved** | Still a working paper as of 2026. Added SSRN reference note. |
| P2.4 (gen_figures.py location) | **Resolved** | Moved to `scripts/07_figures/generate_paper_figures.py`; `docs/RUN_ORDER.md` updated. |
| P2.5 (Introduction trim) | **Resolved** | Paragraphs 5–8 trimmed ~25–30% |
| P2.6 (Nontechnical closing) | **Resolved** | Added: "Systematic tail-risk control works in European multi-asset markets..." |
| P2.7 (Data licensing in Section I) | **Resolved** | Added to Section I.B: "Raw source files are subject to LSEG data licensing restrictions..." |
| P2.8 (HAC t-stat arithmetic/geometric explanation) | **Deferred** | Low priority for this feedback round |
| P2.9 (Section V.A 0.528 ref) | **Resolved** | Covered under P1.4 fix |
| P2.10 (Table I TR note) | **Resolved** | Same as P2.1 |
| P2.11 (Fig 3 reference line) | **Deferred** | Fig 3 dashed line at ~0.553 is consistent with Table VII; caption note would be the fix |

---

## C. P3 Issues Addressed

| Issue | Fix |
|---|---|
| P3.7 (ESI correlation precision) | Section VII.B: "unconditional correlation with z52_ESI over the full weekly sample: r approximately 0.02" |
| P3.8 (Newey-West inline citation) | Section II.F: "(Newey and West, 1987)" added at first mention |

---

## D. Files Changed

| File | Change |
|---|---|
| `paper/drafts/paper_draft_JF_style_v8_FINAL_FOR_FEEDBACK.docx` | New v8 build (all P1+P2+P3 fixes) |
| `paper/drafts/paper_draft_JF_style_v8_FINAL_FOR_FEEDBACK.pdf` | PDF export of v8 DOCX |
| `paper/build_paper_v8.js` | New build script (copied from v7, all fixes applied) |
| `paper/notes/paper_draft_JF_style_v8_FINAL_FOR_FEEDBACK_notes.md` | Editor notes for v8 |
| `scripts/15_regime_constraints_experiment.py` | REGIME_CONSTRAINTS dict corrected (States 2/3) |
| `scripts/09_regime_timeline_figure.py` | Banned symbols removed |
| `scripts/07_figures/generate_paper_figures.py` | Moved from `outputs/gen_figures.py`; Figure 3 RC data updated |
| `reports/final/static_cvar_sharpe_reconciliation.md` | New: root-cause analysis of 0.530 vs 0.553 |
| `reports/final/model_backtest_summary.md` | Paths and state labels fixed |
| `paper/figures/figure_*.png` (all 5) | Regenerated without banned symbols |
| `docs/RUN_ORDER.md` | Added `scripts/07_figures/` entry; corrected bootstrap count |

**No changes to source data, canonical Panel B outputs, or statistical test outputs.**

---

## E. Quantitative Impact on Paper Conclusions

| Claim | v7 reference value | v8 reference value | Conclusion change? |
|---|---|---|---|
| Static CVaR is most robust benchmark | 0.530 Sharpe | 0.530 Sharpe | **None** |
| Regime CVaR-A fails through turnover | 225.8% TO | 225.8% TO | **None** |
| RC-CVaR (baseline) near-static performance | 0.518 net@10bps | 0.519 net@10bps | **None** (immaterial) |
| Bootstrap CIs correctly computed | (always 5,000) | text now says 5,000 | **None** (text fix only) |
| FI bonds improve drawdown but add duration risk | unchanged | unchanged | **None** |

---

## F. Verification Steps Completed

1. **DOCX XML banned-symbol scan:** CLEAN — no em dash, en dash, or math minus in any XML file within the DOCX archive.
2. **Figure PNG visual check:** All five figures regenerated; labels and titles use only ASCII characters.
3. **Table VII numerical consistency:** RC values in Table VII match corrected script 15 output; cross-referenced against `reports/model_improvement/regime_constraints/performance.csv` (Sharpe 0.522 baseline, 0.519 ZEW-swap at 0 bps).
4. **Section cross-reference check:** All in-text RC value references updated (Introduction, Section V.B, Section IX, Figure 3 data).
5. **Build reproducibility:** `node build_paper_v8.js` produces DOCX from scratch in one command with no errors.

---

## G. Remaining Pre-Submission Work

For journal submission (not required for this feedback round):

1. Resolve P2.8 (arithmetic vs. geometric HAC t-stat explanation in Section IV.B)
2. Add Figure 3 caption note explaining the dashed reference line corresponds to the Table VII experiment Static CVaR value (0.553)
3. Verify institutional affiliation and acknowledgments section
4. Final proofread by a native-English reader
5. Confirm JF submission portal format requirements (page limits, supplementary materials policy)
