# AGENTS.md — .issues/ Workspace Guide

## Identity

`.issues/` is a standalone git repository with an `issues-data` orphan branch, stored as a git worktree of the parent repo at `.git/worktrees/-issues/`. It uses the remote `git@github.com:michael-conrad/viewport-editor.git` — the same remote as the parent repo, on the `issues-data` branch.

**This is NOT a submodule.** It is an orphan branch worktree. Do not add it as a submodule or `.gitmodules` entry.

## Tool

Always use `.opencode/tools/local-issues` for issue tracking operations within `.issues/`. Do not manipulate `.issues/` files manually unless the tool cannot perform the required operation.

## Workflow

### Commit and Push

Whenever issue ticket metadata changes — specs, plans, cards, comments, state — the agent MUST:

```
git -C .issues add <changed-files>
git -C .issues commit -m "docs(#N): description of change"
git -C .issues push
```

### Pull (at session start or on request)

```
git -C .issues pull --rebase
```

If conflicts occur during pull, resolve them automatically:
- For `state.yaml`: accept the incoming version (state is ephemeral, latest wins)
- For `spec.md`: accept the incoming version (GitHub issue body is authoritative)
- For `spec-artifacts/` files: attempt automatic merge via `git -C .issues merge --no-edit`; if that fails, accept the local version (spec-artifacts are workspace-local)
- If any conflict cannot be resolved automatically: report the conflict files and HALT

### Check Current Status

```
git -C .issues status
git -C .issues log --oneline -5
```

## Directory Layout

```
.issues/
  {issue_number}/
    spec.md                    — Local mirror of the GitHub Issue spec
    state.yaml                 — Workspace state metadata
    spec-artifacts/
      plan.md                  — Implementation plan (RED/GREEN items, dependency graph)
      cards.md                 — Card catalogue with status and decision log
      dependency-contract.yaml — Dependency contracts and phase ordering
      research/                — Investigation findings, capability probes, evidence notes
      designs/                 — UI wireframes, architecture diagrams, design artifacts
      audit/                   — Adversarial audit verdicts, cross-validate consensus
  AGENTS.md                    — This file
  open/                        — Symlinks or references to open issues
  closed/                      — Archived issues
```

### Example: Spec-Artifact Placement

| Artifact | Path |
|----------|------|
| Card catalogue with all card findings | `.issues/46/spec-artifacts/cards.md` |
| Implementation plan with RED/GREEN items | `.issues/46/spec-artifacts/plan.md` |
| Dependency contract for state machine | `.issues/46/spec-artifacts/dependency-contract.yaml` |
| FastMCP capability probe results | `.issues/46/spec-artifacts/research/fastmcp-capabilities.md` |
| In-memory client migration design | `.issues/46/spec-artifacts/designs/in-memory-fixture.md` |
| Adversarial audit consensus verdict | `.issues/46/spec-artifacts/audit/consensus.yaml` |

## Authorization

Reading and writing `.issues/` is **authorization-free** — it is workspace-local metadata, not implementation code. All spec/plan/card operations within `.issues/` may proceed without `"approved"` or `"go"`.

Creating `feature/*` or `spec/*` branches for code changes still requires `for_implementation` or above scope.

## Relationship to GitHub Issues

- `.issues/{N}/spec.md` mirrors the GitHub Issue body for issue #N
- `.issues/{N}/spec-artifacts/plan.md` is the local implementation plan (not mirrored to GitHub)
- `.issues/{N}/spec-artifacts/cards.md` is the card catalogue with status tracking
- GitHub Issue comments are the authoritative cross-reference directory — see issue bodies for `.issues/` artifact paths