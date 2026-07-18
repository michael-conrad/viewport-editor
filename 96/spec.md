---
title: Auto-reload viewport buffer on external file change when clean
status: draft
created: 2026-07-17
license: MIT
provenance: AI-generated
issue: 96
authors:
  - OpenCode (deepseek-v4-flash)
---

**STATUS:** DRAFT
**CREATED:** 2026-07-17

> **Compliance Requirement:** All steps and sub-steps in this document MUST be followed in order. Failure to comply with any step — including but not limited to verification gates, test phases, audit checkpoints, and review steps — will result in the feature branch being rejected and discarded, requiring a full rework from scratch and loss of all prior work. There is no valid reason to skip, compress, reorder, or omit any step. If a step appears redundant or unnecessary, follow it anyway — the cost of following an extra step is negligible compared to the cost of rework from a skipped step.

## Problem

When a file changes externally (e.g., git checkout, another tool writes it), viewport-editor detects the mtime/size mismatch via `check_conflict()` (in `src/viewport_editor/file_ops.py` and `src/viewport_editor/viewport.py`) and appends a passive YAML warning to the response. But the buffer retains stale content. The agent must manually discard changes and reopen to see fresh data — even when there are zero pending edits (`dirty=False`). This wastes a round-trip and means the agent works against stale data until it notices the warning.

When the buffer has pending edits (`dirty=True`), the warning format is identical to the clean case — a single `warning:` YAML block with no urgency differentiation. The agent has no way to distinguish "safe to reload" from "reload would overwrite edits."

## Root Cause Analysis

The conflict detection system (`check_conflict` → `format_conflict_warning` → `_check_file_conflict`) is a unified path: it detects conflicts identically regardless of dirty state. There are 8 call sites of `_check_file_conflict` in `server.py` across read and edit actions (`_action_open`, `_action_scroll`, `_action_page_up`, `_action_page_down`, `_action_jump`, `_action_autosave`, `_action_set_display_mode`, and `_handle_edit_action`). All 8 follow the same pattern: check conflict → if warning, append `warning:\n{warning}` to the response parts.

Separately, the save-path composite tools — `write_file` action, `edit_text` action, and `file:save` handler — call `_manager.check_conflict()` directly (not via `_check_file_conflict`) and raise errors on conflict instead of appending warnings. `_action_list` does NOT currently check for conflicts at all — it will need a conflict check added.

None of the existing call sites auto-reload; none emits a differentiated signal based on dirty state.

## Alternatives Considered & Why Discarded

| Alternative | Rationale for Discarding |
|---|---|
| Auto-reload unconditionally (ignore dirty state) | Would silently overwrite pending edits — data loss risk |
| Add a separate polling mechanism (watcher thread) | Over-engineered for a single-user editor; `check_conflict` already runs inline on every action |
| Make auto-reload opt-in via config flag | Adds configuration surface for what should be safe default behavior; clean buffer + conflict = always safe to reload |
| Keep single warning format, add dirty flag to warning output | Agent must parse YAML to distinguish cases; differentiated severity is more visible |

## Anti-Lobotomization

Tests MUST NOT be lobotomized. Removing or weakening a behavioral test assertion to work around a timeout, failure, or infrastructure issue is a CRITICAL VIOLATION. SCs must achieve 100% clean PASS. No SC may be weakened, deferred, or reclassified to a lower evidence type to evade implementation. Read [Test Integrity Mandate](guidelines/080-code-standards.md).

## Solution

Introduce a bifurcated conflict response routed through `entry.dirty`:

| Condition | Behavior |
|---|---|
| Conflict detected + buffer clean (`dirty=False`) | Auto-reload buffer from disk, update entry mtime/size, include an info notice |
| Conflict detected + buffer dirty (`dirty=True`) | No reload — emit stronger conflict signal with `severity: external_modification` |

### Affected Files + Anchors

| File | Existing Anchor | What Exists |
|---|---|---|
| `src/viewport_editor/file_ops.py` | `format_conflict_warning()` | Formats conflict dict → YAML warning string |
| `src/viewport_editor/viewport.py` | `ViewportManager.check_conflict()` | Delegates to `file_ops.check_conflict()` |
| `src/viewport_editor/viewport.py` | `ViewportManager.format_conflict_warning()` | Delegates to `file_ops.format_conflict_warning()` |
| `src/viewport_editor/viewport.py` | `ViewportEntry.dirty` field | Boolean flag for pending edits |
| `src/viewport_editor/server.py` | `_check_file_conflict()` | 8 call sites across read and edit actions; `_action_list` lacks conflict check |
| `src/viewport_editor/server.py` | `file:save` handler | Save path with conflict check |
| `src/viewport_editor/server.py` | `write_file` action handler | Composite write with conflict check |
| `src/viewport_editor/server.py` | `edit_text` action handler | Composite edit with conflict check |
| `src/viewport_editor/buffer.py` | `refresh_if_changed()` | Reloads buffer from disk if mtime changed |
| `src/viewport_editor/buffer.py` | `get_buffer_ref()` | Gets live buffer reference |

### New Method: `ViewportManager.auto_reload_if_clean()`

Add to `viewport.py`. Signature:

```python
def auto_reload_if_clean(
    self, session_id: str, viewport_id: str
) -> Optional[str]:
```

Logic:
1. Get entry via `self.get_entry(session_id, viewport_id)`
2. Call `self.check_conflict(entry.file, entry.mtime, entry.size)`
3. If no conflict: return None
4. If `not entry.dirty`: reload buffer via `self._buffer_mgr.refresh_if_changed()`, update `entry.mtime`/`entry.size` from refreshed buffer, return info notice
5. If `entry.dirty`: return `format_external_modification_warning()` (stronger signal)

### New Function: `file_ops.format_external_modification_warning()`

Signature:

```python
def format_external_modification_warning(warning: dict) -> str:
```

Output format:

```
conflict:
  severity: external_modification
  note: file changed on disk while buffer has uncommitted edits — save will overwrite external changes
  file: <path>
  mtime:
    stored: <value>
    current: <value>
```

### Call Site Changes in `server.py`

- Replace `_check_file_conflict()` with `_check_and_maybe_reload()` that calls `_manager.auto_reload_if_clean()`
- Read-action call sites (open, scroll, page-up, page-down, jump, autosave, set-display-mode) — these 7 existing `_check_file_conflict` call sites: replace with `_check_and_maybe_reload()`, append notice or warning to response
- `_action_list` (no current conflict check) — **new behavior**: add `_check_and_maybe_reload()` call, append notice or warning
- `_handle_edit_action` (existing `_check_file_conflict` call site) — replace with `_check_and_maybe_reload()`, append notice or warning
- Save-path call sites (file:save, write_file, edit_text) — these call `_manager.check_conflict()` directly: on conflict+dirty raise ViewportError with stronger signal; on conflict+clean auto-reload then proceed

## Anti-Lobotomization SC

SC-13 explicitly forbids test lobotomization. Evidence type: behavioral.

## Success Criteria

| ID | Criterion | Evidence Type | Verification Method | Remediation | Pipeline Step Binding | Artifact Path | Requirement Traceability | Phase Binding | Verification Gate | Integration Mode | Affinity Group | Re-Entry Step | Test File | Phase Mapping |
|----|-----------|---------------|---------------------|-------------|----------------------|--------------|-------------------------|--------------|-----------------|----------------|--------------|-------------|-----------|--------------|
| SC-1 | Auto-reload fires on open when buffer exists from prior session and file changed externally | behavioral | Test: open file, modify externally, open again — content reflects new disk state, response includes auto-reload notice | On FAIL: verify refresh_if_changed is called; fix branching in auto_reload_if_clean | RED/GREEN | `.issues/96/test/behavioral/` | Root cause: no dirty-branching in conflict path | Phase 1 | pre-commit | green | — | — | `test_phase2_edit_diff.py` | Phase 1 |
| SC-2 | Auto-reload fires on scroll/jump/page-up/page-down when buffer is clean and file changed externally | behavioral | Test: open, modify externally, scroll — response shows new content + notice | On FAIL: verify _check_and_maybe_reload is called at each call site | RED/GREEN | `.issues/96/test/behavioral/` | Root cause: 7 read-action call sites lack dirty-branching | Phase 1 | pre-commit | green | — | — | `test_phase2_edit_diff.py` | Phase 1 |
| SC-3 | Auto-reload fires on list when buffer is clean and file changed externally | behavioral | Test: open, modify externally, list — entry metadata shows new mtime/size, notice present | On FAIL: verify list action calls _check_and_maybe_reload | RED/GREEN | `.issues/96/test/behavioral/` | Root cause: _action_list lacks auto-reload | Phase 1 | pre-commit | green | SC-2 | — | `test_phase1_server_viewport.py` | Phase 1 |
| SC-4 | Auto-reload fires on autosave/set-display-mode when buffer is clean and file changed externally | behavioral | Test: open, modify externally, toggle autosave — notice present | On FAIL: verify _action_autosave and _action_set_display_mode call auto-reload path | RED/GREEN | `.issues/96/test/behavioral/` | Root cause: autosave+display-mode actions lack dirty-branching | Phase 1 | pre-commit | green | SC-2 | — | `test_phase2_edit_diff.py` | Phase 1 |
| SC-5 | file:save (autosave off) auto-reloads before saving when buffer is clean and conflict detected — save succeeds | behavioral | Test: open, save (clean), modify externally, file:save — succeeds, no conflict error | On FAIL: verify save-path checks dirty before raising conflict | RED/GREEN | `.issues/96/test/behavioral/` | Root cause: save path raises on any conflict regardless of dirty | Phase 2 | pre-commit | green | — | — | `test_phase2_edit_diff.py` | Phase 2 |
| SC-6 | file:save (autosave off) emits stronger warning when buffer is dirty and conflict detected — save rejected | behavioral | Test: open, edit (dirty), modify externally, file:save — rejected with external_modification severity | On FAIL: verify format_external_modification_warning is called | RED/GREEN | `.issues/96/test/behavioral/` | Root cause: save path lacks dirty-branching for stronger signal | Phase 2 | pre-commit | green | — | — | `test_phase2_edit_diff.py` | Phase 2 |
| SC-7 | write_file/edit_text auto-reload before saving when buffer is clean and conflict detected | behavioral | Test: write_file with clean buffer + external change — succeeds, no conflict error | On FAIL: verify composite tool paths call auto_reload_if_clean | RED/GREEN | `.issues/96/test/behavioral/` | Root cause: write_file/edit_text raise on any conflict regardless of dirty | Phase 2 | pre-commit | green | SC-5 | — | `test_phase2_edit_diff.py` | Phase 2 |
| SC-8 | write_file/edit_text rejects with stronger warning when buffer is dirty and conflict detected | behavioral | Test: write_file with dirty buffer + external change — rejected with external_modification severity | On FAIL: verify format_external_modification_warning is called in dirty path | RED/GREEN | `.issues/96/test/behavioral/` | Root cause: write_file/edit_text lack dirty-branching for stronger signal | Phase 2 | pre-commit | green | SC-6 | — | `test_phase2_edit_diff.py` | Phase 2 |
| SC-9 | Auto-reload notice format: `file auto-reloaded (external change detected)` | string | grep for the exact string in source | On FAIL: fix notice string constant | code | `.issues/96/test/string/` | Solution spec: defined notice format | Phase 1 | pre-commit | string | — | — | — | Phase 1 |
| SC-10 | Stronger dirty conflict format includes `severity: external_modification` and a prose note about overwriting external changes | string | grep for `severity: external_modification` in source | On FAIL: fix format_external_modification_warning output | code | `.issues/96/test/string/` | Solution spec: defined stronger signal format | Phase 2 | pre-commit | string | — | — | — | Phase 2 |
| SC-11 | After auto-reload, entry.mtime and entry.size reflect current disk state | behavioral | Test: open, modify externally, auto-reload, check entry metadata matches os.stat | On FAIL: verify entry metadata is updated after reload | RED/GREEN | `.issues/96/test/behavioral/` | Root cause: entry metadata stale after external change | Phase 1 | pre-commit | green | — | — | `test_phase2_edit_diff.py` | Phase 1 |
| SC-12 | No behavior change when no conflict detected — existing responses unchanged | string | Existing test suite passes (`uv run pytest test/`) | On FAIL: identify regressed test and fix | CI | `.issues/96/test/regression/` | Safety: must not break existing behavior | Phase 2 | ci | regression | — | Phase 1 | — | Phase 2 |
| SC-13 | No SC may be weakened, deferred, or reclassified to a lower evidence type to evade implementation | behavioral | Assert no SC was changed from behavioral to lower type during implementation | On FAIL: revert SC weakening, re-implement correctly | audit | `.issues/96/test/audit/` | Anti-lobotomization | Phase 2 | pre-approval-gate | audit | — | — | — | Phase 2 |
| SC-14 | `format_external_modification_warning()` produces `severity: external_modification` and overwrite note | behavioral | Unit test: pass conflict dict, verify output YAML structure | On FAIL: fix function output to match spec | RED/GREEN | `.issues/96/test/unit/` | Solution spec: defined stronger signal format | Phase 1 | pre-commit | green | — | — | `test_auto_reload_unit.py` | Phase 1 |
| SC-15 | `auto_reload_if_clean()` returns None when no conflict | behavioral | Unit test: mock check_conflict → None, assert returns None | On FAIL: verify early-return logic in auto_reload_if_clean | RED/GREEN | `.issues/96/test/unit/` | Design: no-conflict short-circuit | Phase 1 | pre-commit | green | — | — | `test_auto_reload_unit.py` | Phase 1 |
| SC-16 | `auto_reload_if_clean()` auto-reloads when clean+conflict | behavioral | Unit test: mock conflict + dirty=False, assert refresh called + notice returned | On FAIL: verify dirty-check branching and refresh_if_changed call | RED/GREEN | `.issues/96/test/unit/` | Design: clean+conflict → auto-reload | Phase 1 | pre-commit | green | SC-15 | — | `test_auto_reload_unit.py` | Phase 1 |
| SC-17 | `auto_reload_if_clean()` returns strong warning when dirty+conflict | behavioral | Unit test: mock conflict + dirty=True, assert no refresh, warning returned | On FAIL: verify dirty-check branching and format_external_modification_warning call | RED/GREEN | `.issues/96/test/unit/` | Design: dirty+conflict → stronger signal | Phase 1 | pre-commit | green | SC-16 | — | `test_auto_reload_unit.py` | Phase 1 |
| SC-18 | `dev` branch merged into `main` with all commits preserved | string | Verify `git log main` contains all commits from `dev`; `git branch -d dev` succeeds | On FAIL: re-attempt merge preserving history | code | — | Trunk-based migration: no losing existing work | Phase 3 | pre-commit | string | — | — | — | Phase 3 |
| SC-19 | `dev` branch deleted locally and on remote | string | `git branch -a` shows no `dev` branch; `git push origin --delete dev` confirmed | On FAIL: delete remaining dev refs | code | — | Trunk-based migration: dev removed | Phase 3 | pre-commit | string | — | — | — | Phase 3 |
| SC-20 | `AGENTS.md` updated to reflect trunk-based development (no `dev` branch, feature branches target `main`, release from `main`) | string | grep for `dev` references in AGENTS.md — only historical release tags remain; `DEFAULT_BRANCH` references point to `main` | On FAIL: update stale dev references | code | — | Trunk-based migration: docs updated | Phase 3 | pre-commit | string | — | — | — | Phase 3 |
| SC-21 | All non-historical references to `dev` as a development branch removed from project files (pyproject.toml, CI configs, scripts, docs) | string | grep for branch references in project config files — no active `dev` branch references remain | On FAIL: update stale dev references | code | — | Trunk-based migration: no stale dev refs | Phase 3 | pre-commit | string | — | — | — | Phase 3 |

> **Compliance Requirement:** All steps and sub-steps in this document MUST be followed in order. Failure to comply with any step — including but not limited to verification gates, test phases, audit checkpoints, and review steps — will result in the feature branch being rejected and discarded, requiring a full rework from scratch and loss of all prior work. There is no valid reason to skip, compress, reorder, or omit any step. If a step appears redundant or unnecessary, follow it anyway — the cost of following an extra step is negligible compared to the cost of rework from a skipped step.

## Implementation Approach

After this spec is approved, invoke `writing-plans` to create `.issues/96/plan.md` before implementation begins.

### Phase 1: Read-Action Auto-Reload

1. Add `format_external_modification_warning()` to `file_ops.py`
2. Add `auto_reload_if_clean()` to `ViewportManager` in `viewport.py`
3. Replace `_check_file_conflict()` with `_check_and_maybe_reload()` in `server.py`
4. Update all 8 existing `_check_file_conflict()` call sites (open, scroll, page-up, page-down, jump, autosave, set-display-mode, _handle_edit_action) and add conflict check to `_action_list` (new behavior)
5. Write unit tests for `format_external_modification_warning()`, `auto_reload_if_clean()`, and `_check_and_maybe_reload()` (SC-14 through SC-17)
6. Write behavioral integration tests for SC-1, SC-2, SC-3, SC-4, SC-9, SC-11

### Phase 2: Save-Path Dirty Awareness

1. Update file:save path to branch on dirty+conflict
2. Update write_file/edit_text paths to branch on dirty+conflict
3. Write behavioral integration tests for SC-5, SC-6, SC-7, SC-8, SC-10, SC-12, SC-13
4. Run full test suite for regression check (SC-12)

### Phase 3: Trunk-Based Migration

1. Merge `dev` into `main` preserving all commits — `git checkout main && git merge dev --no-ff`
2. Delete `dev` branch locally and on remote — `git branch -d dev && git push origin --delete dev`
3. Update `AGENTS.md` — replace all `dev` branch references with `main` as the trunk; update Release Checklist to target `main` directly; remove `dev → main PR` workflow
4. Update `pyproject.toml`, CI configs, scripts, and docs — replace stale `dev` branch references with `main`
5. Update `DEFAULT_BRANCH` references in `.opencode/` to point to `main`
6. Verify no stale `dev` references remain (SC-18 through SC-21)

## Unit Test Plan

In addition to behavioral integration tests (which exercise the full MCP server tool surface), isolated unit tests verify each new function's branching logic directly — without server/client infrastructure.

### Test File

`test/test_auto_reload_unit.py` — following the pattern established by `test_viewport_id_unit.py` (direct imports from source, no conftest fixtures, minimal mocking).

### Unit Tests

| SC | Function Under Test | Test Description | Evidence Type |
|----|-------------------|------------------|---------------|
| SC-14 | `format_external_modification_warning(warning)` | Pass a conflict dict; verify output YAML contains `severity: external_modification` and the prose note about overwriting external changes. Verify no other severity variant is emitted. | behavioral (pytest) |
| SC-15 | `auto_reload_if_clean()` — no conflict path | Mock `check_conflict()` to return `None`. Call `auto_reload_if_clean()`. Assert: returns `None`, `refresh_if_changed()` not called, entry metadata unchanged. | behavioral (pytest) |
| SC-16 | `auto_reload_if_clean()` — conflict + clean path | Mock `check_conflict()` to return a conflict dict, set `entry.dirty=False`. Call `auto_reload_if_clean()`. Assert: `refresh_if_changed()` called, `entry.mtime`/`entry.size` updated, returns info notice string. | behavioral (pytest) |
| SC-17 | `auto_reload_if_clean()` — conflict + dirty path | Mock `check_conflict()` to return a conflict dict, set `entry.dirty=True`. Call `auto_reload_if_clean()`. Assert: `refresh_if_changed()` not called, returns `format_external_modification_warning()` output. | behavioral (pytest) |

### Mocking Strategy

- Use `unittest.mock.patch` or `pytest.monkeypatch` to isolate `ViewportManager.check_conflict()` and `BufferManager.refresh_if_changed()`
- Use a real `ViewportEntry` instance with controlled `.dirty` value and known `.mtime`/`.size`
- No MCP server, no `Client`, no conftest fixtures — pure function-level tests

### RED/GREEN for Unit Tests

Each unit test follows the same TDD cycle as behavioral tests:
- **RED**: Write the unit test first; it fails because the function doesn't exist yet
- **GREEN**: Implement the function; test passes
- **REFACTOR**: Verify no cross-test interference

### Plan Format Requirements

Every dispatch step in the plan MUST use the canonical `skill({name: "..."})` → `task(..., prompt: "execute <task> task from <skill>")` form. Plan steps MUST NOT contain inline procedure text. The full implementation pipeline must be enumerated with no skipped or combined steps: coherence gate, pre-red-baseline, RED/GREEN per item, VbC, audit, cross-validate, regression check, finishing checklist, review-prep, cleanup.

## Risk and Edge Cases

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Auto-reload races with concurrent external write | Low | Data loss on clean buffer | `refresh_if_changed` reads atomically; window is same as manual reopen |
| Dirty flag incorrectly set (false positive) | Medium | Spurious stronger warning | Auto-reload only when `dirty=False`; false-positive dirty means user sees stronger signal (safe) |
| Dirty flag incorrectly clear (false negative) | Medium | Silent data loss | Existing `dirty` tracking is well-tested via autosave/flush; auto-reload only when explicitly `dirty=False` |
| Autosave fires between external change and agent action | Low | Buffer saved before reload detected | Autosave path includes conflict check; will auto-reload if clean at that point |

## Interdependency

No known interdependencies with other open issues.

## Documentation Sources

| Source Category | What Was Consulted | Purpose |
|---|---|---|
| Direct source search | `grep` for `check_conflict` in `src/` | Verify existing conflict detection API |
| Direct source search | `grep` for `format_conflict_warning` in `src/` | Verify existing warning format function |
| Direct source search | `grep` for `_check_file_conflict` in `src/` | Verify 8 call sites via helper + 3 direct calls to `_manager.check_conflict()` |
| Direct source search | `grep` for `auto_reload_if_clean` in `src/` | Confirm method does not exist yet |
| Direct source search | `grep` for `refresh_if_changed` in `src/` | Verify BufferManager refresh API exists |
| Direct source search | `glob` for test files in `test/` | Verify referenced test files exist |
| Live verification | `editor_read_file` for `server.py` `_check_file_conflict()` | Read `_check_file_conflict` implementation |
| Live verification | `editor_read_file` for `server.py` `file:save` handler | Read file:save conflict handling |
| Live verification | `editor_read_file` for `server.py` `write_file`/`edit_text` handlers | Read write_file/edit_text conflict handling |

## Cross-Cutting SCs

SC-12 (regression) — verified once in Phase 2, applies to all phases.

🤖 Co-authored with AI: OpenCode (deepseek-v4-flash)
