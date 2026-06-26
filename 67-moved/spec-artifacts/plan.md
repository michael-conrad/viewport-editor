# Implementation Plan: Update README with v0.3.0, tool table, and AGENTS.md directives

## Goal

Update `README.md` to reflect the current v0.3.0 release, expand the 6-tool surface to the actual 11-tool surface, and add a "Consuming Repo Instructions" section with a copy-paste AGENTS.md template.

## Architecture

Single file (`README.md`) — three sequential phases, each building on the prior. No code changes. No new files.

**Concern boundary:** Phase 1 fixes stale version tag. Phase 2 fixes stale tool inventory. Phase 3 adds new content. Each phase is independently verifiable.

## Tech Stack

- Markdown (README.md)
- uvx (markdown-lint via `pymarkdownlnt`, markdown format via `mdformat`)
- Z3 constraint solver (`.opencode/tools/solve`) for phase state verification

## Phase Structure

| Phase | ID | Concern | Dependencies |
|-------|----|---------|-------------|
| 1 | P_TAG | Update uvx tag from v0.2.0 → v0.3.0 | None |
| 2 | P_TOOLTABLE | Expand 6-tool table → 11-tool table, fix stale action names | None (independent of P1) |
| 3 | P_AGENTSDIR | Add "Consuming Repo Instructions" section with AGENTS.md template | None (independent of P1, P2) |

**Note:** All 3 phases are independent (modify non-overlapping sections of README.md). However, they are executed serially with Z3 state checking between each to verify file integrity. Serial execution ensures that any mid-pipeline failure (lint break, structural damage) is caught at the earliest phase boundary.

---

## Phase 1: Update uvx tag to v0.3.0

**Concern:** Stale version reference in Quick Start section.

**Z3 Contract:** `.issues/67/spec-artifacts/z3-contracts/phase-1.yaml`

```yaml
phase_dependencies: []
variables:
  P1_g1: "uvx block 1 updated"       # OpenCode JSONC block
  P1_g2: "uvx block 2 updated"       # Generic MCP clients JSON block
  P1_g3: "no stale v0.2.0 remains"   # Both occurrences gone
constraints:
  - "P1_g3 => (P1_g1 and P1_g2)"     # All-clear requires both blocks updated
```

### Task 1.1: RED — Write test for desired state, confirm it fails

Write a check that asserts the *desired* state — both uvx blocks reference `@v0.3.0`:

```bash
test "$(grep -c '@v0.3.0' README.md)" -eq 2 && echo "PASS" || echo "FAIL"
```

Run against current README — MUST return **FAIL** because both blocks still reference `@v0.2.0`.

**RED condition:** Assertion `@v0.3.0` count == 2 **FAILS** against current README (returns 0 matches).

### Task 1.2: GREEN — Replace both occurrences

- Replace `@v0.2.0` with `@v0.3.0` in both code blocks
- Use targeted edits (one per code block)

**GREEN condition:** `grep -c '@v0.3.0' README.md` returns 2 and `grep -c '@v0.2.0' README.md` returns 0.

### Task 1.3: Verify — structural + behavioral

- Structural: confirm 2 occurrences of `v0.3.0` in tag contexts
- Behavioral: run `uvx pymarkdownlnt scan README.md` — must pass
- Version consistency: confirm `v0.3.0` matches `pyproject.toml`

### Gate Table: Phase 1

| Gate | Name | Exit Criterion |
|------|------|----------------|
| 1 | sc-coherence-gate | P1 only touches README.md, only modifies version strings in code blocks |
| 2 | pre-red-baseline | File read confirms 2 `@v0.2.0` occurrences |
| 3 | red-phase | RED evidence artifact written to `tmp/67/phase-1-red.txt` |
| 4 | red-doublecheck | Re-read confirms stale state still present (no race) |
| 5 | green-phase | Both replacements applied, 0 stale, 2 current |
| 6 | checkpoint-commit | `git add -A && git commit -m "Phase 1: update uvx tag to v0.3.0"` |
| 7 | structural-checks | `grep -c '@v0.3.0' README.md` == 2, `grep -c '@v0.2.0' README.md` == 0 |
| 8 | green-doublecheck | Confirm pyproject.toml version matches tag |
| 9 | green-vbc | `uvx pymarkdownlnt scan README.md` passes |
| 10 | adversarial-audit | Auditor confirms no unintended edits outside tag blocks |
| 11 | cross-validate | Second auditor confirms same |
| 12 | regression-check | Full README rendering verified (no broken markup) |
| 13 | review-prep | Phase diff reviewed |
| 14 | exec-summary | Phase report with checkpoint tag |

### Z3 State Update (after Phase 1)

```bash
.opencode/tools/solve state update \
  --state-path .issues/67/spec-artifacts/pipeline.state \
  --var-name P1_complete \
  --var-value True
```

### Checkpoint Tag

```bash
git tag -a viewport-editor/67/checkpoint/phase-1-TAG -m "Phase 1: uvx tag v0.3.0"
git tag -l 'viewport-editor/67/checkpoint/phase-1-*'
```

---

## Phase 2: Expand tool table and fix action names

**Concern:** README's tool surface table is stale (6 tools → actual 11, wrong action names).

**Z3 Contract:** `.issues/67/spec-artifacts/z3-contracts/phase-2.yaml`

```yaml
phase_dependencies:
  - phase: P2_TOOLTABLE
    depends_on: []
    constraints:
      - "P2_g1: viewport row has set-display-mode (not switch-mode)"
      - "P2_g2: file row includes delete action"
      - "P2_g3: clipboard row present with 8 actions"
      - "P2_g4: read_file row present"
      - "P2_g5: write_file row present"
      - "P2_g6: edit_text row present"
      - "P2_g7: find_text row present"
      - "P2_g8: section header renamed to 11-Tool Surface"
variables: [P2_g1, P2_g2, P2_g3, P2_g4, P2_g5, P2_g6, P2_g7, P2_g8]
```

### Task 2.1: RED — Write tests for desired table, confirm they fail

Write assertions that check the *desired* table state — 11 tool rows with current names:

```bash
# Assert 11 tool rows exist
grep -c '^\*\*' README.md | grep -q '11' && echo "PASS" || echo "FAIL"
# Assert set-display-mode present (not switch-mode)
grep -q 'set-display-mode' README.md && echo "PASS" || echo "FAIL"
# Assert clipboard row present
grep -q '^\*\*clipboard\*\*' README.md && echo "PASS" || echo "FAIL"
# Assert read_file row present
grep -q '^\*\*read_file\*\*' README.md && echo "PASS" || echo "FAIL"
# Assert delete action in file row
grep -A1 '^\*\*file\*\*' README.md | grep -q 'delete' && echo "PASS" || echo "FAIL"
```

Run against current README — ALL assertions MUST **FAIL** (table is 6 rows, wrong names, missing tools).

**RED condition:** All 6 assertions **FAIL** against current README (6-tool table with stale names).

### Task 2.2: GREEN — Replace tool table

Replace the "6-Tool Surface" section header and table with:

**New header:** `## 11-Tool Surface`

**New table:**

```markdown
| tool | actions |
|------|---------|
| **viewport** | open, close, list, scroll, page-up, page-down, jump, autosave, set-display-mode |
| **edit** | replace, replace-all, insert-lines, delete-lines, swap-lines, move-lines |
| **file** | save, discard, new, save-as, delete |
| **diff** | show, apply |
| **clipboard** | copy, cut, paste, show, stash, pop, swap, stash-list |
| **search** | find |
| **regex** | test, escape |
| **read_file** | composite: open + scroll — single-call file read with viewport lifecycle |
| **write_file** | composite: open + replace-all + save + close — single-call file write with conflict detection |
| **edit_text** | composite: open + replace + save + close — single-call targeted edit with conflict detection |
| **find_text** | composite: search wrapper — single-call text search |
```

**GREEN condition:** 11 tool rows present. Each tool name and action list matches the current server.

### Task 2.3: Verify — string + behavioral

- Structural: grep each tool name in the table section
- Structural: grep for `set-display-mode` (no `switch-mode`)
- Behavioral: `uvx pymarkdownlnt scan README.md` passes

### Gate Table: Phase 2

| Gate | Name | Exit Criterion |
|------|------|----------------|
| 1 | sc-coherence-gate | P2 only modifies tool table section of README.md |
| 2 | pre-red-baseline | Confirm 6 rows, stale action names |
| 3 | red-phase | RED evidence artifact written |
| 4 | red-doublecheck | Re-read confirms stale state |
| 5 | green-phase | 11 rows, all names correct |
| 6 | checkpoint-commit | `git add -A && git commit -m "Phase 2: expand tool table to 11 tools"` |
| 7 | structural-checks | grep per tool name returns exactly 1 row match each |
| 8 | green-doublecheck | `set-display-mode` present, `switch-mode` absent |
| 9 | green-vbc | `uvx pymarkdownlnt scan README.md` passes |
| 10 | adversarial-audit | Auditor confirms all 11 tools match server.py `@mcp.tool()` list |
| 11 | cross-validate | Second auditor confirms |
| 12 | regression-check | Phase 1 edits intact (tag still v0.3.0) |
| 13 | review-prep | Phase diff reviewed |
| 14 | exec-summary | Phase report with checkpoint tag |

### Z3 State Update (after Phase 2)

```bash
.opencode/tools/solve state update \
  --state-path .issues/67/spec-artifacts/pipeline.state \
  --var-name P2_complete \
  --var-value True
```

### Z3 Inter-Phase Check (Phase 1 integrity)

Before proceeding to Phase 3:

```bash
.opencode/tools/solve check \
  --state-path .issues/67/spec-artifacts/pipeline.state \
  --contract-path .issues/67/spec-artifacts/z3-contracts/inter-phase.yaml
```

Where `inter-phase.yaml` asserts:

```yaml
# Inter-phase invariants
variables: [P1_complete, P2_complete]
constraints:
  - "P2_complete => P1_complete"   # Phase 2 must not complete before Phase 1
```

### Checkpoint Tag

```bash
git tag -a viewport-editor/67/checkpoint/phase-2-TOOLTABLE -m "Phase 2: 11-tool table"
git tag -l 'viewport-editor/67/checkpoint/phase-2-*'
```

---

## Phase 3: Add "Consuming Repo Instructions" Section

**Concern:** Missing AGENTS.md plugin directives for consuming repos.

**Z3 Contract:** `.issues/67/spec-artifacts/z3-contracts/phase-3.yaml`

```yaml
phase_dependencies:
  - phase: P3_AGENTSDIR
    depends_on: [P1_complete, P2_complete]
    constraints:
      - "P3_complete => (P1_complete and P2_complete)"
variables:
  P3_g1: "section header present"
  P3_g2: "MCP server JSON block with v0.3.0 present"
  P3_g3: "Path resolution convention documented"
  P3_g4: "Buffer lifecycle documented"
  P3_g5: "Conflict detection noted"
  P3_g6: "11-tool surface referenced"
  P3_g7: "markdown-lint passes"
```

### Task 3.1: RED — Write test for desired section, confirm it fails

Write an assertion that checks the *desired* state — "Consuming Repo Instructions" section header exists:

```bash
grep -q '^## Consuming Repo Instructions' README.md && echo "PASS" || echo "FAIL"
```

Run against current README — MUST return **FAIL** because section does not exist yet.

**RED condition:** Assertion `## Consuming Repo Instructions` header exists **FAILS** against current README.

### Task 3.2: GREEN — Append section to README.md

Insert before the Roadmap section (or after Quick Start section, preserving existing content). The new section contains:

```markdown
## Consuming Repo Instructions

When adding viewport-editor as an MCP plugin, configure it in your `opencode.jsonc`:

```jsonc
{
  "mcp": {
    "viewport-editor": {
      "type": "local",
      "command": ["uvx", "--from", "git+https://github.com/michael-conrad/viewport-editor@v0.3.0", "viewport-editor"],
      "enabled": true
    }
  }
}
```

Then add the following stanza to your repository's `AGENTS.md`:

```markdown
### viewport-editor MCP Plugin

This repo uses [viewport-editor](https://github.com/michael-conrad/viewport-editor) as its editing MCP server.

**11-tool surface** (see README for full action lists):

| Tool | Purpose |
|------|---------|
| **viewport** | Open, navigate, and manage focused editing windows |
| **edit** | Stage text changes into viewport buffers (replace, insert, delete, swap, move) |
| **file** | Commit or discard staged changes to disk |
| **diff** | Show unified diffs of pending edits before saving |
| **clipboard** | Copy/cut/paste content across viewports with provenance tracking |
| **search** | Find text with substring or regex matching |
| **regex** | Test and escape regex patterns |
| **read_file** | Composite: open + scroll — preferred over built-in `read` for single-call reading |
| **write_file** | Composite: open + replace-all + save — preferred over built-in `write` for conflict-safe writing |
| **edit_text** | Composite: open + replace + save — preferred over built-in `edit` for targeted changes with conflict detection |
| **find_text** | Composite: search — preferred over built-in `grep` for structured results |

**recommended agent behavior:**

- Use `read_file`, `write_file`, `edit_text`, `find_text` for single-call operations (empirically validated — see viewport-editor#63 V1 results)
- Use `viewport` + `edit` + `file` for multi-step editing with diff review
- Always call `diff:show` before `file:save` to verify staged changes
- File paths are relative to project root (MCP resolver defaults to `os.getcwd()`)
- The `VIEWPORT_PROJECT_ROOT` environment variable overrides the project root if needed
- Session management is automatic (MCP framework handles session IDs)
- Conflict detection: server tracks file mtime+size externally; stale-file soft warning on reads, hard block on `file:save` (use `force: true` override if change is intentional)
```

**GREEN condition:** Section exists with header, JSON block, and AGENTS.md template.

### Task 3.3: Verify — all SCs

- Structural: grep for section header
- Structural: grep for each template component (JSON block, path resolution, buffer lifecycle, conflict detection, 11-tool reference)
- Behavioral: markdown-lint passes
- Regression: Phase 1 and Phase 2 edits intact

### Gate Table: Phase 3

| Gate | Name | Exit Criterion |
|------|------|----------------|
| 1 | sc-coherence-gate | P3 only appends new section — does not modify existing content |
| 2 | pre-red-baseline | Confirm section absent |
| 3 | red-phase | RED evidence artifact written |
| 4 | red-doublecheck | Re-read confirms section absent |
| 5 | green-phase | Section present with all 5 elements (header, JSON, path, buffer, conflict, tool ref) |
| 6 | checkpoint-commit | `git add -A && git commit -m "Phase 3: add consuming repo instructions"` |
| 7 | structural-checks | grep per element returns match |
| 8 | green-doublecheck | Full read of new section confirms complete template |
| 9 | green-vbc | `uvx pymarkdownlnt scan README.md` passes |
| 10 | adversarial-audit | Auditor checks template completeness against spec SCs |
| 11 | cross-validate | Second auditor confirms |
| 12 | regression-check | Phases 1 and 2 edits intact (tags, tool table) |
| 13 | review-prep | Phase diff reviewed, full README reviewed |
| 14 | exec-summary | Final report with all checkpoint tags |

### Z3 State Update (after Phase 3)

```bash
.opencode/tools/solve state update \
  --state-path .issues/67/spec-artifacts/pipeline.state \
  --var-name P3_complete \
  --var-value True
```

### Z3 Final State Check (all phases complete)

```bash
.opencode/tools/solve check \
  --state-path .issues/67/spec-artifacts/pipeline.state \
  --contract-path .issues/67/spec-artifacts/z3-contracts/final.yaml
```

Where `final.yaml`:

```yaml
variables: [P1_complete, P2_complete, P3_complete]
constraints:
  - "P3_complete => (P1_complete and P2_complete)"
  - "P2_complete => P1_complete"
  - "(and P1_complete P2_complete P3_complete)"  # All must be true for final PASS
```

### Checkpoint Tag

```bash
git tag -a viewport-editor/67/checkpoint/phase-3-AGENTSDIR -m "Phase 3: consuming repo instructions"
git tag -l 'viewport-editor/67/checkpoint/phase-3-*'
```

---

## SC-ID Traceability

| SC ID | Phase | Evidence Type | Verification Method |
|-------|-------|---------------|---------------------|
| SC-1 | P1 | `string` | grep both blocks for `@v0.3.0` |
| SC-2 | P2 | `string` | grep each of 11 tool names in table section |
| SC-3 | P2 | `string` | grep `set-display-mode`, confirm `switch-mode` absent |
| SC-4 | P3 | `structural` | grep section header |
| SC-5 | P3 | `string` | grep for 11-tool surface reference in template |
| SC-6 | P3 | `string` | grep for relative path convention |
| SC-7 | P3 | `string` | grep for save/review workflow |
| SC-8 | P3 | `string` | grep for JSON config block with `@v0.3.0` |
| SC-9 | P3 | `string` | grep for conflict/mtime/size mention |
| SC-10 | P1 | `string` | grep `v0.3.0` in README matches `pyproject.toml` version |
| SC-11 | All | `behavioral` | `uvx pymarkdownlnt scan README.md` passes for each phase |

---

## Implementation Checklist

### Pre-Cleanup

- [ ] Remove any stale `.issues/67/spec-artifacts/` artifacts from prior runs
- [ ] Verify git state clean (`git status`)
- [ ] Create feature branch: `git checkout -b feature/67-readme-update`
- [ ] Create `.issues/67/spec-artifacts/z3-contracts/` directory
- [ ] Initialize pipeline state: `.opencode/tools/solve state init --state-path .issues/67/spec-artifacts/pipeline.state`

### Per-Phase Dispatch

Each phase dispatched via `task(subagent_type="general")` with:

```
authorization_scope: for_implementation
halt_at: verification_complete
pr_strategy: stacked
pipeline_phase: README_UPDATE_PHASE_<N>
```

### Post-Step Z3 State Update (every phase)

After each phase commit:

1. `.opencode/tools/solve state update --state-path .issues/67/spec-artifacts/pipeline.state --var-name P<N>_complete --var-value True`
2. `.opencode/tools/solve check --state-path .issues/67/spec-artifacts/pipeline.state --contract-path .issues/67/spec-artifacts/z3-contracts/inter-phase.yaml`
3. `.opencode/tools/solve status --state-path .issues/67/spec-artifacts/pipeline.state`

### Checkpoint Tag Creation (every phase)

1. `git tag -a viewport-editor/67/checkpoint/phase-<N>-<LABEL> -m "Phase <N>: <description>"`
2. `git tag -l 'viewport-editor/67/checkpoint/phase-<N>-*'` — verify tag exists

### Lifecycle Manifest

```yaml
# .issues/67/spec-artifacts/lifecycle.yaml
events:
  - phase: 1
    action: checkpoint_commit
    tag: viewport-editor/67/checkpoint/phase-1-TAG
    z3_state: <SAT|UNSAT>
  - phase: 2
    action: checkpoint_commit
    tag: viewport-editor/67/checkpoint/phase-2-TOOLTABLE
    z3_state: <SAT|UNSAT>
  - phase: 3
    action: checkpoint_commit
    tag: viewport-editor/67/checkpoint/phase-3-AGENTSDIR
    z3_state: <SAT|UNSAT>
  - phase: final
    action: all_gates_pass
    z3_state: SAT
```

---

## Remediation Protocol

| Rule | Condition | Action |
|------|-----------|--------|
| R.1 | Phase gate FAIL (non-Z3) | Fix root cause, re-run from gate |
| R.2 | Z3 state check UNSAT | Rollback to last checkpoint tag via `git reset --hard <checkpoint-tag>` |
| R.3 | Repeated UNSAT (2+ attempts) | Dispatch researcher sub-agent for diagnosis |
| R.4 | File integrity error (markdown-lint fail) | Fix lint error, re-run gate |
| R.5 | Phase diff damages prior phase content | Rollback to prior checkpoint, re-dispatch |
| R.6 | Max 3 remediation attempts per phase | After 3 failures: HALT, report blocker |
| R.7 | If sub-agent returns BLOCKED | Discard all output, re-task with original scope |
| R.8 | If checkpoint tag missing | `git log --oneline -5` to find last commit, create tag retroactively |
| R.9 | If pipeline.state corrupted | Re-init from last checkpoint: re-run gates P1..PN-1 |
| R.10 | If adversarial auditor returns FAIL | Remediate finding per audit report, re-run from gate 10 |

---

## Phase Completion Protocol

| Step | Action |
|------|--------|
| PC.1 | All 14 gates PASS for phase |
| PC.2 | All SCs assigned to phase verified PASS |
| PC.3 | Z3 state updated and checked SAT |
| PC.4 | Checkpoint tag created and verified |
| PC.5 | Lifecycle manifest event appended |
| PC.6 | Proceed to next phase (or final completion) |

## Overall Completion Protocol

| Step | Action |
|------|--------|
| OC.1 | All 3 phases complete |
| OC.2 | Final Z3 state check SAT (all 3 variables true, inter-phase invariants hold) |
| OC.3 | Full README regression check: markdown-lint, all 3 phase edits intact |
| OC.4 | PR body written per git-workflow PR body requirements |
| OC.5 | Branch pushed to origin |
| OC.6 | PR created via `github_create_pull_request` |
| OC.7 | PR URL extracted from API response `html_url` field |

---

## Key Constraints

- `implementation-pipeline-006` — orchestrator routes via `task()`, no inline work
- `implementation-pipeline-007` — PR merge boundaries respected
- `critical-rules-040` — single-issue PR must be squashed to 1 commit after all phases
- `critical-rules-043` — sub-agent failure → re-task clean-room, no inline fallback
- `critical-rules-044` — pre-analysis sub-agent for each phase before execution
- `critical-rules-052` — no inline submodule git operations
- `critical-rules-016` — every pipeline step mandatory, no skips
- `critical-rules-042` — scope creep prohibited, implement exactly the spec