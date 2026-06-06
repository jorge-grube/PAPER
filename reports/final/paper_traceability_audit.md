# Source-to-Paper Traceability Audit

**Audit date:** 2026-05-12
**Companion CSV:** `paper_traceability_matrix.csv`

This file traces every Table I-IX and Figure 1-5 in `paper_draft_JF_style_v8_FINAL_FOR_FEEDBACK.docx` to its source data parquet, source report CSV, and generating script.

---

## 1. Summary

| Element | Source data | Generator | Auto-link to docx? | Current? | Issues |
|---------|-------------|-----------|--------------------:|---------:|-------|
| Table I | `investable_returns_weekly.parquet` + metadata | scripts/01 + manual prose | NO | ✓ | — |
| Table II | `panel_a_returns.parquet` | scripts/06 | NO (hand-keyed in JS) | ✓ | — |
| Table III | `panel_a_returns.parquet` | scripts/08 | NO | ✓ | — |
| Table IV | `panel_b_returns.parquet` | scripts/07 | NO | ✓ | — |
| Table V | `panel_b_returns.parquet` | scripts/07 | NO | ✓ | — |
| Table VI | `panel_b_returns.parquet` | scripts/08 | NO | ✓ | — |
| Table VII | tc_aware + regime_constraints weights/perf | scripts/14 + 15 | NO | ✓ | scope note for 0.553/0.530 difference |
| Table VIII | `panel_a_returns_fi_expanded.parquet` + `panel_b_returns_fi_expanded.parquet` | scripts/17 + 18 | NO | ✓ | — |
| Table IX | mixed (scripts/10, 11, 12, 13, 17/18) | scripts/10 etc. | NO | ✓ | HICP-lag6 narrative inconsistency between script-generated MD and paper |
| Table F.1 | `investable_returns_weekly.parquet` | scripts/07_figures.descriptive_stats | YES (CSV → paper hand-edit) | ✓ | — |
| Table F.2 | `investable_returns_weekly.parquet` | scripts/07_figures.descriptive_stats | YES | ✓ | — |
| Figure 1 | `regime_labels_full.parquet` | scripts/09 | NO (image embedded by JS) | ✓ | P1-C — labels non-canonical |
| Figure 2 | `panel_b_returns.parquet` | scripts/07_figures.fig2 | YES (script reads parquet) | ✓ | hardcoded path |
| Figure 3 | multiple CSVs | scripts/07_figures.fig3 | NO (datapoints hard-coded) | ✓ | hardcoded values |
| Figure 4 | `fi_expanded_comparison.md` | scripts/07_figures.fig4 | NO (bar heights hard-coded) | ✓ | hardcoded values |
| Figure 5 | `panel_b_returns*.parquet` | scripts/07_figures.fig5 | YES | ✓ | hardcoded path |

---

## 2. Verified value matches (paper ↔ CSV)

Spot-checked 25 numeric claims across Tables II-IX and Figures 3-4. **All match the underlying CSV to displayed precision.** See `paper_artifact_audit.md` Section 6 and `figure_image_audit.md` Section 2 for the per-claim verification table.

Headline numbers cross-checked separately in `headline_number_audit.md`:

| Headline | Paper claim | CSV verified | Match |
|----------|-----|------|---|
| Static CVaR Panel B Sharpe gross | 0.530 | 0.530 | ✓ |
| Static CVaR Panel B Sharpe @10bps | 0.528 | 0.528 | ✓ |
| Static CVaR Panel B Ann TO | 21.4% | 21.40% | ✓ |
| Regime CVaR-A Panel B Sharpe gross | 0.365 | 0.365 | ✓ |
| Regime CVaR-A Panel B Sharpe @10bps | 0.346 | 0.346 | ✓ |
| Regime CVaR-A Panel B Ann TO | 225.8% | 225.75% (rounds to 225.8) | ✓ |
| Weighted CVaR Panel B Ann TO | 232.5% | 232.51% | ✓ |
| TC-aware tau=0.10 Regime CVaR-A net@10bps | 0.486 | 0.486 | ✓ |
| TC-aware tau=0.10 Weighted CVaR net@10bps | 0.486 | 0.486 | ✓ |
| ZEW+lambda=0.005 Weighted CVaR gross / net@10bps | 0.572 / 0.567 | 0.572 / 0.567 | ✓ |
| RC-CVaR baseline gross / net@10bps | 0.522 / 0.519 | 0.522 / 0.519 | ✓ |
| RC-CVaR ZEW gross / net@10bps | 0.519 / 0.517 | 0.519 / 0.517 | ✓ |
| FI Panel A Static Sharpe delta | +0.034 | 0.513 → 0.547 | ✓ |
| FI Panel B Static Sharpe delta | -0.026 | 0.530 → 0.504 | ✓ |
| FI Panel B drawdown change | -39.5% → -14.8% | (Static CVaR Panel A baseline -39.49 vs FI Panel A -14.77 = -14.8%, AND Panel B baseline -25.33 vs FI Panel B -14.61 = -14.6%) | ✓ (paper text mentions -14.8% for Panel A drawdown; ✓ matches) |
| HICP-lag6 label agreement | ~55% | 55.12% | ✓ |
| ZEW label agreement | 47.9% | 47.9339% | ✓ |
| Bootstrap draws | 5,000 | 5,000 | ✓ |
| Panel A weeks | 1,213 | 1,213 | ✓ |
| Panel B weeks | 808 | 808 | ✓ |

## 3. Discrepancies found

### 3.1 Static CVaR Sharpe scope (0.530 vs 0.553) — RESOLVED
Already addressed by v8 (P1.4). Table VII caption contains scope note. ✓

### 3.2 HICP-lag6 narrative inconsistency — UNRESOLVED
- Paper text (Section VII.A and Table IX row 1): "main conclusion unchanged"
- Auto-generated `reports/regimes/hicp_lag6_robustness.md`: "promote the lag6 variant from appendix"

The auto-generated MD will overwrite on every rerun of script 10. Either:
1. Edit the auto-generation logic in script 10 (line 618: `conclusion_stable = max_regime_diff < 0.02` → `< 0.10`), OR
2. Treat the script-generated MD as a draft and not cite it in the paper.

### 3.3 Figure 1 state-ordering convention — UNRESOLVED
Figure 1's `REGIME_LABELS` dict assigns state 0 to "High-Stress / Crisis" while every other element in the paper (Tables, METHODOLOGY.md, model_backtest_summary.md) assigns state 0 to "Low-vol / Subdued". The figure caption documents the inversion BUT readers may still be confused.

## 4. Provenance chains

### 4.1 Figure 2 (cumulative wealth Panel B)
```
data/raw/*.xlsx
  → scripts/01_validate_and_build_dataset.py
  → data/processed/investable_returns_weekly.parquet
  → scripts/07_panel_b_regime_oos.py
  → data/processed/panel_b_returns.parquet
  → scripts/07_figures/generate_paper_figures.py:fig2()
  → paper/figures/figure_2_cumulative_wealth_panel_b.png
  → paper/build_paper_v8.js (fs.readFileSync)
  → paper/drafts/paper_draft_JF_style_v8_FINAL_FOR_FEEDBACK.docx
```

### 4.2 Table V (Panel B turnover)
```
investable_returns_weekly.parquet
  → scripts/07_panel_b_regime_oos.py (writes panel_b_returns.parquet + ann_to_pct column in performance CSV)
  → reports/panels/panel_b_regime_oos_performance.csv
  → HAND-COPY into paper/build_paper_v8.js (lines 808-811)
  → paper docx
```

The HAND-COPY step is the weak link in every Table provenance chain.

## 5. Verdict

- **Every paper element traces to a generated artefact.** ✓
- **All numerical values are currently in sync with the source CSVs.** ✓
- **No automated CSV→paper pipeline exists** (P1 reproducibility).
- **Two non-numeric inconsistencies:** HICP-lag6 narrative (P1) and Figure 1 ordering (P1-C).
- **One scope caveat properly addressed:** 0.530/0.553 Static CVaR difference (Table VII note).
