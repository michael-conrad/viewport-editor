# Synced from GitHub Issue #7

## Parent Plan

#4 — MVP: Viewport-Editor MCP Server

## Concern

Core server infrastructure and the viewport management subsystem — the foundation everything else builds on.

## SCs Covered

SC-1, SC-2, SC-3, SC-4, SC-5, SC-6, SC-7, SC-8, SC-25, SC-26, SC-27, SC-31, SC-32, SC-33, SC-34, SC-35, SC-36, SC-37, SC-38

SC-31 (viewport:scroll by N lines) is a viewport operation. SC-32 (viewport:autosave toggle) is a viewport operation. SC-33 (viewport:list returns all fields) is a viewport operation. SC-34 (relative file paths) is a server-level sanitization concern. SC-35 (session lifecycle cleanup) — server bound to stdio transport, lifespan shutdown discards dirty buffers, stale-session sweep reclaims orphaned sessions. SC-36 (line ending detection), SC-37 (display mode toggle), SC-38 (show mode input decoding).

## Affected Files

- `src/viewport_editor/server.py` — MCP server scaffold, tool registration, prose+YAML responses, disconnect handler, _format_content_block helper, content display in all position-changing actions
- `src/viewport_editor/viewport.py` — Viewport model, registry, all viewport actions, autosave flag, session destroy, get_visible_lines()
- `src/viewport_editor/session.py` — Session state container
- `src/viewport_editor/conflict.py` — Soft conflict detection
- `src/viewport_editor/exceptions.py` — Domain-specific exceptions for isError=true

## Key Tasks

1. ✅ Server scaffold with FastMCP registration
2. ✅ Viewport model, open/close/list/scroll/page-up/page-down/jump/autosave
3. ✅ Page-up/down moves by viewport height (SC-7, SC-8) — includes visible text content
4. ✅ Scroll by N lines (SC-31) — includes visible text content
5. ✅ Jump target with isError=true on not-found (SC-27) — includes visible text content on success
6. ✅ Autosave toggle (SC-32)
7. ✅ Soft conflict warning on ops (SC-25)
8. ✅ Session isolation (SC-26)
9. ✅ Relative paths only (SC-34)
10. ✅ All position-changing viewport actions display visible text content in cat -n format (SC-5, SC-7, SC-8, SC-31)
11. ✅ Session lifecycle (SC-35): stdio transport binding — lifespan shutdown discards all dirty buffers (zero saves); stale-session sweep reclaims orphaned sessions from agent restart without clean teardown
12. ✅ Line ending detection on open (SC-36)
13. ✅ Display mode toggle hide/show (SC-37)
14. ✅ Show mode \uNNNN input decoding (SC-38)

## Dependency

None (Phase 1 is the foundation)

## Verification

`uv run pytest test/ -k "phase1"` — all 36 phase 1 tests pass

---

🤖 Co-authored with AI: OpenCode (ollama-cloud/deepseek-v4-flash)