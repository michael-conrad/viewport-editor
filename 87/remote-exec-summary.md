> **Full spec and artifacts: [`.issues/87/`](https://github.com/michael-conrad/viewport-editor/tree/issues-data/87)** — this issue is a condensed exec summary; the authoritative spec lives in the `issues-data` branch.
>
> **Local artifacts:** `.issues/87/` — implementation plan, card catalogue, dependency contracts, research, designs, audit findings

## Exec Summary

The viewport-editor MCP server rejects all absolute paths in `_resolve_path()`, raising `AbsolutePathError` even for valid paths. MCP clients (AI agents) naturally produce absolute paths and cannot know the server's `project_root`. Replace `_resolve_path()` with a two-branch resolver using `os.path.realpath()` — absolute paths resolve directly, relative paths join with `project_root`. Remove all project-root restrictions. Keep `AbsolutePathError` and `PathEscapeError` classes for backward compatibility.

### Cards (dependency order)
1. **Phase 1 — Replace `_resolve_path()`** — Core implementation: two-branch resolver in `file_ops.py`
2. **Phase 2 — Update behavioral tests** — Update existing tests that assert absolute paths are rejected
3. **Phase 3 — Backward compatibility verification** — Verify exception classes remain importable

### Key Decisions
- **DEC-1**: Use `os.path.realpath()` instead of `os.path.normpath()` — resolves symlinks, prevents traversal
- **DEC-2**: Keep exception classes but stop raising them — backward compatibility for catching code

### Risk Callouts
- **RISK-1**: Backward compat break for code catching `AbsolutePathError`/`PathEscapeError` — mitigated by keeping both classes importable
- **RISK-2**: Absolute path to non-existent file — mitigated by existing `FileNotFoundError_` handling

## AI Agent Instructions

This issue is an executive summary for human stakeholders.
The authoritative spec and plan artifacts are at `.issues/87/`.
After creation, `local-issues sync` MUST be run and the result committed to create the local `.issues/87/` entry.
The implementation plan will be created in `.issues/87/plan.md` after approval.
AI agents MUST read the local spec/plan files for implementation
and MUST NOT base implementation on this summary.

---

🤖 Co-authored with AI: OpenCode (deepseek-v4-flash)
