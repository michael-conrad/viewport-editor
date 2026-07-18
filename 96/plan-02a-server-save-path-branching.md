# Phase 02a — server-save-path-branching

## Phase Metadata

- **Concern:** Branch save-path conflict handling on dirty state in `server.py`
- **Files:** `src/viewport_editor/server.py`
- **SCs:** SC-5, SC-6, SC-7, SC-8
- **Dependencies:** Phase 1e (auto-reload infrastructure verified)
- **Entry:** Phase 1 complete and committed
- **Exit:** Save-path conflict handling branches on dirty state correctly
- **Cost frame:** Cost is measured in defect-discovery-latency, not model roundtrips. Running verification costs minutes of execution time — a bounded delay that surfaces defects before they reach CI. Skipping a verification step to save a tool call costs the full pipeline of rework when the defect surfaces downstream: diagnosis, fix, re-review, re-CI, re-deploy — each of which costs more roundtrips than the skipped verification would have consumed. Correctness is the only success metric — there is no score for tool-call economy.

## Code Path Coverage

- `server.py`: `_handle_file_action` (file:save path), `_handle_edit_action` (write_file/edit_text path), `write_file` action handler, `edit_text` action handler

## Cross-Cutting SCs

None specific to this phase.

## Interface Boundaries

- `_handle_file_action` — modified: conflict response changes from passive warning to auto-reload-or-reject
- `_handle_edit_action` — modified: same branching logic
- `write_file` action handler — modified: conflict check branches on dirty
- `edit_text` action handler — modified: conflict check branches on dirty

## State Transitions

- From: Save paths raise on any conflict regardless of dirty state
- To: Clean+conflict → auto-reload then proceed; dirty+conflict → reject with `severity: external_modification`

### Item 1: file:save clean+conflict (SC-5)

- [ ] 26. **Pre-RED baseline (**inline**).** Verify current save-path behavior: `grep -n "check_conflict" src/viewport_editor/server.py` to confirm existing conflict check locations.
- [ ] 27. **RED (**sub-agent**).** Write behavioral test for SC-5 in `test/test_phase2_edit_diff.py`: file:save with clean buffer + external change — auto-reload triggers, save succeeds. Test must fail because file:save doesn't branch on dirty yet.
- [ ] 28. **GREEN (**sub-agent**).** Update `_handle_file_action` (file:save handler) in `src/viewport_editor/server.py`: after conflict check, branch on `entry.dirty`. If clean+conflict: call `auto_reload_if_clean`, then proceed with save. If dirty+conflict: raise `ViewportError` with `format_external_modification_warning`. **SC gate: this step FAILS if file:save does not auto-reload when clean+conflict.**
- [ ] 28a. **GREEN doublecheck (**inline**).** Run behavioral test from step 27 — confirm PASS.
- [ ] 28b. **REFACTOR (**inline**).** Clean up: verify `_handle_file_action` branching is consistent with read-action pattern, check no duplicate conflict checks.
- [ ] 28c. **Checkpoint commit (**inline**).** `git add -A && git commit -m "feat: auto-reload file:save on clean+conflict"`

### Item 2: file:save dirty+conflict (SC-6)

- [ ] 28d. **RED (**sub-agent**).** Write behavioral test for SC-6 in `test/test_phase2_edit_diff.py`: file:save with dirty buffer + external change — rejected with `severity: external_modification`. Test must fail because file:save doesn't emit stronger warning yet.
- [ ] 28e. **GREEN (**sub-agent**).** Ensure `_handle_file_action` dirty+conflict path raises `ViewportError` with `format_external_modification_warning`. **SC gate: this step FAILS if dirty+conflict does not produce external_modification severity.**
- [ ] 28f. **GREEN doublecheck (**inline**).** Run behavioral test from step 28d — confirm PASS.
- [ ] 28g. **REFACTOR (**inline**).** Clean up: verify error format matches spec, check `ViewportError` is raised with correct message structure.
- [ ] 28h. **Checkpoint commit (**inline**).** `git add -A && git commit -m "feat: reject file:save on dirty+conflict with stronger warning"`

### Item 3: write_file/edit_text clean+conflict (SC-7)

- [ ] 28i. **RED (**sub-agent**).** Write behavioral test for SC-7 in `test/test_phase2_edit_diff.py`: write_file/edit_text with clean buffer + external change — auto-reload triggers, succeeds. Test must fail because write_file/edit_text don't branch on dirty yet.
- [ ] 28j. **GREEN (**sub-agent**).** Update `_handle_edit_action` in `src/viewport_editor/server.py`: same branching logic for the conflict preamble before edit execution. **SC gate: this step FAILS if write_file/edit_text do not auto-reload when clean+conflict.**
- [ ] 28k. **GREEN doublecheck (**inline**).** Run behavioral test from step 28i — confirm PASS.
- [ ] 28l. **REFACTOR (**inline**).** Clean up: verify `_handle_edit_action` branching mirrors `_handle_file_action` pattern, check no duplicate logic.
- [ ] 28m. **Checkpoint commit (**inline**).** `git add -A && git commit -m "feat: auto-reload write_file/edit_text on clean+conflict"`

### Item 4: Edge case — autosave timing interaction

- [ ] 28n2. **Edge case: autosave timing (**inline**).** Verify that when autosave flushes dirty state between external change detection and action execution, the conflict check is re-evaluated. The sequence: external change occurs → autosave flushes buffer to disk (resetting dirty flag) → user action triggers conflict check. The check sees clean buffer + external change → auto-reloads. Document that this is the correct behavior — autosave acts as a synchronization point that resets the dirty state. **SC gate: this step FAILS if autosave timing interaction is not documented as correct behavior.**
- [ ] 28n3. **REFACTOR (**inline**).** Clean up: verify autosave timing documentation is consistent with spec risk table, check no gaps in edge case coverage.

### Item 5: write_file/edit_text dirty+conflict (SC-8)

- [ ] 28o. **RED (**sub-agent**).** Write behavioral test for SC-8 in `test/test_phase2_edit_diff.py`: write_file/edit_text with dirty buffer + external change — rejected with `severity: external_modification`. Test must fail because write_file/edit_text don't emit stronger warning yet.
- [ ] 28p. **GREEN (**sub-agent**).** Update `write_file` and `edit_text` action handlers in `src/viewport_editor/server.py`: after conflict check, branch on `entry.dirty`. Clean+conflict: auto-reload then proceed. Dirty+conflict: return error with stronger warning. **SC gate: this step FAILS if dirty+conflict does not produce external_modification severity.**
- [ ] 28q. **GREEN doublecheck (**inline**).** Run behavioral test from step 28o — confirm PASS.
- [ ] 28r. **REFACTOR (**inline**).** Clean up: verify all 4 save-path call sites use consistent branching, check no stale conflict-handling code remains.
- [ ] 29. **Checkpoint commit (**inline**).** `git add -A && git commit -m "feat: reject write_file/edit_text on dirty+conflict with stronger warning"`

#### Phase 02a VbC

- [ ] 29a. **VbC (**clean-room**).** Verify: save-path branching implemented at all 4 call sites, behavioral tests pass. **→ SC-5, SC-6, SC-7, SC-8** `evidence_type: behavioral`
- [ ] 29b. **Behavioral test evaluation (**clean-room**).** Run `uv run pytest test/test_phase2_edit_diff.py -v` — confirm PASS. **→ SC-5, SC-6, SC-7, SC-8** `evidence_type: behavioral`

**Concern transition:** Leaving save-path branching → entering Phase 2 behavioral tests. Phase 2b depends on Phase 2a's save-path changes.
