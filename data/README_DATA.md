# Data Dictionary

**Last updated:** 2026-05-10  
**Universe:** 11-asset baseline + 14-asset FI-expanded robustness

---

## Raw Data (`data/raw/`)

All raw files are LSEG Workspace (Refinitiv) exports in `.xlsx` format unless noted.  
Most investable series are total return indices in EUR. Exceptions: Brent is a front-month futures price (not a total return index), Gold is a EUR-converted spot price (USD per troy oz, converted at prevailing FX), and EURIBOR 3M is a rate series converted to weekly simple returns via $(1+r_{ann})^{1/52}-1$.

### Baseline Assets (11)

| Column Name | Asset | Source | RIC / Ticker | Notes |
|------------|-------|--------|-------------|-------|
| `EURIBOR_3M` | EURIBOR 3-Month | ECB / LSEG | `EUR3MD=` | Rate series, converted to weekly return |
| `Bloomberg_Commodity` | Bloomberg Commodity Index | LSEG | `BCOM` | Total return index |
| `Brent` | Brent Crude Oil | LSEG | `LCOc1` | Front-month futures price |
| `Gold` | Gold spot | LSEG | `XAU=` | USD per troy oz; EUR-converted |
| `CAC_40` | CAC 40 | LSEG | `.FCHI` | Total return |
| `DAX` | DAX (Germany) | LSEG | `.GDAXI` | Total return |
| `EuroStoxx50` | EURO STOXX 50 | LSEG | `.STOXX50E` | Total return |
| `FTSE_MIB` | FTSE MIB (Italy) | LSEG | `.FTMIB` | Total return |
| `IBEX35` | IBEX 35 (Spain) | LSEG | `.IBEX` | Total return |
| `StoxxEurope600` | STOXX Europe 600 | LSEG | `.STOXX` | Total return; primary benchmark |
| `FTSE_EPRA_NAREIT_Europe` | FTSE EPRA/NAREIT Europe | LSEG | `.FTEPRAEUR` | Real estate total return |

### Fixed Income Assets (FI-Expanded only, `data/raw/fixed_income/`)

| Column Name | Asset | RIC | Currency | Status |
|------------|-------|-----|---------|--------|
| `Germany_GovtBond` | FTSE German Govt Bond TR | `.FTDE_TSYEURT` | EUR | ✅ Included |
| `Spain_GovtBond` | FTSE Spanish Govt Bond TR | `.FTES_TSYEURT` | EUR | ✅ Included |
| `Italy_GovtBond` | FTSE Italian Govt Bond TR | `.FTIT_TSYUSDT` | EUR (converted) | ✅ Included — see note |
| Eurozone Govt Bond TR | FTSE Eurozone Govt Bond TR | — | EUR | 🔵 Panel B robustness only (starts 2012) |
| UK Gilt TR | FTSE UK Gilt TR | — | GBP | ❌ Rejected (starts 2022, GBP) |
| BBG Euro Agg 10+ | Bloomberg Euro Agg Treasury 10+ | — | EUR | ❌ Rejected (starts 2022, monthly) |
| ECB Rates | ECB 10Y sovereign yields | — | — | ❌ Rejected (yield, not total return) |

**Italy RIC note:** `.FTIT_TSYUSDT` — the `USDT` suffix identifies the underlying master index pricing currency (USD). No native EUR RIC (`.FTIT_TSYEURT`) exists in the LSEG catalogue. The LSEG metadata field "Currency Conversion: EUR" confirms the delivered series is EUR-denominated. Confirmed via vol ratio (1.62× Germany, within EUR periphery range 1.3–1.8×) and crisis-period behaviour.

---

## Processed Data (`data/processed/`)

All parquet files use weekly Friday-close dates as the index (dtype: `datetime64[ns]`).

### Price and Return Files

| File | Shape (approx) | Columns | Notes |
|------|---------------|---------|-------|
| `investable_prices_weekly.parquet` | 1369 × 11 | All 11 assets | Total return index levels |
| `investable_returns_weekly.parquet` | 1369 × 11 | All 11 assets | Simple weekly returns |
| `investable_prices_weekly_fi_expanded.parquet` | 1369 × 14 | 11 + 3 FI | FI-expanded price levels |
| `investable_returns_weekly_fi_expanded.parquet` | 1369 × 14 | 11 + 3 FI | FI-expanded simple returns |

### Regime Files

| File | Shape (approx) | Contents |
|------|-------|---------|
| `regime_features_weekly.parquet` | ~3400 × 46 | All engineered macro-financial features (spreads, slopes, z-scores, RV proxies). HMM uses 8 selected z-score columns — see below. |
| `regime_features_weekly_hicp_lag6.parquet` | ~3400 × 46 | Same as above but `hicp_headline_core_gap` lagged **6 weeks** (HICP publication-lag robustness) |
| `regime_labels_wf_156.parquet` | ~1213 × 1 | Walk-forward 4-state HMM labels (integer 0–3, ordered by ascending z52_VIX mean) |
| `regime_probs_wf_156.parquet` | ~1213 × 4 | Posterior probabilities for each of the 4 states per week |
| `regime_labels_full.parquet` | ~1369 × 1 | Full-sample (in-sample, non-OOS) HMM labels — used only for descriptive Figure 1 |

**8 HMM input features** (selected from `regime_features_weekly.parquet` by `REGIME_FEATURES` in `src/models/hmm.py`):

| Feature column | Description |
|----------------|-------------|
| `z52_VIX` | VIX 52-week rolling z-score |
| `z52_VSTOXX` | VSTOXX z-score |
| `z52_MOVE` | MOVE bond volatility index z-score |
| `z52_germany_10y_2y_slope` | Germany 10Y yield minus ECB deposit rate z-score |
| `z52_peripheral_spread_avg` | Average ES/PT/IT sovereign spread to Germany z-score |
| `z52_DXY_USD_Index` | DXY dollar index z-score |
| `z52_Eurozone_Economic_Sentiment_Indicator` | Eurozone ESI z-score |
| `z52_hicp_headline_core_gap` | HICP headline-minus-core inflation gap z-score |

**4-state heuristic labels** (assigned post-estimation from state mean vectors):
- State with lowest mean `z52_VIX` → Risk-on / Expansion
- Next → Low-vol / Subdued
- Next → Neutral / Moderate
- State with highest mean `z52_VIX` → Elevated-risk / Stress (or Acute-stress / Flight-to-quality in extreme episodes)

### Portfolio Return Files

| File | Columns | Notes |
|------|---------|-------|
| `panel_a_returns.parquet` | equal_weight_risky, stoxx600, static_cvar, markowitz | Gross weekly returns |
| `panel_b_returns.parquet` | + regime_cvar_a, weighted_cvar | Gross weekly returns |
| `panel_a_returns_fi_expanded.parquet` | Same strategies, FI-expanded universe | |
| `panel_b_returns_fi_expanded.parquet` | Same strategies, FI-expanded universe | |

---

## Data Quality

- **Sample period:** 2000-01-14 to 2026-04-03
- **Weekly observations:** 1,369
- **Missing rate:** ≤0.1% for all series (holiday alignment)
- **Forward-fill cap:** 5 consecutive business days
- **Currency:** All series in EUR

For full validation statistics, see `reports/data/data_validation_summary.md` and `reports/fi_expanded/fixed_income_file_validation.md`.
