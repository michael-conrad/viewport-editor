---
id: 5
title: 'Phase 3: File Operations + Autosave Integration'
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

File creation, deletion, save-as, and the autosave=on behavior integration.

## SCs Covered

SC-14, SC-15, SC-16, SC-24

## Affected Files

- src/viewport_editor/file_ops.py
- src/viewport_editor/viewport.py
- src/viewport_editor/server.py

## Key Tasks

1. RED: With autosave=on, file:save/diff:show/discard return empty state
2. Implement autosave=on gate in each operation
3. RED: file:new creates file and opens viewport with autosave=off
4. Implement file:new
5. RED: file:save-as with force=false rejects existing target; force=true overwrites
6. Implement file:save-as
7. RED: file:delete removes file on disk
8. Implement file:delete
9. RED: viewport:close with dirty buffer auto-saves
10. Implement auto-save on close

## Dependency

Phase 1 and Phase 2 complete (viewport + buffer + edit pipeline)

## Verification

`uv run pytest test/ -k "phase3"` — all phase 3 tests pass
