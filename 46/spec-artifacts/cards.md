# Card Catalogue: #46 fastmcp switch

## Card 1 — Dependency Switch + file_path Cleanup

| Field | Value |
|-------|-------|
| What | Replace `mcp>=1.0.0` with `fastmcp>=3.0,<4.0` in pyproject.toml; change import; remove `file_path` from 21 `call_tool("edit", ...)` calls |
| Method | `uv add fastmcp` → change `from mcp.server.fastmcp` to `from fastmcp` → remove `file_path` from `call_tool("edit", arguments={...})` calls across test files |
| Risk | Low — `uv add fastmcp` test confirmed FastMCP 3.x resolves and uses strict Pydantic (rejects undeclared kwargs). 21 test call sites pass `file_path` as dead data that must be removed. |
| Note | FastMCP 3.x strict Pydantic rejects undeclared kwargs — 21 `file_path` entries must be removed from `call_tool("edit", arguments={...})` across 4 test files |

**Files requiring `file_path` removal (21 sites):**
- `test/test_phase2_edit_diff.py` — 16
- `test/test_p3_autosave.py` — 3
- `test/test_phase1_server_viewport.py` — 1
- `test/test_phase3_filenew_saveas.py` — 1

## Card 2 — `ctx: Context` Type Annotation (depends on Card 1)

| Field | Value |
|-------|-------|
| What | Change all 7 tool handler `ctx` parameters from `ctx: Any = None` to `ctx: Context` |
| Method | Import `Context` from fastmcp, annotate 7 handlers, verify `ctx.session_id` returns str in handler |
| Risk | Low — `ctx` parameter already exists and is positioned first per #45 |

## Card 3 — Session Management Capability (depends on Card 2)

| Field | Value |
|-------|-------|
| What | Verify `ctx.session_id`, `ctx.set_state`, `ctx.get_state` work for session isolation |
| Method | Build proof-of-concept: two tools sharing session state, two clients confirmed isolated |
| Risk | Medium — `ctx.session_id` raises `RuntimeError` pre-handshake; tool handlers run post-handshake so likely safe |

## Card 4 — In-Memory Test Client (depends on Card 1)

| Field | Value |
|-------|-------|
| What | Replace stdio-subprocess test fixtures with in-memory `Client(server)` |
| Method | Single shared fixture `Client(create_server(...))` across 11 files. Currently uses `mcp.client.session.ClientSession` + `stdio_client`. |
| Risk | Medium — 11 files with different module-scope settings |

## Card 5 — Decorator Compatibility

`@mcp.tool()` returns original function in standalone fastmcp (official SDK returned `FunctionTool`). Zero captures of decorator return value in `src/` — no code depends on return type. No requirements change needed.

## Card 6 — Dependency Bloat

`fastmcp` 4.8M (3,874,374 bytes), `mcp` 2.2M (1,555,251 bytes). Delta: +2.6M net. `fastmcp` transitively depends on `mcp`, so `mcp` is NOT removed. Document delta in spec.

## Card 7 — Lifespan Handler

Same `@asynccontextmanager` + `lifespan=` parameter pattern in both SDKs. No requirements change needed.