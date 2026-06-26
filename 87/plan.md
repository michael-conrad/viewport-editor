# Implementation Plan — [#87](https://github.com/michael-conrad/viewport-editor/issues/87) — Allow Absolute Paths

- **Goal:** Replace `_resolve_path()` with a simple two-branch resolver using `os.path.realpath()`, allowing absolute paths unconditionally while keeping `AbsolutePathError` and `PathEscapeError` for backward compatibility.
- **Architecture:** Single-function replacement in `file_ops.py`. No changes to server.py, viewport.py, or buffer.py — all path resolution routes through `_resolve_path()`.
- **Files:**
  - `src/viewport_editor/file_ops.py` — Replace `_resolve_path()` body
  - `src/viewport_editor/exceptions.py` — No changes (keep both exception classes)
  - `test/test_phase1_server_viewport.py` — Update `test_sc4_absolute_paths_rejected` for new behavior
  - `test/viewport-editor/65/test_phase2_sc6_absolute_path_skip.py` — Update `test_sc6_absolute_path_skip` for new behavior

> **Compliance Requirement:** All steps and sub-steps in this document MUST be followed in order. Failure to comply with any step — including but not limited to verification gates, test phases, audit checkpoints, and review steps — will result in the feature branch being rejected and discarded, requiring a full rework from scratch and loss of all prior work. There is no valid reason to skip, compress, reorder, or omit any step. If a step appears redundant or unnecessary, follow it anyway — the cost of following an extra step is negligible compared to the cost of rework from a skipped step.

> **One-step-at-a-time protocol:** Each numbered step is exactly one sub-agent dispatch. The orchestrator completes step N, reports completion to chat, then proceeds to step N+1. Steps MUST NOT be combined, batched, or executed in parallel. The RED→GREEN transition is a zero-tolerance gate: the RED test's artifact output MUST be read and confirmed as FAILING before any GREEN implementation begins. If the RED test artifact is not read, or if it shows PASS when FAIL was expected, the phase is poisoned — all work in it MUST be discarded and the phase restarted from RED.

## Phase 1 — Replace `_resolve_path()` in `file_ops.py`

- **Concern:** Replace the current `_resolve_path()` with a two-branch resolver using `os.path.realpath()`. Remove `AbsolutePathError` and `PathEscapeError` from the function body. Remove the imports of those exceptions from `file_ops.py`.
- **Files:** `src/viewport_editor/file_ops.py`
- **SCs:** SC-1, SC-2
- **Dependencies:** None (P1 is the root phase)
- **Entry:** Phase 1 begins
- **Exit:** `_resolve_path()` replaced, imports cleaned, all callers still compile

- [ ] 1. **Coherence gate (**clean-room**).** Verify the spec is internally consistent: SC-1 and SC-2 are behavioral, SC-3 and SC-4 are structural. Confirm the change scope is limited to `_resolve_path()` — no callers need modification. **→ SC-1, SC-2**
- [ ] 2. **Pre-RED baseline (**clean-room**).** Read `src/viewport_editor/file_ops.py` and `src/viewport_editor/exceptions.py`. Confirm current `_resolve_path()` raises `AbsolutePathError` on absolute paths and `PathEscapeError` on escape attempts. Record baseline in `./tmp/behavioral-evidence-SC-1-baseline.log`. **→ SC-1, SC-2**
- [ ] 3. **RED phase — behavioral test for SC-1 (**sub-agent**).** Write a test that passes an absolute path outside project root to `_resolve_path()` and asserts it resolves correctly. The test MUST FAIL because the current implementation raises `AbsolutePathError`. **→ SC-1**
- [ ] 4. **Z3 check — RED (**inline**).** `solve check` — verify RED test artifact exists and shows FAIL status. **→ SC-1**
- [ ] 5. **RED doublecheck (**clean-room**).** Read the RED test artifact output. Confirm the test FAILS as expected (raises `AbsolutePathError`). **→ SC-1**
- [ ] 6. **Z3 check — RED doublecheck (**inline**).** `solve check` — verify doublecheck confirms FAIL. **→ SC-1**
- [ ] 7. **Post-RED enforcement (**clean-room**).** Verify no GREEN code has been written yet. Only the RED test file exists. **→ SC-1**
- [ ] 8. **Z3 check — post-RED (**inline**).** `solve check` — verify post-RED enforcement PASS. **→ SC-1**
- [ ] 9. **GREEN phase — implement `_resolve_path()` (**sub-agent**).** Modify `_resolve_path()` so that:
  - When `file_path` starts with `/`, the function resolves it directly via `os.path.realpath()` without raising an error
  - When `file_path` is relative, the function joins it with `project_root` then resolves via `os.path.realpath()`
  - No `AbsolutePathError` or `PathEscapeError` is raised for any path
  - The import line in `file_ops.py` no longer references `AbsolutePathError` or `PathEscapeError`
  - The function returns `Tuple[str, str]` **→ SC-1, SC-2**
- [ ] 10. **Z3 check — GREEN (**inline**).** `solve check` — verify GREEN implementation artifact exists. **→ SC-1, SC-2**
- [ ] 11. **Post-GREEN enforcement (**clean-room**).** Read the modified `_resolve_path()`. Verify:
  - No `AbsolutePathError` or `PathEscapeError` raised
  - `os.path.realpath()` used for both branches
  - Return type is `Tuple[str, str]`
  - Import line no longer references `AbsolutePathError, PathEscapeError` **→ SC-1, SC-2**
- [ ] 12. **Z3 check — post-GREEN (**inline**).** `solve check` — verify post-GREEN enforcement PASS. **→ SC-1, SC-2**
- [ ] 13. **Checkpoint tag create (**inline**).** Create git tag: `viewport-editor/checkpoint/87/phase-1-viewport-editor`. **→ All**
- [ ] 14. **Checkpoint commit (**inline**).** `git add src/viewport_editor/file_ops.py && git commit -m "P1: replace _resolve_path() with two-branch realpath resolver"`. **→ All**
- [ ] 15. **Structural checks (**clean-room**).** Verify:
  - `_resolve_path()` exists in `file_ops.py`
  - No `AbsolutePathError` or `PathEscapeError` references remain in `file_ops.py`
  - All callers (`create_new_file`, `save_as_file`, `flush_entry`, `discard_buffer_changes`, `check_conflict`, `delete_file`) still call `_resolve_path()` with correct signature **→ SC-1, SC-2**
- [ ] 16. **GREEN doublecheck (**clean-room**).** Run the RED test from step 3. It MUST now PASS. Read the test output to confirm. **→ SC-1**
- [ ] 17. **GREEN VbC (**clean-room**).** Verify SC-1 and SC-2 against the implementation:
  - SC-1: Pass absolute path outside project root — resolves correctly
  - SC-2: Pass relative path — resolves against project_root **→ SC-1, SC-2**
- [ ] 18. **Adversarial audit — plan fidelity (**sub-agent**).** Dispatch adversarial auditor to verify the implementation matches the plan. **→ All**
- [ ] 19. **Cross-validate (**sub-agent**).** Dispatch second-family auditor to cross-validate the plan-fidelity verdict. **→ All**
- [ ] 20. **Regression check (**clean-room**).** Run `uv run pytest test/ -x` to confirm no existing tests break. **→ All**

#### Phase 1 VbC

- [ ] 21. **VbC (**clean-room**).** Verify all Phase 1 SCs (SC-1, SC-2) pass with behavioral evidence. Collect evidence artifacts into `./tmp/behavioral-evidence-SC-1.log` and `./tmp/behavioral-evidence-SC-2.log`. **→ SC-1, SC-2**

**Concern transition:** Leaving `_resolve_path()` replacement → entering behavioral test updates. Phase 2 depends on Phase 1's new `_resolve_path()` behavior.

## Phase 2 — Update Behavioral Tests

- **Concern:** Update existing tests in `test/test_phase1_server_viewport.py` and `test/viewport-editor/65/test_phase2_sc6_absolute_path_skip.py` to reflect the new `_resolve_path()` behavior. Remove tests that assert `AbsolutePathError` or `PathEscapeError` from `_resolve_path()`. Add tests for absolute path resolution.
- **Files:** `test/test_phase1_server_viewport.py`, `test/viewport-editor/65/test_phase2_sc6_absolute_path_skip.py`
- **SCs:** SC-1, SC-2
- **Dependencies:** before(P1, P2) — Phase 1 must be complete
- **Entry:** Phase 1 checkpoint committed
- **Exit:** All tests pass, behavioral evidence collected

- [ ] 22. **Pre-RED baseline (**clean-room**).** Read `test/test_phase1_server_viewport.py` and `test/viewport-editor/65/test_phase2_sc6_absolute_path_skip.py`. Identify all tests that assert `AbsolutePathError` or `PathEscapeError` from `_resolve_path()`. Record baseline in `./tmp/behavioral-evidence-P2-baseline.log`. **→ SC-1, SC-2**
- [ ] 23. **RED phase — behavioral test for SC-2 (**sub-agent**).** Write a test that passes a relative path and asserts it resolves against `project_root`. The test MUST FAIL because existing tests may not cover this exact assertion. **→ SC-2**
- [ ] 24. **Z3 check — RED (**inline**).** `solve check` — verify RED test artifact exists and shows FAIL status. **→ SC-2**
- [ ] 25. **RED doublecheck (**clean-room**).** Read the RED test artifact output. Confirm the test FAILS as expected. **→ SC-2**
- [ ] 26. **Z3 check — RED doublecheck (**inline**).** `solve check` — verify doublecheck confirms FAIL. **→ SC-2**
- [ ] 27. **Post-RED enforcement (**clean-room**).** Verify no GREEN code has been written yet. **→ SC-2**
- [ ] 28. **Z3 check — post-RED (**inline**).** `solve check` — verify post-RED enforcement PASS. **→ SC-2**
- [ ] 29. **GREEN phase — update tests (**sub-agent**).** In `test/test_phase1_server_viewport.py` and `test/viewport-editor/65/test_phase2_sc6_absolute_path_skip.py`:
  - Remove tests that assert `AbsolutePathError` from `_resolve_path()`
  - Remove tests that assert `PathEscapeError` from `_resolve_path()`
  - Add test: absolute path outside project root resolves correctly (SC-1)
  - Add test: relative path resolves against project_root (SC-2)
  - Keep tests for `AbsolutePathError` and `PathEscapeError` if they test the exception classes directly (not via `_resolve_path()`) **→ SC-1, SC-2**
- [ ] 30. **Z3 check — GREEN (**inline**).** `solve check` — verify GREEN implementation artifact exists. **→ SC-1, SC-2**
- [ ] 31. **Post-GREEN enforcement (**clean-room**).** Read the modified test file. Verify:
  - No tests assert `AbsolutePathError` or `PathEscapeError` from `_resolve_path()`
  - New tests cover SC-1 and SC-2
  - Test file is syntactically valid Python **→ SC-1, SC-2**
- [ ] 32. **Z3 check — post-GREEN (**inline**).** `solve check` — verify post-GREEN enforcement PASS. **→ SC-1, SC-2**
- [ ] 33. **Checkpoint tag create (**inline**).** Create git tag: `viewport-editor/checkpoint/87/phase-2-viewport-editor`. **→ All**
- [ ] 34. **Checkpoint commit (**inline**).** `git add test/test_phase1_server_viewport.py test/viewport-editor/65/test_phase2_sc6_absolute_path_skip.py && git commit -m "P2: update tests for new _resolve_path() behavior"`. **→ All**
- [ ] 35. **Structural checks (**clean-room**).** Verify:
  - `test/test_phase1_server_viewport.py` has tests for absolute path resolution
  - `test/test_phase1_server_viewport.py` has tests for relative path resolution
  - No tests reference `AbsolutePathError` or `PathEscapeError` in the context of `_resolve_path()` **→ SC-1, SC-2**
- [ ] 36. **GREEN doublecheck (**clean-room**).** Run `uv run pytest test/test_phase1_server_viewport.py test/viewport-editor/65/test_phase2_sc6_absolute_path_skip.py -x`. All tests MUST PASS. Read the output to confirm. **→ SC-1, SC-2**
- [ ] 37. **GREEN VbC (**clean-room**).** Verify SC-1 and SC-2 with behavioral evidence:
  - Run test for absolute path outside project root → PASS
  - Run test for relative path resolution → PASS **→ SC-1, SC-2**
- [ ] 38. **Adversarial audit — plan fidelity (**sub-agent**).** Dispatch adversarial auditor to verify Phase 2 matches the plan. **→ All**
- [ ] 39. **Cross-validate (**sub-agent**).** Dispatch second-family auditor to cross-validate. **→ All**
- [ ] 40. **Regression check (**clean-room**).** Run `uv run pytest test/ -x` to confirm all tests pass. **→ All**

#### Phase 2 VbC

- [ ] 41. **VbC (**clean-room**).** Verify all Phase 2 SCs (SC-1, SC-2) pass with behavioral evidence. Collect evidence into `./tmp/behavioral-evidence-P2.log`. **→ SC-1, SC-2**

**Concern transition:** Leaving behavioral test updates → entering backward compatibility verification. Phase 3 is independent of Phase 1 and Phase 2.

## Phase 3 — Backward Compatibility Verification (Exception Classes)

- **Concern:** Verify that `AbsolutePathError` and `PathEscapeError` remain importable and usable. No code changes needed — this is a verification-only phase.
- **Files:** `src/viewport_editor/exceptions.py`
- **SCs:** SC-3, SC-4
- **Dependencies:** None (P3 is independent)
- **Entry:** Phase 2 checkpoint committed
- **Exit:** Both exception classes confirmed importable, structural evidence collected

- [ ] 42. **Pre-RED baseline (**clean-room**).** Read `src/viewport_editor/exceptions.py`. Confirm both `AbsolutePathError` and `PathEscapeError` classes exist with their original definitions. Record baseline in `./tmp/behavioral-evidence-P3-baseline.log`. **→ SC-3, SC-4**
- [ ] 43. **RED phase — structural test for SC-3 (**sub-agent**).** Write a test that imports `AbsolutePathError` from `viewport_editor.exceptions` and asserts it is a class. The test MUST FAIL if the class was removed. **→ SC-3**
- [ ] 44. **Z3 check — RED (**inline**).** `solve check` — verify RED test artifact exists. **→ SC-3**
- [ ] 45. **RED doublecheck (**clean-room**).** Read the RED test artifact. Confirm the test FAILS (class may have been removed). **→ SC-3**
- [ ] 46. **Z3 check — RED doublecheck (**inline**).** `solve check` — verify doublecheck confirms FAIL. **→ SC-3**
- [ ] 47. **Post-RED enforcement (**clean-room**).** Verify no GREEN code has been written yet. **→ SC-3, SC-4**
- [ ] 48. **Z3 check — post-RED (**inline**).** `solve check` — verify post-RED enforcement PASS. **→ SC-3, SC-4**
- [ ] 49. **GREEN phase — verify exception classes exist (**sub-agent**).** Read `src/viewport_editor/exceptions.py`. Confirm both classes are present. No code changes needed — this is a verification-only GREEN. **→ SC-3, SC-4**
- [ ] 50. **Z3 check — GREEN (**inline**).** `solve check` — verify GREEN verification artifact exists. **→ SC-3, SC-4**
- [ ] 51. **Post-GREEN enforcement (**clean-room**).** Read `exceptions.py`. Verify:
  - `AbsolutePathError` class definition is present
  - `PathEscapeError` class definition is present
  - Both inherit from `ViewportError`
  - No modifications to `exceptions.py` **→ SC-3, SC-4**
- [ ] 52. **Z3 check — post-GREEN (**inline**).** `solve check` — verify post-GREEN enforcement PASS. **→ SC-3, SC-4**
- [ ] 53. **Checkpoint tag create (**inline**).** Create git tag: `viewport-editor/checkpoint/87/phase-3-viewport-editor`. **→ All**
- [ ] 54. **Checkpoint commit (**inline**).** `git add -A && git commit -m "P3: backward compatibility verification for exception classes"`. **→ All**
- [ ] 55. **Structural checks (**clean-room**).** Verify:
  - `AbsolutePathError` is importable from `viewport_editor.exceptions`
  - `PathEscapeError` is importable from `viewport_editor.exceptions`
  - Both classes have their original `__init__` signatures **→ SC-3, SC-4**
- [ ] 56. **GREEN doublecheck (**clean-room**).** Run the RED test from step 43. It MUST now PASS (classes exist). Read the output to confirm. **→ SC-3**
- [ ] 57. **GREEN VbC (**clean-room**).** Verify SC-3 and SC-4 with structural evidence:
  - SC-3: `AbsolutePathError` importable from `exceptions.py`
  - SC-4: `PathEscapeError` importable from `exceptions.py` **→ SC-3, SC-4**
- [ ] 58. **Adversarial audit — plan fidelity (**sub-agent**).** Dispatch adversarial auditor to verify Phase 3 matches the plan. **→ All**
- [ ] 59. **Cross-validate (**sub-agent**).** Dispatch second-family auditor to cross-validate. **→ All**
- [ ] 60. **Regression check (**clean-room**).** Run `uv run pytest test/ -x` to confirm all tests pass. **→ All**

#### Phase 3 VbC

- [ ] 61. **VbC (**clean-room**).** Verify all Phase 3 SCs (SC-3, SC-4) pass with structural evidence. Collect evidence into `./tmp/behavioral-evidence-P3.log`. **→ SC-3, SC-4**

### Global Post-Steps

- [ ] 62. **Collect behavioral evidence (**clean-room**).** Gather all evidence artifacts from `./tmp/behavioral-evidence-*/` into `./tmp/87/artifacts/`. **→ All**
- [ ] 63. **Adversarial audit — concern separation (**sub-agent**).** Dispatch adversarial auditor to verify each phase addresses exactly one concern with no overlap. **→ All**
- [ ] 64. **Cross-validate (**sub-agent**).** Dispatch second-family auditor to cross-validate concern-separation verdict. **→ All**
- [ ] 65. **Regression check (**clean-room**).** Run `uv run pytest test/ -x` to confirm full test suite passes. **→ All**
- [ ] 66. **Review prep (**sub-agent**).** Prepare PR body, verify compare URL, ensure all SCs are documented. **→ All**
- [ ] 67. **Executive summary (**inline**).** Report completion: all 4 SCs verified, 3 phases complete, evidence artifacts collected. **→ All**

> **Compliance Requirement:** All steps and sub-steps in this document MUST be followed in order. Failure to comply with any step — including but not limited to verification gates, test phases, audit checkpoints, and review steps — will result in the feature branch being rejected and discarded, requiring a full rework from scratch and loss of all prior work. There is no valid reason to skip, compress, reorder, or omit any step. If a step appears redundant or unnecessary, follow it anyway — the cost of following an extra step is negligible compared to the cost of rework from a skipped step.

> **One step at a time protocol:** Each numbered step is a single unit of work. The orchestrator completes exactly one step, reports the result, and proceeds to the next step without asking for permission. "Combining steps" means performing work that spans multiple plan step numbers in a single operation — regardless of how many tool calls, dispatches, or response turns it takes. The self-check is: "does the work I just completed correspond to exactly one plan step number?" If the work touches files or concerns from step N and step N+1, it is combined. The RED→GREEN transition is a zero-tolerance gate: the RED test MUST be verified as FAILING (by reading its artifact output) before any GREEN implementation begins. Skipping this verification invalidates the entire phase and all work in it.
>
> **Self-remediation protocol:** If the orchestrator combines steps or skips a gate, it MUST self-remediate by reverting only the work belonging to the incorrectly-combined step and re-dispatching from the failed step. Do NOT revert work from correctly-executed prior steps. No halting, no asking for permission, no "should I?" — the answer is always revert the offending step and re-dispatch.

## Exit Criteria

- **C1.** `_resolve_path()` in `file_ops.py` uses two-branch `os.path.realpath()` — absolute paths resolve directly, relative paths resolve against `project_root`
- **C2.** No `AbsolutePathError` or `PathEscapeError` raised from `_resolve_path()`
- **C3.** No imports of `AbsolutePathError` or `PathEscapeError` remain in `file_ops.py`
- **C4.** `AbsolutePathError` class is importable from `exceptions.py` (SC-3)
- **C5.** `PathEscapeError` class is importable from `exceptions.py` (SC-4)
- **C6.** Behavioral test for absolute path outside project root passes (SC-1)
- **C7.** Behavioral test for relative path resolution passes (SC-2)
- **C8.** Full test suite passes (`uv run pytest test/ -x`)
- **C9.** All checkpoint tags created and committed
- **C10.** All evidence artifacts collected in `./tmp/87/artifacts/`
