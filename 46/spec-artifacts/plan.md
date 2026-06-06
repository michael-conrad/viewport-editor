# Implementation Plan: #46 — Switch to standalone `fastmcp`

## Parent Spec

`.issues/46/spec.md`

## What Must Be True

The spec defines seven success criteria. This plan decomposes them into implementable units such that each SC is satisfied by the end. Each unit runs the full 14-step pipeline:

```
sc-coherence-gate → pre-red-baseline → red-phase → red-doublecheck → green-phase
→ checkpoint-commit → structural-checks → green-doublecheck → green-vbc
→ adversarial-audit → cross-validate → regression-check → review-prep → exec-summary
```

### Precondition (#39/#45)

- `ctx` is already the first parameter in all 7 tool handlers
- Parameter name normalization is merged on `dev`

### SC-1 — `from fastmcp import FastMCP` works, all tools register

Two units:

**1a — Install the package.** `fastmcp` must be present in the project venv as `fastmcp>=3.0,<4.0`.

| Pipeline Gate | Requirement |
|---------------|-------------|
| RED test | `for mcp_test in "import fastmcp", "FastMCP is callable": assert that mcp_test raises ImportError` |
| GREEN code | `uv add fastmcp` |

Constraint: none (first unit).

**1b — Change the import path.** `server.py` must import `FastMCP` from standalone `fastmcp`, not from the bundled SDK. FastMCP 3.x strict Pydantic rejects undeclared kwargs — 21 `call_tool("edit", arguments={"file_path": ...})` calls across 4 test files pass dead `file_path` data and must be removed.

| Pipeline Gate | Requirement |
|---------------|-------------|
| RED test | `from viewport_editor import create_server; server = create_server(); assert len(server.list_tools()) == 7` fails with import error |
| GREEN code | `server.py:16`: `from mcp.server.fastmcp` → `from fastmcp`. Remove `file_path` from 21 `call_tool("edit", ...)` calls in `test_phase2_edit_diff.py` (16), `test_p3_autosave.py` (3), `test_phase1_server_viewport.py` (1), `test_phase3_filenew_saveas.py` (1) |

Constraint: requires 1a.

### SC-2 — Lifespan handler runs on startup and shutdown

The lifespan pattern (`@asynccontextmanager` + `lifespan=`) is identical between bundled and standalone fastmcp. No code change required.

| Pipeline Gate | Requirement |
|---------------|-------------|
| RED test | Server startup logs lifespan enter, shutdown triggers lifespan exit |
| GREEN code | None |

Constraint: requires 1a.

### SC-3 — `ctx.session_id` returns non-empty string

Two units:

**3a — Annotate `ctx` parameters.** All 7 handlers must accept `ctx: Context` instead of `ctx: Any = None`.

| Pipeline Gate | Requirement |
|---------------|-------------|
| RED test | Handler signatures do not have `Context` type on `ctx` param (`inspect.signature`, `typing.get_type_hints`, or runtime failure) |
| GREEN code | `from fastmcp import Context` in `server.py`. All 7 handler signatures: `ctx: Any = None` → `ctx: Context` |

Constraint: requires 1a.

**3b — Verify `ctx.session_id`.** `ctx.session_id` is a built-in property of standalone fastmcp's `Context`. No handler code change beyond 3a.

| Pipeline Gate | Requirement |
|---------------|-------------|
| RED test | Tool call response does not contain a non-empty `session_id` value |
| GREEN code | None |

Constraint: requires 3a.

### SC-4 — Two in-memory clients have different `ctx.session_id` values

No handler code change required.

| Pipeline Gate | Requirement |
|---------------|-------------|
| RED test | Two `Client(server)` instances return identical or empty `session_id` values |
| GREEN code | None |

Constraint: requires SC-3 and SC-5.

### SC-5 — All existing tests pass

Two units:

**5a — Shared in-memory fixture.** `test/conftest.py` must provide a `client` fixture using standalone fastmcp's `Client`.

| Pipeline Gate | Requirement |
|---------------|-------------|
| RED test | Importing `client` from conftest fails or produces wrong results |
| GREEN code | `test/conftest.py` with `client = Client(create_server(...))` + `async with client:` |

Constraint: requires 1a.

**5b — File migration.** 11 test files must use the shared conftest fixture instead of per-file `stdio_client` + `ClientSession`.

| Pipeline Gate | Requirement |
|---------------|-------------|
| RED test | Per file: `import mcp.client.session` or `stdio_client` still present in file source |
| GREEN code | Remove `server_params`, `client_session`, `_get_text()` fixtures. Wire `client_session: ClientSession` params to conftest's `client` fixture. Remove `from mcp.client.session import ClientSession` and `from mcp.client.stdio import stdio_client` imports. |

Constraint: requires 5a.

### SC-6 — Install size delta documented

No code change required.

| Pipeline Gate | Requirement |
|---------------|-------------|
| RED test | N/A (structural) |
| GREEN code | `du -sh` on `fastmcp` and `mcp` site-packages; delta recorded in cards.md |

### SC-7 — Session state isolation

| Pipeline Gate | Requirement |
|---------------|-------------|
| RED test | Client A sets counter=3 via `ctx.set_state`, Client B reads counter — B's counter is not 0 |
| GREEN code | `viewport:ping` handler (or reuse existing) that stores/retrieves state via `ctx.set_state`/`ctx.get_state` |

Constraint: requires SC-3 and SC-5.

---

## Implementation Order

| Order | Unit | Code | Test-Only | Requires |
|-------|------|------|-----------|----------|
| 1 | 1a — Package install | Yes | No | — |
| 2 | 1b — Import path + test cleanup | Yes | No | 1a |
| 3 | 3a — ctx annotation | Yes | No | 1a |
| 4 | 3b — session_id verify | No | Yes | 3a |
| 5 | 5a — conftest fixture | Yes | No | 1a |
| 6 | 5b — test file migration | Yes | No | 5a |
| 7 | SC-2 — lifespan verify | No | Yes | 1a |
| 8 | SC-6 — install size | No | N/A | 1a |
| 9 | SC-4 — unique session IDs | No | Yes | 3b, 5b |
| 10 | SC-7 — state isolation | Yes (handler) | Yes | 3b, 5b |

Units 5, 6, 7, 8 may run in any order (no interdependencies).

---

## Z3 Model

The dependency contract `.issues/46/spec-artifacts/dependency-contract.yaml` models every unit's 14-step pipeline as individual booleans. Per unit: step N requires step N-1, and the domain variable goes `True` only after step 14 (`exec-summary`). All invariants proven VALID. All state transitions verified SAT.

### Variable Map

| Domain Variable | Unit | Z3 Prefix | Pipeline Gates |
|----------------|------|-----------|----------------|
| `DEP_SWITCH` | 1a — Package install | `DEP_p1..p14` | coherence → baseline → red → red-double → green → checkpoint → structural → green-double → vbc → audit → crossval → regression → review → exec |
| `IMPORT_CHANGE` | 1b — Import path | `IMP_p1..p14` | Same 14 steps |
| `CTX_ANNOTATE` | 3a — ctx annotation | `CTX_p1..p14` | Same 14 steps |
| `SESSION_ID_OK` | 3b — session_id verify | `SES_p1..p14` | Same 14 steps |
| `CONFTEST` | 5a — conftest fixture | `CON_p1..p14` | Same 14 steps |
| `TEST_MIGRATED` | 5b — test migration | `TST_p1..p14` | Same 14 steps |
| `LIFESPAN_OK` | SC-2 — lifespan | `LIF_p1..p14` | Same 14 steps |
| `SIZE_DOCUMENTED` | SC-6 — install size | N/A (structural, no pipeline) | Measurement only |
| `DIFF_SESSION_IDS` | SC-4 — unique session IDs | `DIF_p1..p14` | Same 14 steps |
| `STATE_ISOLATION` | SC-7 — state isolation | `STA_p1..p14` | Same 14 steps |

### State Update

After each unit's `exec-summary`, flip its domain variable:

```bash
bash .opencode/tools/solve state update .issues/46/spec-artifacts/state.yaml \
  --contract-path .issues/46/spec-artifacts/dependency-contract.yaml \
  --var-name <VARIABLE> --var-value True

bash .opencode/tools/solve check \
  --state-path .issues/46/spec-artifacts/state.yaml \
  --contract-path .issues/46/spec-artifacts/dependency-contract.yaml
```