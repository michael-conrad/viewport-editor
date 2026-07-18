# Phase 02b — behavioral-tests-phase2

## Phase Metadata

- **Concern:** Write behavioral integration tests for Phase 2 SCs and full regression
- **Files:** `test/test_phase2_edit_diff.py`
- **SCs:** SC-5, SC-6, SC-7, SC-8, SC-10, SC-12, SC-13
- **Dependencies:** Phase 2a (save-path changes committed)
- **Entry:** All Phase 2 source changes complete and committed
- **Exit:** Behavioral tests pass, full regression passes, anti-lobotomization audit passes
- **Cost frame:** Cost is measured in defect-discovery-latency, not model roundtrips. Running verification costs minutes of execution time — a bounded delay that surfaces defects before they reach CI. Skipping a verification step to save a tool call costs the full pipeline of rework when the defect surfaces downstream: diagnosis, fix, re-review, re-CI, re-deploy — each of which costs more roundtrips than the skipped verification would have consumed. Correctness is the only success metric — there is no score for tool-call economy.

## Code Path Coverage

- `test/test_phase2_edit_diff.py`: Behavioral tests for save-path SCs + full regression

## Cross-Cutting SCs

- SC-12: Full regression suite — applies to all phases
- SC-13: Anti-lobotomization audit — applies to all phases

## Interface Boundaries

None — tests exercise MCP tool surface.

## State Transitions

- From: Behavioral tests exist as RED stubs from Phase 2a
- To: All behavioral tests pass, regression passes, audit passes

### Item 1: SC-5 behavioral test

- [ ] 30. **Pre-RED baseline (**inline**).** Verify `test/test_phase2_edit_diff.py` exists with RED tests from Phase 2a.
- [ ] 31. **RED (**sub-agent**).** Run `uv run pytest test/test_phase2_edit_diff.py -v` — confirm expected failures for SC-5 test (file:save clean+conflict).
- [ ] 32. **GREEN (**sub-agent**).** Complete SC-5 behavioral test: file:save with clean buffer + external change — auto-reload triggers, save succeeds. **SC gate: this step FAILS if SC-5 test does not verify auto-reload before save.**
- [ ] 32a. **GREEN doublecheck (**inline**).** Run `uv run pytest test/test_phase2_edit_diff.py -v` — confirm SC-5 test PASS.
- [ ] 32b. **REFACTOR (**inline**).** Clean up: verify test uses `client_session` fixture, check no stale state from prior test runs, verify save-succeeds assertion is precise.
- [ ] 32c. **Checkpoint commit (**inline**).** `git add -A && git commit -m "test: add SC-5 behavioral test for file:save clean+conflict"`

### Item 2: SC-6 behavioral test

- [ ] 32d. **RED (**sub-agent**).** Run `uv run pytest test/test_phase2_edit_diff.py -v` — confirm expected failures for SC-6 test (file:save dirty+conflict).
- [ ] 32e. **GREEN (**sub-agent**).** Complete SC-6 behavioral test: file:save with dirty buffer + external change — rejected with `severity: external_modification`. **SC gate: this step FAILS if SC-6 test does not verify the stronger warning.**
- [ ] 32f. **GREEN doublecheck (**inline**).** Run `uv run pytest test/test_phase2_edit_diff.py -v` — confirm SC-6 test PASS.
- [ ] 32g. **REFACTOR (**inline**).** Clean up: verify error-assertion pattern matches existing test conventions, check no false-positive PASS from missing error.
- [ ] 32h. **Checkpoint commit (**inline**).** `git add -A && git commit -m "test: add SC-6 behavioral test for file:save dirty+conflict"`

### Item 3: SC-7 behavioral test

- [ ] 32i. **RED (**sub-agent**).** Run `uv run pytest test/test_phase2_edit_diff.py -v` — confirm expected failures for SC-7 test (write_file/edit_text clean+conflict).
- [ ] 32j. **GREEN (**sub-agent**).** Complete SC-7 behavioral test: write_file/edit_text with clean buffer + external change — auto-reload triggers, succeeds. **SC gate: this step FAILS if SC-7 test does not verify auto-reload before write.**
- [ ] 32k. **GREEN doublecheck (**inline**).** Run `uv run pytest test/test_phase2_edit_diff.py -v` — confirm SC-7 test PASS.
- [ ] 32l. **REFACTOR (**inline**).** Clean up: verify both write_file and edit_text are tested, check no redundant setup between the two.
- [ ] 32m. **Checkpoint commit (**inline**).** `git add -A && git commit -m "test: add SC-7 behavioral test for write_file/edit_text clean+conflict"`

### Item 4: SC-8 behavioral test

- [ ] 32n. **RED (**sub-agent**).** Run `uv run pytest test/test_phase2_edit_diff.py -v` — confirm expected failures for SC-8 test (write_file/edit_text dirty+conflict).
- [ ] 32o. **GREEN (**sub-agent**).** Complete SC-8 behavioral test: write_file/edit_text with dirty buffer + external change — rejected with `severity: external_modification`. **SC gate: this step FAILS if SC-8 test does not verify the stronger warning.**
- [ ] 32p. **GREEN doublecheck (**inline**).** Run `uv run pytest test/test_phase2_edit_diff.py -v` — confirm SC-8 test PASS.
- [ ] 32q. **REFACTOR (**inline**).** Clean up: verify error format matches SC-6 pattern, check no test pollution between write_file and edit_text tests.
- [ ] 32r. **Checkpoint commit (**inline**).** `git add -A && git commit -m "test: add SC-8 behavioral test for write_file/edit_text dirty+conflict"`

### Item 5: SC-10 string check

- [ ] 32s. **RED (**sub-agent**).** Run `uv run pytest test/test_phase2_edit_diff.py -v` — confirm expected failures for SC-10 test (severity string check).
- [ ] 32t. **GREEN (**sub-agent**).** Complete SC-10 string check: verify stronger conflict format includes `severity: external_modification`. **SC gate: this step FAILS if SC-10 test does not verify the exact severity string.**
- [ ] 32u. **GREEN doublecheck (**inline**).** Run `uv run pytest test/test_phase2_edit_diff.py -v` — confirm SC-10 test PASS.
- [ ] 32v. **REFACTOR (**inline**).** Clean up: verify string check is precise (no false positives), check severity constant is centralized.
- [ ] 32w. **Checkpoint commit (**inline**).** `git add -A && git commit -m "test: add SC-10 string check for severity format"`

### Item 6: SC-12 regression check

- [ ] 32x. **RED (**sub-agent**).** Run `uv run pytest test/` — confirm expected failures for SC-12 regression check (existing tests may fail due to Phase 2 changes).
- [ ] 32y. **GREEN (**sub-agent**).** Run `uv run pytest test/` — confirm zero regressions. Fix any test breakage from Phase 2 changes. **SC gate: this step FAILS if any existing test regresses.**
- [ ] 32z. **GREEN doublecheck (**inline**).** Run `uv run pytest test/` — confirm full regression PASS.
- [ ] 32aa. **REFACTOR (**inline**).** Clean up: verify baseline test count matches pre-change baseline, check no tests were silently skipped.
- [ ] 32ab. **Checkpoint commit (**inline**).** `git add -A && git commit -m "test: add SC-12 regression check"`

### Item 7: SC-13 anti-lobotomization audit

- [ ] 32ac. **RED (**sub-agent**).** Run anti-lobotomization audit — confirm expected failures for SC-13 (behavioral SCs may have been weakened).
- [ ] 32ad. **GREEN (**sub-agent**).** Complete SC-13 anti-lobotomization audit: verify no behavioral SC was weakened to lower type. **SC gate: this step FAILS if any behavioral SC was weakened.**
- [ ] 32ae. **GREEN doublecheck (**inline**).** Re-run anti-lobotomization audit — confirm PASS.
- [ ] 32af. **REFACTOR (**inline**).** Clean up: verify audit covers all behavioral SCs, check no SC was silently reclassified.
- [ ] 33. **Checkpoint commit (**inline**).** `git add -A && git commit -m "test: add SC-13 anti-lobotomization audit"`

#### Phase 02b VbC

- [ ] 33a. **VbC (**clean-room**).** Verify: all behavioral tests pass, full regression passes, anti-lobotomization audit passes. **→ SC-5, SC-6, SC-7, SC-8, SC-10, SC-12, SC-13** `evidence_type: behavioral`
- [ ] 33b. **Behavioral test evaluation (**clean-room**).** Run `uv run pytest test/test_phase2_edit_diff.py -v` — confirm PASS. **→ SC-5, SC-6, SC-7, SC-8, SC-10** `evidence_type: behavioral`
- [ ] 33c. **Regression check (**inline**).** Run `uv run pytest test/` — confirm zero regressions. **→ SC-12** `evidence_type: string`

**Concern transition:** Leaving Phase 2 behavioral tests → entering global post-phase. Phase 3 depends on Phase 2b's verified completion.
