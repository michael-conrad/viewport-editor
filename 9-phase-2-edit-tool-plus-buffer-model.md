---
id: 9
title: 'Phase 2: Edit Tool + Buffer Model'
state: open
author: michael-conrad
labels:
  - plan-sub
created: '2026-05-25T19:18:05Z'
updated: '2026-05-26T02:27:48Z'
---

## Parent Plan

#4 — MVP: Viewport-Editor MCP Server

## Concern

The core editing subsystem — edits always stage into buffer, inspected via diff, flushed on explicit save or autosave.

## SCs Covered

SC-9, SC-10, SC-11, SC-12, SC-13, SC-18, SC-19, SC-20, SC-21, SC-22, SC-23, SC-25

## Affected Files

- src/viewport_editor/editor.py
- src/viewport_editor/buffer.py
- src/viewport_editor/diff_engine.py
- src/viewport_editor/file_ops.py
- src/viewport_editor/server.py

## Key Tasks

1. RED: Buffer model — apply edits, track original vs pending
2. Implement buffer with line tracking
3. RED: edit:replace stages into buffer, file unchanged (autosave=off)
4. Implement edit:replace with buffer integration
5. RED: edit:replace with autosave=on writes to disk atomically
6. Implement autosave flush after edit
7. RED: diff:show returns correct unified diff
8. Implement diff:show
9. RED: file:save rejects on mtime/size mismatch OR missing file
10. Implement hard conflict check on save
11. RED: file:discard reverts buffer to disk state
12. Implement file:discard
13. RED: replace-all, insert, delete, swap, move each stage correctly
14. Implement remaining edit actions
15. RED: Soft conflict warning on edit operations via shared conflict layer
16. Verify SC-25 edit-side conflict warnings

## Dependency

Phase 1 complete (viewport + session infrastructure)

## Verification

`uv run pytest test/ -k "phase2"` — all phase 2 tests pass
