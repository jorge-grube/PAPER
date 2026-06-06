# Model Backtest Summary

*Updated: 2026-05-09. Covers Panel A and Panel B two-panel architecture.*

---

## Overview

This paper evaluates six portfolio strategies across two complementary empirical panels. The two-panel architecture is a deliberate design choice driven by data availability: regime-aware strategies require several years of HMM training data before producing their first out-of-sample (OOS) label, which would exclude the Global Financial Crisis (GFC) from the regime evidence. Rather than discard the pre-2010 history, we use it for a long-horizon panel that does not depend on HMM outputs.

| Panel | Strategies | Start | Obs | Years | Requires HMM |
| --- | --- | --- | --- | --- | --- |
| **A** — Long-horizon | EW-Risky, STOXX 600, Static CVaR, Markowitz | 2003-01-10 | 1 213 | 23.3 | No |
| **B** — Regime OOS | All six (Panel A + Regime CVaR-A + Weighted CVaR) | 2010-10-15 | 808 | 15.5 | Yes |

**Investable universe:** European multi-asset — six European equity indices (CAC 40, DAX, EuroStoxx 50, FTSE MIB, IBEX 35, STOXX Europe 600), listed real estate (FTSE EPRA/NAREIT Europe), Bloomberg Commodity Index, Brent crude oil, gold, plus EURIBOR 3M as risk-free/cash proxy (10 risky assets + cash, 11 series total).

**Returns:** Weekly simple (arithmetic) returns throughout. EURIBOR annualised rate converted to weekly simple return. Homogeneous arithmetic return convention across all risky and cash series.

Both panels share the same rebalancing cadence (every 4 weeks) and the same CVaR parameters (α = 95%, max weight 25% per asset). TC sensitivities are reported at 0, 5, 10, and 25 bps one-way.

---

## Panel A — Long-Horizon Evidence (2003–2026)

### Why Panel A starts in 2003

Panel A strategies require only a history of asset returns — no HMM labels. The binding constraint is a 156-week return burn-in (three years of weekly data) before the first portfolio allocation. With weekly returns available from January 2000, the first valid allocation date is **2003-01-10**, capturing the full 23-year record including the GFC drawdown.

CVaR and Markowitz optimisations use a rolling 260-week (five-year) scenario window rather than an expanding window, to keep LP solve times tractable across 1,213 rebalancing dates.

### Performance (gross, 0 bps TC)

| Strategy | CAGR | Vol | Sharpe | MaxDD | CVaR 95% (wkly) | Calmar |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Equal-Weight Risky (1/N) | +5.89% | 15.24% | 0.368 | −50.09% | −5.24% | 0.118 |
| STOXX Europe 600 | +4.47% | 17.50% | 0.265 | −60.15% | −5.94% | 0.074 |
| Static CVaR | **+7.05%** | **12.22%** | **0.513** | **−39.49%** | **−4.19%** | **0.179** |
| Markowitz (Min-Var) | +5.65% | 12.02% | 0.409 | −45.58% | −4.27% | 0.124 |

*Sharpe = mean(r − EURIBOR 3M) / std(r − EURIBOR 3M) × √52.
CVaR is reported as the weekly average of the worst-5% weekly return observations (not annualised).*

**Key finding:** Static CVaR produces superior Sharpe (0.513 vs 0.368) and substantially lower drawdown (−39.5% vs −50.1%) than the equal-weight benchmark over 23 years. This finding requires no HMM regime model and spans four major market episodes: the GFC (2007–2009), the Eurozone sovereign debt crisis (2010–2012), COVID-19 (2020), and the 2022 inflation shock.

### TC Sensitivity — Panel A (Sharpe)

| Strategy | 0 bps | 5 bps | 10 bps | 25 bps |
| --- | ---: | ---: | ---: | ---: |
| Equal-Weight Risky (1/N) | 0.368 | 0.367 | 0.365 | 0.362 |
| STOXX Europe 600 | 0.265 | 0.265 | 0.265 | 0.265 |
| Static CVaR | 0.513 | 0.512 | 0.511 | 0.508 |
| Markowitz (Min-Var) | 0.409 | 0.409 | 0.408 | 0.406 |

Static CVaR's low annual turnover (~25%) means it retains its Sharpe advantage across all TC levels.

### Statistical Evidence — Panel A

Block-bootstrap Sharpe CIs (block = 13 weeks, n = 5,000):

| Strategy | Sharpe | 95% CI |
| --- | ---: | --- |
| Equal-Weight Risky (1/N) | 0.368 | [−0.023, 0.814] |
| STOXX Europe 600 | 0.265 | [−0.089, 0.668] |
| Static CVaR | 0.513 | [+0.101, 0.987] |
| Markowitz (Min-Var) | 0.409 | [+0.003, 0.867] |

**Static CVaR provides the clearest evidence of positive risk-adjusted performance** (CI lower bound +0.101, firmly above zero). **Markowitz is marginal**, with a lower CI bound close to zero (+0.003). Equal-Weight and STOXX 600 CIs include zero. No HAC test is significant at conventional levels — with 1,213 weekly observations, power is insufficient to formally reject equality of mean excess returns.

---

## Panel B — Fully OOS Regime Evidence (2010–2026)

### Why Panel B starts in 2010

Panel B includes Regime CVaR-A (conditions CVaR scenarios on the current HMM statistical market-state classification) and Weighted CVaR (reweights all scenarios by regime-posterior similarity). Both require an HMM trained exclusively on past data before each rebalance — no look-ahead.

The HMM produces four statistical market-state classifications, interpreted ex post based on their feature means (ascending VIX z-score order):

| Walk-forward state | Economic label | Mean VIX z-score |
| --- | --- | ---: |
| State 0 | Low-vol / Subdued | -0.96 |
| State 1 | Risk-on / Expansion | -0.59 |
| State 2 | Neutral / Moderate | +0.05 |
| State 3 | Elevated-risk / Stress | +1.85 |

These labels are applied ex post for interpretability only; the HMM itself is an unsupervised statistical model with no built-in economic meaning.

The HMM walk-forward uses a minimum training window of 156 weeks (three years). Combined with the 156-week portfolio burn-in, the first valid OOS allocation date is **2010-10-15**.

All HMM labels in Panel B are strictly OOS: at each 4-week step, the HMM is refit on data up to (but not including) the rebalance date. Walk-forward labels are stored in `data/processed/regime_labels_wf_156.parquet`.

The full-sample HMM (Figure 1, `reports/figures/full_sample_regime_timeline.png`) fits a 4-state model to the entire 2004–2026 feature dataset. It is used **for descriptive illustration only** — not for OOS portfolio construction.

### Performance (gross, 0 bps TC)

| Strategy | CAGR | Vol | Sharpe | MaxDD | CVaR 95% (wkly) | Calmar |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Equal-Weight Risky (1/N) | +5.65% | 14.43% | 0.409 | −32.83% | −4.81% | 0.172 |
| STOXX Europe 600 | +5.28% | 15.86% | 0.363 | −31.93% | −5.33% | 0.165 |
| Static CVaR | **+6.03%** | **10.97%** | **0.530** | −25.33% | −3.60% | **0.238** |
| Markowitz (Min-Var) | +5.03% | 10.85% | 0.447 | **−24.94%** | −3.64% | 0.202 |
| Regime CVaR-A | +4.35% | 11.78% | 0.365 | −25.81% | −3.96% | 0.168 |
| Weighted CVaR | +4.35% | 11.62% | 0.368 | −25.41% | −3.88% | 0.171 |

### TC Sensitivity — Panel B (Sharpe)

| Strategy | 0 bps | 5 bps | 10 bps | 25 bps |
| --- | ---: | ---: | ---: | ---: |
| Equal-Weight Risky (1/N) | 0.409 | 0.407 | 0.406 | 0.403 |
| STOXX Europe 600 | 0.363 | 0.363 | 0.363 | 0.363 |
| Static CVaR | 0.530 | 0.529 | 0.528 | 0.525 |
| Markowitz (Min-Var) | 0.447 | 0.446 | 0.445 | 0.444 |
| Regime CVaR-A | 0.365 | 0.355 | 0.346 | 0.317 |
| Weighted CVaR | 0.368 | 0.358 | 0.348 | 0.318 |

### Turnover

| Strategy | Weekly | Annualised |
| --- | ---: | ---: |
| Equal-Weight Risky (1/N) | 0.68% | 35.2% |
| STOXX Europe 600 | 0.00% | 0.0% |
| Static CVaR | 0.41% | 21.4% |
| Markowitz (Min-Var) | 0.24% | 12.3% |
| Regime CVaR-A | **4.34%** | **225.7%** |
| Weighted CVaR | **4.47%** | **232.5%** |

Regime CVaR strategies have ~100× higher turnover than Markowitz. At 10 bps TC the Sharpe degradation is ≈0.02 for static strategies vs ≈0.05 for regime strategies; at 25 bps the regime penalty eliminates any gross advantage.

### Statistical Evidence — Panel B

Block-bootstrap Sharpe CIs (block = 13 weeks, n = 5,000):

| Strategy | Sharpe | 95% CI |
| --- | ---: | --- |
| Equal-Weight Risky (1/N) | 0.409 | [−0.054, 0.926] |
| STOXX Europe 600 | 0.363 | [−0.056, 0.833] |
| Static CVaR | 0.530 | [+0.068, 1.058] |
| Markowitz (Min-Var) | 0.447 | [−0.004, 0.962] |
| Regime CVaR-A | 0.365 | [−0.079, 0.880] |
| Weighted CVaR | 0.368 | [−0.074, 0.891] |

No HAC test is significant. **Static CVaR provides the clearest evidence of positive performance** (CI lower bound +0.068). **Markowitz is marginal** (lower bound −0.004, essentially straddling zero). Regime CVaR-A and Weighted CVaR CIs span more than 0.95 Sharpe units and include zero — their point estimates are statistically indistinguishable from both the benchmark and Static CVaR.

---

## Honest Assessment of Regime CVaR vs Static CVaR

**Static CVaR dominates regime-conditioned CVaR** on every performance dimension:

- **Higher Sharpe:** Static CVaR Sharpe 0.513 (Panel A) and 0.530 (Panel B) vs 0.365/0.368 for regime strategies.
- **Lower vol:** Static CVaR Vol ≈ 11% vs Regime CVaR ≈ 11.6–11.8%.
- **Lower turnover:** Static CVaR ≈21% annually vs ≈225–233% for regime strategies.
- **TC robustness:** Static CVaR degrades 0.530 → 0.525 at 25 bps; regime strategies drop from 0.365/0.368 to 0.317/0.318.
- **Statistical power:** All pairwise differences are statistically indistinguishable at any conventional level.

Two interpretations are plausible. First, the 4-state HMM over 46 features may over-parameterise the market-state signal for this universe and period; Static CVaR's tail-risk constraint already conditions portfolio construction without an explicit latent state. Second, 808 OOS weeks may be insufficient to identify the value of state-conditioning for European multi-asset allocation. The paper contributes a walk-forward HMM conditioning framework for CVaR optimisation and documents its empirical properties honestly.

---

## Methodological Notes

**Investable universe** — 10 risky assets: six European equity indices (CAC 40, DAX, EuroStoxx 50, FTSE MIB, IBEX 35, STOXX Europe 600), FTSE EPRA/NAREIT Europe (listed real estate), Bloomberg Commodity Index, Brent crude oil, gold. Plus EURIBOR 3M as risk-free/cash proxy.

**Returns** — Weekly simple (arithmetic) returns. EURIBOR annualised rate → weekly simple return via (1+r_annual)^(1/52)−1. Homogeneous with risky asset returns.

**Transaction costs** — One-way costs at each rebalancing date. STOXX 600 buy-and-hold TC = 0 by construction.

**Risk-free rate** — EURIBOR 3M (time-varying weekly series). Not a fixed constant.

**CVaR reporting** — Weekly CVaR 95% = mean of worst-5% weekly return observations (not annualised). Annualising by ×52 inflates via GFC tail events.

**HMM market-state classifications** — Walk-forward HMM states are statistical classifications ordered by ascending mean VIX z-score at each refit. Economic labels (Low-vol/Subdued, Risk-on/Expansion, Neutral/Moderate, Elevated-risk/Stress) are applied ex post for interpretability only. The model itself is unsupervised; it does not identify true economic regimes.

**Full-sample HMM** — Fit to entire 2004–2026 dataset for descriptive illustration (Figure 1) only. No OOS portfolio returns derive from full-sample labels.

**Implementation lag** — `_port()` applies a 1-week lag (`w.shift(1)`) before multiplying weights by returns. `min_count=1` ensures all-NaN rows remain NaN rather than collapsing to zero.

---

## File Index

| File | Description |
| --- | --- |
| `reports/panels/panel_a_long_horizon_performance.csv` | Panel A full performance table |
| `reports/panels/panel_a_long_horizon_summary.md` | Panel A detailed summary |
| `reports/panels/panel_a_statistical_tests.md` | Panel A HAC + bootstrap tests |
| `reports/panels/panel_b_regime_oos_performance.csv` | Panel B full performance table |
| `reports/panels/panel_b_regime_oos_tc_sensitivity.csv` | Panel B TC sensitivity |
| `reports/panels/panel_b_regime_oos_summary.md` | Panel B detailed summary |
| `reports/panels/panel_b_statistical_tests.md` | Panel B HAC + bootstrap tests |
| `reports/statistical_tests.md` | Canonical backtest HAC + bootstrap |
| `reports/figures/full_sample_regime_timeline.png` | Descriptive regime timeline (in-sample only) |
| `reports/macro_release_date_risk_audit.md` | Macro variable look-ahead risk classification |
| `data/processed/panel_a_returns.parquet` | Panel A weekly gross returns |
| `data/processed/panel_b_returns.parquet` | Panel B weekly gross returns |
| `data/processed/regime_labels_wf_156.parquet` | OOS walk-forward market-state labels (MIN_TRAIN=156) |
| `data/processed/canonical_backtest_returns.parquet` | Canonical (260-week window) backtest returns |
  