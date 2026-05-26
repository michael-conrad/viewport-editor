---
id: 7
title: 'Phase 1: Server Foundation + Viewport Tool'
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

Core server infrastructure and the viewport management subsystem.

## SCs Covered

SC-1, SC-2, SC-3, SC-4, SC-5, SC-6, SC-7, SC-8, SC-25, SC-26, SC-27, SC-31, SC-32, SC-33, SC-34

## Affected Files

- src/viewport_editor/server.py
- src/viewport_editor/viewport.py
- src/viewport_editor/session.py
- src/viewport_editor/conflict.py

## Key Tasks

1. RED: list_tools returns 6 tools with action parameters in prose+YAML
2. Implement server scaffold with FastMCP registration
3. RED: viewport:open returns viewport_entry with all fields including autosave
4. Implement viewport model, open/close/list/scroll
5. RED: page-up/down moves by viewport height
6. Implement scroll and page operations
7. RED: jump returns isError=true on target not found
8. Implement jump operation
9. RED: viewport:autosave toggles flag without closing viewport; flushes if dirty
10. Implement autosave toggle action
11. RED: soft conflict warning on ops
12. Implement conflict detection
13. RED: session isolation for N concurrent sessions
14. Implement session-isolated registries
15. RED: SC-31 scroll by N lines
16. RED: SC-32 autosave toggle
17. RED: SC-33 viewport:list returns all fields
18. RED: SC-34 relative paths only, absolute paths rejected

## Verification

`uv run pytest test/ -k "phase1"` — all phase 1 tests pass
