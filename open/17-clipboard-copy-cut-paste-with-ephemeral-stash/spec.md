---
remote_issue: 17
remote_url: https://github.com/michael-conrad/viewport-editor/issues/17
promoted_at: 2026-05-31T00:00:00Z
---

# Synced from GitHub Issue #17 at 2026-05-31T00:00:00Z

## Problem

The editor has no clipboard abstraction. Moving content requires `delete-lines` + `insert-lines` with full content inlined — doubling token cost and risking content corruption. There is no way to review a pending move before committing it. The agent must re-type moved content verbatim, which is error-prone.

## Requirements

### Primary Clipboard

1. Session-scoped single clipboard register (not per-viewport)
2. Line-aligned ranges only — stores whole lines from any line range in the file
3. Clipboard stores provenance with content: source file, line range, timestamp
4. Cross-file — copy/cut from any viewport, paste into any viewport
5. `paste` preserves clipboard contents (never auto-clears on paste)
6. `copy` is a read — no buffered-mode switch, no diff in response
7. `cut` copies range to clipboard + stages deletion in buffer
8. `paste at <line>` inserts clipboard content before the given line (insert-before semantics, consistent with `insert-lines`)

### Autosave Gate on Mutations

9. `cut` and `paste`: if autosave=on, switch to buffered mode before staging, return notice in response
10. If already in buffered mode, no notice needed
11. Return diff in tool response (same pattern as `diff:show`) — always, regardless of autosave mode

### Ephemeral Stash

12. `stash <name>` — copies clipboard contents to named storage slot, clipboard stays intact
13. `pop <name>` — replaces clipboard contents with named storage slot contents; stash slot remains intact
14. `swap <name>` — exchanges clipboard ↔ named storage slot
15. Named slots are inert — `paste` never reads from stash, only from primary clipboard
16. No implicit behavior — stash/pop/swap are opt-in
17. Stash slots are ephemeral — overwritten on next `stash` to same name, gone on session teardown
18. `stash list` — shows named slots with name, source file, line range, line count, first-line preview (context-compaction recovery)

### Out of Scope

19. No mid-line / character-range clipboard — line-aligned only
20. No "paste as diff" — handled by existing/planned `diff:apply`
21. No clipboard clear operation — clipboard self-cleans through next copy/cut

## Interdependencies

- **Blocks:** #5 (clipboard cut/paste triggers autosave gate Phase 3 implements), #8 (clipboard overlaps buffer operations with search), #6 (integration tests must cover clipboard if it exists)
- **Required-by:** #5, #8, #6
- **Requires:** #13 (remediation fixes buffer behavior clipboard depends on)
- **SAT ordering:** #17 must complete after #13 and before #5, #8, #6 (proven via Z3 constraint model)