# Phase 01e — behavioral-tests-phase1

## Phase Metadata

- **Concern:** Write behavioral integration tests for Phase 1 SCs
- **Files:** `test/test_phase1_server_viewport.py`
- **SCs:** SC-1, SC-2, SC-3, SC-4, SC-9, SC-11
- **Dependencies:** Phase 1d (unit tests pass)
- **Entry:** All Phase 1 source changes complete and committed
- **Exit:** Behavioral tests pass for all Phase 1 SCs
- **Cost frame:** Cost is measured in defect-discovery-latency, not model roundtrips. Running verification costs minutes of execution time — a bounded delay that surfaces defects before they reach CI. Skipping a verification step to save a tool call costs the full pipeline of rework when the defect surfaces downstream: diagnosis, fix, re-review, re-CI, re-deploy — each of which costs more roundtrips than the skipped verification would have consumed. Correctness is the only success metric — there is no score for tool-call economy.

## Code Path Coverage

- `test/test_phase1_server_viewport.py`: Behavioral tests exercising the full MCP server tool surface

## Cross-Cutting SCs

- SC-9: Auto-reload notice format (string check)
- SC-11: Entry metadata after reload

## Interface Boundaries

None — tests exercise MCP tool surface.

## State Transitions

- From: Behavioral tests exist as RED stubs from Phase 1c
- To: All behavioral tests pass

### Item 1: SC-1 behavioral test

- [ ] 22. **Pre-RED baseline (**inline**).** Verify `test/test_phase1_server_viewport.py` exists with RED tests from Phase 1c.
- [ ] 23. **RED (**sub-agent**).** Run `uv run pytest test/test_phase1_server_viewport.py -v` — confirm expected failures for SC-1 test (open + external change).
- [ ] 24. **GREEN (**sub-agent**).** Complete SC-1 behavioral test: open file, modify externally, open again — verify content reflects new disk state, response includes auto-reload notice. **SC gate: this step FAILS if SC-1 test does not verify auto-reload on open.**
- [ ] 24a. **GREEN doublecheck (**inline**).** Run `uv run pytest test/test_phase1_server_viewport.py -v` — confirm SC-1 test PASS.
- [ ] 24b. **REFACTOR (**inline**).** Clean up: verify test uses `client_session` fixture correctly, check no stale state from prior test runs.
- [ ] 24c. **Checkpoint commit (**inline**).** `git add -A && git commit -m "test: add SC-1 behavioral test for auto-reload on open"`

### Item 2: SC-2 behavioral test

- [ ] 24d. **RED (**sub-agent**).** Run `uv run pytest test/test_phase1_server_viewport.py -v` — confirm expected failures for SC-2 test (scroll/jump/page + external change).
- [ ] 24e. **GREEN (**sub-agent**).** Complete SC-2 behavioral test: open, modify externally, scroll/jump/page-up/page-down — verify new content + notice. **SC gate: this step FAILS if SC-2 test does not verify auto-reload on scroll/jump/page.**
- [ ] 24f. **GREEN doublecheck (**inline**).** Run `uv run pytest test/test_phase1_server_viewport.py -v` — confirm SC-2 test PASS.
- [ ] 24g. **REFACTOR (**inline**).** Clean up: verify test covers all 4 navigation actions (scroll, jump, page-up, page-down), check no redundant assertions.
- [ ] 24h. **Checkpoint commit (**inline**).** `git add -A && git commit -m "test: add SC-2 behavioral test for auto-reload on navigation"`

### Item 3: SC-3 behavioral test

- [ ] 24i. **RED (**sub-agent**).** Run `uv run pytest test/test_phase1_server_viewport.py -v` — confirm expected failures for SC-3 test (list + external change).
- [ ] 24j. **GREEN (**sub-agent**).** Complete SC-3 behavioral test: open, modify externally, list — verify metadata shows new mtime/size + notice. **SC gate: this step FAILS if SC-3 test does not verify auto-reload on list.**
- [ ] 24k. **GREEN doublecheck (**inline**).** Run `uv run pytest test/test_phase1_server_viewport.py -v` — confirm SC-3 test PASS.
- [ ] 24l. **REFACTOR (**inline**).** Clean up: verify list response format matches expected structure, check no duplicate entries.
- [ ] 24m. **Checkpoint commit (**inline**).** `git add -A && git commit -m "test: add SC-3 behavioral test for auto-reload on list"`

### Item 4: SC-4 behavioral test

- [ ] 24n. **RED (**sub-agent**).** Run `uv run pytest test/test_phase1_server_viewport.py -v` — confirm expected failures for SC-4 test (autosave/set-display-mode + external change).
- [ ] 24o. **GREEN (**sub-agent**).** Complete SC-4 behavioral test: open, modify externally, toggle autosave/set-display-mode — verify notice present. **SC gate: this step FAILS if SC-4 test does not verify auto-reload on autosave/display-mode.**
- [ ] 24p. **GREEN doublecheck (**inline**).** Run `uv run pytest test/test_phase1_server_viewport.py -v` — confirm SC-4 test PASS.
- [ ] 24q. **REFACTOR (**inline**).** Clean up: verify autosave interaction is handled correctly (autosave may change dirty state), check no timing issues.
- [ ] 24r. **Checkpoint commit (**inline**).** `git add -A && git commit -m "test: add SC-4 behavioral test for auto-reload on autosave/display-mode"`

### Item 5: SC-9 string check

- [ ] 24s. **RED (**sub-agent**).** Run `uv run pytest test/test_phase1_server_viewport.py -v` — confirm expected failures for SC-9 test (notice format string).
- [ ] 24t. **GREEN (**sub-agent**).** Complete SC-9 string check: verify auto-reload notice contains exact string `"file auto-reloaded (external change detected)"`. **SC gate: this step FAILS if SC-9 test does not verify the exact notice string.**
- [ ] 24u. **GREEN doublecheck (**inline**).** Run `uv run pytest test/test_phase1_server_viewport.py -v` — confirm SC-9 test PASS.
- [ ] 24v. **REFACTOR (**inline**).** Clean up: verify string check is precise (no false positives from substring matching), check notice constant is centralized.
- [ ] 24w. **Checkpoint commit (**inline**).** `git add -A && git commit -m "test: add SC-9 string check for auto-reload notice format"`

### Item 6: SC-11 behavioral test

- [ ] 24x. **RED (**sub-agent**).** Run `uv run pytest test/test_phase1_server_viewport.py -v` — confirm expected failures for SC-11 test (entry metadata after reload).
- [ ] 24y. **GREEN (**sub-agent**).** Complete SC-11 behavioral test: open, modify externally, auto-reload, check entry metadata matches `os.stat`. **SC gate: this step FAILS if SC-11 test does not verify entry metadata update.**
- [ ] 24z. **GREEN doublecheck (**inline**).** Run `uv run pytest test/test_phase1_server_viewport.py -v` — confirm SC-11 test PASS.
- [ ] 24aa. **REFACTOR (**inline**).** Clean up: verify metadata assertions use correct `os.stat` fields, check no stale metadata from prior test state.
- [ ] 25. **Checkpoint commit (**inline**).** `git add -A && git commit -m "test: add SC-11 behavioral test for entry metadata after reload"`

#### Phase 01e VbC

- [ ] 25a. **VbC (**clean-room**).** Verify: all behavioral tests pass, test scenarios cover all Phase 1 SCs. **→ SC-1, SC-2, SC-3, SC-4, SC-9, SC-11** `evidence_type: behavioral`
- [ ] 25b. **Behavioral test evaluation (**clean-room**).** Run `uv run pytest test/test_phase1_server_viewport.py -v` — confirm PASS. **→ SC-1, SC-2, SC-3, SC-4, SC-9, SC-11** `evidence_type: behavioral`

**Concern transition:** Leaving Phase 1 behavioral tests → entering save-path dirty awareness. Phase 2a depends on Phase 1e's verified auto-reload infrastructure.
