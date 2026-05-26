---
id: 1
title: '[SPEC] MVP: Viewport-Editor MCP Server'
state: open
author: michael-conrad
labels:
  - '[SPEC]'
created: '2026-05-25T05:40:18Z'
updated: '2026-05-26T05:54:45Z'
---

# [SPEC] MVP: Viewport-Editor MCP Server

## Problem

Existing file editing tools for AI agents operate on whole-file granularity (Read/Edit/Write) or use programmed text-edit scripts (texted). Both approaches create problems: ambiguous matches on repeated text, massive context consumption for large files, no safe multi-edit staging, and brittle script-based edits that frequently produce wrong results.

## Solution

Build an MCP server providing a **windowed viewport editor**. The agent opens a focused window into a file, edits are scoped to that window, and changes are staged into a buffer for review before saving. A consolidated 6-tool MCP surface minimizes initial context load. Per-viewport autosave toggle (on/off) controls whether the buffer flushes to disk after each edit. All communications in natural language prose and YAML. Discovery via the MCP protocol's standard list_tools call — no dedicated help tool.

## Intent and Executive Summary

- **Problem Statement:** AI agents need a file editing interface that avoids whole-file bloat, ambiguous text matches, and unsafe script-based edits — providing scoped, staged, safe multi-edit workflows through a viewport abstraction.
- **Root Cause / Motivation:** Existing MCP file tools (Read/Edit/Write) operate at whole-file granularity, forcing agents to re-read entire files on every context window and risk ambiguous matches on repeated text blocks.
- **Approach Chosen:** Windowed viewport editor MCP server with 6 consolidated tools (viewport, edit, file, diff, search, regex) supporting per-viewport autosave toggle.
- **Alternatives Considered & Why Discarded:** Enhanced texted with staging, direct MCP protocol extension, single monolithic tool with N parameters, dual-mode architecture.
- **Key Design Decisions:** All SCs are behavioral by design; per-viewport autosave toggle (binary on/off); action-parameter consolidation.

## Verification Mandate

| Tier | Type | Principle | Why |
|------|------|-----------|-----|
| 1 | behavioral | Execute code, observe output | Catches defects at earliest gate |
| 2 | semantic | AI read + judgment | Missed defects compound |
| 3 | string | grep / pattern matching | Brittle, high latency |
| 4 | structural | ls / file existence | Most expensive — false PASS ships defects |

All 34 SCs are behavioral. Structural/string evidence is EVIDENCE_TYPE_MISMATCH.

## Design Requirements

- Prose + YAML only. No JSON in agent-readable content. Protocol JSON Schema exempt.
- File paths relative to project root.
- Discovery via list_tools only.

## Terminology

Buffer, Dirty, File, Viewport, Autosave, Action parameter, Project root, Atomically, Soft conflict warning, Structured results, Session, Fuzzy context matching — all defined.

## Success Criteria (34 SCs all behavioral)

SC-1 through SC-34 covering: MCP server startup (6 tools), viewport operations (open/close/list/scroll/page/jump/autosave), edit operations (replace/replace-all/insert/delete/swap/move), file operations (new/save/save-as/delete/discard), diff (show/apply), search (find), regex (test/escape), conflict detection, session isolation, path sanitization.

## Risks

6 documented risks: tool constraint, conflict detection, diff failure, SC-3 JSON exemption, atomic write OS variance, buffer memory limits, mtime resolution.

## Documentation Sources

MCP Specification, FastMCP Python SDK, Python difflib — all with verified claims.
