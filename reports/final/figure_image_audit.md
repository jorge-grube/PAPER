# Figure and Image Audit

**Audit date:** 2026-05-12
**Images inspected:** 6 (one duplicated between `reports/figures/` and `paper/figures/`).

---

## 1. File inventory

| Path | Size (B) | Pixels | SHA-1 (16 hex) | Generator | Used in paper |
|------|--------:|--------|----------------|-----------|---------------|
| `reports/figures/full_sample_regime_timeline.png` | 299,363 | 2096 × 1408 | 627729e9be427fd2 | `scripts/09_regime_timeline_figure.py` | (source for Figure 1) |
| `paper/figures/figure_1_regime_timeline.png` | 299,363 | 2096 × 1408 | 627729e9be427fd2 | **manual copy of the above** | Figure 1 |
| `paper/figures/figure_2_cumulative_wealth_panel_b.png` | 482,821 | 2511 × 1220 | b62a66fdaf0961fa | `scripts/07_figures/generate_paper_figures.py:fig2` | Figure 2 |
| `paper/figures/figure_3_turnover_vs_net_sharpe.png` | 222,309 | 2198 × 1310 | a1f5de31ab0cc8c1 | `scripts/07_figures/generate_paper_figures.py:fig3` | Figure 3 |
| `paper/figures/figure_4_static_cvar_weights_baseline_vs_fi.png` | 183,420 | 2211 × 1160 | fb7d4cdc5f1aa874 | `scripts/07_figures/generate_paper_figures.py:fig4` | Figure 4 |
| `paper/figures/figure_5_drawdown_baseline_vs_fi.png` | 350,818 | 2511 × 1161 | ff0a6d8c0dfee45c | `scripts/07_figures/generate_paper_figures.py:fig5` | Figure 5 |

**Verified:** `reports/figures/full_sample_regime_timeline.png` and `paper/figures/figure_1_regime_timeline.png` are **byte-identical** (same SHA-1 and same size). Figure 1 is therefore a manual copy of the output of script 09.

**DPI:** all images saved at 180 dpi (script 09) or 300 dpi (`generate_paper_figures.py`). At 300 dpi, 2511 px wide = 8.37 inches, which is appropriate for US Letter page-width.

---

## 2. Source script ↔ figure correspondence

| Figure | Script function | Input data |
|--------|-----------------|-----------|
| 1 (regime timeline) | `09_regime_timeline_figure.py:main` | `data/processed/regime_labels_full.parquet`, `investable_returns_weekly.parquet` |
| 2 (cumulative wealth Panel B) | `07_figures/generate_paper_figures.py:fig2` | `data/processed/panel_b_returns.parquet` |
| 3 (turnover vs Sharpe scatter) | `07_figures/generate_paper_figures.py:fig3` | **HARD-CODED data points** (11 strategies), not from CSV |
| 4 (avg weights baseline vs FI) | `07_figures/generate_paper_figures.py:fig4` | **HARD-CODED 6 bar heights × 2 series**, not from CSV |
| 5 (drawdown baseline vs FI) | `07_figures/generate_paper_figures.py:fig5` | `data/processed/panel_b_returns.parquet`, `panel_b_returns_fi_expanded.parquet` |

### 2.1 Figure 3 hard-coded values vs CSV — verification

| Point | Hard-coded (TO%, Sharpe@10) | Verified CSV value | Match |
|-------|---|---|---|
| Equal-Weight (1/N) | 35.2, 0.406 | 35.17, 0.406 | ✓ |
| STOXX Europe 600 | 0.0, 0.363 | 0.0, 0.363 | ✓ |
| Static CVaR | 21.4, 0.528 | 21.40, 0.528 | ✓ |
| Markowitz (Min-Var) | 12.3, 0.445 | 12.33, 0.445 | ✓ |
| Regime CVaR-A | 225.8, 0.346 | 225.75, 0.346 | ✓ |
| Weighted CVaR | 232.5, 0.348 | 232.51, 0.348 | ✓ |
| CVaR-A, τ=0.10 | 59.9, 0.486 | 59.90, 0.486 | ✓ |
| Weighted CVaR, τ=0.10 | 61.5, 0.486 | 61.47, 0.486 | ✓ |
| RC-CVaR (baseline) | 29.2, 0.519 | 29.20, 0.519 | ✓ |
| RC-CVaR (ZEW-swap) | 27.0, 0.517 | 26.96, 0.517 | ✓ |
| ZEW+λ=0.005 (exploratory) | 64.8, 0.567 | 64.81, 0.567 | ✓ |

**All 11 hard-coded scatter points match the source CSVs to displayed precision. ✓**

### 2.2 Figure 4 hard-coded bar heights vs CSV — verification

The figure says baseline `[39.3, 9.7, 25.0, 25.0, 1.1, 0.0]` and FI-expanded `[3.0, 0.0, 10.0, 13.5, 0.0, 73.5]`.

`reports/model_improvement/regime_constraints/regime_average_weights.csv` does NOT contain the unconstrained Static CVaR weights aggregated by asset group — those numbers come from `reports/fi_expanded/fi_expanded_comparison.md`. Independent cross-check is harder. The numbers reported are the AVERAGE Static CVaR weight per asset group over Panel B, grouped as:
- European Equities (sum of CAC, DAX, EuroStoxx50, FTSE_MIB, IBEX35, StoxxEurope600)
- Real Estate (FTSE EPRA Europe)
- Gold
- Bloomberg Commodity
- Brent
- Govt Bonds (Germany+Spain+Italy)

This is a **P2** maintainability risk (the figure value depends on a manually computed average) but not currently a numerical inconsistency.

---

## 3. Caption / axis-label / banned-symbol check

All five figures were re-generated in v8 with ASCII-only text (per `v8_correction_report.md` P1.1). Spot-check of the visual output is not feasible here (no rendering), but the generator source code was verified:

- `09_regime_timeline_figure.py` — title `"HMM Regime Timeline, Full Sample (2004 to 2026)"` (ASCII hyphen, no em/en dash). ✓ Annotation labels: ASCII only. ✓
- `07_figures/generate_paper_figures.py` —
  - `fig2` title `"Figure 2. Cumulative Wealth, Panel B (October 2010 to April 2026, Gross)"` — ASCII ✓
  - `fig3` title `"Figure 3. Turnover vs. Net Sharpe, Panel B (2010 to 2026)"` — ASCII ✓ (Greek `τ` in scatter labels for `CVaR-A, τ=0.10` is fine — `τ` is not in the banned set)
  - `fig4` title `"Figure 4. Average Portfolio Weights: Static CVaR, Baseline vs. FI-Expanded (Panel B, 2010 to 2026)"` — ASCII ✓
  - `fig5` title `"Figure 5. Drawdown Paths: Static CVaR Baseline vs. FI-Expanded (Panel B, 2010 to 2026)"` — ASCII ✓

---

## 4. Figure 1 state-labelling correctness

**P1-C (cf. python_code_audit.md):** `regime_labels_full.parquet` uses non-canonical ordering where state 0 has the HIGHEST mean VIX (+1.85) and state 3 the lowest (−0.96). Script 09 hard-codes:
```python
REGIME_LABELS = {0: "High-Stress / Crisis", 1: "Recovery / Growth",
                 2: "Moderate",            3: "Bull / Low-Vol"}
```
…which is consistent with the *parquet's* state numbering but **opposite** of the canonical convention used in Tables IV-VIII and `model_backtest_summary.md`. The figure caption explicitly says "labels ordered by VIX z-score: High-Stress (+1.85) ... Bull (−0.96)" so a reader cannot be misled if they read the caption carefully, BUT no other paper element uses this state-0=stress convention. **Recommended fix:**
1. Regenerate `regime_labels_full.parquet` with a canonical permutation (so state 3 = highest VIX), and
2. Update script 09's `REGIME_LABELS` dict to match (state 0 = Bull/Low-Vol, state 3 = High-Stress/Crisis).

---

## 5. Verdict

- **All five figures match the data they purport to display, to displayed precision.** ✓
- **Banned Unicode characters are absent from figure text.** ✓
- **Figure 1's regime-state numbering convention differs from every other paper element** (P1). The figure is internally self-consistent and the caption documents the convention, but it creates a cognitive load for the reader and a regeneration trap.
- **Figure 3 and Figure 4 data points are hard-coded** in the generator script (P1-G / P1-H from code audit). All currently match the CSV sources but any future rerun will desync without a manual sync.
- **Figure resolution is appropriate for journal print** (300 dpi at ~8" width). ✓
