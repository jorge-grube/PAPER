# MDPI Economies Conversion Report
**Source:** `paper/drafts/paper_draft_FINAL.docx` (JF working paper format)
**Target:** `paper/drafts/paper_draft_ECONOMIES_MDPI_FULL.docx` (MDPI Economies submission)
**Date:** 2026-05-18
**Special Issue:** "Next-Generation Macroeconomics: Data-Driven and Artificial Intelligence Approaches"

---

## A. Files Created

| File | Size | Description |
|---|---|---|
| `paper/drafts/paper_draft_ECONOMIES_MDPI_FULL.docx` | 1,427 KB | MDPI manuscript, with author info |
| `paper/drafts/paper_draft_ECONOMIES_MDPI_FULL.pdf` | 1,591 KB | PDF of FULL version, 46 pages |
| `paper/drafts/paper_draft_ECONOMIES_MDPI_BLINDED.docx` | 1,427 KB | MDPI manuscript, blinded for peer review |
| `paper/drafts/paper_draft_ECONOMIES_MDPI_BLINDED.pdf` | 1,591 KB | PDF of BLINDED version, 46 pages |
| `paper/build_paper_ECONOMIES.js` | ~105 KB | Reproducible build script |
| `paper/notes/paper_draft_ECONOMIES_MDPI_notes.md` | — | Editor/submission notes |
| `paper/cover_letter/cover_letter_ECONOMIES_special_issue.docx` | 10 KB | Cover letter (Word) |
| `paper/cover_letter/cover_letter_ECONOMIES_special_issue.txt` | — | Cover letter (plain text) |
| `paper/cover_letter/planned_paper_abstract_250w.txt` | — | 250-word planned-paper abstract |

---

## B. Full vs. Blinded Status

| Element | FULL | BLINDED |
|---|---|---|
| Author name | Jorge Grube | [Author details removed for peer review] |
| Affiliation | Universidad Francisco de Vitoria (full address) | Removed |
| Correspondence email | jorgegrubeml@gmail.com | Removed |
| Acknowledgments | "[INSERT NAMES]" placeholder + AI disclosure | Removed |
| Author Contributions | Full CRediT statement | [Removed for peer review] |
| Conflicts of Interest | "The author declares no conflicts of interest." | Retained (non-identifying) |
| Data availability | Retained | Retained |
| Citations | Retained (all references cite author-year only) | Retained |

---

## C. Abstract Word Count

**175 words** (under 200-word MDPI limit).

Key elements covered:
- Background: high-frequency macro data + machine learning
- Methods: four-state Gaussian HMM, eight features, CVaR, European multi-asset
- Setting: January 2000 to April 2026
- Results: Static CVaR Sharpe 0.530; Regime CVaR-A 226% turnover; implementation-aware 0.486-0.519; FI expansion and 2022 duration shock
- Conclusion: bottleneck is decision-rule design, not regime detection

---

## D. Keywords (8)

1. data-driven macroeconomics
2. macro-financial regimes
3. Hidden Markov Model
4. Conditional Value-at-Risk
5. systemic risk
6. interest rates
7. portfolio allocation
8. implementation frictions

---

## E. Section Mapping (JF → MDPI)

| JF Paper | MDPI Paper | Change |
|---|---|---|
| Introduction (8 paras) | 1. Introduction (8 paras) | Rewritten with AI/data-driven macro framing; European macro-financial crisis context added; "detection vs. decision-making" made central from Para 1 |
| I. Data (3 subsections) | 2.1-2.2 Materials and Methods | Merged into Section 2; renamed to Data and Asset Universe + Macro-Financial Regime Features |
| II. Methodology (6 subsections) | 2.3-2.7 Materials and Methods | Merged; new subsection 2.7 added for Software, Reproducibility, and Data Availability |
| III. Regime Characterization | 3.1 Macro-Financial Regime Characterization | Systemic risk context added (GFC, sovereign crisis, COVID-19) |
| IV. Baseline Results (A+B) | 3.2-3.3 Results | Split into Static CVaR + Naive Regime (3.2) and Turnover and TC Channel (3.3) for clarity |
| V. Implementation-Aware (A+B) | 3.4 Implementation-Aware Regime Translation | Unified; MDPI framing |
| VI. Sovereign FI Expansion (A+B) | 3.5 Sovereign Fixed-Income Expansion | Retained; rate-shock language strengthened |
| VII. Robustness (A-E) | 3.6 Robustness Checks + 3.7 Mechanism Summary | Section 3.7 added with Table 10 |
| VIII. Discussion (A-C) | 4. Discussion (4.1-4.4) | Substantially expanded; AI/macro systems angle (4.1); practical implications (4.3); limitations (4.4) expanded with feature sensitivity, release timing, TC model simplifications |
| IX. Conclusion | 5. Conclusions | Reframed for Economies; explicitly frames detection vs. decision rule lesson |
| References | References | Converted to MDPI author-date format, alphabetical |
| Appendices A-F | Appendix A-F | Retained; TABLE F.1/F.2 renamed to Table A1/A2 |
| (new) | MDPI back matter | All required sections added (Supplementary, Author Contributions, Funding, IRB, ICS, DAS, Acknowledgments, CoI, Abbreviations) |

---

## F. Table and Figure Renumbering

### Tables
| Old | New | Title |
|---|---|---|
| TABLE I | Table 1 | Asset Universe |
| TABLE II | Table 2 | HMM Market-State Characteristics |
| TABLE III | Table 3 | Panel A Performance |
| TABLE IV | Table 4 | Panel B Performance |
| TABLE V | Table 5 | TC Sensitivity |
| TABLE VI | Table 6 | Statistical Tests |
| TABLE VII | Table 7 | TC-Aware and Regime-Constrained CVaR |
| TABLE VIII | Table 8 | FI-Expanded Universe |
| TABLE IX | Table 9 | Robustness Check Summary |
| TABLE X | Table 10 | Mechanism Summary |
| TABLE F.1 | Table A1 | Descriptive Statistics |
| TABLE F.2 | Table A2 | Pairwise Correlations |

### Figures
| Old | New | Title |
|---|---|---|
| FIGURE 1 | Figure 1 | Full-Sample Regime Timeline |
| FIGURE 2 | Figure 2 | Cumulative Wealth Panel B |
| FIGURE 3 | Figure 3 | Turnover vs. Net Sharpe Frontier |
| FIGURE 4 | Figure 4 | Average Portfolio Weights |
| FIGURE 5 | Figure 5 | Drawdown Comparison |

---

## G. Back Matter Inserted

All required MDPI back-matter sections are present in both FULL and BLINDED versions:

| Section | Content |
|---|---|
| Supplementary Materials | Python scripts, processed parquets, robustness tables available on request (LSEG restrictions noted) |
| Author Contributions | Full CRediT taxonomy (FULL); suppressed (BLINDED) |
| Funding | "This research received no external funding." |
| Institutional Review Board Statement | "Not applicable." |
| Informed Consent Statement | "Not applicable." |
| Data Availability Statement | LSEG proprietary raw data; processed data available on request |
| Acknowledgments | "[INSERT NAMES]" placeholder + AI disclosure text (FULL); suppressed (BLINDED) |
| Conflicts of Interest | "The author declares no conflicts of interest." |
| Abbreviations | 15 entries: CVaR, HMM, ESI, HICP, HAC, TC, ECB, FI, VIX, GFC, LP, BIC, EM, OOS, LSEG |

---

## H. Data Availability Statement

"Restrictions apply to the availability of the raw data. The data were obtained from LSEG Workspace/Refinitiv and are available from LSEG subject to license. Processed datasets and code sufficient to reproduce the reported tables and figures can be made available by the author upon reasonable request, subject to licensing restrictions."

---

## I. GenAI Disclosure Status

**Included in FULL version** (in Acknowledgments):
"During the preparation of this manuscript, the author used Claude (Anthropic) for language editing, code review, and document formatting support. The author reviewed and edited all outputs and takes full responsibility for the content of the publication."

**Required author decision**: Confirm whether to include this text. MDPI policy requires AI disclosure when AI tools were used in manuscript preparation. Suppressed in BLINDED version.

---

## J. Remaining Manual Decisions

1. **Acknowledgments names**: Replace "[INSERT NAMES]" with actual names of colleagues, supervisors, or discussants.
2. **GenAI disclosure**: Confirm/modify Claude disclosure text.
3. **Software version verification**: Section 2.7 includes `[VERIFY VERSION]` for NumPy and matplotlib. Replace with actual production versions.
4. **Affiliation**: Verify current institutional name, department, and address.
5. **Correspondence email**: Confirm institutional vs. personal email.
6. **P2.8 deferred**: HAC t-stat arithmetic/geometric explanation (Section 3.2 note) remains unresolved. Address before final submission.
7. **Figure 3 dashed reference line**: Caption note clarifying the ~0.553 reference line (Table 7 experiment Static CVaR vs. Table 4 canonical 0.530) not yet added. Low priority but noted.
8. **DOI links in references**: DOI links are included for published papers. Frazzini et al. (2015) includes SSRN URL only (not yet journal-published as of May 2026).
9. **Submission portal**: Register/login at https://susy.mdpi.com/ for MDPI submission. Verify Special Issue deadline.

---

## K. Special Issue Fit Assessment

| Theme | Coverage |
|---|---|
| Data-driven macroeconomics | DIRECT: HMM on 8 weekly macro-financial indicators; evaluates practical value of data-driven regime detection |
| AI/ML methods | DIRECT: HMM is a probabilistic ML model; paper explicitly addresses AI-assisted decision pipelines |
| Systemic risk | DIRECT: GFC, sovereign crisis, COVID-19, 2022 ECB rate shock all covered; sovereign spread dynamics are key feature |
| Interest rates | DIRECT: yield-curve slope feature; 2022 rate-hiking duration shock is central empirical finding |
| Inflation | ADDRESSED: HICP feature; publication-lag robustness (Section 3.6) |
| Implementation frictions | CENTRAL: turnover, TC sensitivity, implementation-aware design (Sections 3.3-3.4) |
| Transparency and interpretability | ADDRESSED: interpretable regime states; regime-constrained guardrails |
| European context | DIRECT: 10 European assets; ECB; peripheral spreads; European macro episodes |

**Fit: STRONG. All major Special Issue themes are directly addressed.**

---

## L. MDPI Pre-Check Readiness

| Requirement | Status |
|---|---|
| Abstract ≤ 200 words | PASS (175 words) |
| Keywords 3-10 | PASS (8) |
| Numbered sections (Arabic) | PASS (Sections 1-5) |
| Numbered subsections (decimal) | PASS (2.1., 2.2., etc.) |
| Tables numbered Table 1-10 | PASS |
| Figures numbered Figure 1-5 | PASS |
| No Roman numeral sections | PASS |
| No JEL in front matter | PASS (minor footnote only) |
| MDPI back matter complete | PASS |
| References alphabetical author-date | PASS |
| FULL version with author info | PASS |
| BLINDED version for peer review | PASS |
| No banned symbols (em dash, en dash, math minus) | PASS (CLEAN scan) |
| No "10,000 draws" | PASS |
| No overclaim of regime outperformance | PASS |
| Negative results preserved | PASS |
| Empirical integrity | PASS (all numbers unchanged from verified FINAL) |
| GenAI disclosure present | PASS (requires author confirmation) |
| Data availability statement | PASS |
| Acknowledgments placeholder | REQUIRES AUTHOR ACTION |
| Software version placeholders | REQUIRES AUTHOR ACTION |

**Pre-check ready: YES, pending manual items J1-J9 above.**
