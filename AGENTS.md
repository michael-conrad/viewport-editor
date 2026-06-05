# AGENTS.md — .issues/ Workspace Guide

## Identity

`.issues/` is a standalone git repository with an `issues-data` orphan branch, stored as a git worktree of the parent repo at `.git/worktrees/-issues/`. It uses the same remote as the parent repo (determined at runtime via `git -C .issues remote -v`), on the `issues-data` branch.

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

If conflicts occur during pull, resolve them intelligently using your best judgment. Read both sides, understand the intent of each change, and synthesize a merged version. If genuinely unresolvable, report the conflict files and HALT.

### Check Current Status

```
git -C .issues status
git -C .issues log --oneline -5
```

## Directory Layout

```
.issues/
  {issue_number}/
    spec.md                    — The spec (authoritative, may mirror remote or be sole copy)
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

## Relationship to Remote Issue Tracker

- `.issues/{N}/spec.md` IS the spec — it may mirror a remote issue (GitHub/GitBucket) or be the sole authoritative copy. The remote is secondary.
- `.issues/{N}/spec-artifacts/plan.md` is the local implementation plan (not mirrored to remote)
- `.issues/{N}/spec-artifacts/cards.md` is the card catalogue with status tracking
- Files in `.issues/` take precedence over remote issue bodies when both exist. The `.issues/` workspace is the source of truth for implementation planning.