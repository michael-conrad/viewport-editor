# AGENTS.md — Viewport-Editor Repository

## Agent Guidelines

This file provides project-level agent instructions. For testing framework specifics, see:

- `test/tool_selection/AGENTS.md` — Tool selection test framework, timeout mandates, model lists

## Timeout Mandate (MANDATORY — Tier 1)

**Always increase bash tool timeouts as needed, especially for local models.**

The default 120s timeout is NEVER sufficient for model runs — it is a harness configuration error. Failing to extend timeouts for local model inference is a process-integrity failure. A timeout is NOT a model failure — it is a harness configuration error.

Timeouts must be extended per-model. These are MINIMUMS — increase further if the model is cold-loading:

| Model | Min Timeout | Reason |
|-------|-------------|--------|
| `ollama/deepseek-v4-flash:cloud` | 120s | Cloud inference, fast |
| `ollama/devstral-small-2:24b-384k` | 300s | 24B local model |
| `ollama/gemma4:31b-256k` | **3600s** | 19GB model — very slow load |
| `ollama/gpt-oss:20b-128k` | 1800s | 20B local model |
| `ollama/nemotron3:33b-128k` | 1800s | 33B local model |
| `ollama/qwen3.6:35b-256k` | 1800s | 35B local model |

If a model timeout occurs, double the timeout and retry. Do not skip the model.

**Provider config also requires `chunkTimeout`** set to at least 300000ms for slow local models. OpenCode's streaming timeout kills connections if no chunk arrives within `chunkTimeout`.

## Model Set (6 models)

| Priority | Model | Type | Notes |
|----------|-------|------|-------|
| 1 | `ollama/deepseek-v4-flash:cloud` | Cloud | Primary development model |
| 2 | `ollama/devstral-small-2:24b-384k` | Local | Lightweight — lower capability |
| 3 | `ollama/gemma4:31b-256k` | Local | Mid-range, extended context |
| 4 | `ollama/gpt-oss:20b-128k` | Local | Weaker — edge of comprehension |
| 5 | `ollama/nemotron3:33b-128k` | Local | Mid-range, extended context |
| 6 | `ollama/qwen3.6:35b-256k` | Local | Long-context variant |

## LaTeX Papers

Papers live in `papers/<slug>/`. Each paper has:

- `src/paper.tex` — main document (may include additional `.tex` files)
- `src/references.bib` — bibliography
- `figures/` — figures
- `build/` — build artifacts (fully gitignored)
- `paper.pdf` — final PDF at paper root (tracked)
- `build.py` — PEP 723 build script

**Build:** `./papers/<slug>/build.py` (requires `xelatex`, `biber`/`bibtex`, `makeindex`)
**Slugify:** `./papers/slugify "Paper Title"`

**Slug convention:** lowercase, spaces→hyphens, strip non-alphanumeric except hyphens, collapse consecutive hyphens, strip leading/trailing, no transliteration. Duplicate slugs append `-1`, `-2`.

## Release Checklist (MANDATORY)

When creating a tagged release (dev → main PR), the agent MUST perform ALL of the following. Skipping any step is a process-integrity failure.

| Step | Action | Verification |
|------|--------|-------------|
| 1 | Determine next version tag from existing tags | `git tag --sort=-version:refname` |
| 2 | Scan the entire project for occurrences of the current version string. Review each match. Update any that are project version declarations (as opposed to dependency pins, changelog history entries, or unrelated semvers). | Manual review of each occurrence; confirm all project version references are updated |
| 3 | Bump `version` in `pyproject.toml` to match the release tag | `grep 'version =' pyproject.toml` |
| 4 | Bump `__version__` in `src/viewport_editor/__init__.py` to match | `grep __version__ src/viewport_editor/__init__.py` |
| 5 | Verify both version sources are consistent | Extract both values, compare for equality |
| 6 | Commit the version bumps on `dev` before creating the release branch | `git diff --stat` confirms only version files changed |
| 7 | Create release branch and PR targeting `main` | PR body documents changes since last release |
| 8 | After PR merge, create a GitHub Release with release notes | `gh release create <tag> --notes "..."` |
| 9 | Clean up merged release branch | `git branch -D`, `git push origin --delete` |

**Known version sources (double-check anchors):**
- `pyproject.toml` — `version = "<semver>"`
- `src/viewport_editor/__init__.py` — `__version__ = "<semver>"`

These are NOT exhaustive — the discovery step (Step 2) finds all occurrences. These serve as post-bump double-check anchors.