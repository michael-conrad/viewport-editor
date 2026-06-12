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

A viewport is a focused window into a file. The server uses the current working directory as the project root. All file paths are relative to this root — no absolute or host-specific paths in agent-facing interfaces. Every operation returns the full context:

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

## 11-Tool Surface

All operations are exposed through 11 tools with an `action` parameter. This keeps initial context load low while giving the agent rich expressiveness.

| tool | actions |
|------|---------|
| **viewport** | open, close, list, scroll, page-up, page-down, jump, autosave, set-display-mode |
| **edit** | replace, replace-all, insert-lines, delete-lines, swap-lines, move-lines |
| **file** | save, discard, new, save-as, delete |
| **diff** | show, apply |
| **clipboard** | copy, cut, paste, show, stash, pop, swap, stash-list |
| **search** | find |
| **regex** | test, escape |
| **read_file** | composite: open + scroll — single-call file read with viewport lifecycle |
| **write_file** | composite: open + replace-all + save + close — single-call file write with conflict detection |
| **edit_text** | composite: open + replace + save + close — single-call targeted edit with conflict detection |
| **find_text** | composite: search wrapper — single-call text search |

## Quick Start

No setup required. The project root is the current working directory at server start.

### Installation-Free (uvx — from GitHub release tag)

Run directly from the tagged release — no PyPI install, no repo clone needed:

```jsonc
// OpenCode
"mcp": {
    "viewport-editor": {
      "type": "local",
      "command": ["uvx", "--from", "git+https://github.com/michael-conrad/viewport-editor@v0.3.1", "viewport-editor"],
      "enabled": true
    }
}
```

```json
{
  // Other MCP Clients (Claude, Cursor, etc.)
  "mcpServers": {
    "viewport-editor": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/michael-conrad/viewport-editor@v0.3.1", "viewport-editor"]
    }
  }
}
```

### From repo checkout

```
git clone git@github.com:michael-conrad/viewport-editor.git
cd viewport-editor
uv run viewport-editor
```

## Consuming Repo Instructions

When adding viewport-editor as an MCP plugin, configure it in your `opencode.jsonc`:

```jsonc
{
  "mcp": {
    "viewport-editor": {
      "type": "local",
      "command": ["uvx", "--from", "git+https://github.com/michael-conrad/viewport-editor@v0.3.1", "viewport-editor"],
      "enabled": true
    }
  }
}
```

Then add the following stanza to your repository's `AGENTS.md`:

```markdown
### viewport-editor MCP Plugin

This repo uses [viewport-editor](https://github.com/michael-conrad/viewport-editor) as its editing MCP server.

**11-tool surface** (see README for full action lists):

| Tool | Purpose |
|------|---------|
| **viewport** | Open, navigate, and manage focused editing windows |
| **edit** | Stage text changes into viewport buffers (replace, insert, delete, swap, move) |
| **file** | Commit or discard staged changes to disk |
| **diff** | Show unified diffs of pending edits before saving |
| **clipboard** | Copy/cut/paste content across viewports with provenance tracking |
| **search** | Find text with substring or regex matching |
| **regex** | Test and escape regex patterns |
| **read_file** | Composite: open + scroll — preferred over built-in `read` for single-call reading |
| **write_file** | Composite: open + replace-all + save — preferred over built-in `write` for conflict-safe writing |
| **edit_text** | Composite: open + replace + save — preferred over built-in `edit` for targeted changes with conflict detection |
| **find_text** | Composite: search — preferred over built-in `grep` for structured results |

**recommended agent behavior:**

- Use `read_file`, `write_file`, `edit_text`, `find_text` for single-call operations (empirically validated — see viewport-editor#63 V1 results)
- Use `viewport` + `edit` + `file` for multi-step editing with diff review
- Always call `diff:show` before `file:save` to verify staged changes
- File paths are relative to project root (MCP resolver defaults to `os.getcwd()`)
- The `VIEWPORT_PROJECT_ROOT` environment variable overrides the project root if needed
- Session management is automatic (MCP framework handles session IDs)
- Conflict detection: server tracks file mtime+size externally; stale-file soft warning on reads, hard block on `file:save` (use `force: true` override if change is intentional)
```

## Design Principles

- **Prose + YAML only** — tool descriptions, input schemas, and responses use natural language and YAML. No JSON.
- **list_tools for discovery** — no dedicated help tool. The MCP protocol's standard discovery mechanism is sufficient.
- **True delta diffs** — `diff:show` always compares against the original file on disk, not the last save.
- **apply-diff always stages** — diffs are never applied directly to disk. Review first with `diff:show`, then `file:save`.
- **Per-viewport mode** — each viewport selects its own mode (buffered or immediate). Switch modes with `viewport:set-display-mode` (refuses if buffer is dirty).

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
