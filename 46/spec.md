# [SPEC] Switch from official `mcp` SDK to standalone `fastmcp` (PrefectHQ)

## Problem

The viewport-editor depends on `mcp>=1.0.0` (the official MCP Python SDK), which bundles FastMCP 1.0 as `mcp.server.fastmcp`. The standalone PrefectHQ fork (`fastmcp` on PyPI, 25.5k ★) has diverged significantly — 102 releases vs ~50 — with three capabilities the bundled version lacks that are required for #38:

- **`ctx.session_id`** — identifies which MCP session a request belongs to (always available post-handshake, unlike `client_id` which is always `None`)
- **Session state API** (`ctx.set_state`/`ctx.get_state` — per-session persistence across requests)
- **In-memory Client** for testing (no stdio subprocess, no server startup)

The current codebase passes `session_id` as a user-supplied tool parameter — the agent invents session IDs, giving it control over session isolation. `ctx.client_id` is a dead end (always `None`). Standalone `fastmcp`'s `ctx.session_id` provides the connection-derived session identity needed for #38.

## Success Criteria

| ID | Criterion | Evidence Type | Verification Method |
|----|-----------|---------------|-------------------|
| SC-1 | `from fastmcp import FastMCP` works and all tools register | behavioral | `create_server()` + `list_tools()` — 7 tools confirmed |
| SC-2 | Lifespan handler runs on startup and shutdown | behavioral | Server lifecycle: lifespan enter on start, exit on shutdown |
| SC-3 | `ctx.session_id` returns a non-empty string within a tool handler | behavioral | Tool handler returns `ctx.session_id` value via Client |
| SC-4 | Two in-memory clients have different `ctx.session_id` values | behavioral | `Client(server)` × 2 → different session IDs |
| SC-5 | All existing tests pass | behavioral | `uv run pytest test/` |
| SC-6 | Install size delta documented | structural | `du -sh` on installed packages |
| SC-7 | PoC: `ctx.set_state`/`ctx.get_state` demonstrates session isolation | behavioral | Counter isolated per session |

## Cross-References

| Type | Reference | Direction |
|------|-----------|-----------|
| prerequisite | #39/#45 — Parameter name normalization (merged, on dev) | #46 ← #39 |
| enables | #38 — Remove agent-provided session_id | #46 → #38 |
| implementation plan | `.issues/46/spec-artifacts/plan.md` | Red/Green phase decomposition |
| dependency contract | `.issues/46/spec-artifacts/dependency-contract.yaml` | Z3-verified phase ordering |
| card catalogue | `.issues/46/spec-artifacts/cards.md` | Implementation requirements for each card |
| spec folder (GitHub) | [`https://github.com/michael-conrad/viewport-editor/tree/issues-data/46`](https://github.com/michael-conrad/viewport-editor/tree/issues-data/46) | Spec and box artifacts |
| spec (local) | `.issues/46/spec.md` | Authoritative spec (AI agent use) |

## Related Issues

- **#38** — Remove agent-provided `session_id`. This switch is the enabler — without `ctx.session_id` from standalone `fastmcp`, there is no viable path for connection-derived session identity.
- **#39/#45** — Parameter name normalization. `ctx` in first position makes `Context` annotation clean.