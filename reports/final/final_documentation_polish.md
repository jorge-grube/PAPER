# Final Documentation Polish

**Date:** 2026-05-10  
**Role:** Senior reproducibility editor  
**Scope:** Documentation files only. No code, data, outputs, or empirical results changed.

---

## A. Files Changed

| File | Nature of change |
|------|-----------------|
| `README.md` | Replaced "gross Sharpe advantage" framing in the Supported Conclusion block |
| `docs/METHODOLOGY.md` | Replaced all 7 rows of Section 9 robustness table with accurate, nuanced findings |
| `data/README_DATA.md` | Replaced broad "All prices are total return indices in EUR" with instrument-accurate statement |
| `reports/final/final_documentation_polish.md` | This file (created) |

---

## B. Exact Phrases Corrected

### README.md

**Before:**
> "Regime CVaR strategies exhibit substantially higher turnover (~225% annually) that erodes their gross Sharpe advantage at any realistic transaction-cost level."

**After:**
> "Naive regime-filtered CVaR strategies exhibit substantially higher turnover (~225% annually), while implementation-aware variants reduce turnover materially but still do not overturn Static CVaR as the most robust benchmark."

**Why:** The phrase "gross Sharpe advantage" was factually wrong. Regime CVaR-A gross Sharpe (0.365) is substantially *below* Static CVaR (0.530) even before costs. There is no advantage to erode — the strategies are already weaker gross. The corrected framing distinguishes naive filtering (high-turnover, weak) from implementation-aware variants (turnover-controlled, closer to Static CVaR but still not superior).

---

### docs/METHODOLOGY.md — Section 9 Robustness Table

Seven rows replaced. Key changes per row:

| Check | Old (imprecise) | New (accurate) |
|-------|----------------|---------------|
| HICP 6w | "Label agreement ~55%; Sharpe change up to +0.068" | Adds: "main conclusion unchanged — Static CVaR remains the dominant benchmark" |
| ZEW swap | "Qualitatively similar regimes, lower Sharpe" | Corrected: "materially improves regime-CVaR point estimates" but "does not produce statistically robust outperformance over Static CVaR" |
| Rebalance frequency | "4w optimal; 1w too costly, 13w misses signals" | Corrected: "Lower frequency reduces turnover; no cadence overturns Static CVaR" |
| Turnover smoothing | "EWA blending reduces TO ~30% with small Sharpe cost" | Corrected: "reduces turnover substantially, improves net Sharpe, but does not beat Static CVaR" |
| TC-aware CVaR | "Embedded TC penalty adds <0.01 Sharpe at 10 bps" | Corrected: "L1 term sharply reduces turnover and improves net Sharpe; one exploratory ZEW-penalised variant marginally exceeds Static CVaR, but not robustly" |
| Regime constraints | "Hard weight bands improve CVaR, reduce Calmar" | Corrected: "more implementable than scenario filtering; near-Static performance with much lower turnover" |
| FI-expanded | "Regime CVaR benefits structurally similar; 2022 rate-shock a key risk" | Corrected: "improves drawdown control, changes defensive allocation mix; 2022 rate-shock is a key adverse scenario" |

---

### data/README_DATA.md

**Before:**
> "All prices are total return indices in EUR."

**After:**
> "Most investable series are total return indices in EUR. Exceptions: Brent is a front-month futures price (not a total return index), Gold is a EUR-converted spot price (USD per troy oz, converted at prevailing FX), and EURIBOR 3M is a rate series converted to weekly simple returns via $(1+r_{ann})^{1/52}-1$."

**Why:** The original sentence was inaccurate for three instruments. Brent is a futures price with no dividend/carry component; Gold is a spot price that has to be FX-converted; EURIBOR 3M is an interest rate, not a price index of any kind. These distinctions matter for a data dictionary that will be read by reviewers.

---

## C. Internal Consistency Assessment

All three documentation files are now mutually consistent and consistent with the empirical outputs:

| Claim | README.md | METHODOLOGY.md | README_DATA.md | Empirical output |
|-------|-----------|----------------|----------------|-----------------|
| Regime CVaR gross Sharpe | No advantage implied ✅ | 0.365 < 0.530 stated ✅ | n/a | 0.365 confirmed ✅ |
| Implementation-aware variants | "reduce turnover materially" ✅ | Regime constraints / TC-aware ✅ | n/a | Scripts 14–15 ✅ |
| HICP lag duration | 6 weeks ✅ | 6 weeks ✅ | 6 weeks ✅ | `HICP_LAG_WEEKS=6` ✅ |
| HICP Sharpe delta | "up to +0.068" ✅ | "up to +0.068" ✅ | n/a | Report confirms ✅ |
| Statistical test | HAC/NW ✅ | HAC/NW ✅ | n/a | Script 08 ✅ |
| HMM states | 4-state ✅ | 4-state ✅ | 4-state ✅ | `N_STATES=4` ✅ |
| HMM features | 8 z-score ✅ | 8 z-score table ✅ | 8-feature table ✅ | `REGIME_FEATURES` ✅ |
| Brent instrument type | n/a | "Energy commodity" | Front-month futures ✅ | `LCOc1` ✅ |
| Gold instrument type | n/a | "Safe haven" | EUR-converted spot ✅ | `XAU=` ✅ |
| FI Italy EUR | EUR-converted ✅ | EUR-converted ✅ | EUR-converted ✅ | LSEG metadata ✅ |

**Documentation is internally consistent and paper-shareable** (subject to the outstanding warnings noted in `documentation_consistency_audit.md`: paper draft `.docx` not yet audited; HICP robustness positioning decision pending).
