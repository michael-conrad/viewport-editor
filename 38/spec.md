# Synced from GitHub Issue #38

Remove agent-provided session_id, derive from MCP connection context

## Problem

Every viewport-editor tool requires `session_id: str` as an agent-provided parameter. The agent invents session IDs like `"test-sc9"` or `"autosave-test"`, giving it control over session isolation boundaries.

## Prerequisites

| # | Title | Status |
|---|-------|--------|
| #39/#45 | Parameter name normalization | ✅ MERGED (PR #45) |
| #46 | Switch from official `mcp` SDK to standalone `fastmcp` | Open |

## Fix

Switch to standalone `fastmcp`, then derive session identity from the MCP connection via `ctx.session_id`. The agent never sees or provides `session_id`.

Two-phase implementation:

### Phase A: Core Session Derivation (after #46)

- Add `from fastmcp import Context`. Change all tool handlers from `ctx: Any = None` to `ctx: Context`.
- Extract `session_id` from `ctx` in each tool entry point and use as the session key.
- Remove `session_id` tool parameter from all 6 tool stubs.
- Remove `session_id` from all `_action_*` and `_handle_*` handler signatures.

### Phase B: Manager-Level Session Cleanup (follow-up)

- Remove `session_id` from ViewportManager method signatures.
- Remove `session_id` from BufferManager methods.
- Remove `session_id` from test fixture arguments.

## Cross-References

| Type | Reference | Direction |
|------|-----------|-----------|
| prerequisite | #46 - Switch to standalone fastmcp | 38 ← 46 |
| prerequisite | #39/#45 - Parameter name normalization | 38 ← 39 |
| enables | Simplified session management across all tools | 38 → (all tools) |