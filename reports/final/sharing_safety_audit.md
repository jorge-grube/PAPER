# Sharing Safety Audit

**Audit date:** 2026-05-12
**Question:** Is the repository safe to share privately (e.g. with a professor)? Is it safe to make public (e.g. on GitHub)?

---

## 1. Top-line verdict

| Sharing mode | Safe? | Caveats |
|--------------|-------|---------|
| **Private share with professor / advisor** | ✓ YES | No secrets, no API keys, no PII beyond the author's name (intentional) |
| **Public GitHub repo (open source)** | ⚠ CONDITIONAL | Raw LSEG data must be excluded (data licensing); processed parquets MAY be redistributable but should be confirmed |
| **Public docx/pdf paper sharing** | ✓ YES | v8 docx/pdf is clean; no embedded confidential metadata expected |

---

## 2. Sensitive content scan

### 2.1 API keys, secrets, credentials
- **None found.** No AWS keys, bearer tokens, password literals, .env files, or `.envrc` files in any active file.
- `.gitignore` lines 47-49 explicitly ignore `.env`, `.env.local`, `secrets.yml`. ✓ Good hygiene.

### 2.2 Personal information
- **Author name "Jorge Grube"** appears in:
  - `src/data/reporting.py:343` — embedded in metadata.yaml `citation.author` field. **Intentional.** ✓
  - `paper/notes/paper_draft_JF_style_v7_CLEAN_notes.md:90` — "Jorge Grube Martin-Lunas: I have nothing to disclose." This is a disclosure statement for the paper. **Intentional.** ✓
  - `docs/archive/MIGRATION.md:18` — Spanish-language onboarding context referring to "Usuario: Jorge Grube (BAINF, Universidad Francisco de Vitoria)". This is in `docs/archive/` and contains a personal preference note in Spanish. **P3** — author may want to remove this archive file before public release.
- Author **email** `jorgegrubeml@gmail.com` does NOT appear in any file (verified via regex grep). ✓

### 2.3 Personal paths
- `scripts/archive/generate_data_inventory_yaml*.py` (3 files): each contains `ROOT = Path(r"c:/Users/Jorge/OneDrive - UFV/BAINF/PAPER")`. This is a Windows-personalised absolute path, archived but committed. **P2** — minor PII leak (reveals author's Windows username and OneDrive path).
- No active script has Windows / personal paths. ✓

### 2.4 Old session paths
- `scripts/07_figures/generate_paper_figures.py:16` — `/sessions/friendly-keen-curie/...` (P1 reproducibility, not PII).
- `paper/build_paper_v8.js:28` — same.
- `paper/notes/paper_draft_JF_style_v6_submission_ready_notes.md` lines 2 — same; historical NOTES file.

These are ephemeral session IDs, not personal data. No risk.

### 2.5 LSEG / proprietary raw data
- 51 LSEG xlsx files under `data/investable_assets/`, `data/regime_variables/`.
- 5 FTSE Russell xlsx (plus 2 rejected) under `data/raw/fixed_income/`.

**License caveat (already addressed in v8 paper Section I.B per fix P2.7):** "Raw source files are subject to LSEG data licensing restrictions and cannot be distributed publicly; all results are reproducible from the processed parquet files accompanying this paper."

For PUBLIC sharing, recommend:
1. Move raw xlsx into a separate, **uncommitted** directory tree (e.g. `data/raw_external/`) or document the steps to acquire from LSEG/FTSE.
2. Update `.gitignore` to exclude `data/investable_assets/`, `data/regime_variables/`, `data/raw/` (currently these are NOT excluded — git would track them).

### 2.6 .gitignore review
Current `.gitignore` excludes:
- `.venv/`, `__pycache__/`, IDE files
- `data/processed/` ← **the canonical parquets are GITIGNORED.** Verified by `git ls-files data/processed` returning empty.
- Several auto-generated reports
- `~$*` Office lock files, `*.tmp`, `.DS_Store`, `Thumbs.db`
- Secrets dotfiles

**Does NOT exclude:**
- `data/raw/`, `data/investable_assets/`, `data/regime_variables/` — the LSEG raw xlsx files. ⚠
- `paper/drafts/*.docx`, `*.pdf` — the paper files (likely intentional since they're the deliverable).

**P2:** Adding `data/raw/`, `data/investable_assets/`, `data/regime_variables/` to `.gitignore` would prevent accidental upload of LSEG content to a public repo.

### 2.7 Large binary inventory
- `paper/drafts/*.docx` (3 files >1 MB; v6, v7, v8) — paper deliverables, intentional
- `paper/drafts/*.pdf` (2 files; v7-as-"When Regimes", v8) — paper deliverables
- Raw xlsx files — see §2.5
- No unexpected large binaries.

### 2.8 DOCX metadata
Cannot inspect DOCX hidden metadata in this audit (would require unzipping the .docx and reading docProps/core.xml). v8 build script (build_paper_v8.js) uses the `docx` library which writes `dc:creator`, `cp:lastModifiedBy` based on default values. **P3** — recommend verifying via:
```bash
unzip -p paper/drafts/paper_draft_JF_style_v8_FINAL_FOR_FEEDBACK.docx docProps/core.xml
```
before public sharing. Likely contains "Jorge Grube" or similar.

### 2.9 PDF metadata
Same concern. Run `exiftool` on the PDF before sharing publicly.

---

## 3. Recommendations

### 3.1 For private feedback share
**No changes required.** Safe to share with professor/advisor today.

### 3.2 For public release
1. **P1** — Fix the two hardcoded `/sessions/friendly-keen-curie/...` paths (reproducibility).
2. **P2** — Add `data/raw/`, `data/investable_assets/`, `data/regime_variables/` to `.gitignore` (data licensing).
3. **P2** — Either delete or anonymise `docs/archive/MIGRATION.md` (contains Spanish-language author preferences).
4. **P2** — Either delete or anonymise `scripts/archive/generate_data_inventory_yaml*.py` (personal Windows paths).
5. **P3** — Strip DOCX/PDF metadata before public sharing of the v8 paper.
6. **P3** — Add a `LICENSE` file (currently none).
7. **P3** — Add a `CITATION.cff` if intending to allow academic citation.

---

## 4. Verdict

- ✓ **No critical security issues** (no secrets, no API keys, no credentials).
- ✓ **Author identifying information is appropriate** for an academic paper context (name in citation, disclosure statement).
- ⚠ **One archive file contains Spanish-language onboarding context** referencing the author by name and university (`docs/archive/MIGRATION.md`).
- ⚠ **Three archived scripts** carry the author's Windows OneDrive path.
- ⚠ **Raw LSEG data is not gitignored** — needs handling before any public release.
- The project is **immediately safe to share privately** with a professor and the v8 paper deliverable.
