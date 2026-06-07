# PR Creation Plan: #46 — Standalone fastmcp Switch

## Plan Tool Model

```bash
.opencode/tools/plan plan --problem tmp/pr-problem.yaml --engine tamer
```

---

## Step 0 — Load Skill

- [ ] `skill({name: "git-workflow"})` — load git-workflow skill for review-prep, pr-creation, and completion tasks

---

## Step 1 — Dispatch `review-prep` sub-agent (blind task())

- [ ] **Confirm branch state:** `git status` clean, working on `feature/46-card-1a-fastmcp-install`
- [ ] **Generate compare URL:** `https://github.com/michael-conrad/viewport-editor/compare/dev...feature/46-card-1a-fastmcp-install`
- [ ] **Undraft PR body:**
  - Summary of all 10 cards with per-card bullet points
  - SC status table (all PASS)
  - Z3 model SAT
  - Closes: `#46`
- [ ] **Dispatch:** `task(subagent_type="general", prompt="execute review-prep task from git-workflow")`

**Exit criteria:** Compare URL verified (character-match), PR body drafted with spec summary, branch status clean and pushed

---

## Step 2 — Dispatch `spec-summary` sub-agent (blind task())

- [ ] Extract spec summary from `.issues/46/spec.md` for PR body
- [ ] Include dependency graph / Z3 verification status
- [ ] **Dispatch:** `task(subagent_type="general", prompt="execute spec-summary prep for PR body from adversarial-audit --task spec-summary")`

**Exit criteria:** Summary verified accurate against spec content

---

## Step 3 — Dispatch `pr-creation` sub-agent (blind task())

- [ ] Push feature branch: `git push -u origin feature/46-card-1a-fastmcp-install`
- [ ] Create PR via `github_create_pull_request`
  - Base: `dev`
  - Head: `feature/46-card-1a-fastmcp-install`
  - Title: `[#46] Switch from official mcp SDK to standalone fastmcp (PrefectHQ)`
  - Body: Full spec summary with SC status table
- [ ] **Dispatch:** `task(subagent_type="general", prompt="execute pr-creation task from git-workflow")`

**Exit criteria:** PR created — extract `html_url` from API response (NEVER construct from template)

---

## Step 4 — Dispatch `copilot-review` (post-creation)

- [ ] Request Copilot code review: `github_request_copilot_review(owner=michael-conrad, repo=viewport-editor, pullNumber=<N>)`
- [ ] Wait for review to complete (poll if needed)

**Exit criteria:** Copilot review requested

---

## Step 5 — Dispatch `completion` sub-agent (blind task())

- [ ] Post progress comment to issue #46 with PR URL, SC summary, and next steps
- [ ] Update state file: `bash .opencode/tools/solve state update ...` (already current)
- [ ] Push checkpoint tags to remote: `git push origin viewport-editor/checkpoint/46/--*`
- [ ] **Dispatch:** `task(subagent_type="general", prompt="execute completion task from git-workflow")`

**Exit criteria:** Issue comment posted, state documented, branch pushed, all checkpoint tags pushed. **HALT.**

---

## Execution Discipline

| Mandate | Enforcement |
|---------|-------------|
| `skill()` before work | Load `git-workflow` before any git ops |
| Blind `task()` dispatch | Every pipeline step dispatched via `task()`, NEVER inlined |
| No orchestrator preload | Dispatch context: `{ github.owner, github.repo, authorization_scope, halt_at, pr_strategy, pipeline_phase }` only |
| URL sourcing | PR URL extracted from `github_create_pull_request` response `html_url` — NEVER constructed |
| PR base branch | `dev` (feature PR per git-workflow routing rules) |
| Halt | After completion task — NO forward-looking references in final message |

---

## PR Body Template

```
## Summary

Migrate viewport-editor from the bundled MCP SDK's `mcp.server.fastmcp` to
the standalone PrefectHQ `fastmcp` (v3.4.2). 10 cards implemented across
dependency, import, context, test infrastructure, and verification dimensions.

### Cards

| Card | What | Status |
|------|------|--------|
| 1a | Declare `fastmcp>=3.0,\<4.0` dependency | ✅ |
| 1b | Import from standalone `fastmcp`, remove 21 `file_path` kwargs | ✅ |
| 5a | Shared in-memory `Client(server)` fixture in conftest.py | ✅ |
| 5b | Migrate 9 test files to conftest (removed 450 lines duplicated fixture code) | ✅ |
| SC-2 | Lifespan handler behavioral test | ✅ |
| SC-6 | Install size delta documented (+2.5 MB) | ✅ |
| 3a | `ctx: Context` annotation on all 7 tool handlers | ✅ |
| 3b | `ctx.session_id` returns non-empty UUID string | ✅ |
| SC-4 | Unique session IDs across concurrent clients | ✅ |
| SC-7 | Session state isolation via `ctx.set_state`/`ctx.get_state` | ✅ |

### Verification

| SC | Criterion | Result |
|----|-----------|--------|
| SC-1 | `from fastmcp import FastMCP` works, 7 tools register | ✅ |
| SC-2 | Lifespan enter/exit | ✅ |
| SC-3 | `ctx.session_id` non-empty UUID | ✅ |
| SC-4 | Unique session IDs | ✅ |
| SC-5 | All tests pass | ✅ 139/139 |
| SC-6 | Install delta documented | ✅ +2.5 MB |
| SC-7 | Session state isolation | ✅ |

### Z3 Model

All 10 domain variables SAT, all postconditions and invariants satisfied.

Fixes #46
```

## Post-Creation Verification

- [ ] PR URL extracted from API response, not constructed
- [ ] PR title matches convention: `[#46] <description>`
- [ ] Branch push confirmed (`git status` shows up-to-date)
- [ ] Issue progress comment posted with PR link
- [ ] All checkpoint tags pushed to remote
- [ ] **SILENTLY HALT** — no forward-looking references