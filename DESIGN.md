# viewport-editor — Design Document

**MCP server providing a windowed viewport editor for AI agents.**

## Overview

The built-in Read/Edit/Write tools operate on whole-file granularity — the agent reads an entire file, edits by exact string match, and writes the whole result back. This creates problems: ambiguous matches on repeated text, massive context consumption for large files, and no safe multi-edit staging.

`viewport-editor` replaces this paradigm with **scoped viewports** — the agent opens a window into a file, sees only that region, and edits are scoped to that window. Multiple viewports can be open across files simultaneously. Edits can be staged in a buffer and reviewed before saving, with diff preview.

## Core Concepts

### Viewport

A viewport is a window into a file defined by `(file_path, start_line, end_line)`. Every viewport operation returns the visible window content along with the file path and current line range. The agent never works on the entire file — always through a focused lens.

### Buffer

Each file opened in a viewport has an associated buffer holding pending edits. Edits are staged into the buffer and written to disk only on explicit `save`. This allows the agent to make multiple changes, review them with `show-diff`, and decide whether to commit.

### Session Isolation

Buffer state is scoped to the MCP session (connection). Multiple sessions can have buffers for the same file without collision. Staleness is detected via `mtime + size` tracking.

## Operations

### Viewport Management

| Operation | Description |
|-----------|-------------|
| `open` | Open a viewport at `(file, start_line, end_line)` or by structural anchor |
| `close` | Close a viewport (auto-saves if dirty and `auto_save=true`) |
| `list` | List all open viewports with file path and line range |
| `scroll` | Move viewport up/down by N lines |
| `jump` | Navigate to a line number, function, markdown heading, table, or other structural anchor |

### Editing

| Operation | Description |
|-----------|-------------|
| `edit` | Replace text within the current viewport. Staged into buffer. |
| `replace` | Find-and-replace within the current viewport. Staged into buffer. |
| `replace-all` | Batch replace across viewport, entire file, or all open files. Staged into buffer. |

### File Lifecycle

| Operation | Description |
|-----------|-------------|
| `new` | Create a new file at a path, optionally with initial content. Opens in a viewport. |
| `save` | Write buffer to disk. Checks `mtime+size` for conflicts. `force` flag to overwrite. |
| `save-as` | Write buffer to a new path. `force` flag to overwrite existing. Viewport switches to new path. |
| `delete` | Delete a file on disk. |
| `discard` | Discard all pending buffer changes, reload from disk. |

### Diff & Patch

| Operation | Description |
|-----------|-------------|
| `show-diff` | Show pending buffer changes as a unified diff against the original file on disk. |
| `apply-diff` | Stage a unified diff into the buffer for the target file (auto-loads if not open). |
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

| Mode | Behavior |
|------|----------|
| **Immediate** | Edit + auto-save (future, post-MVP) |
| **Buffered (default)** | Edits staged in buffer; explicit `save` required |
| **Implicit save** | Auto-save on viewport close (default `true`) |

**MVP ships with buffered mode only.** Immediate mode is a future enhancement.

## Safety

### Conflict Detection

Every viewport operation (open, scroll, edit) performs a **soft check**: compare current `mtime+size` against the values at buffer load time. If mismatched, a `warning` field is appended to the response. The buffer is not invalidated — the agent can choose to discard and reload or continue.

The `save` operation performs a **hard check**: if `mtime+size` mismatches, the save is rejected unless `force=true` is set. On successful save (regardless of `force`), the stored `mtime+size` is updated to the post-save values.

### Overwrite Protection

`save-as` with `force=false` (default) returns an error if the target path already exists. `force=true` overwrites.

### Diff Safety

`apply-diff` always stages into a buffer. The diff is never applied directly to disk. The agent must review with `show-diff` and then `save` to commit.

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

- `open`, `close`, `list`, `scroll`, `jump` (viewport management)
- `edit` (windowed, buffered)
- `save`, `discard` (buffer lifecycle)
- `show-diff` (diff preview)
- `new`, `save-as`, `delete` (file lifecycle)
- `search` (substring + regex, viewport/file scope)
- `replace`, `replace-all` (scoped + batch)
- `apply-diff` (diff staging)
- `test-regex`, `escape-regex` (regex utilities)
- Conflict detection (soft on ops, hard on save)
- Multi-viewport support
- Session isolation

### Phase 2 (Post-MVP)

- Immediate edit mode
- Structural navigation by language AST
- Configuration file for defaults

## License

MIT
