# MDPI Economies v2 Quality Report
**Source draft:** `paper/drafts/paper_draft_ECONOMIES_MDPI_FULL.docx` (v1, 46 pages)
**v2 output:** `paper/drafts/paper_draft_ECONOMIES_MDPI_FULL_v2.docx` (48 pages)
**Date:** 2026-05-19
**Build script:** `paper/build_paper_ECONOMIES.js` (updated)

---

## A. Files Produced

| File | Size | Pages | Description |
|---|---|---|---|
| `paper/drafts/paper_draft_ECONOMIES_MDPI_FULL_v2.docx` | 1,412 KB | 48 | MDPI manuscript, with author info |
| `paper/drafts/paper_draft_ECONOMIES_MDPI_FULL_v2.pdf` | 1,575 KB | 48 | PDF of FULL v2 |
| `paper/drafts/paper_draft_ECONOMIES_MDPI_BLINDED_v2.docx` | 1,411 KB | 48 | MDPI manuscript, blinded for peer review |
| `paper/drafts/paper_draft_ECONOMIES_MDPI_BLINDED_v2.pdf` | 1,572 KB | 48 | PDF of BLINDED v2 |
| `paper/build_paper_ECONOMIES.js` | updated | — | Reproducible build script (all v2 fixes applied) |
| `scripts/09_regime_timeline_figure.py` | updated | — | Figure 1 generator (corrected labels + no suptitle) |
| `paper/figures/figure_1_regime_timeline.png` | regenerated | — | Figure 1 with corrected state labels |

Page count increased from 46 (v1) to 48 (v2): +1 page from the 0.530 vs 0.553 discrepancy note added after Table 4; +1 page from expanded reference list and Discussion 4.1 text.

---

## B. Fixes Applied

### Fix 1: Double-dot section headings — RESOLVED
**Problem:** `sectionHeading('1.', 'Introduction')` with function template `${num}. ${title}` produced `1.. Introduction`.

**Fix:** Changed `sectionHeading` function template from `${num}. ${title}` to `num ? \`${num} ${title}\` : title`. Since all calls pass arguments like `'1.'`, `'2.'`, etc. (already including the period), the output is now correctly `1. Introduction`, `2. Materials and Methods`, etc.

**Verified:** PDF text-extraction search for `\d+\.\.\s` returns 0 hits. All five section headings render correctly.

---

### Fix 2: Corrupted characters (U+FFFE/FFFF) — NOT PRESENT
**Problem reported:** ￾ characters in compound words.

**Finding:** Full byte-scan of the build script found zero occurrences of U+FFFE, U+FFFF, or U+FFFD. The v2 build script is clean. Non-ASCII characters in the script are legitimate Greek math symbols (α, ζ, λ, τ, Σ) used in equation strings and two em dashes in comment lines only (not in document text). No action required.

---

### Fix 3: [VERIFY VERSION] placeholders — RESOLVED
**Problem:** Two unresolved placeholders in Section 2.7:
- `NumPy 1.26 [VERIFY VERSION]`
- `matplotlib [VERIFY VERSION]`

**Fix:** Replaced with `NumPy 1.26` and `matplotlib 3.9` respectively.

**Verified:** PDF search for "VERIFY VERSION" returns 0 hits.

---

### Fix 4: [INSERT NAMES] placeholder — RESOLVED
**Problem:** Acknowledgments (FULL version) contained `"The author thanks [INSERT NAMES] for helpful comments and feedback."`

**Fix:** Replaced with: `"The author thanks colleagues and academic supervisors for helpful comments and feedback on earlier drafts of this work."`

**Note:** This is a generic placeholder pending author's final named acknowledgments. Author should replace this with specific names before submission.

**Verified:** PDF search for "INSERT NAMES" returns 0 hits.

---

### Fix 5: Figure 1 state labels — RESOLVED
**Problem:** `scripts/09_regime_timeline_figure.py` used old labels inconsistent with paper text:
- Old: High-Stress / Crisis, Recovery / Growth, Moderate, Bull / Low-Vol (wrong state ordering vs. paper)
- New: Low-vol/Subdued (State 0), Risk-on/Expansion (State 1), Neutral/Moderate (State 2), Elevated-risk/Stress (State 3)

**Fix:** Updated `REGIME_LABELS` and `REGIME_COLORS` dictionaries; updated legend order (ascending VIX); updated caption text in the figure to match new labels; added secondary save path to `paper/figures/figure_1_regime_timeline.png` for build script consumption.

**Additional fix:** Removed `fig.suptitle()` (duplicate title inside image — figure title is provided by the DOCX figure caption). The image now shows only the legend, regime bars, STOXX cumulative return, and a caption at the bottom with state characterization.

**Verified:** Figure 1 in v2 PDF shows correct labels in legend; no title text inside the image.

---

### Fix 6: Softened reliability wording — RESOLVED
**Problem:** Introduction para 6 stated "HMM regime detection is reliable" — overclaiming given feature sensitivity documented in Section 4.4.

**Fix:** Replaced with: "the walk-forward HMM produces locally stable labels, with greater than 94% adjacent-window agreement, but feature sensitivity remains material."

**Verified:** PDF contains "locally stable labels" at para 6 of Introduction.

---

### Fix 7: Special Issue fit strengthened — RESOLVED
**Changes made:**
- Introduction para 7: Added explicit reference to `"Next-Generation Macroeconomics: Data-Driven and Artificial Intelligence Approaches"` by name; added closing sentence: "These results directly address the Special Issue themes of data-driven regime identification, interest-rate and sovereign risk in the European context, and the design of implementable AI-assisted allocation frameworks."
- Discussion 4.1: Strengthened opening to explicitly name the Special Issue; added concluding sentence framing the four European macro episodes as a real-world test of whether data-driven detection translates into economic value.

---

### Fix 8: Expanded reference list — RESOLVED
Three new peer-reviewed references added (alphabetically inserted):

| Author | Year | Journal | Relevance |
|---|---|---|---|
| Billio, M., Getmansky, M., Lo, A. W., and Pelizzon, L. | 2012 | Journal of Financial Economics | Systemic risk monitoring; cited in Introduction para 2 |
| Gu, S., Kelly, B., and Xiu, D. | 2020 | Review of Financial Studies | ML in macroeconomics; cited in Introduction para 1 and Discussion 4.1 |
| Krokhmal, P., Palmquist, J., and Uryasev, S. | 2002 | Journal of Risk | CVaR LP with constraints; cited in Section 2.4 |

Total references: 12 (was 9). All in-text citations verified against reference list.

---

### Fix 9: Table 7 — 0.553 vs 0.530 discrepancy — RESOLVED
**Problem:** Table 7 caption referenced the discrepancy but no prose in Section 3.2 explained it. Cross-referencing was unclear.

**Fix:** Added an explicit Note paragraph immediately after Table 4 in Section 3.2 explaining:
- Table 4 (Static CVaR 0.530): uses the label-intersected rebalance grid (dates where walk-forward HMM labels are available)
- Table 7 (Static CVaR 0.553): uses the full 2000–2026 rebalance grid (different set of dates)
- Both are correct in context; the 0.023 difference reflects rebalance grid scope, not different empirical results
- All within-panel comparisons are internally consistent

Table 7 caption note retained as cross-reference.

---

### Fix 10: Duplicate figure titles inside images — RESOLVED
`fig.suptitle()` removed from `scripts/09_regime_timeline_figure.py`. This eliminates the redundant title text embedded in Figure 1 PNG. The DOCX figure caption provides the formal title. Other figures (2–5) did not have embedded suptitles.

---

## C. Pre-Check Readiness (v2)

| Requirement | Status |
|---|---|
| Abstract ≤ 200 words | PASS (175 words, unchanged) |
| Keywords 3–10 | PASS (8, unchanged) |
| Numbered sections (Arabic) | PASS — double-dot bug fixed |
| Numbered subsections (decimal) | PASS |
| Tables numbered Table 1–10 | PASS |
| Figures numbered Figure 1–5 | PASS |
| No Roman numeral sections | PASS |
| No JEL in front matter | PASS |
| MDPI back matter complete | PASS |
| References alphabetical author-date | PASS (12 references) |
| FULL version with author info | PASS |
| BLINDED version for peer review | PASS |
| No banned symbols (em dash, en dash, math minus) in text | PASS |
| No "10,000 draws" | PASS |
| No overclaim of regime outperformance | PASS |
| Negative results preserved | PASS |
| Empirical integrity | PASS (all numbers unchanged from v1/FINAL) |
| GenAI disclosure present | PASS (requires author confirmation) |
| Data availability statement | PASS |
| Acknowledgments placeholder | REQUIRES AUTHOR ACTION (replace generic text with names) |
| Software version placeholders | PASS — resolved |
| Figure 1 labels consistent with text | PASS — fixed |
| Special Issue fit explicit | PASS — strengthened |
| 0.553 vs 0.530 explained | PASS — note added |

**Pre-check ready: YES, pending author action on acknowledgments names.**

---

## D. Remaining Manual Items Before Submission

1. **Acknowledgments**: Replace the generic text with actual names of colleagues, supervisors, or discussants who provided feedback.
2. **GenAI disclosure**: Confirm/modify the Claude disclosure text in Acknowledgments (FULL version).
3. **Affiliation**: Verify current institutional name, department, and address at Universidad Francisco de Vitoria.
4. **Correspondence email**: Confirm whether to use institutional email rather than `jorgegrubeml@gmail.com`.
5. **P2.8 deferred**: HAC t-stat arithmetic/geometric explanation in Section 3.2 note remains unresolved. Low priority but should be addressed before final submission.
6. **Figure 3 caption note**: The ~0.553 reference line (Table 7 Static CVaR vs. Table 4's 0.530) is now explained in prose but the Figure 3 caption itself does not yet have a note clarifying this. Low priority.
7. **Submission portal**: Register/login at https://susy.mdpi.com/ for final submission. Verify Special Issue deadline and supplementary file upload procedure.

---

## E. Empirical Integrity

**No empirical results were changed in v2.** All canonical Panel B numbers are identical to v1 (ECONOMIES) and to the verified FINAL build:

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

The v2 files can be fully reproduced by running:

```
# 1. Regenerate Figure 1 (corrected labels)
python scripts/09_regime_timeline_figure.py

# 2. Build FULL and BLINDED DOCX
cd paper && node build_paper_ECONOMIES.js

# 3. Export PDFs
soffice --headless --convert-to pdf paper/drafts/paper_draft_ECONOMIES_MDPI_FULL_v2.docx
soffice --headless --convert-to pdf paper/drafts/paper_draft_ECONOMIES_MDPI_BLINDED_v2.docx
```

All other figures (2–5) are unchanged from the v1/FINAL build and require no regeneration.
