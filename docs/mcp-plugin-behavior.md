# MCP Plugin Session Behavior

> **Source of truth:** This document is derived exclusively from behavioral test output. No implementation code was read or cited.

## Summary Table

| Property | Evidence | Test |
|----------|----------|------|
| `session_id` parameter absent from tool schemas | All 6 tools lack `session_id` in `inputSchema.properties` | SC-1 |
| Session identity derived from connection | Each `Client` connection gets a UUID session ID | SC-2, SC-4 |
| Same-connection session sharing | Clipboard content shared across viewports on same `Client` | SC-3 |
| Cross-connection session isolation | Different `Client` instances get different session IDs; buffers are independent | SC-4 |
| Sub-agent transport continuity | C2 (sub-agent) has a different session ID than C1 (orchestrator) and sees an empty session | SC-6 |

## Section 1: Schema — Tool Parameters

The `session_id` parameter has been removed from all six tool stubs' `inputSchema` definitions. Test `test_sc1_schema_no_session_id` (SC-1) inspects the `list_tools()` response and verifies that `"session_id"` is absent from the `properties` object of every tool's `inputSchema` — this includes `viewport`, `edit`, `file`, `diff`, `search`, and `clipboard`. The `regex` tool, which never had a `session_id` parameter, is independently verified absent in `test_sc1_regex_no_session_id` (SC-1).

Both open behavioral tests confirm the change is functional: `test_sc1_behavioral_open_no_session_id` (SC-1) opens a viewport without passing `session_id` and succeeds. `test_sc1_behavioral_all_tools_without_session_id` (SC-1) calls all seven tools (`viewport`, `edit`, `file`, `diff`, `clipboard`, `search`, `regex`) without `session_id` in any argument, and all succeed.

## Section 2: Connection-Derived Session Identity

Two sequential `Client` connections to the same server each operate in isolated sessions. Test `test_sc2_two_clients_separate_sessions` (SC-2) demonstrates this: the first client opens a viewport; the second client, connecting separately, calls `viewport:list` and sees `"no open viewports"` — confirming the second connection does not inherit the first connection's state.

Test `test_sc2_viewport_works_without_session_id` (SC-2) confirms that `viewport` open/scroll/close operations work without a `session_id` argument. Test `test_sc2_edit_file_clipboard_work_without_session_id` (SC-2) extends the same proof to `edit`, `file` save, and `clipboard` copy operations.

Test `test_sc4_unique_session_ids` (SC-4) directly probes the connection-derived identity by registering a `probe` tool that captures `ctx.session_id`. Two sequential `Client` connections to the same test server produce different UUID values, proving each connection receives its own session identity.

## Section 3: Same-Connection Session Sharing

Viewports opened through the same `Client` connection share a session. Test `test_sc3_same_client_clipboard_shared` (SC-3) opens two viewports (`test.txt` and `other.txt`) on the same `Client`, copies text from the first viewport to the clipboard, then pastes it into the second viewport. The paste succeeds with a `"pasted from clipboard"` confirmation, confirming clipboard state is shared across viewports within one connection.

Test `test_sc3_same_client_stash_shared` (SC-3) extends the same principle to stash/pop operations: clipboard content stashed from one viewport is successfully popped from a different viewport on the same `Client` connection.

## Section 4: Cross-Connection Session Isolation

Different `Client` connections to the same server are isolated from each other. Test `test_sc4_unique_session_ids` (SC-4) connects two sequential `Client` instances to the same `FastMCP` server, each registering a `probe` tool that captures `ctx.session_id`. The two session IDs differ, confirming the server assigns distinct session identities per connection.

Test `test_sc4_concurrent_clients` (SC-4) extends this to concurrent operation: two `Client` instances connect simultaneously using `asyncio.gather`, each calling `probe` concurrently. The captured session IDs differ, confirming that even simultaneous connections through the same server produce independent session identities.

Together, SC-4 demonstrates that each MCP connection boundary corresponds to an independent session, and no state leaks between connections.

## Section 5: Full-Session Isolation (Separate CLI Invocations)

Test `test_sc6_subagent_session_observation` (SC-6) models separate `opencode-cli run` invocations by opening two independent `Client` connections to the same server. C1 opens a viewport while C2 connects concurrently. Both connections are active simultaneously.

The test output shows the following observational data (zero assertions — printed only):

```text
  C1 session ID:  C1: c7fbf074-eaf7-4522-a347-03976b62aa4a
  C2 session ID:  C2: 70a7ead7-0657-4f7b-aa9d-362284c9c0ed
  Sessions are:   DIFFERENT
  Forwarding needed: YES
  C2 viewport list output:
      no open viewports
```

<<<<<<< HEAD
The two session IDs differ (`c7fbf074-eaf7-4522-a347-03976b62aa4a` vs `70a7ead7-0657-4f7b-aa9d-362284c9c0ed`). C2 calls `viewport:list` while C1's viewport is still open and receives `"no open viewports"`. This demonstrates that **separate connections** (separate CLI invocations) get independent session state.

**Important distinction:** This is NOT equivalent to sub-agent dispatch within a single `opencode-cli run`. A `task()` sub-agent shares the same MCP connection and `ctx.session_id` as the orchestrator. Within one invocation, two viewports on the same file share a buffer — `BufferManager` keys by `(session_id, file_path)`, and all tool calls within one MCP connection share the same `session_id`. Clean-room sub-agent isolation occurs at the invocation boundary, not the viewport boundary.

## Section 6: Same-Connection Viewport Buffer Sharing (Observational)

Behavioral card SC-4 (observational only, no assertion) documents buffer sharing within a single session: two viewports opened on the same file through the same MCP connection share a single `BufferManager` entry. An edit in viewport A is immediately visible in viewport B's diff. This is by design — viewports are display windows into a shared buffer, not independent buffer copies.

**Operational parameters:**

| Parameter | Value |
|-----------|-------|
| Buffer sharing scope | Per `(session_id, file_path)` |
| Viewport-to-viewport isolation (same session) | No — shared buffer |
| Cross-invocation isolation (separate `opencode-cli run`) | Yes — independent session, independent buffer |
| Sub-agent within same invocation | Shares buffer with orchestrator |
| Card SC-4 type | Observational only — no assertion, no expected outcome |
=======
The two session IDs differ (`c7fbf074-eaf7-4522-a347-03976b62aa4a` vs `70a7ead7-0657-4f7b-aa9d-362284c9c0ed`). C2 calls `viewport:list` while C1's viewport is still open and receives `"no open viewports"`. This demonstrates that the sub-agent (C2), connecting through its own MCP transport, operates in a separate session with no visibility into the orchestrator's viewports.

The test classifies `Forwarding needed: YES`, meaning the sub-agent's empty session is the correct isolation behavior for a clean-room dispatch: the sub-agent starts fresh without inheriting the orchestrator's viewport state.

