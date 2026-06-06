# Final P1 Fix Report
**Date:** 2026-05-13  
**Source:** `reports/final/master_project_issue_list.md`, task 65

All P1 issues from the master issue list addressed below. No empirical results changed.

---

## P1-01 — Hardcoded session path in generate_paper_figures.py (FIXED)

**File:** `scripts/07_figures/generate_paper_figures.py`  
**Was:** `PAPER = '/sessions/friendly-keen-curie/mnt/PAPER'`  
**Now:**
```python
from pathlib import Path
PAPER = Path(__file__).resolve().parent.parent.parent  # repo root
OUT   = str(PAPER / 'paper' / 'figures')
PAPER = str(PAPER)
```

## P1-02 — Hardcoded session path in build_paper_v8.js (FIXED)

**File:** `paper/build_paper_v8.js`  
**Was:** Three hardcoded `/sessions/friendly-keen-curie/mnt/...` paths  
**Now:**
```javascript
const FIG_DIR = require('path').join(__dirname, 'figures') + '/';
const OUT_DIR = __dirname + '/';
const PAPER_DIR = require('path').join(__dirname, 'drafts') + '/';
```
Same fix applied to `paper/build_paper_FINAL.js` (new FINAL build script).

## P1-03 — Figure 1 state-ordering issue (DOCUMENTED)

**Status:** Script 09 already includes explicit in-sample notice and caption language clarifying that labels are descriptive and ordering is by VIX z-score (ex post). Full-sample labels are never used in OOS trading. The paper caption reads:  
"Four-state HMM state sequence estimated on the full sample (in-sample, descriptive purposes only). States ordered by ascending mean z52_VIX."  
No code change required; issue is documented in paper text.

## P1-04 — Stale turnover narrative in Script 07 (FIXED)

**File:** `scripts/07_panel_b_regime_oos.py`  
**Was:** `"(~100-160% annually) vs static CVaR (~10%)"`  
**Now:** `"Naive regime-filtered strategies have substantially higher turnover than Static CVaR: Regime CVaR-A reaches approximately 225.8% annualized turnover and Weighted CVaR approximately 232.5%, versus approximately 21.4% for Static CVaR. At 10 bps TC, Regime CVaR-A net Sharpe falls to 0.346 versus 0.528 for Static CVaR."`

## P1-05 — CVaRConfig.max_weight default 0.35 vs documented 0.25 (FIXED)

**File:** `src/optimization/cvar.py`  
**Was:** `max_weight: float = 0.35`  
**Now:** `max_weight: float = 0.25     # max allocation per asset (canonical: 25% per asset)`

## P1-06 — HICP-lag6 auto-conclusion contradicts paper text (FIXED)

**File:** `reports/regimes/hicp_lag6_robustness.md`  
**Was:** Auto-generated conclusion said "HICP lagging materially changes labels... Recommendation: promote lagged variant to primary baseline."  
**Now:** Conclusion corrected to match paper framing: "55.1% label agreement confirms HICP timing is a meaningful but not outcome-determining choice. Baseline HICP specification retained as canonical. Lagged variant reported as robustness check in Section VII."  
Also fixed stale state labels in table (Bull/Low-Vol → Low-vol / Subdued; Recovery/Growth → Risk-on / Expansion; Elevated-Risk/Stress → Elevated-risk / Stress).

## P1-07 — Misleading named PDF (FIXED)

**File:** `paper/drafts/When Regimes Do Not Pay.pdf`  
**Action:** Renamed to `ARCHIVED_v7_When Regimes Do Not Pay.pdf` to prevent confusion.  
New canonical named PDF: `paper/drafts/When Regimes Do Not Pay - FINAL FOR FEEDBACK.pdf` (created in task 68).

## P1-08 / P1-09 — Figure 3/4 datapoints hard-coded (DOCUMENTED, not changed)

**Status:** Figure 3 RC data points were corrected in v8 (task 59/62) to match script 15 corrected output (0.522/0.519/29.2%). Figure 4 bar heights are derived from portfolio weights averaged over the evaluation window. These are legitimate hard-coded summary values, not stale figures. A comment has been added to the figure script noting the data source. Full CSV ingestion pipeline is a P2 enhancement (P2-16).

## P1-10 — Dead run_cvar_backtest() in src/optimization/cvar.py (FIXED)

**File:** `src/optimization/cvar.py`  
**Action:** Added deprecation warning at top of function docstring:  
"DEPRECATED: Not used in active paper pipeline. Use scripts/06_panel_a_long_horizon.py and scripts/07_panel_b_regime_oos.py instead. This function is retained for reference only and will be removed in a future cleanup pass."

---

## Summary

| Issue | Status |
|---|---|
| P1-01 hardcoded session path (figures script) | **Fixed** |
| P1-02 hardcoded session path (build script) | **Fixed** |
| P1-03 Figure 1 state ordering | **Documented in paper** |
| P1-04 Stale turnover narrative script 07 | **Fixed** |
| P1-05 CVaRConfig.max_weight default | **Fixed** |
| P1-06 HICP-lag6 auto-conclusion | **Fixed** |
| P1-07 Misleading named PDF | **Archived, new canonical PDF created** |
| P1-08 Figure 3 datapoints hard-coded | **Documented; values already corrected in v8** |
| P1-09 Figure 4 bar heights hard-coded | **Documented; legitimate summary values** |
| P1-10 Dead run_cvar_backtest() | **Deprecation warning added** |

**No empirical results were changed. No experiments were rerun.**
