# MDPI Economies — v7 Submission Audit
**Date:** 2026-05-25  
**Files audited:**
- `paper/drafts/paper_draft_ECONOMIES_MDPI_FULL_v7.docx` (1.6 MB)
- `paper/drafts/paper_draft_ECONOMIES_MDPI_FULL_v7.pdf` (2.0 MB, 28 pages)
- `paper/drafts/paper_draft_ECONOMIES_MDPI_BLINDED_v7.docx` (1.6 MB)
- `paper/drafts/paper_draft_ECONOMIES_MDPI_BLINDED_v7.pdf` (1.9 MB, 28 pages)

---

## 1. Prohibited Symbol Check

| Symbol | Expected | Result |
|--------|----------|--------|
| Em dash `—` | 0 | **0 — PASS** |
| En dash `–` | 0 | **0 — PASS** |
| Corrupted hyphen `￾` | 0 | **0 — PASS** |

Verified by automated scan of PDF text extraction. All inline hyphens and ranges use standard ASCII hyphen-minus `-` as required.

---

## 2. Figure Audit

### 2a. Figure Count and Order

| Figure | Description | Location | Status |
|--------|-------------|----------|--------|
| Figure 1 | Methodological workflow diagram | End of Section 2 | **PASS** |
| Figure 2 | HMM state characteristics (z-score bar chart) | Section 3.1 | **PASS** |
| Figure 3 | Full-sample regime timeline (2000–2026) | Section 3.1 | **PASS** |
| Figure 4 | Cumulative wealth, Panel B strategies | Section 3.2 | **PASS** |
| Figure 5 | Turnover vs. net Sharpe frontier | Section 3.3 | **PASS** |
| Figure 6 | Average asset-group weights, Static CVaR | Section 3.4 | **PASS** |
| Figure 7 | Drawdown curves, baseline vs FI-expanded | Section 3.4 | **PASS** |

Figure order confirmed sequential in PDF (captions extracted in order: 1, 2, 3, 4, 5, 6, 7).

### 2b. Figure Width

All figures rendered with `transformation.width = Math.round(CONTENT/1440*96)` ≈ 698 px (= 10,466 DXA = 7.27 in), matching the full table content width. No `BODY_INDENT` applied to figure paragraphs.

### 2c. No Internal "Figure N" Titles in Images

`generate_paper_figures.py` was updated to remove all `ax.set_title('Figure X…')` calls. Figures 2–7 (the matplotlib outputs) contain no embedded title annotations.

---

## 3. MDPI Document Structure

### Section order (verified by PDF character positions)

| Position | Element |
|----------|---------|
| 1,917 | 1. Introduction |
| ~6,000 | 2. Data and Methodology |
| 20,335 | 3. Results |
| 40,860 | 4. Discussion |
| 47,806 | 5. Conclusions |
| 49,743 | Author Contributions *(back matter)* |
| 50,112 | Funding |
| ~50,400 | Data Availability Statement |
| ~50,700 | Acknowledgments / AI Disclosure / Conflicts |
| 51,791 | **References** |
| ~53,000 | Appendix A (OMML equations) |
| ~58,000 | Appendix F (Correlation table) |

Back matter appears **before** References — correct per MDPI Economies template.

---

## 4. Equation Rendering (Appendix A)

OMML injection via `scripts/inject_omml_equations.py` succeeded for both FULL and BLINDED versions.

| Placeholder | Found | Replaced | Status |
|-------------|-------|----------|--------|
| `__OMML_EQ1__` | Yes | OMML `<m:oMath>` | **PASS** |
| `__OMML_EQ2__` | Yes | OMML `<m:oMath>` | **PASS** |

Both placeholders absent from final PDF. Equations render as native Word math objects in DOCX.

---

## 5. Text Fixes Applied

| Issue | Fix Applied | Status |
|-------|-------------|--------|
| Em dash in Para 7 Introduction | Replaced `—` with `,` | **PASS** |
| Em dash in Section 4.1 Discussion | Replaced `—` with `;` | **PASS** |
| Em dash in Conclusions Para 1 | Replaced `—` with `,` | **PASS** |
| Em dash in Conclusions Para 2 | Replaced `—` with `,` | **PASS** |
| Bernanke & Boivin sentence | Changed "modern deep-learning approaches" to "data-rich macroeconomic nowcasting frameworks" | **PASS** |
| Introduction numerical spoilers | Removed 0.530, 226%, 0.346, 0.486, 0.519, 29% from Introduction Para 6; replaced with qualitative summary | **PASS** |
| Detection language | Changed "reliably identify stress regimes" to "characterize stress regimes" | **PASS** |

---

## 6. References Audit

| Check | Status |
|-------|--------|
| Diebold & Mariano (1995) removed | **PASS** — not present in PDF |
| All remaining references cited in text | Not individually verified, but DM was the only removal target |
| References in alphabetical order | **PASS** (Acerbi → Rockafellar) |

---

## 7. Introduction Spoiler Check

Numerical values that reveal core results before Section 3 — checked in Introduction (chars 1,917–6,000):

| Value | Present in Introduction | Status |
|-------|------------------------|--------|
| 0.530 | No | **PASS** |
| 226% | No | **PASS** |
| 0.346 | No | **PASS** |
| 0.486 | No | **PASS** |
| 0.519 | No | **PASS** |
| 29% | No | **PASS** |

These values remain present in their correct locations in Section 3 (Results) and Section 5 (Conclusions).

---

## 8. Data Confidentiality Statement

The phrase "Raw data are from LSEG/Refinitiv/Workspace and are proprietary" appears in the Data Availability Statement. No proprietary data files are included in the submission package.

---

## 9. Blinded Version

`paper_draft_ECONOMIES_MDPI_BLINDED_v7.docx` and its PDF were built with `blinded=true`. Author names, affiliations, acknowledgments, funding, and author contribution statements are suppressed per MDPI double-blind requirements. OMML injection applied identically.

---

## 10. File Summary

| File | Size | Pages | Status |
|------|------|-------|--------|
| `paper_draft_ECONOMIES_MDPI_FULL_v7.docx` | 1.6 MB | — | Ready |
| `paper_draft_ECONOMIES_MDPI_FULL_v7.pdf` | 2.0 MB | 28 | Ready |
| `paper_draft_ECONOMIES_MDPI_BLINDED_v7.docx` | 1.6 MB | — | Ready |
| `paper_draft_ECONOMIES_MDPI_BLINDED_v7.pdf` | 1.9 MB | 28 | Ready |

**Submit:** `paper_draft_ECONOMIES_MDPI_BLINDED_v7.docx` (or PDF) as the manuscript file.  
**Keep on record:** FULL version with author information.

---

## 11. Known Remaining Items (Not Blocking Submission)

- **Table 7 split** (optional): Table 7 could be split into Tables 7 (Panel B summary) and 8 (FI-expanded summary) per original v7 spec. Not implemented; content is complete and readable as a single table.
- **Section 2.4 inline equations**: Rendered as Unicode math text (Option C), not OMML. These are simple inline expressions and render acceptably in Word and PDF. OMML is applied only to the display equations in Appendix A.
- **Statistical significance**: Bootstrap CIs span ±0.4 Sharpe units; no strategy difference is statistically distinguishable at conventional power. This is explicitly acknowledged in Section 4.3 (Limitations) and is an honest characterization of the sample.
