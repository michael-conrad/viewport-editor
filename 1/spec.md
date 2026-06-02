# Synced from GitHub Issue #1

# [SPEC] MVP: Viewport-Editor MCP Server

## Problem

Existing file editing tools for AI agents operate on whole-file granularity (Read/Edit/Write) or use programmed text-edit scripts (texted). Both approaches create problems: ambiguous matches on repeated text, massive context consumption for large files, no safe multi-edit staging, and brittle script-based edits that frequently produce wrong results.

## Solution

Build an MCP server providing a **windowed viewport editor**. The agent opens a focused window into a file, edits are scoped to that window, and changes are staged into a buffer for review before saving. A consolidated 6-tool MCP surface minimizes initial context load. Per-viewport autosave toggle (on/off) controls whether the buffer flushes to disk after each edit. All communications in natural language prose and YAML. Discovery via the MCP protocol's standard list_tools call — no dedicated help tool.

## Intent and Executive Summary

- **Problem Statement:** AI agents need a file editing interface that avoids whole-file bloat, ambiguous text matches, and unsafe script-based edits — providing scoped, staged, safe multi-edit workflows through a viewport abstraction.
- **Root Cause / Motivation:** Existing MCP file tools (Read/Edit/Write) operate at whole-file granularity, forcing agents to re-read entire files on every context window and risk ambiguous matches on repeated text blocks. texted provides structured editing but lacks staging, conflict detection, and session isolation.
- **Approach Chosen:** Windowed viewport editor MCP server with 6 consolidated tools (viewport, edit, file, diff, search, regex) supporting per-viewport autosave toggle. Edits scope to a focused window into the file and always stage into a buffer. With autosave off (default), buffer requires explicit `file:save` to flush to disk. With autosave on, buffer flushes to disk atomically after each edit, equivalent to unbuffered writes.
- **Alternatives Considered & Why Discarded:**
  - Enhanced texted with staging — discarded because script-based edits remain brittle and texted's Emacs-Lisp-like DSL is unfamiliar to most AI agents
  - Direct MCP protocol extension — discarded because it couples to MCP internals rather than providing an independent tool surface
  - Single monolithic tool with N parameters — discarded because it loads all affordances into one context, defeating the purpose of reduced surface area
  - Dual-mode architecture (buffered vs immediate code paths) — discarded because autosave-on with zero-delay flush produces identical behavior through a single buffer code path, eliminating bifurcation
- **Key Design Decisions:**
  1. **All SCs are `behavioral` by design** — behavioral testing catches defects at the earliest possible gate.
  2. **Per-viewport autosave toggle** — a simple binary `on`/`off`.
  3. **Action-parameter consolidation** — 6 tools with action enums rather than 18+ individual tools.
  4. **Every viewport action returns visible text content** — the agent never navigates blind.
  5. **Line ending detection on first viewport display** — the file's line ending convention (\n, \r\n, \r) is detected and reported to the agent.
  6. **Show/hide non-printing characters mode** — per-viewport display toggle. In show mode, tabs, nulls, and non-printing characters render as `\uNNNN`. Agent can input `\uNNNN` in show mode to insert the real character. Display only — buffer content is never modified.
  7. **Deterministic execution** — all operations produce repeatable results given the same inputs and state. Every SC produces the same PASS/FAIL from any reasonable auditor. Behavioral tests are executable verification commands, not structural checks.

## Verification Mandate

| Tier | Type | Principle | Why (Cost in Defect-Discovery-Latency) |
|------|------|-----------|----------------------------------------|
| 1 (lowest total cost) | `behavioral` | Verify runtime behavior by executing code and observing output | Catches defects at the earliest possible gate — the behavioral test. Zero downstream rework. The one-time execution cost is bounded; the cost of an undiscovered defect is unbounded. |
| 2 | `semantic` | Verify intent and correctness by AI agent read + analytical judgment | Defect may be missed or hallucinated away — introduces downstream risk. More expensive than behavioral because a missed defect compounds. |
| 3 | `string` | Verify content by grep / pattern matching | Brittle — grep matches text, not behavior. A passing grep tells you nothing about correctness. High defect latency. |
| 4 (highest total cost) | `structural` | Verify existence by `ls` / file presence | Proves the artifact was created, not that it works. False PASS here is the most expensive outcome — it creates a downstream defect that will require full rework: diagnosis, fix, re-review, re-CI, re-deploy. |

**Cost frame:** All SCs are `behavioral`. Structural or string evidence for any behavioral SC is EVIDENCE_TYPE_MISMATCH — treated as FAIL. No evidence type downgrade permitted. **All SCs inherit this cost-frame from the Verification Mandate section above.**

## Design Requirements

- All MCP communications use natural language prose and YAML exclusively. No JSON in tool descriptions, response bodies, or agent-visible output. Protocol-mandated JSON Schema for MCP `inputSchema` at the transport layer is exempt.
- File paths are relative to a configured project root.
- Discovery via list_tools only.
- **Line ending detection:** Every viewport:open response includes a `line_ending:` field indicating the file's line ending convention (\n, \r\n, or \r). Detection: scan first 100 lines, report the dominant terminator.
- **Per-viewport display mode:** Each viewport has a `display_mode` field (`hide` or `show`). In `hide` mode (default), content displays raw characters as-is. In `show` mode, non-printing characters render as `\uNNNN` and backslash escapes to `\\`. Agent can input `\uNNNN` in show mode to insert the real character. Toggle via `viewport:set-display-mode show|hide`.

## Reference Design

Full design document at [`DESIGN.md`](https://github.com/michael-conrad/viewport-editor/blob/main/DESIGN.md) in this repo.

## Tool Surface (6 Tools)

All operations consolidated into 6 tools with an `action` parameter:

1. **viewport** — open, close, list, scroll, page-up, page-down, jump, autosave, set-display-mode
2. **edit** — replace, replace-all, insert-lines, delete-lines, swap-lines, move-lines
3. **file** — new, save, save-as, delete, discard
4. **diff** — show, apply
5. **search** — find
6. **regex** — test, escape

## Success Criteria

| ID | Criterion | Evidence Type |
|----|-----------|---------------|
| SC-1 | MCP server starts and exposes exactly 6 tools with action parameters | behavioral |
| SC-2 | list_tools is the only discovery mechanism; no dedicated help tool | behavioral |
| SC-3 | All tool descriptions and response content use prose + YAML. Protocol-mandated JSON Schema for MCP inputSchema at the transport layer is exempt. No JSON in agent-readable output. | behavioral |
| SC-4 | File paths are relative to configured project root; no absolute paths accepted | behavioral |
| SC-5 | viewport:open returns a viewport entry with file, start_line, end_line, visible text content, mtime, size, autosave, and line_ending | behavioral |
| SC-6 | viewport:open accepts autosave parameter (on/off); defaults to off | behavioral |
| SC-7 | viewport:page-up moves viewport up by its own height (previous text block); response includes visible text content at new position | behavioral |
| SC-8 | viewport:page-down moves viewport down by its own height (next text block); response includes visible text content at new position | behavioral |
| SC-9 | edit:replace stages into buffer; does not write to disk | behavioral |
| SC-10 | diff:show returns unified diff of pending buffer changes | behavioral |
| SC-11 | file:save writes buffer to disk; rejects on mtime+size mismatch OR missing file (unless force) | behavioral |
| SC-12 | file:discard discards buffer changes and reloads from disk | behavioral |
| SC-13 | With autosave=on: each edit flushes buffer to disk atomically after the operation | behavioral |
| SC-14 | With autosave=on: file:save is a no-op (buffer already flushed), diff:show returns empty, file:discard shows empty state | behavioral |
| SC-15 | file:new creates file and opens viewport with autosave=off | behavioral |
| SC-16 | file:save-as with force=false rejects if target exists; force=true overwrites | behavioral |
| SC-17 | search:find returns structured results with line numbers; substring default, regex with flag | behavioral |
| SC-18 | edit:replace-all stages all matches into buffer; flushes to disk if autosave=on | behavioral |
| SC-19 | edit:insert-lines inserts lines at specified line number | behavioral |
| SC-20 | edit:delete-lines deletes a range of lines | behavioral |
| SC-21 | edit:swap-lines exchanges two line positions | behavioral |
| SC-22 | edit:move-lines relocates a range to a target line position | behavioral |
| SC-23 | diff:apply stages diff into buffer; auto-loads file if not open | behavioral |
| SC-24 | viewport:close with dirty buffer auto-saves (default). Closing an already-closed viewport is a no-op. | behavioral |
| SC-25 | Soft conflict warning on viewport and edit operations when file changed on disk or file missing | behavioral |
| SC-26 | Session isolation: N sessions editing the same file each maintain independent buffers. | behavioral |
| SC-27 | viewport:jump returns error with isError=true if target not found | behavioral |
| SC-28 | regex:test returns match positions | behavioral |
| SC-29 | regex:escape returns string with metacharacters escaped | behavioral |
| SC-30 | file:delete removes file on disk | behavioral |
| SC-31 | viewport:scroll moves the viewport up or down by N lines; response includes visible text content at new position | behavioral |
| SC-32 | viewport:autosave toggles the autosave flag on an open viewport without closing it. | behavioral |
| SC-33 | viewport:list returns all open viewports with file, range, mtime, size, and autosave | behavioral |
| SC-34 | File paths are relative to project root; no absolute or host-specific paths | behavioral |
| SC-35 | Server lifecycle is bound to the AI agent's stdio transport: when the server runs, dirty buffers live in memory and are never implicitly flushed; when the server exits, all dirty buffers are discarded via lifespan shutdown with zero saves. Orphaned sessions from agent software restart without clean teardown are reclaimed by a stale-session sweep (default 4-hour idle timeout). | behavioral |
| SC-36 | viewport:open detects and reports the file's line ending convention (\n, \r\n, or \r) in the `line_ending:` field | behavioral |
| SC-37 | Per-viewport display_mode toggle (hide/show) controls non-printing character rendering. hide (default) shows raw chars; show renders non-printing chars as \uNNNN and backslash as \\ | behavioral |
| SC-38 | In show mode, agent can input \uNNNN to insert the real character. Actual buffer content stored unaffected | behavioral |

## Implementation Phases

| Phase | Sub-Issue | Concern | Key Files |
|-------|-----------|---------|-----------|
| P1 | #7 | Server + Viewport Foundation | server.py, viewport.py, session.py, conflict.py, exceptions.py |
| P2 | #9 | Edit Tool + Buffer Model | editor.py, buffer.py, diff_engine.py, file_ops.py |
| P3 | #5 | File Operations + Autosave | file_ops.py, viewport.py |
| P4 | #8 | Diff, Search, Regex Tools | diff_engine.py, search.py, regex_ops.py |
| P5 | #6 | Integration Tests | test/ |

---

🤖 Co-authored with AI: OpenCode (ollama-cloud/deepseek-v4-flash)