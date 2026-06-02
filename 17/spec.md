# Synced from GitHub Issue #17 at 2026-06-01T02:38:25Z

## Parent Plan

#4 — MVP: Viewport-Editor MCP Server

## Concern

Core clipboard register — copy, cut, and paste. Session-scoped, line-aligned, cross-file, with autosave gate integration.

## SCs Covered

| SC | Requirement | Description |
|----|-------------|-------------|
| SC-39 | 1, 3, 4, 6 | copy creates session-scoped clipboard with provenance (source file, line range, timestamp); copy is a read — no buffered-mode switch |
| SC-40 | 7 | cut copies range to clipboard + stages deletion in buffer |
| SC-41 | 5, 8 | paste inserts clipboard content before target line (insert-before semantics); paste preserves clipboard (never auto-clears) |
| SC-42 | 9, 10, 11 | cut and paste trigger autosave gate if autosave=on (switch to buffered mode, return notice); if already buffered, no notice; return diff in response |
| SC-46 | 15 | paste never reads from stash — only from primary clipboard |
| SC-48 | 2 | line-aligned ranges only — no mid-line or character-range clipboard |

## Out of Scope

- SC-43, SC-44, SC-45, SC-47 (stash/pop/swap/list) — moved to #22 (Clipboard Stash)

## SC-to-Task Traceability

| # | Task | SCs | Test Function | Behavioral Evidence Artifact |
|---|------|-----|---------------|------------------------------|
| 1 | RED: copy creates session-scoped clipboard with provenance | SC-39, SC-48 | `test_copy_creates_clipboard_with_provenance` — after copy, clipboard has source_file, line_range, timestamp; `test_copy_line_aligned_only` — mid-line range is line-aligned | `./tmp/behavioral-evidence-SC-39.log` |
| 2 | Implement copy (session-scoped register, provenance, line-aligned) | SC-39, SC-48 | `test_copy_cross_file` — copy from one viewport, provenance shows correct source file; `test_copy_no_buffered_switch` — copy does not switch to buffered mode | `./tmp/behavioral-evidence-SC-39-cross.log` |
| 3 | RED: cut copies to clipboard + stages deletion | SC-40 | `test_cut_stages_deletion_in_buffer` — after cut, clipboard has content and buffer shows pending deletion | `./tmp/behavioral-evidence-SC-40.log` |
| 4 | Implement cut | SC-40 | `test_cut_autosave_gate` — cut with autosave=on switches to buffered mode; `test_cut_already_buffered` — cut when already buffered returns no notice | `./tmp/behavioral-evidence-SC-40-autosave.log` |
| 5 | RED: paste inserts before line, preserves clipboard | SC-41 | `test_paste_insert_before` — paste at line N inserts clipboard content before line N; `test_paste_preserves_clipboard` — clipboard still has content after paste | `./tmp/behavioral-evidence-SC-41.log` |
| 6 | Implement paste | SC-41 | `test_paste_cross_viewport` — copy from viewport A, paste into viewport B; `test_paste_empty_clipboard_is_error` — paste with empty clipboard returns isError | `./tmp/behavioral-evidence-SC-41-cross.log` |
| 7 | RED: cut/paste autosave gate + diff response | SC-42 | `test_paste_autosave_gate` — paste with autosave=on switches to buffered; `test_cut_paste_diff_response` — cut and paste return diff in tool response | `./tmp/behavioral-evidence-SC-42.log` |
| 8 | Implement autosave gate for cut/paste + diff response | SC-42 | `test_paste_already_buffered_no_notice` — paste when already buffered returns no notice; `test_cut_paste_diff_format` — diff matches diff:show format | `./tmp/behavioral-evidence-SC-42-format.log` |
| 9 | RED: paste never reads from stash | SC-46 | `test_paste_ignores_stash` — after stash, paste still uses clipboard, not stash | `./tmp/behavioral-evidence-SC-46.log` |

## Dependencies

- **Requires:** #18 (bug fixes — flush_entry CRLF/mkstemp fix, close auto-save fix)
- **Blocks:** #22 (Clipboard Stash), Autosave Integration (#25), File New + Save-As (#23), Diff Apply (#26), Integration Tests
- **SAT ordering:** After #18, before all downstream issues

## Verification (behavioral)

Per-SC behavioral evidence artifacts as defined above.

**Regression guard:**
`uv run pytest test/ -k "phase1 or phase2 or p3_clipboard" > ./tmp/behavioral-evidence-regression-p3-clipboard.log 2>&1`

**Clipboard core suite:**
`uv run pytest test/ -k "p3_clipboard" > ./tmp/behavioral-evidence-p3-clipboard.log 2>&1`

**Evidence artifacts are exempt from ./tmp/ cleanup per the spec §Behavioral Evidence Capture Protocol and survive until PR merge cleanup.**

## Workflow Pipeline (Pre-RED to PR Cleanup)

### Pre-Work
1. Create feature branch `feature/p3-clipboard-core`
2. Tag submodule SHA at `.opencode` if this repo is treated as a submodule of a parent project
3. Sync dev: `git checkout dev && git pull && git checkout -b feature/p3-clipboard-core`
4. Pre-flight: verify #18 bug fixes are merged to dev, Phase 1+2 modules exist and tests pass

### Coherence Gate (Pre-RED)
1. Sub-agent verifies clipboard register can be added to server.py without breaking existing Phase 1+2 API
2. Confirm no superseding issues or staleness
3. On BLOCKED: report defect and HALT. On PASS: proceed.

### RED Phase → GREEN Phase → Completeness Gate → Adversarial Audit → Finishing Checklist → Review Prep → Post-PR Cleanup

(Standard pipeline per project workflow — see #18 for full template)

Feature branch: `feature/p3-clipboard-core`

---

🤖 Co-authored with AI: OpenCode (glm-5.1)