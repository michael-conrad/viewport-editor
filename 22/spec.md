# Synced from GitHub Issue #22 at 2026-06-02T02:47:08Z

## Parent Plan

#4 — MVP: Viewport-Editor MCP Server

## Concern

Ephemeral named storage slots for the clipboard — stash, pop, swap, and list. Slots are inert (paste never reads from them), overwritten on re-stash, and gone on session teardown.

## SCs Covered

| SC | Requirement | Description |
|----|-------------|-------------|
| SC-43 | 12 | stash copies clipboard contents to named storage slot; clipboard stays intact |
| SC-44 | 13 | pop replaces clipboard contents with named slot contents; stash slot remains intact |
| SC-45 | 14 | swap exchanges clipboard and named slot |
| SC-47 | 18 | stash list shows named slots with name, source file, line range, line count, first-line preview |

## Out of Scope

- SC-46 (paste never reads from stash) — verified in Clipboard Core (#17), not re-tested here
- SC-39/SC-40/SC-41 (copy/cut/paste) — verified in Clipboard Core (#17)

## SC-to-Task Traceability

| # | Task | SCs | Test Function | Behavioral Evidence Artifact |
|---|------|-----|---------------|------------------------------|
| 1 | RED: stash copies clipboard to named slot | SC-43 | `test_stash_copies_clipboard` — after stash, clipboard intact and named slot has content; `test_stash_overwrite` — stash to same name overwrites previous | `./tmp/behavioral-evidence-SC-43.log` |
| 2 | Implement stash | SC-43 | `test_stash_empty_clipboard_is_error` — stash with empty clipboard returns isError | `./tmp/behavioral-evidence-SC-43-empty.log` |
| 3 | RED: pop replaces clipboard from named slot | SC-44 | `test_pop_replaces_clipboard` — after pop, clipboard has slot content, slot remains intact | `./tmp/behavioral-evidence-SC-44.log` |
| 4 | Implement pop | SC-44 | `test_pop_nonexistent_slot_is_error` — pop with unknown name returns isError | `./tmp/behavioral-evidence-SC-44-errors.log` |
| 5 | RED: swap exchanges clipboard and named slot | SC-45 | `test_swap_exchanges` — after swap, clipboard has slot content and slot has former clipboard content | `./tmp/behavioral-evidence-SC-45.log` |
| 6 | Implement swap | SC-45 | `test_swap_empty_clipboard_is_error` — swap with empty clipboard returns isError | `./tmp/behavioral-evidence-SC-45-error.log` |
| 7 | RED: stash list returns metadata | SC-47 | `test_stash_list_shows_metadata` — stash list returns name, source_file, line_range, line_count, first_line_preview | `./tmp/behavioral-evidence-SC-47.log` |
| 8 | Implement stash list | SC-47 | `test_stash_list_empty_returns_empty` — no stashes returns empty list; `test_stash_list_after_multiple_stash` — shows all named slots | `./tmp/behavioral-evidence-SC-47-multi.log` |

## Dependencies

- **Requires:** #17 (Clipboard Core — primary register must exist before stash can reference it)
- **Blocks:** #6 (Integration Tests must cover stash operations)
- **SAT ordering:** After Clipboard Core, before Integration Tests

## Verification (behavioral)

Per-SC behavioral evidence artifacts as defined above.

**Regression guard:**
`uv run pytest test/ -k "phase1 or phase2 or p3_clipboard or p3_stash" > ./tmp/behavioral-evidence-regression-stash.log 2>&1`

**Stash suite:**
`uv run pytest test/ -k "p3_stash" > ./tmp/behavioral-evidence-stash.log 2>&1`

**Evidence artifacts are exempt from ./tmp/ cleanup per the spec §Behavioral Evidence Capture Protocol and survive until PR merge cleanup.**

## Workflow Pipeline (Pre-RED to PR Cleanup)

### Pre-Work
1. Create feature branch `feature/p3-stash`
2. Tag submodule SHA at `.opencode`
3. Sync dev: `git checkout dev && git pull && git checkout -b feature/p3-stash`
4. Pre-flight: verify #17 (Clipboard Core) is merged, all P1+P2+clipboard tests pass

### Coherence Gate (Pre-RED)
1. Verify clipboard register and provenance model exist in codebase
2. Confirm no superseding issues
3. On BLOCKED: HALT. On PASS: proceed.

### RED Phase → GREEN Phase → Completeness Gate → Adversarial Audit → Finishing Checklist → Review Prep → Post-PR Cleanup

(Standard pipeline per project workflow — see #18 for full template)

---

🤖 Co-authored with AI: OpenCode (ollama-cloud/glm-5.1)