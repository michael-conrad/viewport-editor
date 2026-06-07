# [SPEC-FIX] Remove agent-provided session_id, derive from MCP connection context

> **AI AGENT MANDATE — Read ALL local spec artifacts before any implementation dispatch.**
> The files in `.issues/{N}/` are the authoritative source for implementation scope, pipeline steps, and cancellation decisions. This remote issue body is a condensed summary only.
>
> **Required reading before any implementation dispatch:**
> 1. `.issues/{N}/spec.md` — this file (spec, intent, SCs)
> 2. `.issues/{N}/spec-artifacts/plan.md` — dispatch table with pipeline steps mapped to skill tasks
> 3. `.issues/{N}/spec-artifacts/problem.yaml` — Z3-validated state machine, fluent/goal definitions
> 4. `.issues/{N}/spec-artifacts/cards.md` — card catalogue with feasibility findings and cancellations
>
> Acting on this remote body alone, without loading the local plan and problem model, produces scope errors, stale-pipeline execution, and spec-contradictory work. This mandate is enforced by `.issues/AGENTS.md`.

## Intent and Executive Summary

**Problem Statement:** Every viewport-editor tool requires `session_id: str` as an agent-provided parameter. The agent invents session IDs like `"test-sc9"` or `"autosave-test"`, giving it control over session isolation boundaries. This means: (1) false isolation — agent can share or isolate sessions artificially, compromising all behavioral test results to date; (2) extra parameter burden — every tool call requires the agent to decide and pass a session string; (3) design violation — session isolation is supposed to be per-MCP-connection, not per-invented-key.

**Root Cause / Motivation:** The original design used the official `mcp` SDK which lacked `ctx.session_id`. The codebase compensated by routing a user-supplied `session_id: str` parameter through every layer. Prerequisite #46 (switch to standalone `fastmcp`) provides `ctx.session_id`, making the compensation removable.

**Approach Chosen:** Derive session identity from `ctx.session_id` at the tool entry point in `server.py`. Remove `session_id` from all tool parameters and handler signatures. Three-pass: core derivation (Card 1), SC-6 observational test (Card 2), documentation + rollback (Card 3). Manager-method signatures left unchanged — managers are internal API never called by agents, and every viable removal approach introduces structural risk (breaks session isolation or introduces concurrency bugs).

**Alternatives Considered & Why Discarded:**
- **Keep `session_id` parameter + `ctx.session_id` side-by-side:** Adds complexity, dual session sources create confusion. Discarded because `ctx.session_id` is always available post-handshake — no scenario where the agent needs to override it.
- **Store `session_id` on Manager objects (constructor injection):** Would require creating per-session Manager instances. Cleaner from OO perspective but introduces lifecycle complexity — managers would need to be created/destroyed per connection. Discarded because current design uses string-keyed dicts (`_entries: Dict[str, Dict[str, ViewportEntry]]`) which work correctly with `ctx.session_id` as the key.
- **Manager method signatures left unchanged.** Managers are internal API never called by agents — the real vulnerability (agent-controlled session injection) was already fixed by Card 1. Three approaches were examined during feasibility analysis: (a) `current_session` instance variable introduces mutable shared state and a thread-safety bug under concurrent clients; (b) per-session constructor injection is incompatible with the singleton pattern and test structure; (c) flattening data structures removes session-level keying but destroys session isolation (contradicts SC-4). All three rejected — managers stay as-is with zero residual risk.

**Key Design Decisions:**
1. Extract `ctx.session_id` at the tool entry point in `server.py`, pass it down as the session string key — minimal surface change.
2. ViewportManager and BufferManager keep string-keyed dicts internally; only the *source* of the string changes.
3. Manager method signatures retain `session_id` parameter — they are internal API, never agent-exposed. The agent already cannot control session identity (Card 1). Removing the parameter from signatures adds structural risk without security benefit.

## Objective

Remove the agent-provided `session_id` parameter from all tool and internal APIs. Derive session identity from `ctx.session_id` instead. The agent never sees or provides `session_id` — session isolation is connection-derived.

## Problem

Every tool handler receives `session_id: str = ""` as a user-supplied parameter passed through `arguments={}` in the MCP tool call. The agent controls this boundary:

- Can share sessions between unrelated contexts by reusing the same session_id
- Can artificially isolate sessions by inventing different IDs
- Must decide what string value to pass on every tool invocation — extra cognitive burden
- Behavioral test results are compromised because the agent controlled session isolation

Prerequisite #46 (switch to standalone `fastmcp`) provides `ctx.session_id` — a connection-derived UUID per `Client` — as the authoritative session identity.

## Context

The viewport-editor serves as an opencode MCP plugin. Session identity is currently a user-supplied `session_id: str` parameter passed through every tool call. The agent invents these IDs, making session isolation an agent-controlled boundary rather than a connection-derived one.

The dependency is `fastmcp>=3.0,<4.0` (established by prerequisite #46), which provides `ctx.session_id` — a UUID assigned per `Client(transport=server)` connection, available inside any tool handler. Three layers pass `session_id` as a string key:

1. **server.py** — tool stubs and handler functions receive `session_id` from call arguments
2. **viewport.py** — ViewportManager methods accept `session_id` and key internal `_entries` dicts by it
3. **buffer.py** — BufferManager methods accept `session_id` and key internal `_buffers` dicts by it

The `session.py` module and `exceptions.py` use the string key for session lifecycle and error reporting.

When opencode dispatches a clean-room sub-agent, the sub-agent may connect via a new transport connection (different `ctx.session_id`) or share the orchestrator's (same `ctx.session_id`) — SC-6 will determine this observationally.

Files that never use `session_id`: `editor.py`, `file_ops.py`, `diff_engine.py`, `clipboard.py`, `__init__.py`, `__main__.py`. The `regex` tool handler also has no `session_id` parameter.

## Fix Approach

Three-pass implementation — see `spec-artifacts/plan.md` for the dispatch table and `spec-artifacts/problem.yaml` for the Z3 state machine.

### Pass 1: Core Session Derivation — Card 1 (COMPLETE, PR #49)

In `server.py`:

1. **Extract `ctx.session_id` at tool entry points** — in each of 6 tool functions, replace `session_id` parameter extraction with `session_id = ctx.session_id`
2. **Remove `session_id` tool parameter** from all 6 tool stub signatures
3. **Remove `session_id`** from all `_action_*` and `_handle_*` handler function signatures
4. **Confirm all 7 tools register** via `list_tools()`

The `regex` tool never had a `session_id` parameter — no change needed.

### Pass 2: Observational Session Behavior — Card 2 (SC-6)

Write empirical test that documents session behavior of two `Client(transport=server)` connections. No assertions — observational only. See SC-6 section below.

### Pass 3: Documentation & Rollback — Card 3

Produce `docs/mcp-plugin-behavior.md` documenting observed session behavior from test output only. No code reading as evidence.

## Prerequisites

| # | Title | Why |
|---|-------|-----|
| #39/#45 | Parameter name normalization | Moved `ctx` to first parameter position in all 7 tool signatures. Makes `ctx: Context` typing clean. |
| #46 | Switch from official `mcp` SDK to standalone `fastmcp` | `fastmcp>=3.0,<4.0` provides `ctx.session_id` — connection-derived UUID per Client. All 7 handlers annotated `ctx: Context`. In-memory `Client(transport=server)` fixture in conftest.py. |

## Risk: `ctx.session_id` Pre-Handshake

`ctx.session_id` raises `RuntimeError` if the MCP session hasn't been established yet (e.g., during middleware `on_request`). All tool handlers run post-handshake, so this is not an issue. Guard with `ctx.request_context is not None` if defensive code is needed.

## Affected Files

| File | Anchor | Changes |
|------|--------|---------|
| `src/viewport_editor/server.py` | 6 tool stubs (viewport, edit, file, diff, clipboard, search) | Remove `session_id: str = ""` param; extract `ctx.session_id` and pass to handlers |
| `src/viewport_editor/server.py` | `_handle_viewport_action`, `_action_open/close/list/scroll/page_up/page_down/jump/autosave/set_display_mode` | Remove `session_id` param (19 handlers) |
| `src/viewport_editor/server.py` | `_handle_edit_action`, `_handle_file_action`, `_handle_diff_action`, `_handle_clipboard_action`, `_handle_search_action`, `_action_find` | Remove `session_id` param |
| `src/viewport_editor/session.py` | `Session.__init__`, `create_session`, `get_session`, `remove_session`, `get_session_ids` | Keep as-is (keys remain strings) |
| `test/test_sc6_subagent_session_observation.py` | New file | SC-6 observational test — two-client transport observation |

## Constraints & Assumptions

1. `ctx.session_id` is a UUID string (format verified by fastmcp docs and SC-3/SC-4 tests from #46)
2. Tool handlers always run post-handshake — `ctx.session_id` never raises `RuntimeError` in production
3. Two viewports opened via the same Client share `ctx.session_id` — they belong to the same session (desired, shared clipboard/stashes)
4. Two fastmcp `Client` instances in tests each get unique `session_id` (correct isolation)
5. `Session.__init__` and module-level `_sessions` dict are string-keyed — no change to their signatures
6. Session identity is a UUID — no user-facing string needed
7. `regex` tool never had `session_id` — no change needed

## Edge Cases

| Case | Behavior | Risk |
|------|----------|------|
| `ctx.session_id` used before handshake | Raises `RuntimeError` | Tool handlers run post-handshake — no risk |
| Multiple viewports in one conversation | Share `ctx.session_id` — same connection | Desired (shared clipboard, stashes) |
| Two `fastmcp.Client` instances in tests | Each gets unique `session_id` | Correct isolation |
| Sub-agent dispatched via `task()` gets own connection | Different `ctx.session_id` → isolated state | Documented by SC-6; may need session forwarding |

## Success Criteria

| ID | Criterion | Evidence Type | Verification Method | Behavioral Test |
|----|-----------|---------------|-------------------|-----------------|
| SC-1 | No tool in the MCP schema accepts `session_id` as a parameter | `behavioral` | `list_tools` inspection via Client | [`test/test_sc1_no_session_id_param.py`] |
| SC-2 | `ctx.session_id` is used as the session key in every tool handler | `behavioral` | Tools return their `session_id` in response | [`test/test_sc2_session_id_derivation.py`] |
| SC-3 | Two viewports opened via the same Client share the same session (clipboard, stashes) | `behavioral` | Copy via one viewport, paste via another | [`test/test_sc3_session_id.py`] |
| SC-4 | Viewports opened via different Clients have isolated state | `behavioral` | Same file edit in two clients — independent buffers | [`test/test_sc4_session_isolation.py`] |
| SC-5 | All existing tests pass after fixture update (`session_id` removed from call args) | `behavioral` | `uv run pytest test/` | N/A (regression suite) |
| SC-6 | Two Clients simulating orchestrator + clean-room sub-agent — one opens viewport, other lists viewports. Documents whether session forwarding is needed. | `behavioral` (observational) | Python test using in-memory `Client(transport=server)` with probe tool | [`test/test_sc6_subagent_session_observation.py`] |
| SC-7 | `docs/mcp-plugin-behavior.md` exists and documents observed session behavior from test output | `behavioral` (observational) | SC-1 through SC-6 test output as evidence; no code-reading | N/A (documentation artifact) |

## SC-7: Observational Documentation Specification

### Rationale

SC-7 documents what was observed from running the behavioral test suite (SC-1 through SC-6). All evidence must come from test output — no code reading, no source inspection, no claims about implementation internals.

### Investigation Topics (from test output only)

1. **Schema change** — `list_tools()` output from SC-1 shows tools without `session_id` parameter
2. **Connection-derived identity** — `ctx.session_id` values printed by SC-2 test show UUIDs per connection
3. **Same-connection sharing** — SC-3 test output shows clipboard content shared across viewports
4. **Cross-connection isolation** — SC-4 test output shows different session IDs and independent buffers
5. **Sub-agent transport continuity** — SC-6 test output shows whether C2 sees C1's viewports

### Evidence Sources

| Topic | Evidence Source | Method |
|-------|----------------|--------|
| Schema | SC-1 tool parameter inspection | `list_tools()` response printed by test |
| Session ID | SC-2 `ctx.session_id` echo | Test output showing UUID values |
| Session sharing | SC-3 clipboard paste across viewports | Test output showing paste success |
| Session isolation | SC-4 two-client edit test | Test output showing independent buffers |
| Sub-agent transport | SC-6 probe_sid observation | Test output showing C1/C2 session comparison |

### Phasing

SC-6 runs after Card 1 (which is DONE). Pass 3 docs run after SC-6.

## Related Issues

| Issue | Relationship | URL |
|-------|-------------|-----|
| #46 — Switch to standalone fastmcp | Prerequisite — provides `ctx.session_id` via `fastmcp>=3.0,<4.0`. Must be resolved before Pass 1. | https://github.com/michael-conrad/viewport-editor/issues/46 |
| #39/#45 — Parameter name normalization | Prerequisite — moves `ctx` to first parameter position for clean `Context` typing. | https://github.com/michael-conrad/viewport-editor/issues/39 |

## Rollback

Tag `fix/pre-session-id-refactor` marks the pre-refactor state.
