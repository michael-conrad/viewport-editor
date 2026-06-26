# Implementation Plan — MCP-Level AGENTS.md Injection for Sibling File Operations

**Issue:** https://github.com/michael-conrad/viewport-editor/issues/65
**Spec:** `.issues/65/spec.md`
**Branch:** `feature/65-agents-injection`

---

## Phase 1: Core Detection + Session Tracking

**Concern:** Implement `_find_sibling_agents_md()` detection, `injected_agents_files` session tracking, and `_inject_agents_notice()` helper.
**Files:** `src/viewport_editor/file_ops.py`, `src/viewport_editor/session.py`, `src/viewport_editor/server.py`
**SCs covered:** SC-5, SC-12

- [ ] 1. **SC-COHERENCE-GATE — orchestrator routes to pre-analysis**: Verify spec SCs for Phase 1 are internally consistent and complete. Confirm SC-5 (structural: `injected_agents_files` on Session) and SC-12 (structural: `os.path.realpath()` usage) have clear, unambiguous PASS/FAIL definitions. Check that SC-5 foundational for Phase 2 injection logic — Session field must exist before any tool wiring can use it.
- [ ] 2. **PRE-RED-BASELINE — orchestrator routes to exploration**: Run `uv run pytest test/` full test suite. Confirm all existing tests PASS before introducing changes. Record baseline test count and any pre-existing failures for later regression comparison.
- [ ] 3. **RED-PHASE — orchestrator routes to RED sub-agent**:
  - **Test file (SC-5):** `test/viewport-editor/65/test_session_injected_agents_field.py` — structural assertion: `Session` dataclass has `injected_agents_files: set[str]`
  - **Test file (SC-12):** `test/viewport-editor/65/test_find_sibling_agents_realpath.py` — structural assertion: `_find_sibling_agents_md` calls `os.path.realpath()` on both `file_path` and `project_root`
  - Write tests, execute them, confirm FAIL (exit non-zero) since implementation doesn't exist yet
  - Capture output to `./tmp/65/artifacts/phase1-test-output.log`
- [ ] 4. **RED-DOUBLECHECK — orchestrator inline**: Confirm RED evidence artifact `./tmp/65/artifacts/phase1-test-output.log` exists and shows non-zero exit code for both test runs.
- [ ] 5. **GREEN-PHASE — orchestrator routes to GREEN sub-agent (clean-room, receives spec + test paths only)**:
  - Implement `_find_sibling_agents_md()` in `src/viewport_editor/file_ops.py`:
    - `os.path.realpath()` on `file_path` and `project_root`
    - Nearest-ancestor walk-up from file directory to project root
    - Self-injection guard (skip if resolved path IS the AGENTS.md)
    - Returns `str | None`
    - Error handling: `try/except` for unreadable AGENTS.md (permissions, encoding) — returns `None`
  - Add `injected_agents_files: set[str]` to `Session` dataclass in `src/viewport_editor/session.py`
  - Implement `_inject_agents_notice()` in `src/viewport_editor/server.py`:
    - Calls `_find_sibling_agents_md`, checks dedup against `session.injected_agents_files`
    - Builds `<system-reminder>` block in built-in format
    - Appends to response text before return
    - Records injected path in session
  - Run tests, confirm PASS (exit 0)
  - Capture output to `./tmp/65/artifacts/phase1-test-output.log`
- [ ] 6. **CHECKPOINT-COMMIT — orchestrator inline**: `git commit -m "phase 1 checkpoint"` with `_find_sibling_agents_md`, `injected_agents_files`, `_inject_agents_notice` implementation plus structural test files.
- [ ] 7. **STRUCTURAL-CHECKS — orchestrator routes to structural sub-agent**: `uvx ruff check --fix src/ test/`, `uvx ruff format src/ test/`, `uvx pyright src/`. Fix any lint/type errors from new code.
- [ ] 8. **GREEN-DOUBLECHECK — orchestrator inline**: Confirm GREEN evidence artifact `./tmp/65/artifacts/phase1-test-output.log` shows exit 0 for both structural tests. Confirm both `injected_agents_files` field and `os.path.realpath()` calls are present in source.
- [ ] 9. **GREEN-VBC — orchestrator routes to VbC sub-agent**: Verification-before-completion against Phase 1 SCs (SC-5, SC-12). Confirm structural evidence artifacts match SC criteria.
- [ ] 10. **ADVERSARIAL-AUDIT — orchestrator routes to resolve-models**: Dispatches 2 adversarial auditors for plan-fidelity + concern-separation against Phase 1 deliverables.
- [ ] 11. **CROSS-VALIDATE — orchestrator inline**: Verify dual-auditor consensus on all Phase 1 SCs. If DISAGREE or FAIL, remediate and re-verify before proceeding.
- [ ] 12. **REGRESSION-CHECK — orchestrator routes to regression sub-agent**: Run `uv run pytest test/` full test suite. Confirm nothing previously passing is now broken. Compare against PRE-RED-BASELINE count.
- [ ] 13. **REVIEW-PREP — orchestrator routes to review-prep sub-agent**: Compare URL (verified from session-init `github.html_url`), PR body draft for Phase 1 deliverables.
- [ ] 14. **EXEC-SUMMARY — orchestrator inline**: Read all sub-agent result contracts from Phase 1. Produce phase completion report with SC status (SC-5: structural PASS, SC-12: structural PASS), artifact paths, byline.

### Inter-Phase Handoff (Phase 1 → Phase 2)

- Update Z3 state file: solve state update with Phase 1 gate states (all 14 gates with PASS/FAIL)
- Run solve check: confirm Phase 1 dependency contract still SAT
- Verify checkpoint tag exists for Phase 1
- Append lifecycle manifest event for Phase 1 completion

---

## Phase 2: Tool Integration

**Concern:** Wire AGENTS.md injection into `viewport:open` handler and composite `read_file` handler. Handle format matching, dedup integration, self-injection guard, and project-root boundary enforcement.
**Files:** `src/viewport_editor/server.py`
**SCs covered:** SC-1, SC-2, SC-3, SC-4, SC-6, SC-7, SC-8, SC-11

- [ ] 1. **SC-COHERENCE-GATE — orchestrator routes to pre-analysis**: Verify 8 Phase 2 SCs are internally consistent. SC-1 (behavioral: viewport:open injection), SC-2 (behavioral: dedup), SC-3 (behavioral: root fallback), SC-4 (behavioral: nearest-ancestor), SC-6 (behavioral: absolute-path skip), SC-7 (behavioral: unreadable skip), SC-8 (behavioral: self-injection guard), SC-11 (string: format match). Confirm SC-1 through SC-4 all depend on Phase 1's `_inject_agents_notice` — Phase 1 dependency must be verified SAT.
- [ ] 2. **PRE-RED-BASELINE — orchestrator routes to exploration**: Run `uv run pytest test/` full test suite. Confirm all Phase 1 changes did not introduce regressions.
- [ ] 3. **RED-PHASE — orchestrator routes to RED sub-agent**:
  - **Test file (SC-1):** `test/viewport-editor/65/test_viewport_open_injection.py` — behavioral test: open a file under a directory with AGENTS.md → response contains `<system-reminder>` with AGENTS.md content
  - **Test file (SC-2):** `test/viewport-editor/65/test_dedup_same_session.py` — behavioral test: open two files under same AGENTS.md → only first response has injection
  - **Test file (SC-3):** `test/viewport-editor/65/test_root_agents_fallback.py` — behavioral test: open file in dir without AGENTS.md but with one at project root → root AGENTS.md injected
  - **Test file (SC-4):** `test/viewport-editor/65/test_nearest_ancestor_wins.py` — behavioral test: file under `a/b/AGENTS.md` where `a/AGENTS.md` also exists → `a/b/AGENTS.md` injected
  - **Test file (SC-6):** `test/viewport-editor/65/test_absolute_path_skip.py` — behavioral test: open `/etc/passwd` → no `<system-reminder>` in response
  - **Test file (SC-7):** `test/viewport-editor/65/test_unreadable_agents_skip.py` — behavioral test: AGENTS.md with 000 permissions → injection silently skipped
  - **Test file (SC-8):** `test/viewport-editor/65/test_self_injection_guard.py` — behavioral test: open `AGENTS.md` itself → no self-injection
  - **Test file (SC-11):** `test/viewport-editor/65/test_injection_format.py` — string test: grep response for `<system-reminder>\nInstructions from:` pattern
  - Write all test files, execute them, confirm FAIL (exit non-zero)
  - Capture output to `./tmp/65/artifacts/phase2-test-output.log`
- [ ] 4. **RED-DOUBLECHECK — orchestrator inline**: Confirm RED evidence artifact `./tmp/65/artifacts/phase2-test-output.log` exists and shows non-zero exit code.
- [ ] 5. **GREEN-PHASE — orchestrator routes to GREEN sub-agent (clean-room, receives spec + test paths only)**:
  - Wire `_inject_agents_notice()` into `_action_open()` handler in `src/viewport_editor/server.py` — processes response text through injection before return
  - Wire `_inject_agents_notice()` into composite `read_file` handler in `src/viewport_editor/server.py` — delegates to same helper, same Session dedup
  - Verify injection format: `<system-reminder>\nInstructions from: {path}\n{content}\n</system-reminder>` appended to single `content[0].text` string (no separate content array items)
  - Verify self-injection guard in `_find_sibling_agents_md` already catches file_path == AGENTS.md from Phase 1
  - Run all 8 Phase 2 tests, confirm PASS (exit 0)
  - Capture output to `./tmp/65/artifacts/phase2-test-output.log`
- [ ] 6. **CHECKPOINT-COMMIT — orchestrator inline**: `git commit -m "phase 2 checkpoint"` with tool integration changes plus all 8 behavioral + string test files.
- [ ] 7. **STRUCTURAL-CHECKS — orchestrator routes to structural sub-agent**: `uvx ruff check --fix src/ test/`, `uvx ruff format src/ test/`, `uvx pyright src/`. Fix any lint/type errors from new code.
- [ ] 8. **GREEN-DOUBLECHECK — orchestrator inline**: Confirm GREEN evidence artifact `./tmp/65/artifacts/phase2-test-output.log` shows exit 0 for all 8 test runs.
- [ ] 9. **GREEN-VBC — orchestrator routes to VbC sub-agent**: Verification-before-completion against Phase 2 SCs (SC-1 through SC-4, SC-6 through SC-8, SC-11). Confirm behavioral evidence artifacts exist for SC-1 through SC-8, string evidence for SC-11.
- [ ] 10. **ADVERSARIAL-AUDIT — orchestrator routes to resolve-models**: Dispatches 2 adversarial auditors for plan-fidelity + concern-separation against Phase 2 deliverables.
- [ ] 11. **CROSS-VALIDATE — orchestrator inline**: Verify dual-auditor consensus on all Phase 2 SCs. If DISAGREE or FAIL, remediate and re-verify.
- [ ] 12. **REGRESSION-CHECK — orchestrator routes to regression sub-agent**: Run `uv run pytest test/` full test suite. Confirm nothing previously passing is broken.
- [ ] 13. **REVIEW-PREP — orchestrator routes to review-prep sub-agent**: Compare URL (verified from session-init), PR body draft for Phase 2 deliverables.
- [ ] 14. **EXEC-SUMMARY — orchestrator inline**: Read all sub-agent result contracts. Produce phase completion report: SC-1 behavioral PASS, SC-2 behavioral PASS, SC-3 behavioral PASS, SC-4 behavioral PASS, SC-6 behavioral PASS, SC-7 behavioral PASS, SC-8 behavioral PASS, SC-11 string PASS. Artifact paths. Byline.

### Inter-Phase Handoff (Phase 2 → Phase 3)

- Update Z3 state file: solve state update with Phase 2 gate states
- Run solve check: confirm Phase 2 dependency contract still SAT
- Verify checkpoint tag exists for Phase 2
- Append lifecycle manifest event for Phase 2 completion

---

## Phase 3: Behavioral Tests

**Concern:** Write behavioral tests for composite `read_file` injection (SC-9), cross-tool dedup between `read_file` + `viewport:open` (SC-10), and the overall behavioral test mandate (SC-BEHAVIORAL-MANDATE).
**Files:** `test/viewport-editor/65/`
**SCs covered:** SC-9, SC-10

- [ ] 1. **SC-COHERENCE-GATE — orchestrator routes to pre-analysis**: Verify Phase 3 SCs. SC-9 (behavioral: composite read_file injection), SC-10 (behavioral: cross-tool dedup). Both depend on Phase 2 injection wiring being complete — confirm Phase 2 checkpoints SAT. Also verify behavioral test mandate SC (SC-BEHAVIORAL-MANDATE) is in spec and enforceable.
- [ ] 2. **PRE-RED-BASELINE — orchestrator routes to exploration**: Run `uv run pytest test/` full test suite. Confirm Phase 2 regressions are clean.
- [ ] 3. **RED-PHASE — orchestrator routes to RED sub-agent**:
  - **Test file (SC-9):** `test/viewport-editor/65/test_read_file_injection.py` — behavioral test: `read_file` on a file under AGENTS.md → response contains AGENTS.md content in `<system-reminder>`
  - **Test file (SC-10):** `test/viewport-editor/65/test_cross_tool_dedup.py` — behavioral test: `read_file` then `viewport:open` on files under same AGENTS.md → single injection total across both tools
  - Write tests, execute, confirm FAIL
  - Capture output to `./tmp/65/artifacts/phase3-test-output.log`
- [ ] 4. **RED-DOUBLECHECK — orchestrator inline**: Confirm RED evidence artifact exists and shows non-zero exit.
- [ ] 5. **GREEN-PHASE — orchestrator routes to GREEN sub-agent (clean-room)**: No implementation code changes needed in Phase 3 — injection wiring already done in Phase 2. Verify `read_file` composite delegates to the same `_inject_agents_notice` wired in Phase 2 via the `_action_open` path. Run both SC-9 and SC-10 tests, confirm PASS. If tests fail, inspect whether `read_file` has a separate path that bypasses `_inject_agents_notice` — remediate by wiring injection into that path.
  - Capture output to `./tmp/65/artifacts/phase3-test-output.log`
- [ ] 6. **CHECKPOINT-COMMIT — orchestrator inline**: `git commit -m "phase 3 checkpoint"` with behavioral test files.
- [ ] 7. **STRUCTURAL-CHECKS — orchestrator routes to structural sub-agent**: `uvx ruff check --fix src/ test/`, `uvx ruff format src/ test/`, `uvx pyright src/`. Verify no lint errors from test files.
- [ ] 8. **GREEN-DOUBLECHECK — orchestrator inline**: Confirm GREEN evidence artifact shows exit 0 for both SC-9 and SC-10 test runs.
- [ ] 9. **GREEN-VBC — orchestrator routes to VbC sub-agent**: Verification-before-completion against Phase 3 SCs (SC-9, SC-10). Confirm behavioral evidence artifacts exist.
- [ ] 10. **ADVERSARIAL-AUDIT — orchestrator routes to resolve-models**: Dispatches 2 adversarial auditors for plan-fidelity + concern-separation against Phase 3 deliverables.
- [ ] 11. **CROSS-VALIDATE — orchestrator inline**: Verify dual-auditor consensus on Phase 3 SCs.
- [ ] 12. **REGRESSION-CHECK — orchestrator routes to regression sub-agent**: Run `uv run pytest test/` full test suite. Confirm nothing previously passing is broken.
- [ ] 13. **REVIEW-PREP — orchestrator routes to review-prep sub-agent**: Compare URL (verified from session-init), PR body draft for full issue deliverable.
- [ ] 14. **EXEC-SUMMARY — orchestrator inline**: Read all sub-agent result contracts. Produce phase completion report: SC-9 behavioral PASS, SC-10 behavioral PASS. Artifact paths. Byline.

### Inter-Phase Handoff (Phase 3 → Post-All-Phases Sweep)

- Update Z3 state file: solve state update with Phase 3 gate states (all PASS)
- Run solve check: confirm full dependency contract SAT
- Verify checkpoint tag exists for Phase 3
- Append lifecycle manifest event for Phase 3 completion

---

## Post-All-Phases Sweep

- [ ] **FINISHING CHECKLIST — orchestrator routes to finishing sub-agent**: Verify `git status` clean, run `uvx ruff check --fix src/ test/` and `uvx ruff format src/ test/` and `uvx pyright src/` from scratch across entire project, `uv run coverage run -m pytest test/` coverage sweep. Confirm all SCs PASS — no unverified SCs remain.
- [ ] **PR CREATION — orchestrator routes to git-workflow pr-creation**: Create PR via `github_create_pull_request`, extract `html_url` from API response. PR body includes: Summary → Outcome → SC verification table → compare URL. Feature branch targets `dev`.
- [ ] **POST-MERGE CLEANUP — orchestrator routes to git-workflow cleanup**: Delete merged branches, close downstream tracking issues, sync `dev`.

---

## Dependency Map

```
Phase 1 (detection + session) → Phase 2 (tool wiring) → Phase 3 (behavioral tests)
    ↓                              ↓
  SC-5, SC-12                    SC-1, SC-2, SC-3, SC-4, SC-6, SC-7, SC-8, SC-11
                                    ↓
                                  Phase 3
                                  SC-9, SC-10
```

All phases are strictly sequential. Phase 2 depends on Phase 1's `_inject_agents_notice` and `injected_agents_files`. Phase 3 depends on Phase 2's injection wiring being complete in both `viewport:open` and `read_file` handlers.