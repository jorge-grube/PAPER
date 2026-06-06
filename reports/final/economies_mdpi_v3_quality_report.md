# MDPI Economies v3 Quality Report
**Source draft:** `paper/drafts/paper_draft_ECONOMIES_MDPI_FULL_v2.docx` (v2, 48 pages)
**v3 output:** `paper/drafts/paper_draft_ECONOMIES_MDPI_FULL_v3.docx` (51 pages)
**Date:** 2026-05-19
**Build script:** `paper/build_paper_ECONOMIES.js` (updated)
**Figure script:** `scripts/09_regime_timeline_figure.py` (updated)

---

## A. Files Produced

| File | Size | Pages | Description |
|---|---|---|---|
| `paper/drafts/paper_draft_ECONOMIES_MDPI_FULL_v3.docx` | 1,345 KB | 51 | MDPI manuscript, with author info |
| `paper/drafts/paper_draft_ECONOMIES_MDPI_FULL_v3.pdf` | ~1,600 KB | 51 | PDF of FULL v3 |
| `paper/drafts/paper_draft_ECONOMIES_MDPI_BLINDED_v3.docx` | 1,345 KB | 51 | MDPI manuscript, blinded for peer review |
| `paper/drafts/paper_draft_ECONOMIES_MDPI_BLINDED_v3.pdf` | ~1,600 KB | 51 | PDF of BLINDED v3 |
| `paper/build_paper_ECONOMIES.js` | updated | — | Reproducible build script (all v3 fixes applied) |
| `scripts/09_regime_timeline_figure.py` | updated | — | Figure 1 generator (embedded caption removed) |
| `paper/figures/figure_1_regime_timeline.png` | regenerated | — | Figure 1 without embedded footnote text |

Page count increased from 48 (v2) to 51 (v3): +3 pages from 13 new reference entries, expanded in-text citations, Table 7 prose note, and additional CVaR coherence sentences in Section 2.4.

---

## B. Fixes Applied

### Fix 1: Abstract over word limit — RESOLVED
**Problem:** Abstract was 202 words (MDPI limit: 200).

**Fix:** Trimmed redundant phrasing in opening sentences and the final sentence to reach 193 words.

**Verified:** PDF extraction word count = 193 words. PASS.

---

### Fix 2: 47.9% ZEW claim — RESOLVED (CONTENT ERROR)
**Problem:** Section 4.4 (Limitations) stated that the ZEW indicator "accounts for approximately 47.9% of the variance explained by the first principal component." This was factually wrong — 47.9% is the label agreement rate between the baseline HMM and the ZEW-swap HMM, not a PCA variance share.

**Fix:**
- Replaced the incorrect PCA claim with the correct label-agreement interpretation in Section 4.4.
- Updated Table 10 cell from "47.9% feature variance share" to "47.9% label agreement with baseline."
- The 47.9% value appears correctly in two places in the PDF: Section 3.5 (exploratory ZEW result) and Section 4.4 (robustness table), both now using label-agreement language.

**Verified:** PDF search for "47.9% variance" and "47.9%.*principal" → 0 hits. "47.9%.*label" → 2 correct occurrences.

---

### Fix 3: Overclaiming detection language — RESOLVED
**Problem (a):** Conclusions stated "reliable regime detection is a necessary but not sufficient condition" — implying the detection itself is reliable, which conflicts with the feature sensitivity finding.

**Fix:** Changed to "interpretable regime detection is not sufficient for improved portfolio outcomes."

**Problem (b):** Discussion 4.1 stated the stress state "reliably identifies" elevated conditions without qualification.

**Fix:** Changed to "identifies" with an explicit caveat: "subject to the caveat that state assignments are sensitive to feature construction choices."

**Problem (c):** Conclusions originally contained "The detection layer succeeds." (fixed in v2 session, retained here).

**Fix (retained):** "The detection layer is economically interpretable, but not invariant to feature design."

**Verified:** PDF search for "reliable regime detection is a necessary" → 0 hits. "detection layer" → 1 hit with correct softened language.

---

### Fix 4: Figure 1 embedded caption removed — RESOLVED
**Problem:** `scripts/09_regime_timeline_figure.py` contained a `fig.text()` call that embedded a multi-line descriptive footnote directly inside the PNG image. This created redundant text that should appear in the DOCX figure caption only.

**Fix:** Removed the `fig.text(0.5, -0.03, caption, ...)` block entirely. The image now contains only the legend, regime bars, STOXX cumulative return curve, crisis annotations, and the in-sample notice box.

**Figure 1 was regenerated** and saved to both `reports/figures/full_sample_regime_timeline.png` and `paper/figures/figure_1_regime_timeline.png`.

**Verified:** Regenerated PNG is visually clean — no embedded footnote text at the bottom of the image.

---

### Fix 5: Table 7 clarity — RESOLVED
**Problem:** The "Static CVaR" row in Table 7 used the same label as Table 4 but reported a different Sharpe (0.553 vs. 0.530 in Table 4), confusing readers about whether results were inconsistent.

**Fix (a):** Added an explicit prose note immediately before Table 7: *"Table 7 uses experiment-specific rebalance grids and is intended for within-experiment comparison only. The Static CVaR row in Table 7 reflects the full 2000 to 2026 rebalance grid (Sharpe 0.553) and is not directly comparable to Table 4 (Sharpe 0.530, label-intersected grid). The main Panel B benchmark for cross-strategy comparison remains Table 4."*

**Fix (b):** Renamed the Static CVaR rows in both Panel A and Panel B of Table 7 to **"Static CVaR, experiment-grid benchmark"** to make the distinction explicit in the table itself.

**Verified:** PDF contains "experiment-grid" in 2 table rows and in the prose note.

---

### Fix 6: Expanded reference list to 25 — RESOLVED
**Problem:** v2 had 12 references. MDPI reviewers expect 20–30 references for an empirical macro-finance paper.

**Fix:** Added 13 new peer-reviewed references (alphabetically inserted), bringing total to **25**:

| Author | Year | Journal | In-text citation location |
|---|---|---|---|
| Acerbi, C., and Tasche, D. | 2002 | Journal of Banking and Finance | Section 2.4 (CVaR coherence) |
| Adrian, T., and Brunnermeier, M. K. | 2016 | American Economic Review | Introduction para 2 (systemic risk) |
| Bernanke, B. S., and Boivin, J. | 2003 | Journal of Monetary Economics | Introduction para 1 (data-rich macro) |
| Black, F., and Litterman, R. | 1992 | Financial Analysts Journal | Discussion 4.1 (strategic allocation) |
| Campbell, J. Y., and Viceira, L. M. | 2002 | Oxford University Press | Discussion 4.1 (strategic allocation) |
| DeMiguel, V., Garlappi, L., and Uppal, R. | 2009 | Review of Financial Studies | Section 3.2 (1/N benchmark) |
| Diebold, F. X., and Mariano, R. S. | 1995 | Journal of Business and Economic Statistics | Section 2.6 (statistical tests) |
| Engle, R. F., and Manganelli, S. | 2004 | Journal of Business and Economic Statistics | Section 2.4 (tail risk measures) |
| Kim, C.-J. | 1994 | Journal of Econometrics | Section 2.3 (HMM specification) |
| Lo, A. W. | 2002 | Financial Analysts Journal | Section 2.6 (Sharpe statistics) |
| Longin, F., and Solnik, B. | 2001 | Journal of Finance | Introduction para 4 (correlation regimes) |
| Markowitz, H. | 1952 | Journal of Finance | Section 2.4 (min-variance benchmark) |
| Rabiner, L. R. | 1989 | Proceedings of the IEEE | Introduction para 1 + Section 2.3 (HMM) |

All references include DOI links. All in-text citations verified against the reference list.

**Verified:** PDF reference count (by DOI/URL marker) = 25. All 13 new authors appear in both in-text and reference sections.

---

### Fix 7: AI disclosure updated — RESOLVED
**Problem:** v2 disclosure listed only Claude (Anthropic).

**Fix:** Updated to: *"During the preparation of this manuscript, the author used ChatGPT (OpenAI) and Claude (Anthropic) for language editing, code review, document formatting support, and research workflow assistance."*

**Verified:** PDF contains "ChatGPT (OpenAI)" in Acknowledgments.

---

### Fix 8: Build script assembly section restored — RESOLVED
**Problem:** The build script tail was truncated during v3 editing operations, losing the `buildDoc()` function and `Packer.toBuffer()` calls. Detected via `node --check` syntax error at line 1827.

**Fix:** Removed the orphaned partial string fragment at line 1827 and appended the complete assembly section: `buildDoc(blinded)` function, `buildAppendixF()` inclusion, and dual `Packer.toBuffer()` calls outputting `_v3.docx` files.

**Verified:** `node --check build_paper_ECONOMIES.js` → no errors. Both DOCX files built successfully.

---

## C. Pre-Check Readiness (v3)

| Requirement | Status |
|---|---|
| Abstract ≤ 200 words | PASS (193 words) |
| Keywords 3–10 | PASS (8, unchanged) |
| Numbered sections (Arabic) | PASS |
| Numbered subsections (decimal) | PASS |
| Tables numbered Table 1–10 | PASS |
| Figures numbered Figure 1–5 | PASS |
| No Roman numeral sections | PASS |
| No JEL in front matter | PASS |
| MDPI back matter complete | PASS |
| References alphabetical author-date | PASS (25 references) |
| FULL version with author info | PASS |
| BLINDED version for peer review | PASS |
| No banned symbols (em dash, en dash, math minus) in text | PASS |
| No "10,000 draws" | PASS |
| No overclaim of regime outperformance | PASS |
| Negative results preserved | PASS |
| Empirical integrity | PASS (all numbers unchanged from v2/FINAL) |
| GenAI disclosure present | PASS (ChatGPT + Claude, requires author confirmation) |
| Data availability statement | PASS |
| Acknowledgments placeholder | REQUIRES AUTHOR ACTION (replace generic text with names) |
| 47.9% ZEW interpretation | PASS — label agreement (not PCA variance share) |
| Detection language softened | PASS — "interpretable, not invariant to feature design" |
| Figure 1 labels consistent with text | PASS (inherited from v2) |
| Figure 1 no embedded caption text | PASS — fig.text() removed |
| Special Issue fit explicit | PASS (inherited from v2) |
| 0.553 vs 0.530 explained | PASS — prose note + renamed Table 7 rows |
| Reference count ≥ 20 | PASS (25 references) |
| All new citations verified in reference list | PASS |

**Pre-check ready: YES, pending author action on acknowledgments names.**

---

## D. Remaining Manual Items Before Submission

1. **Acknowledgments**: Replace the generic text with actual names of colleagues, supervisors, or discussants who provided feedback.
2. **GenAI disclosure**: Confirm/modify the ChatGPT and Claude disclosure text in Acknowledgments (FULL version).
3. **Affiliation**: Verify current institutional name, department, and address at Universidad Francisco de Vitoria.
4. **Correspondence email**: Confirm whether to use institutional email rather than `jorgegrubeml@gmail.com`.
5. **P2.8 deferred**: HAC t-stat arithmetic/geometric explanation in Section 3.2 note remains low-priority but should be addressed before final submission.
6. **Figure 3 caption note**: The ~0.553 reference line (Table 7 Static CVaR vs. Table 4's 0.530) is explained in Table 7 prose but Figure 3 caption does not explicitly note the grid difference. Low priority.
7. **Submission portal**: Register/login at https://susy.mdpi.com/ for final submission. Verify Special Issue deadline and supplementary file upload procedure.

---

## E. Empirical Integrity

**No empirical results were changed in v3.** All canonical Panel B numbers are identical to v1 (ECONOMIES), v2, and the verified FINAL build:

| Metric | Value |
|---|---|
| Static CVaR gross Sharpe (Table 4 grid) | 0.530 |
| Regime CVaR-A gross Sharpe | 0.365 |
| Regime CVaR-A annual turnover | 225.8% |
| RC-CVaR baseline net Sharpe | 0.519 |
| TC-penalized net Sharpe (λ=0.005) | 0.486 |
| Static CVaR gross Sharpe (Table 7 grid) | 0.553 |

---

## F. Build Reproducibility

The v3 files can be fully reproduced by running:

```bash
# 1. Regenerate Figure 1 (no embedded caption)
python scripts/09_regime_timeline_figure.py

# 2. Build FULL and BLINDED DOCX
cd paper && node build_paper_ECONOMIES.js

# 3. Export PDFs
python scripts/office/soffice.py --headless --convert-to pdf paper/drafts/paper_draft_ECONOMIES_MDPI_FULL_v3.docx
python scripts/office/soffice.py --headless --convert-to pdf paper/drafts/paper_draft_ECONOMIES_MDPI_BLINDED_v3.docx
```

All other figures (2–5) are unchanged from the v2/FINAL build and require no regeneration.

---

## G. v3 vs v2 Change Summary

| Area | v2 | v3 |
|---|---|---|
| Abstract | 175 words | 193 words (trimmed from 202 words after v2 scan) |
| 47.9% ZEW | Wrong: "PCA variance share" | Correct: "label agreement with baseline HMM" |
| Detection claims | "reliable", "reliably identifies", "The detection layer succeeds." | "interpretable", "identifies [with feature caveat]", "interpretable, not invariant to feature design" |
| Figure 1 | Correct labels, no suptitle, embedded footnote text in image | Correct labels, no suptitle, **no embedded text** — clean image |
| Table 7 Static CVaR row | "Static CVaR" | "Static CVaR, experiment-grid benchmark" |
| Table 7 prose note | Absent | Added explicit note before table explaining grid scope difference |
| References | 12 | 25 (+13 new with in-text citations) |
| AI disclosure | Claude (Anthropic) only | ChatGPT (OpenAI) and Claude (Anthropic) |
| Page count | 48 | 51 |
