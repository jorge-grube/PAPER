# MDPI Economies Manuscript — Editor Notes
**Files:**
- `paper/drafts/paper_draft_ECONOMIES_MDPI_FULL.docx` (1,427 KB, 46 pages) — with author info
- `paper/drafts/paper_draft_ECONOMIES_MDPI_FULL.pdf` (1,591 KB, 46 pages)
- `paper/drafts/paper_draft_ECONOMIES_MDPI_BLINDED.docx` (1,427 KB, 46 pages) — peer review
- `paper/drafts/paper_draft_ECONOMIES_MDPI_BLINDED.pdf` (1,591 KB, 46 pages)
- `paper/build_paper_ECONOMIES.js` (~105 KB) — reproducible build script
**Date:** 2026-05-18
**Target:** MDPI Economies, Special Issue "Next-Generation Macroeconomics: Data-Driven and Artificial Intelligence Approaches"

---

## Title

**Selected:** "From Regime Detection to Decision Rules: A Data-Driven Macro-Financial CVaR Framework for European Multi-Asset Portfolios"

Rationale: Directly signals the paper's central contribution (detection vs. decision-rule design), uses "Data-Driven" to match the Special Issue title, and specifies the method (CVaR) and scope (European multi-asset).

---

## Abstract Word Count

**175 words** (under 200-word MDPI limit). Covers: background, HMM method, CVaR, European context, results (0.530 Sharpe, 226% TO, 0.486-0.519 implementation-aware), FI expansion and 2022 duration shock, and the key conclusion (bottleneck is decision-rule design, not regime detection).

---

## Keywords (8)

1. data-driven macroeconomics
2. macro-financial regimes
3. Hidden Markov Model
4. Conditional Value-at-Risk
5. systemic risk
6. interest rates
7. portfolio allocation
8. implementation frictions

---

## JF → MDPI Structure Mapping

| JF Section | MDPI Section |
|---|---|
| Introduction | 1. Introduction |
| I. Data | 2. Materials and Methods (2.1-2.2) |
| II. Methodology | 2. Materials and Methods (2.3-2.7) |
| III. Regime Characterization | 3.1. Macro-Financial Regime Characterization |
| IV. Baseline Results | 3.2. Static CVaR and Naive Regime Conditioning + 3.3. Turnover and TC Channel |
| V. Implementation-Aware | 3.4. Implementation-Aware Regime Translation |
| VI. Sovereign FI Expansion | 3.5. Sovereign Fixed-Income Expansion |
| VII. Robustness | 3.6. Robustness Checks |
| (TABLE X in VIII) | 3.7. Mechanism Summary (Table 10) |
| VIII. Discussion | 4. Discussion (4.1-4.4) |
| IX. Conclusion | 5. Conclusions |
| References | References (alpha, author-date) |
| Appendices A-F | Appendix A-F (renamed) |
| — | MDPI back matter (all sections) |

---

## Table and Figure Renumbering

| JF Label | MDPI Label | Content |
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
| FIGURE 1 | Figure 1 | Regime Timeline |
| FIGURE 2 | Figure 2 | Cumulative Wealth |
| FIGURE 3 | Figure 3 | Turnover vs. Net Sharpe |
| FIGURE 4 | Figure 4 | Average Weights |
| FIGURE 5 | Figure 5 | Drawdown Comparison |

---

## Back Matter Inserted

All required MDPI back-matter sections are present in both FULL and BLINDED versions:
- Supplementary Materials
- Author Contributions (FULL: full CRediT statement; BLINDED: "[Removed for peer review]")
- Funding: "This research received no external funding."
- Institutional Review Board Statement: "Not applicable."
- Informed Consent Statement: "Not applicable."
- Data Availability Statement: LSEG proprietary; processed data available on request
- Acknowledgments (FULL: "[INSERT NAMES]" placeholder + AI disclosure; BLINDED: removed)
- Conflicts of Interest: "The author declares no conflicts of interest."
- Abbreviations: 15 abbreviations defined (CVaR, HMM, ESI, HICP, HAC, TC, ECB, FI, VIX, GFC, LP, BIC, EM, OOS, LSEG)

---

## Required Manual Decisions Before Submission

1. **Acknowledgments**: Insert names of colleagues, supervisors, or discussants who provided feedback. Currently placeholder: "[INSERT NAMES]".
2. **AI disclosure**: The current text reads "the author used Claude (Anthropic) for language editing, code review, and document formatting support." Confirm whether to include this per MDPI's AI disclosure policy.
3. **GenAI disclosure**: MDPI requires explicit AI use disclosure. The text is included; confirm/modify.
4. **Software version verification**: `build_paper_ECONOMIES.js` includes `[VERIFY VERSION]` for NumPy and matplotlib. Replace with actual library versions used in the production run.
5. **Affiliation**: Verify current institutional affiliation name and address at Universidad Francisco de Vitoria.
6. **Corresponding author email**: Currently `jorgegrubeml@gmail.com` — confirm whether to use institutional email.
7. **Submission portal**: Verify MDPI Economies submission portal at https://susy.mdpi.com/ for any updated format requirements, supplementary file upload procedure, and Special Issue deadline.
8. **P2.8 deferred issue**: HAC t-stat arithmetic/geometric explanation in Section 3.2 note remains unresolved. Low priority but should be addressed before final submission.

---

## Compliance Checklist

| Check | Status |
|---|---|
| Abstract ≤ 200 words | PASS (175 words) |
| Keywords 3-10 | PASS (8) |
| Required MDPI sections present | PASS |
| Tables numbered Table 1-10 | PASS |
| Figures numbered Figure 1-5 | PASS |
| No Roman numeral section headings | PASS |
| No JF running head | PASS (replaced with "Economies 2026") |
| JEL in minor note only | PASS (footnote-style, not front matter heading) |
| Back matter complete | PASS |
| References alphabetical author-date | PASS |
| FULL version has author info | PASS |
| BLINDED version removes author info | PASS |
| No em dash | PASS (CLEAN scan) |
| No en dash | PASS (CLEAN scan) |
| No math minus | PASS (CLEAN scan) |
| No "10,000 draws" | PASS (5,000 throughout) |
| No claim Regime CVaR beats Static CVaR | PASS |
| Negative results preserved | PASS |
| All empirical numbers verified | PASS (unchanged from FINAL) |

---

## Special Issue Fit Assessment

The paper fits the Special Issue "Next-Generation Macroeconomics: Data-Driven and Artificial Intelligence Approaches" on multiple dimensions:

**Data-driven macroeconomics**: The HMM is estimated on eight weekly macro-financial indicators, directly embodying the data-driven approach. The paper evaluates whether such data-driven regime detection generates economic value, providing a rigorous test of the data-driven paradigm.

**AI/Machine learning**: The HMM is a probabilistic graphical model in the machine-learning tradition. The paper explicitly frames the detection-vs-implementation bottleneck as a lesson for AI-assisted macro-financial systems.

**Systemic risk and interest rates**: The paper covers the 2008 GFC, 2011-2012 sovereign debt crisis, COVID-19 crash, and 2022 ECB rate-hiking cycle — four major European systemic risk episodes. Sovereign spread dynamics and duration risk are central empirical findings.

**Implementation frictions**: The turnover-penalized CVaR and regime-constrained weight band results directly address how to design implementable decision rules that survive real-world transaction costs.

**Assessment**: Ready for MDPI pre-check submission.
