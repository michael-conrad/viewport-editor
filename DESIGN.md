# viewport-editor — Design Document

**MCP server providing a windowed viewport editor for AI agents.**

## Overview

The built-in Read/Edit/Write tools operate on whole-file granularity — the agent reads an entire file, edits by exact string match, and writes the whole result back. This creates problems: ambiguous matches on repeated text, massive context consumption for large files, and no safe multi-edit staging.

`viewport-editor` replaces this paradigm with **scoped viewports** — the agent opens a window into a file, sees only that region, and edits are scoped to that window. Multiple viewports can be open across files simultaneously. Edits can be staged in a buffer and reviewed before saving, with diff preview.

## Core Concepts

### Viewport

A viewport is a window into a file. It carries full context for the agent:

```
viewport_entry: {
  file: "src/main.py",
  start_line: 10,
  end_line: 40,
  mtime: 1716500000,
  size: 12345,
  mode: "buffered" | "immediate"
}
```

Every viewport operation returns this object so the agent always knows what file, range, and mode it is working in.

### Buffer

Each file opened in a viewport has an associated buffer holding pending edits. In `buffered` mode, edits are staged into the buffer and written to disk only on explicit `save`. In `immediate` mode, each edit writes to disk atomically with no staging.

### Session Isolation

Buffer state is scoped to the MCP session (connection). Multiple sessions can have buffers for the same file without collision. Staleness is detected via `mtime + size` tracking.

## Operations

### Viewport Management

| Operation | Description |
|-----------|-------------|
| `open` | Open a viewport at `(file, start_line, end_line)` or by structural anchor. Accepts optional `mode` parameter (default: `"buffered"`). |
| `close` | Close a viewport. In buffered mode, auto-saves if dirty and `auto_save=true`. |
| `list` | List all open viewports with file path, line range, mtime, size, and mode. |
| `scroll` | Move viewport up/down by N lines. |
| `jump` | Navigate to a line number, function, markdown heading, table, or other structural anchor. |

### Editing

| Operation | Description |
|-----------|-------------|
| `edit` | Replace text within the current viewport. Staged into buffer (buffered) or written to disk immediately (immediate). |
| `replace` | Find-and-replace within the current viewport. Behavior depends on viewport mode. |
| `replace-all` | Batch replace across viewport, entire file, or all open files. Behavior depends on viewport mode. |

### File Lifecycle

| Operation | Description |
|-----------|-------------|
| `new` | Create a new file at a path, optionally with initial content. Opens in a viewport. |
| `save` | Write buffer to disk. Only meaningful in buffered mode (immediate mode has no pending buffer). Checks `mtime+size` for conflicts. `force` flag to overwrite. |
| `save-as` | Write buffer to a new path. `force` flag to overwrite existing. Viewport switches to new path. |
| `delete` | Delete a file on disk. |
| `discard` | Discard all pending buffer changes, reload from disk. Only meaningful in buffered mode. |

### Diff & Patch

| Operation | Description |
|-----------|-------------|
| `show-diff` | Show pending buffer changes as a unified diff against the original file on disk. Only meaningful in buffered mode. |
| `apply-diff` | Stage a unified diff into the buffer for the target file (auto-loads if not open). Behavior depends on viewport mode. |
| `test-regex` | Test a regex pattern against text or a viewport, returning match positions. |
| `escape-regex` | Escape regex metacharacters in a literal string for safe use in regex patterns. |

### Search

| Operation | Description |
|-----------|-------------|
| `search` | Search a file for a pattern (substring default, `regex=true` for regex). Scoped to viewport, entire file, or all open files. Returns structured results with line numbers. |

## Search Modes

| Parameter | Default | Description |
|-----------|---------|-------------|
| `pattern` | — | The search string or regex pattern |
| `regex` | `false` | Enable regex matching |
| `case_sensitive` | `false` | Case-sensitive matching |
| `scope` | `"viewport"` | `"viewport"`, `"file"`, or `"all_open"` |

## Operational Modes

Mode is set per-viewport (not global). Each viewport declaration includes a `mode` field.

| Mode | Behavior | Operations Affected |
|------|----------|---------------------|
| **Buffered (default)** | Edits staged in buffer; explicit `save` required | `edit`, `replace`, `replace-all`, `apply-diff` stage into buffer. `save` flushes. `show-diff` previews. `discard` reverts. |
| **Immediate** | Each edit writes to disk atomically | `edit`, `replace`, `replace-all`, `apply-diff` write directly to file. `save`, `show-diff`, `discard` are no-ops or return empty state. |

The agent selects the mode when opening a viewport via the `mode` parameter on `open`. Default is `"buffered"`.

## Safety

### Conflict Detection

Every viewport operation (open, scroll, edit) performs a **soft check**: compare current `mtime+size` against the values at buffer load time. If mismatched, a `warning` field is appended to the response. The buffer is not invalidated — the agent can choose to discard and reload or continue.

The `save` operation performs a **hard check**: if `mtime+size` mismatches, the save is rejected unless `force=true` is set. On successful save (regardless of `force`), the stored `mtime+size` is updated to the post-save values.

### Overwrite Protection

`save-as` with `force=false` (default) returns an error if the target path already exists. `force=true` overwrites.

### Diff Safety

`apply-diff` always stages into a buffer (even in immediate mode, the diff is staged first for review). The agent must review with `show-diff` and then `save` to commit.

## Session Isolation Model

| Dimension | Unit |
|-----------|------|
| Session identity | MCP connection |
| Buffer identity | `(file_path, session)` |
| Buffer freshness | File `mtime + size` at load time |
| Conflict detection | On save: reject if file changed since buffer loaded (unless `force`) |

## Structural Navigation Targets

The `jump` operation must support the following anchors at minimum:

- Line number
- Function/method name (by language parser or regex heuristic)
- Markdown heading (by `#` level)
- Table (markdown tables)
- Search result (from a prior `search`)

## Tool Naming

The MCP server exposes operations as individual tools following the `viewport-editor` namespace convention (e.g., `viewport-editor_open`, `viewport-editor_edit`, `viewport-editor_save`).

## Relationship to Existing Tools

| Tool | Status |
|------|--------|
| **texted** | Will be retired after viewport-editor reaches feature parity |
| **Built-in Read/Edit/Write** | Coexist — not deprecated |

## Roadmap

### MVP (Phase 1)

- All operations listed above
- Per-viewport mode selection (buffered default, immediate available)
- Buffered mode: buffer lifecycle, save, discard, diff preview
- Immediate mode: atomic write on each edit operation
- `apply-diff` always stages into buffer (even in immediate mode)
- `show-diff` for diff preview (meaningful in buffered mode)
- Conflict detection (soft on ops, hard on buffered save)
- Multi-viewport support
- Session isolation
- `test-regex`, `escape-regex` utilities

### Phase 2 (Post-MVP)

- Structural navigation by language AST
- Configuration file for defaults

## License

MIT
