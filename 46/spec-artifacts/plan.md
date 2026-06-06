# Implementation Plan: #46 — Switch to standalone `fastmcp`

## Parent Spec

`.issues/46/spec.md`

## What Must Be True

The spec defines seven success criteria. Each unit below satisfies part of one or more SCs. Every unit runs the full 14-step pipeline: `sc-coherence-gate → pre-red-baseline → red-phase → red-doublecheck → green-phase → checkpoint-commit → structural-checks → green-doublecheck → green-vbc → adversarial-audit → cross-validate → regression-check → review-prep → exec-summary`.

### Precondition (#39/#45)

- `ctx` is already the first parameter in all 7 tool handlers
- Parameter name normalization is merged on `dev`

---

### 1a — Install `fastmcp` package

**Satisfies:** SC-1  
**RED:** importing `fastmcp` fails or `FastMCP` is not callable  
**GREEN:** `fastmcp` is present in the project venv  
**Depends on:** nothing

---

### 1b — Import from `fastmcp`, not `mcp.server.fastmcp`

**Satisfies:** SC-1  
**RED:** `create_server()` does not produce a `FastMCP` instance with 7 tools registered  
**GREEN:** import path changed; 21 dead `file_path` kwargs removed from `call_tool("edit", ...)` test sites (FastMCP 3.x strict Pydantic rejects undeclared kwargs)  
**Depends on:** 1a

---

### 3a — `ctx: Context` annotation on all 7 handlers

**Satisfies:** SC-3  
**RED:** handler `ctx` parameter lacks `Context` type annotation (introspection or runtime)  
**GREEN:** `from fastmcp import Context` added; all 7 handler signatures use `ctx: Context`  
**Depends on:** 1a

---

### 3b — `ctx.session_id` returns non-empty string

**Satisfies:** SC-3  
**RED:** tool handler does not return a non-empty `session_id` value  
**GREEN:** none (test only — `ctx.session_id` is a built-in property of standalone fastmcp's `Context`)  
**Depends on:** 3a

---

### 5a — Shared in-memory client fixture in conftest

**Satisfies:** SC-5  
**RED:** conftest `client` fixture does not exist or produces incorrect tool call results  
**GREEN:** `test/conftest.py` provides `client = Client(create_server(...))` fixture  
**Depends on:** 1a

---

### 5b — Migrate test files to conftest fixture

**Satisfies:** SC-5  
**RED:** per-file `stdio_client` or `ClientSession` fixtures still present  
**GREEN:** 11 test files use shared conftest fixture; per-file fixture duplication removed  
**Depends on:** 5a

---

### SC-2 — Lifespan handler verification

**Satisfies:** SC-2  
**RED:** lifespan enter/exit not invoked by fastmcp runtime  
**GREEN:** none (test only — pattern is identical between SDKs)  
**Depends on:** 1a

---

### SC-6 — Install size documented

**Satisfies:** SC-6  
**GREEN:** `du -sh` on fastmcp and mcp site-packages; delta recorded in cards.md  
**Depends on:** 1a

---

### SC-4 — Unique session IDs

**Satisfies:** SC-4  
**RED:** two `Client(server)` instances return identical or empty `session_id` values  
**GREEN:** none (test only)  
**Depends on:** 3b, 5b

---

### SC-7 — Session state isolation

**Satisfies:** SC-7  
**RED:** client A sets state, client B reads the same state (not isolated)  
**GREEN:** handler stores/retrieves state via `ctx.set_state`/`ctx.get_state`  
**Depends on:** 3b, 5b

---

## Dependencies

```
1a ──→ 1b ──→ 3a ──→ 3b ───┐
 │                           ├──→ SC-4
 │                           │
 └──→ 5a ──→ 5b ────────────┤
 │                           └──→ SC-7
 ├──→ SC-2
 └──→ SC-6
```

Units 5a, 5b, SC-2, SC-6 have no interdependencies — any order after 1a.

---

## Z3 Model

`.issues/46/spec-artifacts/dependency-contract.yaml` models each unit's 14 pipeline gates as booleans. A unit's domain variable is `True` only after all 14 gates pass. All 11 domain dependency theorems and all pipeline serialization theorems proven VALID. Initial state verified SAT.

### Variable Map

| Domain Variable | Unit | Pipeline Prefix |
|----------------|------|-----------------|
| `DEP_SWITCH` | 1a | `DEP_p1..p14` |
| `IMPORT_CHANGE` | 1b | `IMP_p1..p14` |
| `CTX_ANNOTATE` | 3a | `CTX_p1..p14` |
| `SESSION_ID_OK` | 3b | `SES_p1..p14` |
| `CONFTEST` | 5a | `CON_p1..p14` |
| `TEST_MIGRATED` | 5b | `TST_p1..p14` |
| `LIFESPAN_OK` | SC-2 | `LIF_p1..p14` |
| `SIZE_DOCUMENTED` | SC-6 | (structural — no pipeline) |
| `DIFF_SESSION_IDS` | SC-4 | `DIF_p1..p14` |
| `STATE_ISOLATION` | SC-7 | `STA_p1..p14` |

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