# Phase 03b — trunk-migration-docs

## Phase Metadata

- **Concern:** Update AGENTS.md and project configs for trunk-based development
- **Files:** `AGENTS.md`, `pyproject.toml`, `.opencode/` files, CI configs, scripts
- **SCs:** SC-20, SC-21
- **Dependencies:** Phase 3a (dev merged and deleted)
- **Entry:** `dev` branch deleted, `main` is the trunk
- **Exit:** All stale `dev` references removed, trunk-based workflow documented
- **Cost frame:** Cost is measured in defect-discovery-latency, not model roundtrips. Running verification costs minutes of execution time — a bounded delay that surfaces defects before they reach CI. Skipping a verification step to save a tool call costs the full pipeline of rework when the defect surfaces downstream: diagnosis, fix, re-review, re-CI, re-deploy — each of which costs more roundtrips than the skipped verification would have consumed. Correctness is the only success metric — there is no score for tool-call economy.

## Code Path Coverage

- `AGENTS.md`: Replace `dev` branch references with `main`; update Release Checklist to target `main` directly; remove `dev → main PR` workflow
- `pyproject.toml`: Check for stale `dev` branch references
- `.opencode/` files: Update `DEFAULT_BRANCH` references to point to `main`
- CI configs, scripts: Replace stale `dev` references with `main`

## Cross-Cutting SCs

None.

## Interface Boundaries

None — documentation and config changes only.

## State Transitions

- From: Project references `dev` as development branch
- To: Project uses `main` as sole trunk, trunk-based workflow documented

### Item 1: Update AGENTS.md (SC-20)

- [ ] 38. **Pre-RED baseline (**inline**).** Grep for `dev` branch references in `AGENTS.md`: `grep -n "dev" AGENTS.md`.
- [ ] 39. **GREEN (**sub-agent**).** Update `AGENTS.md`: replace all `dev` branch references with `main` as the trunk; update Release Checklist to target `main` directly; remove `dev → main PR` workflow. **SC gate: this step FAILS if any active dev branch reference remains.**
- [ ] 39a. **GREEN doublecheck (**inline**).** Run `grep -n "dev" AGENTS.md` — only historical release tag references should remain.
- [ ] 39b. **REFACTOR (**inline**).** Verify consistency: check that `DEFAULT_BRANCH` references point to `main`.
- [ ] 39c. **Checkpoint commit (**inline**).** `git add AGENTS.md && git commit -m "docs: migrate AGENTS.md to trunk-based development"`

### Item 2: Update project configs (SC-21)

- [ ] 40. **Pre-RED baseline (**inline**).** Grep for stale `dev` branch references across project: `grep -rn "branch.*dev\|base.*dev\|target.*dev" --include="*.{md,toml,yml,yaml,sh,py,json}" --exclude-dir=.git --exclude-dir=.venv --exclude-dir=__pycache__ .`
- [ ] 41. **GREEN (**sub-agent**).** Update all stale `dev` branch references in project configs: `pyproject.toml`, CI configs, scripts, `.opencode/` files. Replace with `main`. **SC gate: this step FAILS if any stale dev reference remains.**
- [ ] 41a. **GREEN doublecheck (**inline**).** Re-run grep from step 40 — confirm zero matches for active dev branch references.
- [ ] 41b. **REFACTOR (**inline**).** Verify no broken references: check that updated files are internally consistent.
- [ ] 41c. **Checkpoint commit (**inline**).** `git add -A && git commit -m "chore: migrate project configs to trunk-based development"`

#### Phase 03b VbC

- [ ] 41d. **VbC (**clean-room**).** Verify: AGENTS.md updated, all stale dev references removed, trunk-based workflow documented. **→ SC-20, SC-21** `evidence_type: string`

**Concern transition:** Leaving trunk migration → entering global post-phase. Phase 4 depends on Phase 3b's docs being complete.
