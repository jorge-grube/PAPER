# Final Paper Reframe Report
**Paper:** When Regimes Do Not Pay: Tail-Risk Allocation, Sovereign Bonds, and Implementation Frictions in European Multi-Asset Portfolios  
**Author:** Jorge Grube  
**Report date:** 2026-05-13  
**Covers:** Intellectual reframe applied in FINAL build (detection-vs-implementation)

---

## The Reframe

### From (v8 framing)

The v8 paper read as a horse race: we test several regime-conditioned CVaR strategies against a static benchmark, and the static benchmark wins. This framing is accurate but not intellectually distinctive — it is an empirical result looking for an interpretation.

### To (FINAL framing)

The FINAL paper separates two questions that previous literature conflates:

1. **Detection quality**: Can the HMM assign reliable regime labels out-of-sample?
2. **Implementation viability**: Can those labels be translated into stable, low-turnover portfolio weights?

The empirical answer to Question 1 is **yes**: adjacent-window label agreement exceeds 94% of weeks; HICP-lag6 agreement is 55% (sensitive but not outcome-determining); the four-state structure is consistent across feature perturbations.

The empirical answer to Question 2 is **no** for naive implementation, and **partially yes** for implementation-aware variants.

This reframe changes the paper's contribution from "static beats regime" to "regime detection is not the binding constraint; regime translation is."

---

## Changes Applied

### 1. Abstract

Old (v8): Evaluation framing — "we evaluate whether HMM regime conditioning improves..."  
New (FINAL): Question framing — "We ask whether HMM-detected market regimes can be translated into out-of-sample CVaR portfolio gains."  
Closing: "The central finding is not that regimes are undetectable, but that detected regimes cannot be translated into stable, low-turnover portfolio weights without forfeiting the return advantage."  
Word count: 97 (under 100-word target).

### 2. Introduction Para 1

New opening sentence: introduces the detection/translation distinction before any performance results.  
Key sentence added verbatim:  
> "The central question is not whether regimes can be detected, but whether detected regimes can be translated into stable, low-turnover portfolio weights."

### 3. Introduction Para 5 (central finding)

v8: "Our central finding is that regime conditioning does not improve out-of-sample risk-adjusted performance..."  
FINAL: "Our central finding is that regime detection is reliable but regime implementation is structurally costly."

Now anchored with the label-agreement statistic (>94% adjacent-window agreement) to substantiate the "detection succeeds" claim before presenting the "implementation fails" evidence.

### 4. Introduction Para 6 (variants)

v8: "The high turnover is structural..."  
FINAL: "Two implementation-aware approaches address the translation failure directly."

Reframes L1 penalty and regime constraints as solutions to a translation problem, not as post-hoc fixes.

### 5. Introduction Para 8 (contributions)

Second contribution now reads: "we identify the LP scenario discontinuity as the primary mechanism of regime CVaR failure, distinguishing detection quality from implementation cost, a distinction absent from most prior regime portfolio work."

### 6. TABLE X (new, Section VIII)

A 6-row × 5-column mechanism summary table added between Discussion subsections A and B. Columns: Mechanism, Root Cause, Empirical Signature, Implementation Fix, Remaining Gap. Provides a diagnostic map connecting theory to empirics to practical resolution.

### 7. Limitations Subsection (expanded, Section VIII.C)

Added two new paragraphs on:
- HMM labels as statistical constructs (55% HICP-lag agreement)
- Feature sensitivity (ZEW ~47.9% of PC1 variance)
- Macro release timing (HICP ~4 week lag, ESI ~3 week lag)
- Simplified TC model (no bid-ask, no market impact, no corporate credit)

---

## What Did NOT Change

No empirical results were modified. No tables, figures, or statistical outputs were changed. The reframe is purely editorial: it reorganises what the paper claims to be about without altering any data or calculations.

---

## Rationale for Title Retention

The title "When Regimes Do Not Pay" is retained (Option A). Although Option B ("Detecting Regimes Is Not Enough") more directly signals the detection-vs-implementation theme, Option A has the following advantages:
- Established in all prior drafts, notes, and reports
- Broader reader recognition ("Do Not Pay" signals a null result without requiring the detection/implementation distinction to be understood from the title alone)
- The subtitle ("Tail-Risk Allocation, Sovereign Bonds, and Implementation Frictions") already signals the implementation dimension
- JF conventions favor concise, provocative titles over explanatory ones

The detection-vs-implementation distinction is made explicit in the abstract, para 1, and para 5 of the introduction, and in TABLE X, which is sufficient for a reader to encounter it early and often without it needing to be in the title.
