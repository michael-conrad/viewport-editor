# [SPEC] Allow Absolute Paths

> **Compliance Requirement:** All steps and sub-steps in this document MUST be followed in order. Failure to comply with any step — including but not limited to verification gates, test phases, audit checkpoints, and review steps — will result in the feature branch being rejected and discarded, requiring a full rework from scratch and loss of all prior work. There is no valid reason to skip, compress, reorder, or omit any step. If a step appears redundant or unnecessary, follow it anyway — the cost of following an extra step is negligible compared to the cost of rework from a skipped step.

## Intent and Executive Summary

| Field | Value |
|-------|-------|
| **Problem Statement** | The viewport-editor MCP server rejects all absolute paths in `_resolve_path()`, raising `AbsolutePathError` even when the path is valid. MCP clients (AI agents) naturally produce absolute paths and cannot know the server's `project_root`. |
| **Root Cause / Motivation** | `_resolve_path()` in `file_ops.py:22-30` has a blanket rejection: `if file_path.startswith("/"): raise AbsolutePathError(file_path)`. This fires before any path-escape check, making the server unusable with absolute paths from AI agents. |
| **Approach Chosen** | Replace `_resolve_path()` with a two-branch resolver using `os.path.realpath()`. Absolute paths resolve directly; relative paths join with `project_root`. Remove all project-root restrictions. Keep `AbsolutePathError` and `PathEscapeError` classes for backward compatibility. |
| **Alternatives Considered & Why Discarded** | (1) Allow absolute paths only within project root — rejected because the editor needs to access files anywhere on the filesystem. (2) Add a `--allow-absolute-paths` flag — rejected because there is no security reason to block absolute paths. |
| **Key Design Decisions** | DEC-1: Use `os.path.realpath()` instead of `os.path.normpath()` — resolves symlinks, more robust. DEC-2: Keep exception classes but stop raising them from `_resolve_path()`. |

## Problem

The viewport-editor MCP server rejects **all** absolute paths in `_resolve_path()` (`src/viewport_editor/file_ops.py:22-30`). When an AI agent or user passes an absolute path like `/home/user/project/src/main.py`, the server raises `AbsolutePathError` with message `"Absolute paths not allowed: {file_path}"`.

This is problematic because:

- MCP clients (AI agents) naturally produce absolute paths — they don't know the server's `project_root`
- The `workdir` parameter in bash tool calls uses absolute paths
- The editor needs to access files anywhere on the filesystem

## Current Behavior

`_resolve_path()` in `src/viewport_editor/file_ops.py:22-30`:

```python
def _resolve_path(file_path: str, project_root: str) -> Tuple[str, str]:
    if file_path.startswith("/"):
        raise AbsolutePathError(file_path)
    resolved = os.path.normpath(os.path.join(project_root, file_path))
    resolved_str = str(resolved)
    norm_root = os.path.normpath(project_root)
    if not resolved_str.startswith(str(norm_root)):
        raise PathEscapeError(file_path)
    return resolved_str, file_path
```

Two restrictions: (1) absolute paths rejected outright, (2) relative paths must stay within project root.

## Proposed Change

Replace `_resolve_path()` with a simple resolver that has no project-root restrictions:

```python
def _resolve_path(file_path: str, project_root: str) -> Tuple[str, str]:
    if file_path.startswith("/"):
        resolved = os.path.realpath(file_path)
    else:
        resolved = os.path.realpath(os.path.join(project_root, file_path))
    return str(resolved), file_path
```

- Absolute paths: resolve directly via `os.path.realpath()`
- Relative paths: join with `project_root`, then `os.path.realpath()`
- No `AbsolutePathError` — absolute paths are always allowed
- No `PathEscapeError` — no project-root boundary enforcement

## Affected Files

| File | Change |
|------|--------|
| `src/viewport_editor/file_ops.py` | Replace `_resolve_path()` — remove all path restrictions, use `os.path.realpath()` |
| `src/viewport_editor/exceptions.py` | `AbsolutePathError` and `PathEscapeError` are no longer raised by `_resolve_path()`. Keep both classes for backward compatibility. |

## Scope

### In Scope

- Allow absolute paths unconditionally in `_resolve_path()`
- Remove `PathEscapeError` from `_resolve_path()` for relative paths
- Keep `AbsolutePathError` and `PathEscapeError` classes importable
- Update existing tests that assert absolute paths are rejected

### Out of Scope

- Changes to `server.py`, `viewport.py`, or `buffer.py` — all path resolution routes through `_resolve_path()`
- Adding new configuration flags or environment variables
- Symlink security hardening beyond `os.path.realpath()`

## Success Criteria

> **Compliance Requirement:** All steps and sub-steps in this document MUST be followed in order. Failure to comply with any step — including but not limited to verification gates, test phases, audit checkpoints, and review steps — will result in the feature branch being rejected and discarded, requiring a full rework from scratch and loss of all prior work. There is no valid reason to skip, compress, reorder, or omit any step. If a step appears redundant or unnecessary, follow it anyway — the cost of following an extra step is negligible compared to the cost of rework from a skipped step.

| ID | Criterion | Evidence Type | Verification Method | Remediation | Pipeline Step Binding | Artifact Path | Requirement Traceability | Phase Binding | Verification Gate | Integration Mode | Affinity Group | Re-Entry Step | Test File | Phase Mapping |
|----|-----------|---------------|---------------------|-------------|----------------------|--------------|-------------------------|--------------|-----------------|----------------|--------------|-------------|-----------|--------------|
| SC-1 | Absolute path to any file on the filesystem resolves correctly | `behavioral` | Pass absolute path outside project root to `read_file`/`edit_text`/`write_file` — file is opened successfully | If FAIL: verify `_resolve_path()` uses `os.path.realpath()` for absolute branch; re-run test | phase-1-green-doublecheck | `.issues/87/artifacts/behavioral-evidence-SC-1.log` | DEC-1 | post-implementation | standalone | none | null | `test/test_phase1_server_viewport.py` | P1 |
| SC-2 | Relative path resolves correctly against project root | `behavioral` | Pass relative path — resolves correctly against `project_root` | If FAIL: verify `_resolve_path()` joins with `project_root` for relative branch; re-run test | phase-1-green-doublecheck | `.issues/87/artifacts/behavioral-evidence-SC-2.log` | DEC-1 | post-implementation | standalone | none | null | `test/test_phase1_server_viewport.py` | P1 |
| SC-3 | `AbsolutePathError` class still exists (backward compat) | `structural` | `AbsolutePathError` is importable from `exceptions.py` | If FAIL: restore `AbsolutePathError` class definition in `exceptions.py` | phase-3-green-doublecheck | `.issues/87/artifacts/structural-evidence-SC-3.log` | DEC-2 | post-implementation | standalone | none | null | `test/test_exceptions.py` | P3 |
| SC-4 | `PathEscapeError` class still exists (backward compat) | `structural` | `PathEscapeError` is importable from `exceptions.py` | If FAIL: restore `PathEscapeError` class definition in `exceptions.py` | phase-3-green-doublecheck | `.issues/87/artifacts/structural-evidence-SC-4.log` | DEC-2 | post-implementation | standalone | none | null | `test/test_exceptions.py` | P3 |

### All-or-Nothing Gate

**ALL success criteria MUST pass for implementation to be considered complete.** Any SKIPPED SC is treated as FAIL. Any FAILED SC triggers autonomous remediation by the producing agent. The gate holds position until remediation is verified. If re-verification also fails (double-failure), HALT with blocker report.

### Behavioral Test Mandate

Before any implementation, write unit or integration tests that verify the changed behavior. Confirm RED state (test fails before change). If the tests are missing from the working tree when implementation begins, they must be re-created before any source changes.

## Decision Ledger

| DEC-ID | Decision | Rationale | Requirement Key | Affected SCs |
|--------|----------|-----------|-----------------|--------------|
| DEC-1 | Use `os.path.realpath()` instead of `os.path.normpath()` | Resolves symlinks, prevents symlink-based path traversal | MUST | SC-1, SC-2 |
| DEC-2 | Keep exception classes but stop raising them | Backward compatibility for code that catches these exceptions | MUST | SC-3, SC-4 |

## Risk Traceability

| RISK-ID | Risk Description | Likelihood | Impact | Mitigation | Verifying SC |
|---------|-----------------|------------|--------|------------|--------------|
| RISK-1 | Backward compat break for code catching `AbsolutePathError` | Medium | Low | Keep the exception class; it's no longer raised by `_resolve_path()` but remains importable | SC-3 |
| RISK-2 | Backward compat break for code catching `PathEscapeError` | Medium | Low | Keep the exception class; it's no longer raised by `_resolve_path()` but remains importable | SC-4 |
| RISK-3 | Absolute path to non-existent file | Low | Low | Existing `FileNotFoundError_` handling still works | SC-1 |

## Revision Policy

| Artifact | Cascade Trigger | Action on Parent Revision |
|----------|----------------|---------------------------|
| Implementation plan | MUST | Revise to match revised spec |
| Behavioral tests | SHOULD | Review for continued validity |
| Risk traceability | MAY | Update if new risks introduced |

## Decomposition Classification

| Classification | Number of Phases | Sub-Issue Requirements | PR Strategy |
| -------------- | ---------------- | ---------------------- | ----------- |
| multi-phase | 3 | One sub-issue per phase | stacked |

## Regression Invariants

1. Existing relative path resolution MUST continue to work correctly against `project_root`
2. `AbsolutePathError` MUST remain importable from `viewport_editor.exceptions`
3. `PathEscapeError` MUST remain importable from `viewport_editor.exceptions`
4. All existing public API signatures in `server.py`, `viewport.py`, and `buffer.py` MUST remain unchanged

## Implementation Notes

- No changes needed to `server.py`, `viewport.py`, or `buffer.py` — all path resolution routes through `_resolve_path()`
- The `_inject_agents_notice()` function in `server.py:640` already uses `os.path.realpath()` — this change makes `_resolve_path()` consistent
- Both exception classes kept for backward compatibility; callers that catch them will no longer trigger on path resolution

## Plan Creation Mandate

After this spec is approved, invoke `writing-plans` to create `.issues/87/plan.md` before implementation begins.

## Documentation Sources

| Source Category | What Was Consulted | Purpose |
|----------------|-------------------|---------|
| Direct source search | `srclight_get_symbol("_resolve_path")` | Verify current implementation |
| Direct source search | `grep -r "AbsolutePathError" src/` | Verify all usages of the exception |
| Direct source search | `grep -r "PathEscapeError" src/` | Verify all usages of the exception |
| Direct source search | `grep -r "_resolve_path" src/` | Identify all callers |
| Live verification | `uv run pytest test/ -x` | Confirm baseline test state |

---

🤖 Co-authored with AI: OpenCode (deepseek-v4-flash)
