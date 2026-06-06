# Implementation Plan: #46 — Switch to standalone `fastmcp`

## Parent Spec

`.issues/46/spec.md`

## What Must Be True

| Unit | Satisfies | Code Change Required | Depends On |
|------|-----------|---------------------|------------|
| 1a — install `fastmcp` package | SC-1 | `uv add fastmcp` | — |
| 1b — import from `fastmcp`, not `mcp.server.fastmcp`; remove dead `file_path` from 21 test `edit()` call sites | SC-1 | `server.py:16` import path; 4 test files, 21 call sites | 1a |
| 3a — `ctx: Context` annotation on all 7 handlers (currently `ctx: Any = None`) | SC-3 | `from fastmcp import Context`; 7 handler signatures | 1a |
| 3b — `ctx.session_id` returns non-empty string in handler | SC-3 | none (test only) | 3a |
| 5a — shared `client` fixture in `test/conftest.py` using `Client(create_server(...))` | SC-5 | `test/conftest.py` | 1a |
| 5b — migrate 11 test files from per-file `stdio_client` + `ClientSession` to conftest fixture; remove duplicate fixtures | SC-5 | all 11 test files | 5a |
| SC-2 — lifespan handler enter/exit works with standalone fastmcp | SC-2 | none (test only) | 1a |
| SC-6 — install size delta documented in cards.md | SC-6 | `du -sh` measurement only | 1a |
| SC-4 — two `Client(server)` instances produce different `session_id` | SC-4 | none (test only) | 3b, 5b |
| SC-7 — `ctx.set_state`/`ctx.get_state` session isolation | SC-7 | handler with state storage (optional: reuse existing or add new) | 3b, 5b |

Units 5a, 5b, SC-2, SC-6 have no interdependencies — any order after 1a.

Each unit passes the full 14-step pipeline (`sc-coherence-gate → pre-red-baseline → red-phase → red-doublecheck → green-phase → checkpoint-commit → structural-checks → green-doublecheck → green-vbc → adversarial-audit → cross-validate → regression-check → review-prep → exec-summary`) before its domain variable flips to `True` in the Z3 model.

## Z3 Model

`.issues/46/spec-artifacts/dependency-contract.yaml` — 10 domain variables, 126 pipeline gate variables. Each unit's domain variable is only `True` after all 14 pipeline gates pass. Domain dependency ordering enforced via invariants. All 11 dependency theorems and all pipeline serialization theorems proven VALID.

### State Update

After each unit completes:

```bash
bash .opencode/tools/solve state update .issues/46/spec-artifacts/state.yaml \
  --contract-path .issues/46/spec-artifacts/dependency-contract.yaml \
  --var-name <VARIABLE> --var-value True

bash .opencode/tools/solve check \
  --state-path .issues/46/spec-artifacts/state.yaml \
  --contract-path .issues/46/spec-artifacts/dependency-contract.yaml
```