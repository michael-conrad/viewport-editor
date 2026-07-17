> **Full spec and artifacts: [`.issues/96/`](https://github.com/michael-conrad/viewport-editor/tree/issues-data/96/)** — this issue is a condensed exec summary; the authoritative spec lives in the `issues-data` branch.
>
> **Local artifacts:** `.issues/96/` — implementation plan, card catalogue, dependency contracts, research, designs, audit findings

## Problem

When a file changes externally, viewport-editor detects the conflict but keeps stale buffer content — wasting a round-trip. The agent gets a passive YAML warning but must manually discard and reopen to see fresh data, even with zero pending edits. When the buffer is dirty, the warning format is identical, offering no urgency signal.

## Goals

- Auto-reload clean buffers on external file change without agent intervention
- Differentiate conflict signals between clean (safe reload) and dirty (overwrite risk)
- Zero regression in existing conflict detection behavior

## Non-Goals

- File watcher or polling mechanism (existing inline check_conflict is sufficient)
- Configurable auto-reload opt-in (auto-reload is the safe default for clean buffers)

## Scope

- Add `format_external_modification_warning()` to `src/viewport_editor/file_ops.py`
- Add `auto_reload_if_clean()` to `ViewportManager` in `src/viewport_editor/viewport.py`
- Replace `_check_file_conflict()` with auto-reload-aware routing in `server.py`
- Update save-path actions (file:save, write_file, edit_text) to branch on dirty+conflict

## Approach

Introduce a bifurcated conflict response routed through `entry.dirty`. Clean buffers auto-reload from disk; dirty buffers get a stronger conflict signal with `severity: external_modification`. Three affected source files, two implementation phases.

## Impact

**Risks:** Auto-reload race with concurrent external write (low — refresh_if_changed reads atomically). False-negative dirty flag causing silent overwrite (mitigated by existing well-tested dirty tracking).

**Call to action:** Review the full spec in `.issues/96/spec.md` and provide feedback on this issue.

🤖 Co-authored with AI: OpenCode (deepseek-v4-flash)
