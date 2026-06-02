# Synced from GitHub Issue #19 at 2026-06-01T22:25:16Z

## Problem

`.issues/` and `.opencode/` are not in `.gitignore`, so `git status` reports them as untracked directories. Both are worktree/submodule directories that should never be tracked by the parent repo.

## Fix

Added `.issues/` and `.opencode/` to `.gitignore` (alphabetically sorted).

## Separately Reported (Upstream)

The `.opencode/tools/local-issues` script has a broken PEP 723 bash guard on line 2:

```
"execuvrun--script$0$@"  # broken — all tokens concatenated
```

Should be:

```
"exec" "uv" "run" "--script" "$0" "$@"  # correct — separate tokens with spaces
```

This causes bash to interpret the Python script when invoked as `bash .opencode/tools/local-issues`, creating stray artifact files (`fcntl`, `os`, `re`, `shutil`, `subprocess`, `sys`) in the project root. Filed upstream at `michael-conrad/.opencode`.

## Verification

- `git status --short` no longer shows `.issues/` or `.opencode/` as untracked
- Stray artifact files (`fcntl`, `os`, `re`, etc.) cleaned up

🤖 Co-authored with AI: OpenCode (ollama-cloud/glm-5.1)