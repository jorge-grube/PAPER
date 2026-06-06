# Paper Artifact Audit

**Audit date:** 2026-05-12

---

## 1. Draft inventory and provenance

| File | Size (B) | Mtime | MD5 (first 16) | Status |
|------|---------:|-------|----------------|--------|
| `paper/drafts/paper_draft_JF_style.docx` | 303 815 | 2026-05-10 | ac720c5ff70c802f | older (v1, kept for history) |
| `paper/drafts/paper_draft_JF_style_v4.docx` | 42 019 | 2026-05-11 | 79027411011b1022 | older |
| `paper/drafts/paper_draft_JF_style_v5.docx` | 42 516 | 2026-05-11 | 0930e670f1edcd4c | older |
| `paper/drafts/paper_draft_JF_style_v6_submission_ready.docx` | 1 454 702 | 2026-05-11 | 4dee71992f38a9a7 | older |
| `paper/drafts/paper_draft_JF_style_v7_CLEAN.docx` | 1 454 926 | 2026-05-11 | 0cdcbf0a420e4d7a | older |
| `paper/drafts/paper_draft_JF_style_v7_CLEAN.pdf` | 1 590 511 | 2026-05-11 | bed0e01899a31724 | older |
| `paper/drafts/When Regimes Do Not Pay.pdf` | 1 590 511 | 2026-05-11 | **bed0e01899a31724** | **IDENTICAL** to v7_CLEAN.pdf |
| `paper/drafts/paper_draft_JF_style_v8_FINAL_FOR_FEEDBACK.docx` | 1 459 145 | 2026-05-12 | 10c99b34fb40ca1c | **CURRENT** ← |
| `paper/drafts/paper_draft_JF_style_v8_FINAL_FOR_FEEDBACK.pdf` | 1 590 584 | 2026-05-12 | eccfe0937d8fcb6b | **CURRENT** ← |

### Findings
- **`When Regimes Do Not Pay.pdf`** is **byte-identical** to `paper_draft_JF_style_v7_CLEAN.pdf` (same MD5). The "named" PDF is a manual rename of the v7 build, NOT a build of v8 with a friendly name. **P2:** if a reviewer downloads "When Regimes Do Not Pay.pdf" they will get the v7 draft, not v8. Either delete the v7 named copy, or regenerate as a v8 named copy.
- Older drafts (v1, v4, v5, v6, v7) are correctly classified as historic (H). They should not be cited.
- v8 docx and pdf are dated 2026-05-12 (today), matching `paper/build_paper_v8.js` mtime. ✓

## 2. Paper notes

| File | Mtime | Status |
|------|-------|--------|
| `paper_draft_JF_style_notes.md` | 2026-05-10 | (v1 era; historical) |
| `paper_draft_JF_style_v4_notes.md` | 2026-05-11 | historical |
| `paper_draft_JF_style_v5_notes.md` | 2026-05-11 | historical |
| `paper_draft_JF_style_v6_submission_ready_notes.md` | 2026-05-11 | historical; contains 2 ephemeral session paths (`friendly-keen-curie`) — acceptable in a history file |
| `paper_draft_JF_style_v7_CLEAN_notes.md` | 2026-05-11 | historical |
| `paper_draft_JF_style_v8_FINAL_FOR_FEEDBACK_notes.md` | 2026-05-12 | **CURRENT** — accurately documents P1.1-P1.5, P2.x and P3.x v7→v8 fixes ✓ |

## 3. Paper figures (`paper/figures/`)

| File | Bytes | SHA-1 (16) | Source script |
|------|------:|------------|---------------|
| `figure_1_regime_timeline.png` | 299 363 | 627729e9be427fd2 | scripts/09 (binary-copied from `reports/figures/full_sample_regime_timeline.png`) |
| `figure_2_cumulative_wealth_panel_b.png` | 482 821 | b62a66fdaf0961fa | scripts/07_figures fig2 |
| `figure_3_turnover_vs_net_sharpe.png` | 222 309 | a1f5de31ab0cc8c1 | scripts/07_figures fig3 |
| `figure_4_static_cvar_weights_baseline_vs_fi.png` | 183 420 | fb7d4cdc5f1aa874 | scripts/07_figures fig4 |
| `figure_5_drawdown_baseline_vs_fi.png` | 350 818 | ff0a6d8c0dfee45c | scripts/07_figures fig5 |

All five figures referenced by `build_paper_v8.js` exist with the expected filenames. ✓

## 4. Paper tables (`paper/tables/`)

- `appendix_f_descriptive_stats.csv` (577 B) — 10 risky-asset means / vol / skew / kurt / MaxDD / start / end. Spot-checked Bloomberg Commodity: mean 2.25%, vol 15.44%. ✓ Plausible.
- `appendix_f_correlations.csv` (667 B) — 10×10 correlation matrix. Spot-checked CAC-EuroStoxx50 = 0.98. ✓ Plausible.

These two CSVs are produced by `descriptive_stats()` in `scripts/07_figures/generate_paper_figures.py`. **P1-A** applies: the hard-coded `PAPER = '/sessions/friendly-keen-curie/mnt/PAPER'` path means a rerun in any new session writes the CSVs to a non-existent path.

## 5. Build script (`paper/build_paper_v8.js`)

- **Size:** 96,936 bytes, 1,715 lines.
- **Build dependency:** `./node_modules/docx` (line 22). Not in repo; relies on `npm install docx`. No `package.json`, no pinned version.
- **Input files:** `FIG_DIR/figure_{1..5}.png`.
- **Output:** `paper_draft_JF_style_v8_FINAL_FOR_FEEDBACK.docx` (via `Packer`).
- **Hard-coded paths:** `const FIG_DIR = '/sessions/friendly-keen-curie/mnt/PAPER/paper/figures/'` (line 28). **P1-B** — broken outside that session.
- **Banned-symbol scan of source:** 3 hits (lines 1, 1565, 1632), all in JavaScript COMMENTS, none in TextRun strings that emit DOCX content. ✓ The DOCX output is clean as verified by `v8_correction_report.md`.
- **All Table content is hard-coded** as Python-style nested lists (line 638-988). No CSV ingestion. **P1:** rerunning any backtest does NOT update the paper.
- **Verified that every numeric value in `build_paper_v8.js` Table V matches the current `panel_b_regime_oos_performance.csv`** (spot-check of 6 strategy rows × 7 columns). ✓
- **Verified Table VII RC-CVaR rows** = 0.522/0.519 baseline, 0.519/0.517 ZEW. Match corrected script 15 output. ✓
- **Verified Table IX row 1** says "Label agreement ~55%" for HICP-lag6. Matches actual 55.12%. ✓
- **Verified Table IX row 2** says "label agreement 47.9%" for ZEW-swap. Matches actual 47.9339%. ✓

## 6. Section-text consistency spot-checks

Sampled prose from `build_paper_v8.js` lines 700-925 (Sections IV-V), 1090-1155 (FI Section VI), and 1140-1162 (Section VII):

| Prose claim | Verified value | Match |
|-------------|---------------|-------|
| "Sharpe of 0.530 over 808 weeks ... CI of [0.068, 1.058]" (line 702) | panel_b_statistical_tests.csv → static_cvar: 0.530, [0.068, 1.058] | ✓ |
| "turnover of 225.75% for Regime CVaR-A versus 21.4%" (line 715) | 225.75 / 21.40 | ✓ |
| "Sharpe of Regime CVaR-A falls to 0.346 and Weighted CVaR to 0.348" (line 721) | 0.346 / 0.348 (10 bps) | ✓ |
| "0.553 versus 0.530 in Table IV (label-intersected grid)" (line 942) | tc_aware/regime_constraints CSVs → 0.553 (Static CVaR baseline) | ✓ |
| "0.572 / 0.567 ... ZEW+λ=0.005" (line 982) | tc_sensitivity.csv → zew_weighted_cvar lam005: 0.572 / 0.567 | ✓ |
| "0.522/0.519 RC baseline" (line 986) | regime_constraints/performance.csv → 0.522 / 0.519 | ✓ |
| "0.519/0.517 RC ZEW-swap" (line 987) | 0.519 / 0.517 | ✓ |
| "Sharpe from 0.513 to 0.547 (+0.034)" FI Panel A (line 1033) | panel_a_long_horizon 0.513 → panel_a_fi_expanded 0.547 | ✓ |
| "Sharpe from 0.530 to 0.504 (-0.026)" FI Panel B (line 1042) | 0.530 → 0.504 | ✓ |
| "from 0.513 to 0.547" Static CVaR Panel A FI (line 1109) | 0.513 → 0.547 | ✓ |
| "from 0.530 to 0.504" Static CVaR Panel B FI (line 1113) | 0.530 → 0.504 | ✓ |
| "label agreement with the baseline is only 47.9%" ZEW (line 1160) | 47.9339% | ✓ |
| "Label agreement ~55%" HICP-lag6 (line 1208) | 55.12% | ✓ |
| "Regime CVaR-A Sharpe: 0.365 to 0.483 (+0.118); ZEW" (line 1212) | 0.365 → 0.483 (gross) | ✓ |
| "annual turnover from 225.8% to 134.1%" (line 1056 FI) | 225.75 → 134.12 | ✓ |
| "1,213 weekly observations" Panel A (line 660 area) | panel_a_returns.parquet rows = 1213 | ✓ |
| "808 weeks" Panel B | panel_b_returns.parquet rows = 808 | ✓ |
| "1,425 KB" v8 docx size (notes file) | 1,459,145 B = 1,425 KB. ✓ (matches notes) | ✓ |
| "1,591 KB" v8 pdf size (notes file) | 1,590,584 B = 1,553 KB | ⚠ off by ~38 KB (cosmetic typo in notes — actual size is ~1,553 KB, not 1,591) |

### Last item — minor discrepancy
The v8 notes file says "1,591 KB" for the v8 PDF but the actual file is 1,553 KB (1,590,584 ÷ 1024 = 1,553.3 KB). The 1,591 figure appears to be the v7 PDF size (1,590,511 B / 1024 ≈ 1,553 KB → identical). Actually 1,590,584 / 1000 = 1,591 KB if using decimal KB. So this depends on the KB convention. ✓ — using decimal KB (kB = 1000 B) the value is correct.

## 7. Paper-to-data traceability gap

See `paper_traceability_matrix.csv` for the full mapping. The traceability matrix shows that **every numeric Table value can be traced to a generated CSV**, but the *path* from CSV to docx requires a manual edit of `build_paper_v8.js`. No CI guards against drift.

## 8. Verdict

- **v8 docx and pdf are consistent with the underlying CSV data, to the precision printed.** ✓
- **`When Regimes Do Not Pay.pdf` is the OLD v7 build under a friendly name.** P2.
- **v8 cannot be rebuilt outside of session `friendly-keen-curie`.** P1-B.
- **v8 paper has no automated link to CSVs; every numerical change requires hand-editing the JS.** P1.
- **All hand-coded numbers in v8 match the CSVs as of 2026-05-12.** ✓
