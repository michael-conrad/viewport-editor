---
id: 4
title: '[PLAN] MVP: Viewport-Editor MCP Server'
state: open
author: michael-conrad
labels:
  - plan
  - needs-approval
created: '2026-05-25T19:17:47Z'
updated: '2026-05-26T05:59:11Z'
---

# [PLAN] MVP: Viewport-Editor MCP Server

Spec: #1 — 34 behavioral SCs across 6 tools, per-viewport autosave toggle, session isolation, conflict detection.

## Architecture

Single buffer path with per-viewport autosave flag. Layers: session, viewport, buffer, operation (editor/file_ops/diff_engine/search/regex_ops), conflict, server.

## Phases

**Phase 1:** Server Foundation + Viewport Tool (15 SCs)
**Phase 2:** Edit Tool + Buffer Model (12 SCs)
**Phase 3:** File Operations + Autosave Integration (4 SCs)
**Phase 4:** Diff, Search, and Regex Tools (4 SCs)
**Phase 5:** Integration Tests

All phases: behavioral verification mandate, TDD (RED→GREEN), no structural evidence.
