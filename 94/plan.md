# Implementation Plan — [#94](https://github.com/michael-conrad/viewport-editor/issues/94) — Change default autosave from off to on

- **Spec:** [#94](https://github.com/michael-conrad/viewport-editor/issues/94)
- **Goal:** Change the default value of `autosave` from `False` to `True` across all code paths so that every viewport opened without an explicit `autosave` argument auto-flushes edits to disk.
- **Architecture:** Update three default values in `viewport.py` (dataclass field, `open()` parameter, `open_new()` parameter) and one fallback expression in `server.py`. Update two test assertions that check the old default. No structural changes — defaults only.
- **Files:**
  - `src/viewport_editor/viewport.py` — lines 46, 112, 401
  - `src/viewport_editor/server.py` — line 759
  - `test/test_phase1_server_viewport.py` — lines 138-150
  - `test/test_phase3_filenew_saveas.py` — lines 63-97

> **Compliance Requirement:** All steps and sub-steps in this document MUST be followed in order. Failure to comply with any step — including but not limited to verification gates, test phases, audit checkpoints, and review steps — will result in the feature branch being rejected and discarded, requiring a full rework from scratch and loss of all prior work. There is no valid reason to skip, compress, reorder, or omit any step. If a step appears redundant or unnecessary, follow it anyway — the cost of following an extra step is negligible compared to the cost of rework from a skipped step.

> **One-step-at-a-time protocol:** Each numbered step is exactly one sub-agent dispatch. The orchestrator completes step N, reports completion to chat, then proceeds to step N+1. Steps MUST NOT be combined, batched, or executed in parallel. The RED→GREEN transition is a zero-tolerance gate: the RED test's artifact output MUST be read and confirmed as FAILING before any GREEN implementation begins. If the RED test artifact is not read, or if it shows PASS when FAIL was expected, the phase is poisoned — all work in it MUST be discarded and the phase restarted from RED.

## Phase 1 — autosave-default-on

- **Concern:** Change default autosave from False to True across all code paths and update test assertions
- **Files affected:** `src/viewport_editor/viewport.py`, `src/viewport_editor/server.py`, `test/test_phase1_server_viewport.py`, `test/test_phase3_filenew_saveas.py`
- **SCs:** SC-1, SC-2, SC-3, SC-4, SC-5, SC-6
- **Dependencies:** None
- **Entry:** Plan approved, feature branch created on `dev`
- **Exit:** All 6 SCs verified PASS, branch committed and pushed

### Pre-RED Common

- [ ] 1. **Coherence gate (**clean-room**).** Verify spec SCs are coherent with the codebase — confirm `viewport.py` has `autosave: bool = False` at lines 46, 112, 401 and `server.py` has `autosave=autosave if autosave is not None else False` at line 759. **→ SC-1, SC-2, SC-3, SC-4, SC-5, SC-6**
- [ ] 2. **Pre-RED baseline (**clean-room**).** Run `uv run pytest test/ -k autosave -v` and record baseline PASS/FAIL state. **→ SC-4**

### Per-Item RED+green Chains

- [ ] 3. **RED: Update test assertions to expect `autosave: True` (**sub-agent**).**
  - [ ] 3.1. In `test/test_phase1_server_viewport.py:138-150`, rename `test_sc6_open_accepts_autosave_param_defaults_off` to `test_sc6_open_accepts_autosave_param_defaults_on` and change assertion from `autosave: False` to `autosave: True`.
  - [ ] 3.2. In `test/test_phase3_filenew_saveas.py:63-97`, change the SC-15 assertion from `autosave=False` to `autosave=True`.
  - [ ] 3.3. Run `uv run pytest test/test_phase1_server_viewport.py::test_sc6_open_accepts_autosave_param_defaults_on test/test_phase3_filenew_saveas.py -v` — confirm FAIL (tests expect `True` but code still returns `False`). **→ SC-4**
- [ ] 4. **Z3 check RED (**inline**).** `solve check` — verify RED step produced FAIL artifact. **→ SC-4**
- [ ] 5. **RED doublecheck (**clean-room**).** Read test output artifact — confirm the RED test assertion is correct (expects `True`, gets `False`). **→ SC-4**
- [ ] 6. **Z3 check RED doublecheck (**inline**).** `solve check` — verify RED doublecheck confirms FAIL. **→ SC-4**
- [ ] 7. **Post-RED enforcement (**clean-room**).** Verify no other test assertions reference `autosave: False` as a default — grep for `autosave.*False` in `test/` excluding explicit-param tests. **→ SC-4**
- [ ] 8. **Z3 check post-RED (**inline**).** `solve check` — verify post-RED enforcement passed. **→ SC-4**

- [ ] 9. **GREEN: Change defaults in `viewport.py` (**sub-agent**).**
  - [ ] 9.1. `ViewportEntry.autosave: bool = True` (line 46).
  - [ ] 9.2. `ViewportManager.open()` parameter default: `autosave: bool = True` (line 112).
  - [ ] 9.3. `ViewportManager.open_new()` → `autosave=True` (line 401). **→ SC-1, SC-2, SC-3**
- [ ] 10. **GREEN: Change fallback in `server.py` (**sub-agent**).**
  - [ ] 10.1. `_action_open()` fallback: `autosave=autosave if autosave is not None else True` (line 759). **→ SC-1, SC-2**
- [ ] 11. **Z3 check GREEN (**inline**).** `solve check` — verify GREEN changes applied. **→ SC-1, SC-2, SC-3**
- [ ] 12. **Post-GREEN enforcement (**clean-room**).** Run `uv run pytest test/ -k autosave -v` — confirm all autosave tests PASS. **→ SC-4**
- [ ] 13. **Z3 check post-GREEN (**inline**).** `solve check` — verify post-GREEN enforcement passed. **→ SC-4**
- [ ] 14. **Checkpoint tag create (**inline**).** Create git tag `<parent>/checkpoint/94/phase-1-autosave-default-on-<submodule>`. **→ SC-4**
- [ ] 15. **Checkpoint commit (**inline**).** `git add -A && git commit -m "checkpoint: phase-1-autosave-default-on"`. **→ SC-4**

### Structural Checks

- [ ] 16. **Structural checks (**clean-room**).** Verify:
  - [ ] 16.1. `grep 'autosave: bool = True' src/viewport_editor/viewport.py` — line 46 has `True`.
  - [ ] 16.2. `grep 'autosave: bool = True' src/viewport_editor/viewport.py` — line 112 has `True`.
  - [ ] 16.3. `grep 'autosave=True' src/viewport_editor/viewport.py` — line 401 has `True`.
  - [ ] 16.4. `grep 'autosave if autosave is not None else True' src/viewport_editor/server.py` — line 759 has `True`.
  - [ ] 16.5. `grep 'autosave: True' test/test_phase1_server_viewport.py` — assertion updated.
  - [ ] 16.6. `grep 'autosave=True' test/test_phase3_filenew_saveas.py` — assertion updated. **→ SC-1, SC-2, SC-3, SC-4**
- [ ] 17. **GREEN doublecheck (**clean-room**).** Run `uv run pytest test/ -k autosave -v` — confirm all PASS. **→ SC-4**

### Verification

- [ ] 18. **VbC: Behavioral verification (**clean-room**).**
  - [ ] 18.1. SC-1: `opencode-cli run` → open viewport without autosave param, verify response contains `autosave: True`.
  - [ ] 18.2. SC-2: `opencode-cli run` → open viewport with `autosave: False`, verify response contains `autosave: False`.
  - [ ] 18.3. SC-3: `opencode-cli run` → `file:new`, verify response shows `autosave: True`.
  - [ ] 18.4. SC-5: `uv run pytest test/ -k test_autosave_on_diff_show_empty -v` — PASS.
  - [ ] 18.5. SC-6: `opencode-cli run` → open viewport, edit, close — verify file content changed on disk. **→ SC-1, SC-2, SC-3, SC-5, SC-6**
- [ ] 19. **Adversarial audit (**clean-room**).** Dispatch adversarial auditor to audit plan fidelity and concern separation. **→ SC-1, SC-2, SC-3, SC-4, SC-5, SC-6**
- [ ] 20. **Cross-validate (**clean-room**).** Cross-validate VbC evidence against SC evidence type requirements — all 6 SCs are `behavioral`, verify behavioral evidence exists for each. **→ SC-1, SC-2, SC-3, SC-4, SC-5, SC-6**
- [ ] 21. **Regression check (**clean-room**).** Run full test suite `uv run pytest test/ -v` — confirm no regressions. **→ SC-4**

### Review Prep

- [ ] 22. **Review prep (**clean-room**).** Run `git-workflow --task review-prep` — verify branch is ready for PR. **→ SC-4**
- [ ] 23. **Executive summary (**inline**).** Report completion: summary, outcome, blockers, URL, byline. **→ All**

#### Phase 1 VbC

- [ ] 24. **VbC (**clean-room**).** Verify all 6 SCs PASS with behavioral evidence artifacts in `./tmp/behavioral-evidence-*/`. **→ SC-1, SC-2, SC-3, SC-4, SC-5, SC-6**

> **Compliance Requirement:** All steps and sub-steps in this document MUST be followed in order. Failure to comply with any step — including but not limited to verification gates, test phases, audit checkpoints, and review steps — will result in the feature branch being rejected and discarded, requiring a full rework from scratch and loss of all prior work. There is no valid reason to skip, compress, reorder, or omit any step. If a step appears redundant or unnecessary, follow it anyway — the cost of following an extra step is negligible compared to the cost of rework from a skipped step.

> **One step at a time protocol:** Each numbered step is a single unit of work. The orchestrator completes exactly one step, reports the result, and proceeds to the next step without asking for permission. "Combining steps" means performing work that spans multiple plan step numbers in a single operation — regardless of how many tool calls, dispatches, or response turns it takes. The self-check is: "does the work I just completed correspond to exactly one plan step number?" If the work touches files or concerns from step N and step N+1, it is combined. The RED→GREEN transition is a zero-tolerance gate: the RED test MUST be verified as FAILING (by reading its artifact output) before any GREEN implementation begins. Skipping this verification invalidates the entire phase and all work in it.
>
> **Self-remediation protocol:** If the orchestrator combines steps or skips a gate, it MUST self-remediate by reverting only the work belonging to the incorrectly-combined step and re-dispatching from the failed step. Do NOT revert work from correctly-executed prior steps. No halting, no asking for permission, no "should I?" — the answer is always revert the offending step and re-dispatch.

## Exit Criteria

- **C1.** `ViewportEntry.autosave` defaults to `True` in `viewport.py:46`
- **C2.** `ViewportManager.open()` defaults `autosave=True` in `viewport.py:112`
- **C3.** `ViewportManager.open_new()` passes `autosave=True` in `viewport.py:401`
- **C4.** `_action_open()` fallback resolves to `True` in `server.py:759`
- **C5.** Test `test_sc6_open_accepts_autosave_param_defaults_on` asserts `autosave: True` and PASSes
- **C6.** Test SC-15 in `test_phase3_filenew_saveas.py` asserts `autosave=True` and PASSes
- **C7.** All autosave tests pass: `uv run pytest test/ -k autosave -v`
- **C8.** Behavioral tests SC-1 through SC-6 all PASS with behavioral evidence artifacts
- **C9.** Full test suite passes with no regressions
