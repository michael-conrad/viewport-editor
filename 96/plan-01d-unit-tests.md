# Phase 01d — unit-tests

## Phase Metadata

- **Concern:** Write unit tests for new functions (`test_auto_reload_unit.py`)
- **Files:** `test/test_auto_reload_unit.py`
- **SCs:** SC-14, SC-15, SC-16, SC-17
- **Dependencies:** Phase 1c (all new functions exist in source)
- **Entry:** All new functions implemented in source
- **Exit:** Unit tests pass for all new functions
- **Cost frame:** Cost is measured in defect-discovery-latency, not model roundtrips. Running verification costs minutes of execution time — a bounded delay that surfaces defects before they reach CI. Skipping a verification step to save a tool call costs the full pipeline of rework when the defect surfaces downstream: diagnosis, fix, re-review, re-CI, re-deploy — each of which costs more roundtrips than the skipped verification would have consumed. Correctness is the only success metric — there is no score for tool-call economy.

## Code Path Coverage

- `test/test_auto_reload_unit.py`: Unit tests for `format_external_modification_warning()` and `auto_reload_if_clean()`

## Cross-Cutting SCs

None.

## Interface Boundaries

None — pure function-level tests.

## State Transitions

- From: Unit tests exist as RED stubs from Phase 1a/1b
- To: All unit tests pass

### Item 1: SC-14 unit test

- [ ] 18. **Pre-RED baseline (**inline**).** Verify `test/test_auto_reload_unit.py` exists with RED tests from earlier phases.
- [ ] 19. **RED (**sub-agent**).** Run `uv run pytest test/test_auto_reload_unit.py -v` — confirm expected failures for SC-14 test (format_external_modification_warning output format).
- [ ] 20. **GREEN (**sub-agent**).** Complete SC-14 unit test implementation in `test/test_auto_reload_unit.py`: pass a conflict dict, verify output YAML contains `severity: external_modification` and the prose note. **SC gate: this step FAILS if SC-14 test does not verify the exact output format.**
- [ ] 20a. **GREEN doublecheck (**inline**).** Run `uv run pytest test/test_auto_reload_unit.py -v` — confirm SC-14 test PASS.
- [ ] 20b. **REFACTOR (**inline**).** Clean up: verify test follows `test_viewport_id_unit.py` pattern (direct imports, no conftest fixtures), check no test pollution across functions.
- [ ] 20c. **Checkpoint commit (**inline**).** `git add -A && git commit -m "test: add SC-14 unit test for format_external_modification_warning"`

### Item 2: SC-15 unit test

- [ ] 20d. **RED (**sub-agent**).** Run `uv run pytest test/test_auto_reload_unit.py -v` — confirm expected failures for SC-15 test (no-conflict path).
- [ ] 20e. **GREEN (**sub-agent**).** Complete SC-15 unit test implementation: mock `check_conflict` → None, assert `auto_reload_if_clean` returns None, `refresh_if_changed` not called. **SC gate: this step FAILS if SC-15 test does not verify the no-conflict short-circuit.**
- [ ] 20f. **GREEN doublecheck (**inline**).** Run `uv run pytest test/test_auto_reload_unit.py -v` — confirm SC-15 test PASS.
- [ ] 20g. **REFACTOR (**inline**).** Clean up: verify mocking strategy is consistent, check no cross-test interference with SC-14 test.
- [ ] 20h. **Checkpoint commit (**inline**).** `git add -A && git commit -m "test: add SC-15 unit test for no-conflict path"`

### Item 3: SC-16 unit test

- [ ] 20i. **RED (**sub-agent**).** Run `uv run pytest test/test_auto_reload_unit.py -v` — confirm expected failures for SC-16 test (clean+conflict path).
- [ ] 20j. **GREEN (**sub-agent**).** Complete SC-16 unit test implementation: mock conflict + `dirty=False`, assert `refresh_if_changed` called, notice returned, `entry.mtime`/`entry.size` updated. **SC gate: this step FAILS if SC-16 test does not verify auto-reload behavior.**
- [ ] 20k. **GREEN doublecheck (**inline**).** Run `uv run pytest test/test_auto_reload_unit.py -v` — confirm SC-16 test PASS.
- [ ] 20l. **REFACTOR (**inline**).** Clean up: verify mock setup for `refresh_if_changed` is correct, check entry metadata assertions match `BufferManager` API.
- [ ] 20m. **Checkpoint commit (**inline**).** `git add -A && git commit -m "test: add SC-16 unit test for clean+conflict path"`

### Item 4: SC-17 unit test

- [ ] 20n. **RED (**sub-agent**).** Run `uv run pytest test/test_auto_reload_unit.py -v` — confirm expected failures for SC-17 test (dirty+conflict path).
- [ ] 20o. **GREEN (**sub-agent**).** Complete SC-17 unit test implementation: mock conflict + `dirty=True`, assert no refresh, warning returned with `severity: external_modification`. **SC gate: this step FAILS if SC-17 test does not verify the stronger warning.**
- [ ] 20p. **GREEN doublecheck (**inline**).** Run `uv run pytest test/test_auto_reload_unit.py -v` — confirm SC-17 test PASS.
- [ ] 20q. **REFACTOR (**inline**).** Clean up: verify all 4 unit tests run independently without interference, check test file follows project conventions.
- [ ] 21. **Checkpoint commit (**inline**).** `git add -A && git commit -m "test: add SC-17 unit test for dirty+conflict path"`

#### Phase 01d VbC

- [ ] 21a. **VbC (**clean-room**).** Verify: all unit tests pass, mocking strategy is correct, no cross-test interference. **→ SC-14, SC-15, SC-16, SC-17** `evidence_type: behavioral`
- [ ] 21b. **Behavioral test evaluation (**clean-room**).** Run `uv run pytest test/test_auto_reload_unit.py -v` — confirm PASS. **→ SC-14, SC-15, SC-16, SC-17** `evidence_type: behavioral`

**Concern transition:** Leaving unit tests → entering behavioral tests for Phase 1. Phase 1e depends on Phase 1d's unit tests passing.
