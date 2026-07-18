# Phase 01c — server-read-action-reload

## Phase Metadata

- **Concern:** Replace `_check_file_conflict` with `_check_and_maybe_reload` in `server.py` read-action call sites
- **Files:** `src/viewport_editor/server.py`
- **SCs:** SC-1, SC-2, SC-3, SC-4, SC-11
- **Dependencies:** Phase 1b (`auto_reload_if_clean` exists)
- **Entry:** `auto_reload_if_clean()` defined on `ViewportManager`
- **Exit:** All 7 existing `_check_file_conflict` call sites replaced, `_action_list` includes conflict check
- **Cost frame:** Cost is measured in defect-discovery-latency, not model roundtrips. Running verification costs minutes of execution time — a bounded delay that surfaces defects before they reach CI. Skipping a verification step to save a tool call costs the full pipeline of rework when the defect surfaces downstream: diagnosis, fix, re-review, re-CI, re-deploy — each of which costs more roundtrips than the skipped verification would have consumed. Correctness is the only success metric — there is no score for tool-call economy.

## Code Path Coverage

- `server.py`: Define `_check_and_maybe_reload()` helper, update 7 call sites (`_action_open`, `_action_scroll`, `_action_jump`, `_action_page_up`, `_action_page_down`, `_action_autosave`, `_action_set_display_mode`), add conflict check to `_action_list`

## Cross-Cutting SCs

- SC-11: After auto-reload, entry.mtime and entry.size reflect current disk state

## Interface Boundaries

- New function `_check_and_maybe_reload(file_path, entry) -> Optional[str]` replaces `_check_file_conflict`
- `_check_file_conflict` removed (breaking change — internal only)

## State Transitions

- From: `_check_file_conflict` at 7 read-action call sites + no conflict check on `_action_list`
- To: `_check_and_maybe_reload` at all 8 read-action call sites

### Item 1: Helper function (prerequisite)

- [ ] 14. **Pre-RED baseline (**inline**).** Verify `_check_and_maybe_reload` does not exist yet: `grep -rn "_check_and_maybe_reload" src/`.
- [ ] 15. **RED (**sub-agent**).** Write unit test for `_check_and_maybe_reload` helper in `test/test_auto_reload_unit.py`: mock `auto_reload_if_clean`, verify the helper delegates correctly. Test must fail because helper doesn't exist yet.
- [ ] 16. **GREEN (**sub-agent**).** Define `_check_and_maybe_reload(file_path, entry) -> Optional[str]` in `src/viewport_editor/server.py` that calls `_manager.auto_reload_if_clean()` instead of old `_check_file_conflict` pattern. **SC gate: this step FAILS if the function does not delegate to auto_reload_if_clean.**
- [ ] 16a. **GREEN doublecheck (**inline**).** Run unit test from step 15 — confirm PASS.
- [ ] 16b. **REFACTOR (**inline**).** Clean up: verify `_check_file_conflict` is no longer called from the helper, check no stale references to old function, verify return type matches call site expectations.
- [ ] 16c. **Checkpoint commit (**inline**).** `git add -A && git commit -m "feat: add _check_and_maybe_reload helper"`

### Item 2: _action_open (SC-1)

- [ ] 16d. **RED (**sub-agent**).** Write behavioral test for SC-1 (open + external change) in `test/test_phase1_server_viewport.py`. Test must fail because `_action_open` doesn't call auto-reload yet.
- [ ] 16e. **GREEN (**sub-agent**).** Replace `_check_file_conflict` with `_check_and_maybe_reload` at `_action_open` call site. Append returned notice/warning to response parts. **SC gate: this step FAILS if _action_open does not auto-reload when clean+conflict.**
- [ ] 16f. **GREEN doublecheck (**inline**).** Run behavioral test from step 16d — confirm PASS.
- [ ] 16g. **REFACTOR (**inline**).** Clean up: verify response assembly pattern is consistent with other call sites, check no duplicate warning appending.
- [ ] 16h. **Checkpoint commit (**inline**).** `git add -A && git commit -m "feat: auto-reload on _action_open"`

### Item 3: scroll/jump/page (SC-2)

- [ ] 16i. **RED (**sub-agent**).** Write behavioral test for SC-2 (scroll/jump/page + external change) in `test/test_phase1_server_viewport.py`. Test must fail because scroll/jump/page don't call auto-reload yet.
- [ ] 16j. **GREEN (**sub-agent**).** Replace `_check_file_conflict` with `_check_and_maybe_reload` at `_action_scroll`, `_action_jump`, `_action_page_up`, `_action_page_down` call sites. **SC gate: this step FAILS if scroll/jump/page do not auto-reload when clean+conflict.**
- [ ] 16k. **GREEN doublecheck (**inline**).** Run behavioral test from step 16i — confirm PASS.
- [ ] 16l. **REFACTOR (**inline**).** Clean up: verify all 4 call sites use identical replacement pattern, check no stale `_check_file_conflict` calls remain at these sites.
- [ ] 16m. **Checkpoint commit (**inline**).** `git add -A && git commit -m "feat: auto-reload on scroll/jump/page actions"`

### Item 4: _action_list (SC-3)

- [ ] 16n. **RED (**sub-agent**).** Write behavioral test for SC-3 (list + external change) in `test/test_phase1_server_viewport.py`. Test must fail because `_action_list` doesn't check conflicts yet.
- [ ] 16o. **GREEN (**sub-agent**).** Add `_check_and_maybe_reload` call to `_action_list` — append notice/warning to response. **SC gate: this step FAILS if _action_list does not include conflict check.**
- [ ] 16p. **GREEN doublecheck (**inline**).** Run behavioral test from step 16n — confirm PASS.
- [ ] 16q. **REFACTOR (**inline**).** Clean up: verify list response format is consistent with other actions, check no duplicate metadata.
- [ ] 16r. **Checkpoint commit (**inline**).** `git add -A && git commit -m "feat: add conflict check to _action_list"`

### Item 5: autosave/display-mode (SC-4)

- [ ] 16s. **RED (**sub-agent**).** Write behavioral test for SC-4 (autosave/set-display-mode + external change) in `test/test_phase1_server_viewport.py`. Test must fail because autosave/display-mode don't call auto-reload yet.
- [ ] 16t. **GREEN (**sub-agent**).** Replace `_check_file_conflict` with `_check_and_maybe_reload` at `_action_autosave` and `_action_set_display_mode` call sites. **SC gate: this step FAILS if autosave/display-mode do not auto-reload when clean+conflict.**
- [ ] 16u. **GREEN doublecheck (**inline**).** Run behavioral test from step 16s — confirm PASS.
- [ ] 16v. **REFACTOR (**inline**).** Clean up: verify autosave interaction is correct (autosave may flush dirty state between external change and action), check no double-reload.
- [ ] 16w. **Checkpoint commit (**inline**).** `git add -A && git commit -m "feat: auto-reload on autosave and set-display-mode"`

### Item 6: Edge case — race condition with concurrent write

- [ ] 16w2. **Edge case: concurrent write race (**inline**).** Verify that when a read action and an external write happen simultaneously, the auto-reload does not overwrite the external write. The safe failure mode is: auto-reload reads the file, then the external write completes, then the user's next action sees the external write's content. Document that this race is accepted per the spec's risk table — the window is bounded by the time between `check_conflict` and `refresh_if_changed`, and the next action will detect the new conflict. **SC gate: this step FAILS if the race condition is not documented as accepted risk.**
- [ ] 16w3. **REFACTOR (**inline**).** Clean up: verify race condition documentation is consistent with spec risk table, check no gaps in edge case coverage.

### Item 7: Entry metadata after reload (SC-11)

- [ ] 16x. **RED (**sub-agent**).** Write behavioral test for SC-11 (entry metadata after reload) in `test/test_phase1_server_viewport.py`. Test must fail because metadata update doesn't happen yet.
- [ ] 16y. **GREEN (**sub-agent**).** Ensure `auto_reload_if_clean` updates `entry.mtime` and `entry.size` from refreshed buffer after `refresh_if_changed()`. **SC gate: this step FAILS if entry metadata is not updated after reload.**
- [ ] 16z. **GREEN doublecheck (**inline**).** Run behavioral test from step 16x — confirm PASS.
- [ ] 16aa. **REFACTOR (**inline**).** Clean up: verify metadata update is consistent with `BufferManager` refresh API, check no stale metadata remains.
- [ ] 17. **Checkpoint commit (**inline**).** `git add -A && git commit -m "feat: update entry metadata after auto-reload"`

#### Phase 01c VbC

- [ ] 17a. **VbC (**clean-room**).** Verify: `_check_and_maybe_reload` defined, all 8 call sites updated, behavioral tests pass. **→ SC-1, SC-2, SC-3, SC-4, SC-11** `evidence_type: behavioral`
- [ ] 17b. **Behavioral test evaluation (**clean-room**).** Run `uv run pytest test/test_phase1_server_viewport.py -v` — confirm PASS. **→ SC-1, SC-2, SC-3, SC-4, SC-11** `evidence_type: behavioral`

**Concern transition:** Leaving server read-action call sites → entering unit tests. Phase 1d depends on Phase 1c's server changes being in place.
