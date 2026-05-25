<!-- SPDX-FileCopyrightText: 2026 Michael Conrad -->
<!-- SPDX-License-Identifier: MIT -->
<!-- Provenance: AI-generated -->

# viewport-editor

**An MCP server that gives AI agents a focused, windowed editing experience — the way a human uses an editor.**

Built-in Read/Edit/Write tools force agents to load entire files, match strings blindly against the full text, and risk ambiguous replacements. viewport-editor replaces this with **viewports**: focused windows into files where every edit is scoped, every change can be staged and reviewed, and the agent always knows exactly what file, range, and mode it is working in.

## Why This Exists

AI agents edit files differently than humans. A human opens a 500-line file, sees a 30-line window, works within it, scrolls when needed, and saves. An agent using current tooling must:

1. Read the entire 500-line file (costly context)
2. Construct a string match against all 500 lines (ambiguous)
3. Blindly replace and write back (no review)

viewport-editor collapses this to: open a viewport, edit within it, review before saving.

## How It Works

### Viewport

A viewport is a focused window into a file. Every operation returns the full context:

```yaml
viewport_entry:
  file: src/main.py
  start_line: 10
  end_line: 40
  mtime: 1716500000
  size: 12345
  mode: buffered
```

The agent always knows what it is looking at, where it is, and what mode it is in.

### Buffer

Each viewport has a buffer. In **buffered mode** (default), edits stage into the buffer and write to disk only on explicit `save`. The agent can make multiple changes, preview a diff, and decide whether to commit.

In **immediate mode**, each edit writes to disk atomically.

### Session Isolation

Buffer state is scoped to the MCP connection. Multiple agent sessions can edit the same file without collision. Staleness is detected via mtime + size — soft warning on operations, hard block on save (with a `force` override).

## 6-Tool Surface

All operations are exposed through 6 tools with an `action` parameter. This keeps initial context load low while giving the agent rich expressiveness.

| tool | actions |
|------|---------|
| **viewport** | open, close, list, scroll, page-up, page-down, jump, switch-mode |
| **edit** | replace, replace-all, insert-lines, delete-lines, swap-lines, move-lines |
| **file** | new, save, save-as, delete, discard |
| **diff** | show, apply |
| **search** | find |
| **regex** | test, escape |

## Quick Start

Add to your OpenCode, Claude, Cursor, or any MCP-compatible client configuration:

```json
{
  "mcpServers": {
    "viewport-editor": {
      "command": "python",
      "args": ["-m", "viewport_editor", "/path/to/project/root"]
    }
  }
}
```

The server receives a project root path at initialization. All file paths are relative to this root — no absolute or host-specific paths in agent-facing interfaces.

## Design Principles

- **Prose + YAML only** — tool descriptions, input schemas, and responses use natural language and YAML. No JSON.
- **list_tools for discovery** — no dedicated help tool. The MCP protocol's standard discovery mechanism is sufficient.
- **True delta diffs** — `diff:show` always compares against the original file on disk, not the last save.
- **apply-diff always stages** — diffs are never applied directly to disk. Review first with `diff:show`, then `file:save`.
- **Per-viewport mode** — each viewport selects its own mode (buffered or immediate). Switch modes with `viewport:switch-mode` (refuses if buffer is dirty).

## Relationship to Other Tools

| tool | relationship |
|------|-------------|
| Built-in Read/Edit/Write | Coexist. Use for simple whole-file operations. Use viewport-editor for complex editing. |

## Roadmap

- **Phase 1 (MVP)**: All 6 tools, both operational modes, conflict detection, multi-viewport, session isolation
- **Phase 2**: AST-based structural navigation, configuration file for defaults

## License

MIT

---

🤖 Co-authored with AI: OpenCode (ollama-cloud/deepseek-v4-flash)
