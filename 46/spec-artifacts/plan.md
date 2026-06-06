# Implementation Plan: #46 — Switch to standalone `fastmcp`

## Parent Spec

`.issues/46/spec.md`

## What Must Be True

The spec defines seven success criteria. This plan decomposes them into implementable units such that each SC is satisfied by the end.

### Precondition (#39/#45)

- `ctx` is already the first parameter in all 7 tool handlers
- Parameter name normalization is merged on `dev`

### SC-1 — `from fastmcp import FastMCP` works, all tools register

Two things must change:

**1a — Install the package.** `fastmcp` must be present in the project venv. Package is at PyPI as `fastmcp>=3.0,<4.0`.

**1b — Change the import path.** `server.py` currently imports `from mcp.server.fastmcp import FastMCP`. Must become `from fastmcp import FastMCP`. FastMCP 3.x uses strict Pydantic — any `call_tool("edit", arguments={...})` that passes `file_path` as an undeclared kwarg will be rejected. There are 21 such calls across 4 test files that must have `file_path` removed.

Constraint: 1b requires 1a.

### SC-2 — Lifespan handler runs on startup and shutdown

The lifespan pattern (`@asynccontextmanager` + `lifespan=` parameter) is identical between bundled and standalone fastmcp. No code change required. Verification test only.

### SC-3 — `ctx.session_id` returns non-empty string

Two things must change:

**3a — Annotate `ctx` parameters.** All 7 handlers currently use `ctx: Any = None`. Must become `ctx: Context`. The `Context` class is imported from `fastmcp`. Standalone fastmcp's type-hint injection makes `ctx.session_id` accessible.

**3b — Verify `ctx.session_id`.** `ctx.session_id` is a built-in property of standalone fastmcp's `Context`. No handler code changes beyond 3a. Verification test confirms a tool handler returns a non-empty `session_id`.

Constraint: 3a requires 1a. 3b requires 3a.

### SC-4 — Two in-memory clients have different `ctx.session_id` values

No handler code change required. Verification test: create two `Client(server)` instances, make a tool call through each, confirm different `session_id` values.

Constraint: requires SC-3 and SC-5 (in-memory client test infrastructure).

### SC-5 — All existing tests pass

All 11 test files currently use per-file `stdio_client` + `ClientSession` fixtures with subprocess server. Two things must change to use standalone fastmcp's in-memory `Client`:

**5a — Shared fixture.** Create `test/conftest.py` with `client = Client(create_server(...))` fixture.

**5b — File migration.** Remove per-file `server_params`, `client_session` fixtures, `stdio_client` imports, and `_get_text()` helpers. Wire to conftest fixture.

Constraint: 5a requires 1a. 5b requires 5a.

### SC-6 — Install size delta documented

No code change required. Measure `du -sh` on `fastmcp` and `mcp` site-packages. Record delta.

### SC-7 — Session state isolation

Add a handler (or use an existing one) that stores/retrieves state via `ctx.set_state`/`ctx.get_state`. Verification test: client A sets counter=3, client B reads counter=0.

Constraint: requires SC-3 and SC-5.

---

## Implementation Order

Each item below runs the 14-step pipeline: `sc-coherence-gate → pre-red-baseline → red-phase → red-doublecheck → green-phase → checkpoint-commit → structural-checks → green-doublecheck → green-vbc → adversarial-audit → cross-validate → regression-check → review-prep → exec-summary`.

| Order | Item | What | Code | Test-Only | Requires |
|-------|------|------|------|-----------|----------|
| 1 | 1a | `uv add fastmcp` | Yes | No | — |
| 2 | 1b | Change import, remove 21 `file_path` args | Yes | No | 1a |
| 3 | 3a | `ctx: Any = None` → `ctx: Context` on 7 handlers | Yes | No | 1a |
| 4 | 3b | `ctx.session_id` returns non-empty str | No | Yes | 3a |
| 5 | 5a | Create `test/conftest.py` in-memory fixture | Yes | No | 1a |
| 6 | 5b | Migrate 11 test files to conftest fixture | Yes | No | 5a |
| 7 | 2 | Lifespan handler verification | No | Yes | 1a |
| 8 | 6 | Install size measurement | No | N/A | 1a |
| 9 | 4 | Two clients → different session IDs | No | Yes | 3b, 5b |
| 10 | 7 | Session state isolation PoC | Yes (handler) | Yes | 3b, 5b |

Items 5, 6, 7, 8 may run in any order (no interdependencies).

---

## State Tracking

The file `.issues/46/spec-artifacts/dependency-contract.yaml` defines a Z3 model with boolean variables for each item above. The file `.issues/46/spec-artifacts/state.yaml` holds the current state. After each item completes, flip its variable to `True`:

```bash
bash .opencode/tools/solve state update .issues/46/spec-artifacts/state.yaml \
  --contract-path .issues/46/spec-artifacts/dependency-contract.yaml \
  --var-name <VARIABLE> --var-value True

bash .opencode/tools/solve check \
  --state-path .issues/46/spec-artifacts/state.yaml \
  --contract-path .issues/46/spec-artifacts/dependency-contract.yaml
```