# Phase 01b — viewport-auto-reload

## Phase Metadata

- **Concern:** Add `auto_reload_if_clean()` to `ViewportManager` in `viewport.py`
- **Files:** `src/viewport_editor/viewport.py`
- **SCs:** SC-15, SC-16, SC-17
- **Dependencies:** Phase 1a (`format_external_modification_warning` exists)
- **Entry:** `format_external_modification_warning()` defined in `file_ops.py`
- **Exit:** `auto_reload_if_clean()` defined with correct branching logic
- **Cost frame:** Cost is measured in defect-discovery-latency, not model roundtrips. Running verification costs minutes of execution time — a bounded delay that surfaces defects before they reach CI. Skipping a verification step to save a tool call costs the full pipeline of rework when the defect surfaces downstream: diagnosis, fix, re-review, re-CI, re-deploy — each of which costs more roundtrips than the skipped verification would have consumed. Correctness is the only success metric — there is no score for tool-call economy.

## Code Path Coverage

- `viewport.py`: New method `auto_reload_if_clean()` on `ViewportManager`
- Calls: `get_entry()` → `check_conflict()` → branch on `entry.dirty` → `refresh_if_changed()` or `format_external_modification_warning()`

## Cross-Cutting SCs

None specific to this phase.

## Interface Boundaries

- New method `ViewportManager.auto_reload_if_clean(session_id, viewport_id) -> Optional[str]`
- Consumed by `server.py` `_check_and_maybe_reload()` (Phase 1c)

## State Transitions

- From: No auto-reload method exists
- To: `auto_reload_if_clean()` defined with no-conflict → None, clean+conflict → reload + notice, dirty+conflict → warning

### Item 1: No-conflict path (SC-15)

- [ ] 9. **Pre-RED baseline (**inline**).** Verify `auto_reload_if_clean` does not exist yet: `grep -rn "auto_reload_if_clean" src/`.
- [ ] 10. **RED (**sub-agent**).** Write unit test for SC-15 in `test/test_auto_reload_unit.py`: mock `check_conflict` → None, assert `auto_reload_if_clean` returns None, `refresh_if_changed` not called. Test must fail because method doesn't exist yet.
- [ ] 11. **GREEN (**sub-agent**).** Implement `auto_reload_if_clean(self, session_id, viewport_id) -> Optional[str]` on `ViewportManager` with the no-conflict path only: get entry, call `check_conflict`, if no conflict return None. **SC gate: this step FAILS if no-conflict path does not return None.**
- [ ] 11a. **GREEN doublecheck (**inline**).** Run unit test from step 10 — confirm PASS.
- [ ] 11b. **REFACTOR (**inline**).** Clean up: verify method signature matches spec, check no unused imports in `viewport.py`, verify `get_entry` call pattern matches existing usage.
- [ ] 11c. **Checkpoint commit (**inline**).** `git add -A && git commit -m "feat: add auto_reload_if_clean no-conflict path"`

### Item 2: Clean+conflict path (SC-16)

- [ ] 12. **RED (**sub-agent**).** Write unit test for SC-16 in `test/test_auto_reload_unit.py`: mock conflict + `dirty=False`, assert `refresh_if_changed` called, notice returned, `entry.mtime`/`entry.size` updated. Test must fail because clean+conflict path doesn't exist yet.
- [ ] 12a. **GREEN (**sub-agent**).** Add clean+conflict branch to `auto_reload_if_clean`: if `not entry.dirty`, call `self._buffer_mgr.refresh_if_changed()`, update `entry.mtime`/`entry.size`, return info notice `"file auto-reloaded (external change detected)"`. **SC gate: this step FAILS if clean+conflict does not reload and return notice.**
- [ ] 12b. **GREEN doublecheck (**inline**).** Run unit test from step 12 — confirm PASS.
- [ ] 12c. **REFACTOR (**inline**).** Clean up: verify `refresh_if_changed` call pattern matches existing usage, check `entry.mtime`/`entry.size` update is consistent with `BufferManager` API, verify notice string matches SC-9 format.
- [ ] 12d. **Checkpoint commit (**inline**).** `git add -A && git commit -m "feat: add auto_reload_if_clean clean+conflict path"`

### Item 3: Dirty+conflict path (SC-17)

- [ ] 12e. **RED (**sub-agent**).** Write unit test for SC-17 in `test/test_auto_reload_unit.py`: mock conflict + `dirty=True`, assert no refresh, warning returned with `severity: external_modification`. Test must fail because dirty+conflict path doesn't exist yet.
- [ ] 12f. **GREEN (**sub-agent**).** Add dirty+conflict branch to `auto_reload_if_clean`: if `entry.dirty`, return `format_external_modification_warning(warning)`. **SC gate: this step FAILS if dirty+conflict does not return the stronger warning.**
- [ ] 12g. **GREEN doublecheck (**inline**).** Run unit test from step 12e — confirm PASS.
- [ ] 12h. **REFACTOR (**inline**).** Clean up: verify `format_external_modification_warning` import is present, check all three branches are mutually exclusive, verify no dead code.
- [ ] 12i. **Checkpoint commit (**inline**).** `git add -A && git commit -m "feat: add auto_reload_if_clean dirty+conflict path"`

### Item 4: Edge case verification

- [ ] 12j. **Edge case: dirty flag false positive (**inline**).** Verify that when `entry.dirty` is incorrectly True (false positive), `auto_reload_if_clean` returns the stronger warning instead of auto-reloading. This is the safe failure mode — the agent sees a stronger signal rather than silently overwriting. **SC gate: this step FAILS if false-positive dirty causes data loss.**
- [ ] 12k. **Edge case: dirty flag false negative (**inline**).** Verify that when `entry.dirty` is incorrectly False (false negative), `auto_reload_if_clean` auto-reloads the buffer. This is the unsafe failure mode — mitigated by existing well-tested dirty tracking. Document that this risk is accepted per the spec's risk table. **SC gate: this step FAILS if false-negative dirty is not documented as accepted risk.**
- [ ] 12l. **REFACTOR (**inline**).** Clean up: verify edge case documentation is consistent with spec risk table, check no gaps in branching logic coverage.
- [ ] 13. **Checkpoint commit (**inline**).** `git add -A && git commit -m "feat: add edge case verification for auto_reload_if_clean"`

#### Phase 01b VbC

- [ ] 13a. **VbC (**clean-room**).** Verify: method exists, branching logic correct, unit tests pass. **→ SC-15, SC-16, SC-17** `evidence_type: behavioral`
- [ ] 13b. **Behavioral test evaluation (**clean-room**).** Run `uv run pytest test/test_auto_reload_unit.py -v` — confirm PASS. **→ SC-15, SC-16, SC-17** `evidence_type: behavioral`

**Concern transition:** Leaving viewport auto-reload method → entering server read-action call site replacement. Phase 1c depends on Phase 1b's `auto_reload_if_clean()`.
