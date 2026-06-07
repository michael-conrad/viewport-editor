# Card Catalogue — Spec #38 (Revised): Remove agent-provided session_id

## Dependency Order

```
Card 1 — server.py tool stubs/handlers .......... DONE (PR #49, merged dev)
Card 2 — SC-6 observational test ............... PENDING
Card 3 — Phase C docs (observational) ........... PENDING
Card 4 — rollback tag + issue close ............ PENDING
```

**Phase B (manager method signatures) — CANCELLED** after feasibility research.
Managers are internal API never called by agents. Every approach to remove
`session_id` from manager signatures either breaks session isolation
(contradicts SC-4), introduces concurrency bugs, or changes nothing meaningful.

## Card 1 — Core Session Derivation

**Status:** DONE (PR #49, merged to dev)
**Target:** `src/viewport_editor/server.py`
**Scope:** 6 tool stubs + 19 handler functions
**Related files:** All SC-1 through SC-5 tests, 10 migrated test files
**Verification:** SC-1 through SC-5 PASS (behavioral tests at 149/149)

## Card 2 — SC-6 Observational Test

**Status:** PENDING
**Target:** `test/test_sc6_subagent_session_observation.py`

**Clean-room implementation spec:**

```
Write test_sc6_subagent_session_observation.py:
  - Own server: create_server(str(tmp_path)), NOT conftest fixtures
  - Register probe_sid(ctx: Context, label: str) -> str tool echoing ctx.session_id
  - Two sequential Client(transport=server) connections
  - C1: viewport open test.txt, probe session_id
  - C2: viewport list, probe session_id
  - Print: C1 sid, C2 sid, same/different, C2 viewport list result
  - ZERO assertions — observational only
  - Lint: ruff clean
```

**Verification:** `uv run pytest test/test_sc6_subagent_session_observation.py -v --tb=short` — 1 PASS
**Adversarial audit:** Dual cross-family auditor verification required
**PR:** Single branch, targets dev

## Card 3 — Phase C Observational Documentation

**Status:** PENDING
**Target:** `docs/mcp-plugin-behavior.md`

**Evidence constraint:** ALL content must cite test output from SC-1 through SC-6.
No code reading, no source inspection, no claims about implementation internals.

**Required topics:**
1. Schema — SC-1 `list_tools()` output shows no `session_id` parameter
2. Connection identity — SC-2 test shows `ctx.session_id` UUIDs per connection
3. Same-connection sharing — SC-3 test shows clipboard shared across viewports
4. Cross-connection isolation — SC-4 test shows independent buffer state
5. Sub-agent transport — SC-6 test shows C2 viewport isolation vs C1

**Verification:** File exists. Evidence source cited for every claim.
No code-reading claims present.
**PR:** Single branch, targets dev (may combine with Card 2 branch).

## Card 4 — Rollback Tag + Issue Close

**Target:** Git tag + GitHub issue
1. Tag: `git tag fix/pre-session-id-refactor` at commit before PR #49 base
2. Close: `github_issue_write(method="update", state="closed", state_reason="completed")`
3. Comment: PR #49 ref + SC-1 through SC-6 verification summary
4. Remove `approved-for-*` labels if present