# Implementation Plan — [#96](https://github.com/michael-conrad/viewport-editor/issues/96) — Auto-reload viewport buffer on external file change when clean

- **Goal:** When a file changes externally and the buffer is clean (`dirty=False`), auto-reload the buffer from disk and update entry metadata. When the buffer is dirty (`dirty=True`), emit a stronger conflict signal with `severity: external_modification`. Migrate to trunk-based development: merge `dev` into `main`, delete `dev`, update docs.
- **Architecture:** Bifurcated conflict response routed through `entry.dirty`. New `auto_reload_if_clean()` on `ViewportManager` delegates to `file_ops.check_conflict()` then branches on dirty state. New `format_external_modification_warning()` in `file_ops.py` produces stronger YAML signal. New `_check_and_maybe_reload()` in `server.py` replaces `_check_file_conflict()` at all call sites. Phase 3: merge `dev` → `main`, delete `dev`, update AGENTS.md and project configs for trunk-based workflow.
- **Files:** `src/viewport_editor/file_ops.py`, `src/viewport_editor/viewport.py`, `src/viewport_editor/server.py`, `test/test_auto_reload_unit.py`, `test/test_phase1_server_viewport.py`, `test/test_phase2_edit_diff.py`, `AGENTS.md`, `pyproject.toml`
- **Dispatch:** `git-workflow` (pre-work), `implementation-pipeline` (execute), `test-driven-development` (execute), `finishing-a-development-branch` (checklist)

## Blast Radius

| Phase | Affected Components | Impact | Risk |
|-------|-------------------|--------|------|
| Phase 1a | `file_ops.py` | Direct — new function | Low |
| Phase 1b | `viewport.py` | Direct — new method | Low |
| Phase 1c | `server.py` | Direct — replace helper at 7+1 call sites | Medium |
| Phase 1d | `test/test_auto_reload_unit.py` | Direct — new unit test file | Low |
| Phase 1e | `test/test_phase1_server_viewport.py` | Direct — new behavioral tests | Low |
| Phase 2a | `server.py` | Direct — branch save-path conflict handling | Medium |
| Phase 2b | `test/test_phase2_edit_diff.py` | Direct — new behavioral tests + regression | Low |
| Phase 3a | `AGENTS.md`, `pyproject.toml`, CI configs, `.opencode/` | Direct — trunk-based migration docs | Low |
| Phase 3b | `dev` branch | Direct — merge into `main`, delete | Low |

## Concern Map Reference

| Concern | Phase | Description |
|---------|-------|-------------|
| Auto-reload clean buffers on read actions | Phase 1a–1e | Read-action call sites auto-reload when clean+conflict |
| Branch save-path conflict handling on dirty state | Phase 2a–2b | Save paths auto-reload when clean, reject when dirty |
| Trunk-based development migration | Phase 3a–3b | Merge dev→main, delete dev, update docs for trunk-based workflow |
| Global orchestration | Phase 0, 4 | Branch setup, regression, audit, finishing, cleanup |

> **Compliance Requirement:** All steps and sub-steps in this document MUST be followed in order. Failure to comply with any step — including but not limited to verification gates, test phases, audit checkpoints, and review steps — will result in the feature branch being rejected and discarded, requiring a full rework from scratch and loss of all prior work. There is no valid reason to skip, compress, reorder, or omit any step. If a step appears redundant or unnecessary, follow it anyway — the cost of following an extra step is negligible compared to the cost of rework from a skipped step.

> **One-step-at-a-time protocol:** Each step in this plan is a single dispatch. The orchestrator dispatches exactly one sub-agent per step, receives the result contract, and proceeds to the next step. No step bundles multiple dispatches. No step is skipped because it "seems unnecessary." Every step fires in order.

> **Step Status instruction:** Each step in this plan is a single dispatch. The orchestrator dispatches exactly one sub-agent per step, receives the result contract, and proceeds to the next step. No step bundles multiple dispatches. No step is skipped because it "seems unnecessary." Every step fires in order.

## Phase Table

| Phase | Name | Concern | SCs | Dependencies | Step Range | Dispatch |
|-------|------|---------|-----|--------------|------------|----------|
| 0 | global-pre-phase | Branch setup, baseline verification | — | None | 1–3 | `git-workflow` + `clean-room` + `inline` |
| 1a | file-ops-format-warning | Add `format_external_modification_warning()` to `file_ops.py` | SC-9, SC-10, SC-14 | Phase 0 | 4–8 | `implementation-pipeline` |
| 1b | viewport-auto-reload | Add `auto_reload_if_clean()` to `ViewportManager` | SC-15, SC-16, SC-17 | Phase 1a | 9–13 | `implementation-pipeline` |
| 1c | server-read-action-reload | Replace `_check_file_conflict` with `_check_and_maybe_reload` | SC-1, SC-2, SC-3, SC-4, SC-11 | Phase 1b | 14–17 | `implementation-pipeline` |
| 1d | unit-tests | Write `test_auto_reload_unit.py` | SC-14, SC-15, SC-16, SC-17 | Phase 1c | 18–21 | `test-driven-development` |
| 1e | behavioral-tests-phase1 | Write behavioral tests for Phase 1 SCs | SC-1, SC-2, SC-3, SC-4, SC-9, SC-11 | Phase 1d | 22–25 | `test-driven-development` |
| 2a | server-save-path-branching | Branch save-path conflict handling on dirty state | SC-5, SC-6, SC-7, SC-8 | Phase 1e | 26–29 | `implementation-pipeline` |
| 2b | behavioral-tests-phase2 | Write behavioral tests for Phase 2 SCs + regression | SC-5, SC-6, SC-7, SC-8, SC-10, SC-12, SC-13 | Phase 2a | 30–33 | `test-driven-development` |
| 3a | trunk-migration-merge | Merge `dev` into `main`, delete `dev` | SC-18, SC-19 | Phase 2b | 34–37 | `git-workflow` |
| 3b | trunk-migration-docs | Update AGENTS.md, project configs for trunk-based | SC-20, SC-21 | Phase 3a | 38–41 | `implementation-pipeline` |
| 4 | global-post-phase | Full regression, audit, finishing checklist, review-prep, cleanup | SC-12, SC-13 | Phase 3b | 42–47 | `finishing-a-development-branch` |

> **Compliance Requirement:** All steps and sub-steps in this document MUST be followed in order. Failure to comply with any step — including but not limited to verification gates, test phases, audit checkpoints, and review steps — will result in the feature branch being rejected and discarded, requiring a full rework from scratch and loss of all prior work. There is no valid reason to skip, compress, reorder, or omit any step. If a step appears redundant or unnecessary, follow it anyway — the cost of following an extra step is negligible compared to the cost of rework from a skipped step.

> **Cost frame:** Cost is measured in defect-discovery-latency, not model roundtrips. Running verification costs minutes of execution time — a bounded delay that surfaces defects before they reach CI. Skipping a verification step to save a tool call costs the full pipeline of rework when the defect surfaces downstream: diagnosis, fix, re-review, re-CI, re-deploy — each of which costs more roundtrips than the skipped verification would have consumed. Correctness is the only success metric — there is no score for tool-call economy.

> **Self-remediation protocol:** When a sub-agent returns BLOCKED or FAIL, the orchestrator MUST discard all output from that sub-agent and re-task clean-room with the same scoped context. If re-task also fails, report double-failure with both failure artifacts and HALT. The orchestrator MUST NOT inline-fix, patch, or salvage output from a failed sub-agent.

## Exit Criteria

- C1. Feature branch created and checked out
- C2. Baseline tests pass before any changes
- C3. `format_external_modification_warning()` added to `file_ops.py` with correct output format
- C4. `auto_reload_if_clean()` added to `ViewportManager` with correct branching logic
- C5. `_check_and_maybe_reload()` replaces `_check_file_conflict()` at all read-action call sites
- C6. `_action_list` includes conflict check
- C7. Unit tests pass for all new functions
- C8. Behavioral tests pass for Phase 1 SCs
- C9. Save-path conflict handling branches on dirty state
- C10. Behavioral tests pass for Phase 2 SCs
- C11. Full regression suite passes (`uv run pytest test/`)
- C12. Anti-lobotomization audit passes
- C13. Finishing checklist complete
- C14. Review-prep complete
- C15. Cleanup complete
- C16. `dev` branch merged into `main` with all commits preserved
- C17. `dev` branch deleted locally and on remote
- C18. `AGENTS.md` updated for trunk-based development (no `dev` branch)
- C19. All stale `dev` references removed from project files
