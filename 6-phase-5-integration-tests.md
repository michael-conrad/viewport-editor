---
id: 6
title: 'Phase 5: Integration Tests'
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

End-to-end integration testing across all subsystems.

## Affected Files

- All modules may need minor adjustments
- test/ — Integration test suite spanning all 6 tools

## Key Tasks

1. RED: Full buffered workflow (open → edit → diff → save → close → verify disk)
2. RED: Autosave=on workflow (open with autosave=on → edit → verify disk changed immediately)
3. RED: Autosave toggle workflow (open autosave=off → edit → toggle on → verify flush)
4. RED: N-session isolation (N concurrent sessions, same file, independent buffers)
5. RED: Conflict detection save rejection
6. Run full suite: `uv run pytest test/` — all tests pass

## Dependency

All prior phases complete (all 6 tools operational)

## Verification

`uv run pytest test/` — complete test suite passes
