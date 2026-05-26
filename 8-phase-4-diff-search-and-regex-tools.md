---
id: 8
title: 'Phase 4: Diff, Search, and Regex Tools'
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

Auxiliary tools supporting the editing workflow — importing diffs, locating text, and regex preparation.

## SCs Covered

SC-17, SC-23, SC-28, SC-29

## Affected Files

- src/viewport_editor/diff_engine.py
- src/viewport_editor/search.py
- src/viewport_editor/regex_ops.py
- src/viewport_editor/server.py

## Key Tasks

1. RED: diff:apply stages diff into buffer; auto-loads file if not open
2. Implement diff parser and buffer staging
3. RED: search:find returns structured results with line numbers
4. Implement search:find (substring default, regex with flag)
5. RED: regex:test returns match positions
6. Implement regex:test
7. RED: regex:escape escapes metacharacters correctly
8. Implement regex:escape

## Dependency

Phase 1 and Phase 2 complete (viewport + buffer model)

## Verification

`uv run pytest test/ -k "phase4"` — all phase 4 tests pass
