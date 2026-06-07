# Card Catalogue — Spec #38: Remove agent-provided session_id

## Dependency Order

```
Card 1 (server.py — tool stubs + handlers) → Card 2 (viewport.py — ViewportManager)
                                                                      ↓
Card 3 (buffer.py — BufferManager)
Card 4 (test fixtures — 16 files)              ← requires Card 1
Card 5 (SC-1 through SC-5 verification)        ← requires Cards 1-4
Card 6 (SC-6 observational test)               ← independent
Card 7 (Phase C — docs/mcp-plugin-behavior.md)  ← requires SC-6 complete
```

## Card 1 — Core Session Derivation (Phase A)

**Target:** `src/viewport_editor/server.py`

**Scope:** 6 tool stubs + 19 handler functions

**Required changes:**
- Remove `session_id: str = ""` from all 6 tool stub signatures (viewport, edit, file, diff, clipboard, search)
- Add `session_id = ctx.session_id` inside each stub before calling handler
- Remove `session_id` parameter from all `_action_*` and `_handle_*` handler signatures
- Handlers continue to receive session_id as a positional string arg — source changes from agent-provided to ctx-derived

**Excluded from scope:** `regex` tool — never had `session_id` parameter

**Verification:** SC-1 (list_tools inspection), SC-2 (tool returns session_id)

## Card 2 — ViewportManager Session Cleanup (Phase B)

**Target:** `src/viewport_editor/viewport.py`

**Scope:** 29 methods on ViewportManager

**Required changes:**
- Remove `session_id: str` parameter from all method signatures (close, list, scroll, jump, apply_edit, etc.)
- Callers in server.py already receive `session_id` from `ctx.session_id` — pass as positional arg
- Internal dict keying (string-keyed `_entries`) remains unchanged — only the *source* of the string changes

**Excluded from scope:** `sweep_stale_sessions`, `check_conflict`, `format_conflict_warning` — these do not take `session_id`

**Verification:** SC-5 regression (all tests pass)

## Card 3 — BufferManager Session Cleanup (Phase B)

**Target:** `src/viewport_editor/buffer.py`

**Scope:** 9 methods on BufferManager

**Required changes:**
- Remove `session_id: str` parameter from all method signatures (get_or_create, get_lines, set_content, etc.)
- Callers in server.py already receive `session_id` from `ctx.session_id` — pass as positional arg
- Internal dict keying (string-keyed `_buffers`) remains unchanged

**Verification:** SC-5 regression (all tests pass)

## Card 4 — Test Fixture Cleanup (Phase B)

**Target:** 16 test files across `test/`

**Scope:** Remove every `"session_id":` key-value pair from all `arguments={}` dicts in tool calls

**Required behavior:** Once Card 1 removes the session_id parameter from tool stubs, FastMCP strict validation will reject undeclared kwargs. Every test that passes `"session_id": "..."` will fail.

**Verification:** SC-5 regression (`uv run pytest test/`)

## Card 5 — Verification (SCs 1-5)

**Target:** Behavioral test files + `uv run pytest test/`

**Scope:** 5 behavioral SCs

**Required behavior:**
- SC-1: No tool in MCP schema accepts `session_id` as parameter — verified by `list_tools` inspection
- SC-2: Each tool handler uses `ctx.session_id` as session key — verified by tool returning session_id in response
- SC-3: Two viewports via same Client share session (clipboard, stashes) — verified by copy/paste across viewports
- SC-4: Two Clients have isolated state — verified by independent buffer state
- SC-5: All existing tests pass without `session_id` in call args — verified by `uv run pytest test/`

## Card 6 — SC-6 Observational Test

**Target:** `test/test_sc6_subagent_session_observation.py`

**Scope:** Single observational test examining whether a second Client sees viewports opened by the first

**Required behavior:**
- Register a `probe_sid` tool on the server that echoes `ctx.session_id` back in response
- Client 1 opens a viewport, Client 2 lists viewports
- No pass/fail assertion — the test documents actual behavior
- The finding (same or different session_id) determines whether session forwarding is needed for sub-agent workflows

**Verification:** Non-blocking — observational documentation

## Card 7 — Phase C Documentation

**Target:** `docs/mcp-plugin-behavior.md`

**Scope:** 6 investigation topics

**Required topics:**
1. Transport continuity — does a sub-agent share transport with orchestrator?
2. Session reconnection — what happens when MCP server restarts mid-conversation?
3. Connection lifecycle — tool calls before handshake or after disconnect?
4. Error recovery — agent response to tool errors (retry? report? halt?)
5. Tool discovery — agent correctly enumerates tools from MCP schema?
6. Concurrent session isolation — two opencode sessions sharing same plugin?

**Verification:** Non-blocking — documentation artifact