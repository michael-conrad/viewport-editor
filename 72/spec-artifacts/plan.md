# Plan: LaTeX paper storage infrastructure

**Spec:** #72
**Scope:** `for_pr`
**Phases:** 2

## Phase 1: Infrastructure setup

### Task 1.1 — Create `papers/` directory

- `mkdir -p papers/`

### Task 1.2 — Add `.gitignore` entry

- Append `# LaTeX build artifacts` and `papers/*/build/*` to `.gitignore`

### Task 1.3 — Create `papers/slugify`

- PEP 723 script with bash polyglot guard
- Takes title string as argument, outputs slug to stdout
- Slug rules: lowercase, spaces→hyphens, strip non-alnum except hyphens, collapse consecutive, strip leading/trailing, no transliteration

### Task 1.4 — Add LaTeX Papers section to AGENTS.md

- New section after Model Set table
- Document layout, build command, slugify command, slug convention

## Phase 2: Reference paper + build script

### Task 2.1 — Create reference paper directory

- `papers/a-note-on-distribution-shifting/`
- `src/paper.tex` — minimal LaTeX document
- `src/references.bib` — empty bibliography
- `figures/` — empty directory
- `build/` — empty directory

### Task 2.2 — Create `build.py`

- PEP 723 with bash polyglot guard
- Toolchain: `xelatex` + `biber`/`bibtex` + `makeindex`
- Build sequence: xelatex → biber/bibtex → makeindex (if idx exists) → xelatex ×2 → cp to paper root
- Detect `biber` vs `bibtex` at runtime
- Guard: verify tools on `$PATH`

### Task 2.3 — Build and verify

- Run `./papers/a-note-on-distribution-shifting/build.py`
- Verify `paper.pdf` exists at paper root
