# AGENTS.md — .issues/ Workspace Guide

## Identity

`.issues/` is a standalone git repository with an `issues-data` orphan branch, stored as a git worktree of the parent repo at `.git/worktrees/-issues/`. It uses the same remote as the parent repo (determined at runtime via `git -C .issues remote -v`), on the `issues-data` branch.

**This is NOT a submodule.** It is an orphan branch worktree. Do not add it as a submodule or `.gitmodules` entry.

## Tool

Always use `.opencode/tools/local-issues` for issue tracking operations within `.issues/`. Do not manipulate `.issues/` files manually unless the tool cannot perform the required operation.

### Invocation

```
.opencode/tools/local-issues <command> [flags]
```

First invocation auto-initializes `.issues/` — creates the orphan branch, worktree, and initial commit. No separate setup step needed.

### Usage Examples

```
# List all issues
.opencode/tools/local-issues list

# Sample output:
# #1 [open]
# #46 [open]
# #47 [open]

# Read an issue
.opencode/tools/local-issues read --number 46

# Create a new issue (auto-numbered)
.opencode/tools/local-issues create --title "My spec" --labels SPEC

# Create with explicit number
.opencode/tools/local-issues create --number 99 --title "Bug fix" --labels BUG

# Search issues
.opencode/tools/local-issues search --query "fastmcp"

# Link sub-issues to a parent
.opencode/tools/local-issues link --number 46 --sub 47 48 --type sub-issue

# Add a comment
.opencode/tools/local-issues comment --number 46 --type internal --body "Investigation complete"

# Close an issue
.opencode/tools/local-issues close --number 99 --reason completed

# Update an issue body from file
.opencode/tools/local-issues update --number 46 --body-file ./tmp/spec-v2.md

# Check promotion readiness
.opencode/tools/local-issues promote --number 46
```

### Standards

- All spec files use `.md` extension with optional YAML frontmatter
- All metadata files use `.yaml` extension
- Comments are stored as YAML with `type: internal|stakeholder` field
- Sub-issues use the `link` command for parent-child relationships
- GitHub/GitBucket sync uses `--github` / `--remote-url` flags on `update` and `comment`

## Workflow

All git operations (commit, push) are handled automatically by the tool after mutation commands. You do NOT need to run `git -C .issues` commands manually.

| Action | Command | Auto-commit? | Auto-push? |
|--------|---------|-------------|-------------|
| List issues | `local-issues list` | N/A (read-only) | N/A |
| Read issue | `local-issues read --number N` | N/A (read-only) | N/A |
| Search | `local-issues search --query "..."` | N/A (read-only) | N/A |
| Create issue | `local-issues create --title "..."` | ✅ Yes | ✅ Yes |
| Update issue | `local-issues update --number N ...` | ✅ Yes | ✅ Yes |
| Add comment | `local-issues comment --number N --body "..."` | ✅ Yes | ✅ Yes |
| Close issue | `local-issues close --number N --reason completed` | ✅ Yes | ✅ Yes |
| Link sub-issues | `local-issues link --number N --sub M --type sub-issue` | ✅ Yes | ✅ Yes |
| Renumber | `local-issues renumber --from N --to M` | ✅ Yes | ✅ Yes |

### Pull at session start

```
.opencode/tools/local-issues list
```

The `list` command auto-initializes the `.issues/` worktree if missing. However, it does not pull remote changes. To sync before starting work:

```
git -C .issues pull --rebase origin issues-data
```

This is the ONLY manual `git -C .issues` command needed.

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

## GitHub URLs for .issues/ Cross-References

When linking to `.issues/` files from GitHub issue bodies, use full URLs to the `issues-data` branch. The branch root IS the `.issues/` directory root.

### Pattern

```
Folder:   https://github.com/{owner}/{repo}/tree/issues-data/{N}
File:     https://github.com/{owner}/{repo}/blob/issues-data/{N}/{path}
```

### Convention

- **Only the spec folder gets a full URL** — for human readers browsing via GitHub
- **Artifact paths stay relative** (`.issues/N/spec-artifacts/plan.md`) — for AI agents reading locally
- The folder URL is sufficient: it shows spec.md, spec-artifacts/, and all sub-files

### Examples (viewport-editor)

| Target | URL |
|--------|-----|
| Issue folder | `https://github.com/michael-conrad/viewport-editor/tree/issues-data/46` |
| spec.md file | `https://github.com/michael-conrad/viewport-editor/blob/issues-data/46/spec.md` |

### Example: Cross-References Table in Github Issue

```
## Cross-References

| Type | Reference | Direction |
|------|-----------|-----------|
| spec folder (view on GitHub) | [`.issues/46/`](https://github.com/michael-conrad/viewport-editor/tree/issues-data/46) | Spec and artifacts |
| implementation plan | `.issues/46/spec-artifacts/plan.md` | Red/Green phase decomposition |
| card catalogue | `.issues/46/spec-artifacts/cards.md` | Investigation findings and decisions |
```