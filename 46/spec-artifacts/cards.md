# Card Catalogue: #46 fastmcp switch investigation

## Card 1 — Dependency Switch + file_path Cleanup ✅ IMPLEMENTED

| Field | Value |
|-------|-------|
| Status | **implemented** |
| What | `uv add fastmcp` → change import → remove `file_path` from 21 `call_tool("edit", ...)` calls |
| Evidence | `from fastmcp import FastMCP` resolves to `fastmcp.server.server`. 135/135 tests pass. All 7 tools register via runtime `list_tools()`. FastMCP 3.4.0 installed. |
| Risk | Low — confirmed |
| Note | FastMCP 3.x strict Pydantic rejects undeclared kwargs. 21 `file_path` entries removed from `call_tool("edit", arguments={...})` across 4 test files. `pyproject.toml` updated to `fastmcp>=3.0,<4.0`. |

**Affected files (21 sites removed):**
- `test/test_phase2_edit_diff.py` — 16
- `test/test_p3_autosave.py` — 3
- `test/test_phase1_server_viewport.py` — 1
- `test/test_phase3_filenew_saveas.py` — 1

**RED test file created:** `test/test_red_46_card1_switch.py` — 2 RED tests (import check + file_path grep), now GREEN.

## Card 2 — `ctx: Context` Type Annotation

| Field | Value |
|-------|-------|
| Status | pending |
| Method | Replace `ctx: Any = None` with `ctx: Context` in all 7 handlers |
| Current state | All 7 handlers still use `ctx: Any = None` — annotation change not yet applied |
| Risk | Low |
| Requires | Card 1 |

## Card 3 — Session Management Capability

| Field | Value |
|-------|-------|
| Status | pending |
| Method | PoC: two tools sharing state via ctx.set_state/ctx.get_state |
| Risk | Medium |
| Requires | Card 2 |

## Card 4 — In-Memory Test Client

| Field | Value |
|-------|-------|
| Status | pending |
| Method | Single shared fixture `Client(create_server(...))` across 11 files |
| Current state | Tests still use `mcp.client.session.ClientSession` + `stdio_client` — not migrated |
| Risk | Medium |

## Card 5 — Decorator Compatibility ✅ CONFIRMED (no code change)

| Field | Value |
|-------|-------|
| Status | **confirmed — no code change needed** |
| Method | Verify `@mcp.tool()` still callable |
| Evidence | `grep` confirms zero captures of `@mcp.tool()` decorator return value in `src/`. No code relies on the return type — the decorator is used only for side-effect registration. Standalone fastmcp returns original function; official SDK returned `FunctionTool`. No behavioral impact. |
| Risk | None |

## Card 6 — Dependency Bloat (measured, spec corrected)

| Field | Value |
|-------|-------|
| Status | **measured** |
| Method | `du -sh` on installed packages |
| Evidence | fastmcp 4.8M (3,874,374 bytes), mcp 2.2M (1,555,251 bytes). Delta: +2.6M net. Note: fastmcp transitively depends on mcp, so mcp is NOT removed. |
| Risk | Low — CLI server extras are unused but harmless |
| Note | Spec originally cited 28.8 MB vs 621 KB (PyPI download sizes). Corrected to actual on-disk sizes. |

## Card 7 — Lifespan Handler ✅ CONFIRMED (no code change)

| Field | Value |
|-------|-------|
| Status | **confirmed — no code change needed** |
| Method | Verify `_server_lifespan` async generator works with standalone fastmcp |
| Evidence | Same `@asynccontextmanager` + `lifespan=` parameter pattern. Pattern confirmed identical in both SDKs. Server starts and lifespan manager invoked identically. |
| Risk | None |

## Decision Log

| Date | Finding | Decision |
|------|---------|----------|
| 2026-06-04 | FastMCP 3.x strict Pydantic rejects undeclared kwargs. 21 `edit()` test calls pass `file_path` — dead field never forwarded to handler. | Card 1 must remove `file_path` from edit() test calls. #39's test passes on dev and stays GREEN. |
| 2026-06-05 | Card 1 implemented: 135/135 tests pass, all 7 tools register at runtime via `create_server() + list_tools()`. FastMCP 3.4.0 resolves to `fastmcp.server.server`. | Switch to standalone fastmcp is VIABLE for Card 1. Proceed with Cards 2-4. |
| 2026-06-05 | Card 5: `grep` confirms zero `= @mcp.tool()` captures across `src/`. Decorator used only for side-effect registration. | No code change needed. Documented and closed. |
| 2026-06-05 | Card 6: Actual on-disk sizes are fastmcp 4.8M vs mcp 2.2M (delta +2.6M). Original spec cited PyPI download sizes (28.8 MB / 621 KB) which were incorrect for installed footprint. | Spec corrected to actual `du -sh` measurements. |
| 2026-06-05 | Card 7: `_server_lifespan` uses same `@asynccontextmanager` pattern in both SDKs. FastMCP accepts `lifespan=` identically. | No code change needed. Documented and closed. |