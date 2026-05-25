<!-- SPDX-FileCopyrightText: 2026 Michael Conrad -->
<!-- SPDX-License-Identifier: MIT -->
<!-- Provenance: AI-generated -->

# viewport-editor — Design Document

**MCP server providing a windowed viewport editor for AI agents.**

## Overview

The built-in Read/Edit/Write tools operate on whole-file granularity — the agent
reads an entire file, edits by exact string match, and writes the whole result
back. This creates three problems:

- **Ambiguous matches**: repeated text in a file causes edit failures.
- **High context cost**: reading a 500-line file to change 3 lines.
- **No edit staging**: every edit is immediate, blind, and irreversible.

viewport-editor replaces this with scoped viewports — focused windows into
files, with per-viewport mode selection, buffered staging with diff review, and
a consolidated 6-tool MCP surface that minimizes context load.

See [COMPARISON.md](./COMPARISON.md) for an AI agent's perspective on how this
compares to other editing tools.

## Discovery Mechanism

The MCP protocol's built-in list_tools call is the sole discovery mechanism.
Agents call list_tools on connection to enumerate available tools, read their
descriptions, and inspect action parameter enums. No dedicated help tool is
exposed. Tool descriptions are written per best practice: front-loaded with
purpose, concise, and explicit about constraints and side effects.

## Design Requirements

- All MCP communications use natural language prose and YAML exclusively.
  No JSON in tool descriptions, input schemas, or responses.
- File paths are relative to a configured project root. The MCP server
  receives the root path at initialization. No absolute or host-specific
  paths appear in any agent-facing interface.

## Core Concepts

### Viewport

A viewport is a window into a file carrying full context:

```
viewport_entry:
  file: src/main.py
  start_line: 10
  end_line: 40
  mtime: 1716500000
  size: 12345
  mode: buffered [dirty|clean]
```

Every viewport operation returns this object. The agent always knows which
file, range, and mode it is working in.

### Buffer

Each file opened in a viewport has an associated buffer holding pending edits.
In buffered mode, edits stage into the buffer and write to disk only on
explicit save. In immediate mode, each edit writes to disk atomically.

### Session Isolation

Buffer state is scoped to the MCP session. Multiple sessions can have buffers
for the same file without collision. Staleness detection uses mtime + size.

## Consolidated Tool Surface (6 Tools)

All operations are exposed through 6 tools with an action parameter.
This minimizes context load on initial MCP plugin injection. Tool descriptions
and responses use prose + YAML exclusively.

### 1. viewport

| action | description |
|--------|-------------|
| open | Open a viewport at file:start_line:end_line or by structural anchor. Optional mode: buffered (default) or immediate. |
| close | Close a viewport. Auto-saves if dirty and auto_save is true. |
| list | List all open viewports with file, range, mtime, size, and mode. |
| scroll | Move viewport up or down by N lines. |
| page-up | Move viewport up by its own height (previous block of text). |
| page-down | Move viewport down by its own height (next block of text). |
| jump | Navigate to a structural anchor: line number, function name, markdown heading, table, or search result. |
| switch-mode | Switch the viewport between buffered and immediate mode. If buffered with unsaved changes, refuse with message: "buffer has unsaved changes, save or discard before switching mode." |

### 2. edit

| action | description |
|--------|-------------|
| replace | Find and replace text within the current viewport. In buffered mode, stages into buffer. In immediate mode, writes to disk atomically. |
| replace-all | Batch replace across viewport, entire file, or all open files. Scope parameter selects the target. Behavior depends on viewport mode. |
| insert-lines | Insert one or more lines at a specified line number within the viewport. Behavior depends on viewport mode. |
| delete-lines | Delete a range of lines within the viewport. Behavior depends on viewport mode. |
| swap-lines | Exchange two line positions within the viewport. Behavior depends on viewport mode. |
| move-lines | Relocate a range of lines to a target line position within the viewport. Behavior depends on viewport mode. |

### 3. file

| action | description |
|--------|-------------|
| new | Create a new file at a path, optionally with initial content. Opens in a viewport in buffered mode. |
| save | Write buffer to disk. Hard mtime+size conflict check. Force flag to overwrite. No-op in immediate mode. |
| save-as | Write buffer to a new path. Force flag to overwrite existing. Viewport switches to new path. |
| delete | Delete a file on disk. |
| discard | Discard all pending buffer changes and reload from disk. Only meaningful in buffered mode. |

### 4. diff

| action | description |
|--------|-------------|
| show | Show pending buffer changes as a unified diff against the original file on disk. Only meaningful in buffered mode. |
| apply | Stage a unified diff into the buffer for the target file. Auto-loads the file if not already open. Always stages into buffer, even in immediate mode, so the agent can review before saving. |

### 5. search

| action | description |
|--------|-------------|
| find | Search a file for a pattern. Substring matching by default, regex with a flag. Scope parameter: viewport, file, or all_open. Returns structured results with line numbers. |

### 6. regex

| action | description |
|--------|-------------|
| test | Test a regex pattern against text or a viewport. Returns match positions. |
| escape | Escape regex metacharacters in a literal string for safe use in regex patterns. |

## Operational Modes

Modes are set per-viewport. Each viewport entry includes a mode field.

| mode | behavior | operations affected |
|------|----------|---------------------|
| buffered (default) | Edits stage into buffer. Explicit save required. | edit actions, diff:apply stage into buffer. file:save flushes. diff:show previews. file:discard reverts. |
| immediate | Each edit writes to disk atomically. | edit actions, diff:apply write directly. file:save, diff:show, file:discard are no-ops or return empty state. |

The agent selects the mode when opening a viewport via the mode parameter on
viewport:open. Default is buffered.

## Search Parameters

| parameter | default | description |
|-----------|---------|-------------|
| pattern | required | The search string or regex pattern |
| regex | false | Enable regex matching |
| case_sensitive | false | Case-sensitive matching |
| scope | viewport | viewport, file, or all_open |

## Safety

### Conflict Detection

Every viewport operation (open, scroll, page-up, page-down, edit actions)
performs a soft check: compare current mtime and size against the values
at buffer load time. If mismatched, a warning field is appended to the
response. The buffer is not invalidated — the agent can continue or discard
and reload.

The file:save operation performs a hard check. If mtime or size mismatches,
the save is rejected unless the force flag is set. On any successful save, the
stored mtime and size update to the post-save values.

### Overwrite Protection

file:save-as with force false returns an error if the target path exists.
Force true overwrites.

### Diff Safety

diff:apply always stages into a buffer. The diff is never applied directly to
disk. The agent must review with diff:show and then file:save to commit.

## Session Isolation Model

| dimension | unit |
|-----------|------|
| session identity | MCP connection |
| buffer identity | file_path + session |
| buffer freshness | file mtime + size at load time |
| conflict detection | on save: reject if file changed since buffer loaded (unless force) |

## Structural Navigation Targets

The viewport:jump action must support these anchors at minimum:

- Line number
- Function or method name (by language parser or regex heuristic)
- Markdown heading (by hash level)
- Table (markdown tables)
- Search result (from a prior search:find)

## Relationship to Built-in Tools

| tool | relationship |
|------|-------------|
| Built-in Read/Edit/Write | Coexist. Use for simple whole-file operations. Use viewport-editor for complex editing. |

## Roadmap

### MVP — Phase 1

All 6 tools with all actions listed above. Per-viewport mode selection.
Buffered and immediate modes co-implemented. Conflict detection.
Multi-viewport support. Session isolation. Prose + YAML throughout.
File paths relative to project root. list_tools as discovery mechanism.

### Phase 2

- Structural navigation by language AST
- Configuration file for defaults

## License

MIT

---

🤖 Co-authored with AI: OpenCode (ollama-cloud/deepseek-v4-flash)
