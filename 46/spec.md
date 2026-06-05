# Synced from GitHub Issue #46

## Problem

The viewport-editor depends on `mcp>=1.0.0` (the official MCP Python SDK), which bundles FastMCP 1.0 as `mcp.server.fastmcp`. The standalone PrefectHQ fork (`fastmcp` on PyPI, 25.5k ★) has diverged significantly and provides capabilities the bundled version lacks for solving #38.

## Requirements (Card Catalogue)

See `cards.md` for the 7 investigation cards.

## Success Criteria

| ID | Criterion | Evidence Type |
|----|-----------|---------------|
| SC-1 | `from fastmcp import FastMCP` works and all tools register | structural |
| SC-2 | Lifespan handler runs on startup and shutdown | behavioral |
| SC-3 | `ctx.session_id` returns a non-empty string within a tool handler | behavioral |
| SC-4 | Two in-memory clients have different `ctx.session_id` values | behavioral |
| SC-5 | All existing tests pass | behavioral |
| SC-6 | Install size delta documented | structural |
| SC-7 | PoC: `ctx.set_state`/`ctx.get_state` demonstrates session isolation | behavioral |

## Cross-References

| Type | Reference | Direction |
|------|-----------|-----------|
| prerequisite | #39/#45 - Parameter name normalization (merged) | 46 ← 39 |
| enables | #38 - Remove agent-provided session_id | 46 → 38 |