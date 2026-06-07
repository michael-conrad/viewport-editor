# Verification Plan: #46 — Standalone fastmcp Switch

## Precondition Check

- [ ] Branch is `feature/46-card-1a-fastmcp-install`
- [ ] Z3 model reports SAT for all 10 domain variables
- [ ] Working tree is clean (`git status`)

---

## SC-1: `from fastmcp import FastMCP` works, 7 tools register

**Evidence type:** behavioral

- [ ] `uv run python -c "from fastmcp import FastMCP; print(FastMCP('test'))"` — no ImportError
- [ ] `uv run pytest test/test_phase1_server_viewport.py::test_sc1_exactly_6_tools -xq` — PASS
- [ ] `from viewport_editor.server import create_server; from fastmcp import Client; async with Client(transport=create_server('/tmp')) as c: tools = await c.list_tools(); assert len(tools) == 7` — 7 tools confirmed
- [ ] Confirm `from mcp.server.fastmcp import FastMCP` does NOT appear in `src/` (grep returns 0)
- [ ] Confirm `from fastmcp import FastMCP` appears in `src/viewport_editor/server.py:16`

---

## SC-2: Lifespan handler runs on startup and shutdown

**Evidence type:** behavioral

- [ ] `uv run pytest test/test_sc2_lifespan.py -xq` — PASS
- [ ] Verify lifespan pattern: `create_server()` uses `@asynccontextmanager` + `lifespan=` parameter
- [ ] `grep -n 'lifespan=' src/viewport_editor/server.py` — confirms lifespan parameter present

---

## SC-3: `ctx.session_id` returns non-empty string within tool handler

**Evidence type:** behavioral

- [ ] `uv run pytest test/test_sc3_session_id.py::test_sc3_session_id_is_non_empty_string -xq` — PASS
- [ ] `uv run python -c "from fastmcp import FastMCP, Context, Client; s=FastMCP('t'); @s.tool() def p(ctx:Context)->str: return ctx.session_id; import asyncio; asyncio.run(async def(): async with Client(transport=s) as c: r=await c.call_tool('p',{}); print(r.content[0].text)); assert len(r.content[0].text) > 0"` — non-empty UUID

---

## SC-4: Two in-memory clients have different `ctx.session_id` values

**Evidence type:** behavioral

- [ ] `uv run pytest test/test_sc4_session_isolation.py -xq` — PASS
- [ ] `uv run pytest test/test_sc3_session_id.py::test_sc3_two_clients_different_session_ids -xq` — PASS

---

## SC-5: All existing tests pass

**Evidence type:** behavioral

- [ ] `uv run pytest test/ -xq` — 139 passed, 0 failed
- [ ] Compare count: expected 139 (132 baseline + 7 new SC tests)

---

## SC-6: Install size delta documented

**Evidence type:** structural

- [ ] `.issues/46/spec-artifacts/cards.md` Card 6 contains `du -sb` sizes for fastmcp and mcp
- [ ] `du -sb .venv/lib/python3.13/site-packages/fastmcp` — verify < 10 MB
- [ ] `du -sb .venv/lib/python3.13/site-packages/mcp` — verify < 5 MB
- [ ] Documented sizes match actual: fastmcp ≈ 4.1 MB, mcp ≈ 1.6 MB, delta ≈ +2.5 MB

---

## SC-7: `ctx.set_state`/`ctx.get_state` demonstrates session isolation

**Evidence type:** behavioral

- [ ] `uv run pytest test/test_sc7_state_isolation.py -xq` — PASS
- [ ] Isolation proof: Client A sets state, Client B reads None (fresh session)
- [ ] Counter proof: Client A increments 1→2, Client B starts at 1

---

## Structural Verification

- [ ] `uvx ruff check --fix src/ test/` — lint clean
- [ ] `uvx ruff format --check src/ test/` — format clean
- [ ] `uvx pyright src/` — type check clean (0 errors)

---

## Cards Complete (from Z3 state)

| Card | Variable | Status |
|------|----------|--------|
| 1a — dep declaration | `DEP_SWITCH` | ✅ |
| 1b — import + file_path removal | `IMPORT_CHANGE` | ✅ |
| 5a — conftest fixture | `CONFTEST` | ✅ |
| 5b — test migration | `TEST_MIGRATED` | ✅ |
| SC-2 — lifespan test | `LIFESPAN_OK` | ✅ |
| SC-6 — install size | `SIZE_DOCUMENTED` | ✅ |
| 3a — ctx annotation | `CTX_ANNOTATE` | ✅ |
| 3b — session_id test | `SESSION_ID_OK` | ✅ |
| SC-4 — unique IDs | `DIFF_SESSION_IDS` | ✅ |
| SC-7 — state isolation | `STATE_ISOLATION` | ✅ |

---

## Post-Verification

- [ ] All SC checklist items marked PASS
- [ ] Z3 model `bash .opencode/tools/solve check --state-path .issues/46/spec-artifacts/state.yaml --contract-path .issues/46/spec-artifacts/dependency-contract.yaml` — SAT with all True
- [ ] Branch is ready for review-prep / PR