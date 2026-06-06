# Turnover and Transaction-Cost Audit

**Audit date:** 2026-05-12

## 1. Definitions and conventions (as implemented)

Every active backtest script (06, 07, 10, 11, 12, 13, 14, 15, 17, 18) uses the SAME conventions, copy-pasted as helper functions. The relevant helpers, verified line-by-line:

```python
def _weekly_to(w_df):
    return w_df.diff().abs().sum(axis=1) / 2.0

def _eq_drift_to(ret_r):
    n  = ret_r.shape[1]
    rp = ret_r.mean(axis=1)
    wd = ret_r.apply(lambda r: (1/n)*(1+r)/(1+rp), axis=0)
    return (wd - 1/n).abs().sum(axis=1) / 2.0

def _apply_tc(gross, to, rate):
    return gross - rate * to.shift(1).fillna(0.0).reindex(gross.index).fillna(0.0)

def _port(w_df, ret):
    return (w_df.shift(1) * ret.reindex(columns=w_df.columns)).sum(axis=1, min_count=1)
```

### 1.1 Turnover formula

**One-way turnover** for week *t*:
```
TO_t = (1/2) Σ_i |w_{t,i} − w_{t-1,i}|
```

This is correct: it counts **one side** of round-trip trades. Some textbooks use `Σ|Δw|` (two-way); both are valid as long as the TC rate is matched. Here `TC = rate × TO` with the half-factor in `TO`, so `rate = 10 bps` is the cost per €1 of buy- (or sell-)side notional. ✓ Industry-standard convention.

### 1.2 Drift adjustment for Equal-Weight

The 1/N portfolio drifts between rebalances. `_eq_drift_to` computes the realised drift turnover at each rebalance step by computing the post-drift weights `(1/n)(1+r_i)/(1+r_p)` and comparing to the target `1/n`. Then it takes the half-absolute sum. This is the **correct definition of the drift-induced turnover** for a 1/N portfolio rebalanced every period to the equal target. ✓

For STOXX 600 (single-asset benchmark), `to_st = 0`. ✓

### 1.3 Static / Regime / Weighted CVaR / Markowitz turnover

These strategies hold weights flat between 4-weekly rebalances. `_weekly_to` will produce:
- 0 on non-rebalance weeks (weights don't change),
- |Δ_rebal| / 2 on rebalance weeks.

### 1.4 Annualisation

`ann_to_pct = weekly_to.mean() * 52 * 100`

This is annualisation of the **average weekly** turnover. For a strategy that rebalances every 4 weeks:

```
mean_weekly_TO = (Σ_rebal_weeks |Δw|/2) / N_total_weeks
              = (N_rebalances × avg_per_rebalance_TO) / (4 × N_rebalances)
              = avg_per_rebalance_TO / 4
ann_TO        = (avg_per_rebalance_TO / 4) × 52
              = avg_per_rebalance_TO × 13
```

So **the reported "annualised turnover" equals the average per-rebalance turnover × 13** (i.e. 13 rebalances per year, which is correct for a 4-weekly schedule).

### 1.5 TC charge

`net_t = gross_t − rate × TO_{t-1}`

`TO_{t-1}` is the previous week's turnover. Why the lag? Because `_port` uses `w_df.shift(1) * ret` — the weight at week *t-1* generates the return at week *t*. The rebalance trade therefore *executes* at week *t-1*'s close, and the implementation lag means the cost is realised in week *t*. The `.shift(1).fillna(0.0)` aligns cost incidence with return timing. ✓ Correct convention.

## 2. Reconciliation against verified numbers

Verified directly from `reports/panels/panel_b_regime_oos_performance.csv`:

| Strategy | weekly_to_pct | ann_to_pct (CSV) | Computed = weekly × 52 | Implied per-rebal TO (× 4) | User-known |
|----------|--------------:|-----------------:|----------------------:|---------------------------:|-----------:|
| equal_weight_risky | 0.6764 | 35.17 | 35.17 | n/a (rebalanced every week, drift)¹ | — |
| stoxx600 | 0.0 | 0.0 | 0.0 | 0.0 | — |
| static_cvar | 0.4116 | 21.40 | 21.40 | 1.65% | **21.4%** ✓ |
| markowitz | 0.2371 | 12.33 | 12.33 | 0.95% | — |
| regime_cvar_A | 4.3414 | 225.75 | 225.75 | **17.37%** | **225.8% / 17.4%** ✓ |
| weighted_cvar | 4.4713 | 232.51 | 232.51 | 17.89% | **232.5%** ✓ |

¹ EW is conceptually re-set to 1/N at each 4-week rebalance, so per-rebalance TO ≈ 4 × weekly drift TO. The reported 35.17% is the realised drift-induced TO over a year.

**Answer to the user's direct question:**
- **Is 225.8% correct?** ✓ Yes — `panel_b_regime_oos_performance.csv` row `regime_cvar_A,...,4.3414,225.75,...` rounds to 225.8%. 4.3414 weekly × 52 = 225.75 ≈ 225.8%.
- **Does it mean about 17.4% per 4-week rebalance?** ✓ Yes — 225.75 / 13 = 17.365% per rebalance; weekly_to × 4 (since only 1 of every 4 weeks has nonzero TO) = 4.3414 × 4 = 17.37%.
- **Are transaction-cost-adjusted Sharpe ratios affected?** They are correctly computed using the lagged-turnover convention. `Sharpe@10bps` for Regime CVaR-A is 0.346, which equals what the user expects. ✓
- **Is the turnover label in the paper correct?** The paper text correctly states "225.75% for Regime CVaR-A versus 21.4% for Static CVaR" (build_paper_v8.js line 715) and "232.5%" for Weighted (line 716). ✓

## 3. Cross-strategy table (all active scripts)

Reconstructed from CSVs already produced.

| Strategy | Source CSV | Ann. TO (%) | Avg per-rebal TO (%) (= Ann/13) | Convention | Status |
|----------|------------|-----------:|--------------------------------:|------------|--------|
| **Panel A (1213 wk, 2003-2026)** |
| Equal-Weight Risky | panel_a_long_horizon_performance.csv | 36.28 | drift | half-abs Σ, ×52 mean-weekly | ✓ |
| STOXX 600 | " | 0.00 | 0.00 | constant 100% | ✓ |
| Static CVaR | " | 24.87 | 1.91 | std (half-abs Σ × 13) | ✓ |
| Markowitz | " | 16.83 | 1.29 | std | ✓ |
| **Panel B (808 wk, 2010-2026)** |
| Equal-Weight Risky | panel_b_regime_oos_performance.csv | 35.17 | drift | std | ✓ |
| Static CVaR | " | 21.40 | 1.65 | std | ✓ matches user |
| Regime CVaR-A | " | 225.75 | 17.37 | std | ✓ matches user "225.8%, 17.4%" |
| Weighted CVaR | " | 232.51 | 17.89 | std | ✓ matches user 232.5% |
| **Panel B HICP-lag6** |
| Static CVaR | panel_b_regime_oos_performance_hicp_lag6.csv | 19.70 | 1.52 | std | ✓ |
| Regime CVaR-A | " | 205.56 | 15.81 | std | ✓ |
| Weighted CVaR | " | 221.56 | 17.04 | std | ✓ |
| **Panel B ZEW-swap** |
| Regime CVaR-A (ZEW) | panel_b_performance_zew_swap.csv | 201.39 | 15.49 | std | ✓ |
| Weighted CVaR (ZEW) | " | 206.05 | 15.85 | std | ✓ |
| **TC-aware CVaR (10 bps net)** |
| Regime CVaR-A tau=0.10 | tc_aware_cvar/turnover_summary.csv | 59.90 | 4.61 | std | ✓ |
| Weighted CVaR tau=0.10 | " | 61.47 | 4.73 | std | ✓ |
| ZEW Weighted CVaR lam=0.005 | " | 64.81 | 4.99 | std | ✓ (matches user 64.8% Fig 3) |
| **Regime-constrained CVaR** |
| RC baseline | regime_constraints/performance.csv | 29.20 | 2.25 | std | ✓ matches user "29.2%" |
| RC ZEW-swap | " | 26.96 | 2.07 | std | ✓ matches user "27.0%" |
| **FI-Expanded Panel B** |
| Static CVaR (FI-Exp) | fi_expanded/panel_b_performance_fi_expanded.csv | 13.12 | 1.01 | std | ✓ |
| Regime CVaR-A (FI-Exp) | " | 134.12 | 10.32 | std | ✓ matches paper "from 225.8 to 134.1" |
| Weighted CVaR (FI-Exp) | " | 127.14 | 9.78 | std | ✓ |
| Regime-Constrained (FI-Exp) | " | 34.60 | 2.66 | std | ✓ |

**Convention consistency:** ALL strategies in ALL active CSVs use the same half-absolute-sum × 52 (mean-weekly) convention. No mixed conventions detected.

## 4. TC application correctness

For each script, `_apply_tc(gross, to, rate)` is called with `rate = tc/10_000`. For `tc=10` (10 bps), `rate = 0.001`. The TC drag at week *t* is:

```
drag_t = 0.001 × TO_{t-1}
```

Computed example for Regime CVaR-A (mean turnover 4.34% weekly, lagged once):
```
expected_drag_annual = 0.001 × 4.34% × 52 = 0.226% (22.6 bps annually)
```

Verify by comparing gross vs net@10bps CAGR for Regime CVaR-A: 4.35% → 4.11% = −0.24% absolute drag. ≈ matches 22.6 bps after compounding. ✓

For Static CVaR: 0.001 × 0.41% × 52 = 0.021% annual drag. Verify CAGR 6.03% → 6.01% = −0.02%. ✓

## 5. Turnover-related claims in the paper

| Claim location | Claim | CSV value | Match |
|---------------|-------|----------|-------|
| build_paper_v8.js:715 | "annual turnover of 225.75% for Regime CVaR-A versus 21.4% for Static CVaR" | 225.75 / 21.4 | ✓ |
| build_paper_v8.js:716 | "Weighted CVaR is similar at 232.5%" | 232.51 | ✓ |
| build_paper_v8.js:808 | Table V row Static CVaR ann_to "21.4" | 21.40 | ✓ |
| build_paper_v8.js:810 | Table V row Regime CVaR-A ann_to "225.8" | 225.75 | ✓ |
| build_paper_v8.js:811 | Table V row Weighted CVaR ann_to "232.5" | 232.51 | ✓ |
| build_paper_v8.js:832 | Table VI row Static CVaR ann_to "21.4" | 21.40 | ✓ |
| build_paper_v8.js:834-835 | RC-A 225.8; W-CVaR 232.5 | 225.75 / 232.51 | ✓ |
| build_paper_v8.js:895 | "annual turnover from 225.8% to 59.9%" (tau=0.10 effect) | 225.75 → 59.90 | ✓ |
| build_paper_v8.js:923-925 | RC-CVaR baseline 29.2%, ZEW 27.0% | 29.20 / 26.96 | ✓ |
| build_paper_v8.js:977 | Table VII Static CVaR (baseline) 20.6% | 20.65 (tc_aware_cvar/turnover_summary.csv) | ✓ |
| build_paper_v8.js:982 | "Weighted CVaR, ZEW+lambda=0.005" 64.8% | 64.81 | ✓ |
| build_paper_v8.js:1056 | FI-expanded "turnover falls from 225.8% to 134.1%" | 225.75 → 134.12 | ✓ |
| build_paper_v8.js:1372 | Conclusion: "225.8% versus 21.4% annually" | 225.75 / 21.40 | ✓ |
| **scripts/07_panel_b_regime_oos.py:381-383** *(auto-generated MD)* | "(~100–160% annually) vs static CVaR (~10%)" | NOT in CSV | **✗ stale narrative** |

The script's own narrative is stale (P1-D). The paper itself is consistent with the CSVs.

## 6. Turnover-related claims in `reports/final/model_backtest_summary.md`

| Claim | Value | Match? |
|-------|-------|--------|
| (cross-referenced separately in `markdown_report_audit.md`) | — | — |

## 7. Verdict

**All numerical turnover values in the paper and CSVs are internally consistent and correctly computed.** The only TC-related defect is **P1-D** in `scripts/07_panel_b_regime_oos.py` lines 381-383: hard-coded summary narrative quotes stale "(~100-160%) vs (~10%)" values that will be re-written into `reports/panels/panel_b_regime_oos_summary.md` on every rerun. The narrative numbers in that markdown should be parameterised on actual CSV values, e.g.:

```python
turn_static = g0.loc["static_cvar", "ann_to_pct"]
turn_regime = g0.loc["regime_cvar_A", "ann_to_pct"]
"...high turnover (~{turn_regime:.0f}% annually) vs static CVaR (~{turn_static:.0f}%)."
```

The 225.8% headline number is correct and internally consistent.
