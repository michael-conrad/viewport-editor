# Implementation Plan: #46 — Switch to standalone `fastmcp`

## Parent Spec

`.issues/46/spec.md`

## Precondition (#39/#45)

- `ctx` is already the first parameter in all 7 tool handlers
- Parameter name normalization is merged on `dev`

---

## Units

### 1a — Install `fastmcp` package

**Satisfies:** SC-1  
**RED:** `from fastmcp import FastMCP` fails or `FastMCP` is not callable  
**GREEN:** `fastmcp` present in project venv at `fastmcp>=3.0,<4.0`  
**Depends on:** nothing  
**Pipeline:**

| Gate | Exit Criterion |
|------|----------------|
| sc-coherence-gate | RED/GREEN items are coherent with the spec's SC-1 |
| pre-red-baseline | pre-change state recorded |
| red-phase | RED test exists and fails |
| red-doublecheck | RED test fails for the right reason |
| green-phase | code change makes RED test pass |
| checkpoint-commit | working state committed |
| structural-checks | lint, typecheck, format pass |
| green-doublecheck | GREEN test passes for the right reason |
| green-vbc | all SC-1 criteria satisfied |
| adversarial-audit | dual-family auditor verifies spec and plan fidelity |
| cross-validate | cross-family consensus: PASS |
| regression-check | `uv run pytest test/` — nothing broken |
| review-prep | branch status, compare URL, PR body |
| exec-summary | push, state update, issue comment, halt |

---

### 1b — Import from `fastmcp`, not `mcp.server.fastmcp`

**Satisfies:** SC-1  
**RED:** `create_server()` does not return a `FastMCP` instance with 7 registered tools  
**GREEN:** import path changed; 21 dead `file_path` kwargs removed from `call_tool("edit", ...)` test sites (FastMCP 3.x strict Pydantic rejects undeclared kwargs)  
**Depends on:** 1a  
**Pipeline:**

| Gate | Exit Criterion |
|------|----------------|
| sc-coherence-gate | RED/GREEN items are coherent with SC-1 |
| pre-red-baseline | pre-change state recorded |
| red-phase | RED test exists and fails |
| red-doublecheck | RED test fails for the right reason |
| green-phase | code change makes RED test pass |
| checkpoint-commit | working state committed |
| structural-checks | lint, typecheck, format pass |
| green-doublecheck | GREEN test passes for the right reason |
| green-vbc | all SC-1 criteria satisfied |
| adversarial-audit | dual-family auditor verifies spec and plan fidelity |
| cross-validate | cross-family consensus: PASS |
| regression-check | `uv run pytest test/` — nothing broken |
| review-prep | branch status, compare URL, PR body |
| exec-summary | push, state update, issue comment, halt |

---

### 3a — `ctx: Context` annotation on all 7 handlers

**Satisfies:** SC-3  
**RED:** handler `ctx` parameter lacks `Context` type annotation  
**GREEN:** `from fastmcp import Context` added; all 7 handler signatures use `ctx: Context`  
**Depends on:** 1a  
**Pipeline:**

| Gate | Exit Criterion |
|------|----------------|
| sc-coherence-gate | RED/GREEN items are coherent with SC-3 |
| pre-red-baseline | pre-change state recorded |
| red-phase | RED test exists and fails |
| red-doublecheck | RED test fails for the right reason |
| green-phase | code change makes RED test pass |
| checkpoint-commit | working state committed |
| structural-checks | lint, typecheck, format pass |
| green-doublecheck | GREEN test passes for the right reason |
| green-vbc | all SC-3 criteria satisfied |
| adversarial-audit | dual-family auditor verifies spec and plan fidelity |
| cross-validate | cross-family consensus: PASS |
| regression-check | `uv run pytest test/` — nothing broken |
| review-prep | branch status, compare URL, PR body |
| exec-summary | push, state update, issue comment, halt |

---

### 3b — `ctx.session_id` returns non-empty string

**Satisfies:** SC-3  
**RED:** tool handler does not return a non-empty `session_id` value  
**GREEN:** none (test only)  
**Depends on:** 3a  
**Pipeline:**

| Gate | Exit Criterion |
|------|----------------|
| sc-coherence-gate | RED/GREEN items are coherent with SC-3 |
| pre-red-baseline | pre-change state recorded |
| red-phase | RED test exists and fails |
| red-doublecheck | RED test fails for the right reason |
| green-phase | no code change (test only) — verify RED passes |
| checkpoint-commit | working state committed |
| structural-checks | lint, typecheck, format pass |
| green-doublecheck | GREEN test passes for the right reason |
| green-vbc | all SC-3 criteria satisfied |
| adversarial-audit | dual-family auditor verifies spec and plan fidelity |
| cross-validate | cross-family consensus: PASS |
| regression-check | `uv run pytest test/` — nothing broken |
| review-prep | branch status, compare URL, PR body |
| exec-summary | push, state update, issue comment, halt |

---

### 5a — Shared in-memory client fixture in conftest

**Satisfies:** SC-5  
**RED:** conftest `client` fixture does not exist or produces incorrect results  
**GREEN:** `test/conftest.py` provides `client = Client(create_server(...))` fixture  
**Depends on:** 1a  
**Pipeline:**

| Gate | Exit Criterion |
|------|----------------|
| sc-coherence-gate | RED/GREEN items are coherent with SC-5 |
| pre-red-baseline | pre-change state recorded |
| red-phase | RED test exists and fails |
| red-doublecheck | RED test fails for the right reason |
| green-phase | code change makes RED test pass |
| checkpoint-commit | working state committed |
| structural-checks | lint, typecheck, format pass |
| green-doublecheck | GREEN test passes for the right reason |
| green-vbc | all SC-5 criteria satisfied |
| adversarial-audit | dual-family auditor verifies spec and plan fidelity |
| cross-validate | cross-family consensus: PASS |
| regression-check | `uv run pytest test/` — nothing broken |
| review-prep | branch status, compare URL, PR body |
| exec-summary | push, state update, issue comment, halt |

---

### 5b — Migrate test files to conftest fixture

**Satisfies:** SC-5  
**RED:** per-file `stdio_client` or `ClientSession` fixtures still present  
**GREEN:** 11 test files use shared conftest fixture; per-file fixture duplication removed  
**Depends on:** 5a  
**Pipeline:**

| Gate | Exit Criterion |
|------|----------------|
| sc-coherence-gate | RED/GREEN items are coherent with SC-5 |
| pre-red-baseline | pre-change state recorded |
| red-phase | RED test exists and fails |
| red-doublecheck | RED test fails for the right reason |
| green-phase | code change makes RED test pass |
| checkpoint-commit | working state committed |
| structural-checks | lint, typecheck, format pass |
| green-doublecheck | GREEN test passes for the right reason |
| green-vbc | all SC-5 criteria satisfied |
| adversarial-audit | dual-family auditor verifies spec and plan fidelity |
| cross-validate | cross-family consensus: PASS |
| regression-check | `uv run pytest test/` — nothing broken |
| review-prep | branch status, compare URL, PR body |
| exec-summary | push, state update, issue comment, halt |

---

### SC-2 — Lifespan handler verification

**Satisfies:** SC-2  
**RED:** lifespan enter/exit not invoked by fastmcp runtime  
**GREEN:** none (test only)  
**Depends on:** 1a  
**Pipeline:**

| Gate | Exit Criterion |
|------|----------------|
| sc-coherence-gate | RED/GREEN items are coherent with SC-2 |
| pre-red-baseline | pre-change state recorded |
| red-phase | RED test exists and fails |
| red-doublecheck | RED test fails for the right reason |
| green-phase | no code change (test only) — verify RED passes |
| checkpoint-commit | working state committed |
| structural-checks | lint, typecheck, format pass |
| green-doublecheck | GREEN test passes for the right reason |
| green-vbc | all SC-2 criteria satisfied |
| adversarial-audit | dual-family auditor verifies spec and plan fidelity |
| cross-validate | cross-family consensus: PASS |
| regression-check | `uv run pytest test/` — nothing broken |
| review-prep | branch status, compare URL, PR body |
| exec-summary | push, state update, issue comment, halt |

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
**Pipeline:**

| Gate | Exit Criterion |
|------|----------------|
| sc-coherence-gate | RED/GREEN items are coherent with SC-4 |
| pre-red-baseline | pre-change state recorded |
| red-phase | RED test exists and fails |
| red-doublecheck | RED test fails for the right reason |
| green-phase | no code change (test only) — verify RED passes |
| checkpoint-commit | working state committed |
| structural-checks | lint, typecheck, format pass |
| green-doublecheck | GREEN test passes for the right reason |
| green-vbc | all SC-4 criteria satisfied |
| adversarial-audit | dual-family auditor verifies spec and plan fidelity |
| cross-validate | cross-family consensus: PASS |
| regression-check | `uv run pytest test/` — nothing broken |
| review-prep | branch status, compare URL, PR body |
| exec-summary | push, state update, issue comment, halt |

---

### SC-7 — Session state isolation

**Satisfies:** SC-7  
**RED:** client A sets state, client B reads the same state (not isolated)  
**GREEN:** handler stores/retrieves state via `ctx.set_state`/`ctx.get_state`  
**Depends on:** 3b, 5b  
**Pipeline:**

| Gate | Exit Criterion |
|------|----------------|
| sc-coherence-gate | RED/GREEN items are coherent with SC-7 |
| pre-red-baseline | pre-change state recorded |
| red-phase | RED test exists and fails |
| red-doublecheck | RED test fails for the right reason |
| green-phase | code change makes RED test pass |
| checkpoint-commit | working state committed |
| structural-checks | lint, typecheck, format pass |
| green-doublecheck | GREEN test passes for the right reason |
| green-vbc | all SC-7 criteria satisfied |
| adversarial-audit | dual-family auditor verifies spec and plan fidelity |
| cross-validate | cross-family consensus: PASS |
| regression-check | `uv run pytest test/` — nothing broken |
| review-prep | branch status, compare URL, PR body |
| exec-summary | push, state update, issue comment, halt |

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

`.issues/46/spec-artifacts/dependency-contract.yaml` models each unit's 14 pipeline gates as booleans. A unit's domain variable is `True` only when all 14 gates pass. 11 domain dependency theorems and all pipeline serialization theorems proven VALID.

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
| `SIZE_DOCUMENTED` | SC-6 | (structural) |
| `DIFF_SESSION_IDS` | SC-4 | `DIF_p1..p14` |
| `STATE_ISOLATION` | SC-7 | `STA_p1..p14` |

### State Update

```bash
bash .opencode/tools/solve state update .issues/46/spec-artifacts/state.yaml \
  --contract-path .issues/46/spec-artifacts/dependency-contract.yaml \
  --var-name <VARIABLE> --var-value True

bash .opencode/tools/solve check \
  --state-path .issues/46/spec-artifacts/state.yaml \
  --contract-path .issues/46/spec-artifacts/dependency-contract.yaml
```