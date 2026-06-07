# Implementation Plan — Spec #38: Remove agent-provided session_id

**Domain:** spec-38-session-id
**Plan length:** 14 steps
**Status:** SOLVED_SATISFICING

## Dependency Order

```
Phase A ──→ Phase B ──→ Phase C
 (steps 1-5)   (steps 6-12)  (step 14)
```

## Step Plan

### Phase A: Core Session Derivation

| # | Action | Files | Verification |
|---|--------|-------|-------------|
| 1 | `phase_a_extract_ctx_session_id()` — Add `session_id = ctx.session_id` inside each of 6 tool stubs before calling handler | `server.py` | SC-2 |
| 2 | `verify_sc2()` — Confirm each tool handler now returns its `session_id` from `ctx`, proving derivation works | test | `test_sc2_session_id_derivation.py` |
| 3 | `phase_a_remove_session_id_from_stubs()` — Remove `session_id: str = ""` from all 6 tool stub signatures | `server.py` | SC-1 |
| 4 | `phase_b_remove_from_buffer()` — Remove `session_id: str` from all 9 BufferManager method signatures | `buffer.py` | SC-5 |
| 5 | `mark_phase_a_done()` | — | — |

### Phase B: Manager-Level Cleanup

| # | Action | Files | Verification |
|---|--------|-------|-------------|
| 6 | `phase_b_remove_from_tests()` — Remove `"session_id":` entries from all `arguments={}` dicts in test files | `test/` (16 files) | SC-5 |
| 7 | `phase_b_remove_from_viewport()` — Remove `session_id: str` from all 29 ViewportManager method signatures | `viewport.py` | SC-5 |
| 8 | `mark_phase_b_done()` | — | — |

### Verification (SCs 1-6)

| # | Action | SC | Method |
|---|--------|----|--------|
| 9 | `verify_sc1()` | SC-1 — no tool accepts `session_id` param | `list_tools` via Client |
| 10 | `verify_sc4()` | SC-4 — two Clients have isolated state | In-memory `Client` test |
| 11 | `verify_sc6()` | SC-6 — observational: sub-agent transport continuity | `test_sc6_subagent_session_observation.py` |
| 12 | `verify_sc5()` | SC-5 — all existing tests pass | `uv run pytest test/` |
| 13 | `verify_sc3()` | SC-3 — two viewports same Client share session | Copy/paste across viewports |

### Phase C: Documentation

| # | Action | Artifact | Verification |
|---|--------|----------|-------------|
| 14 | `phase_c_produce_docs()` — Create `docs/mcp-plugin-behavior.md` with 6 investigation topics | `docs/mcp-plugin-behavior.md` | SC-7 |

## Validated By Planner

The Tamer planner confirmed this plan satisfies all goals (`phase_done(phase_a)`, `phase_done(phase_b)`, `phase_done(phase_c)`) with 14 steps. Rollback action (`git reset --hard fix/pre-session-id-refactor`) is available if SC-5 fails.