<!-- SPDX-FileCopyrightText: 2026 Michael Conrad -->
<!-- SPDX-License-Identifier: MIT -->
<!-- Provenance: AI-generated -->

# Comparison: How AI Agents Experience Editor Tooling

*This document is written from the perspective of an AI agent using each tool.
It describes what the agent sees, what it must do to accomplish a task, and where
each approach creates friction. It is not a feature checklist — it is a user
experience report from the agent's side of the protocol.*

---

## The Built-in Read/Edit/Write Tools

These are the default tools present in most AI agent environments. The agent has
three operations: read a file, replace a string in a file, write a file.

### What the Agent Experiences

When I need to edit a 400-line file, I must:

1. **Read the entire file.** Every line. Even if I only need line 37 and line 284.
   I pay the context cost for all 400 lines before I can do anything.

2. **Construct an exact string match.** I must find a unique substring in the file
   that anchors my edit. If the text appears twice (a variable name used in two
   functions, a common import, a repeated comment), my edit fails with "multiple
   matches." I must find a longer, more specific anchor — consuming more of my
   reasoning budget.

3. **Replace and write the entire file back.** I cannot make five edits and review
   them together. Each edit is a full read, full match, full write cycle. If I
   make three edits in sequence, I read the full file three times.

4. **No safety net.** The write is immediate. There is no "show me what changed."
   No staging area. No "discard." If my string match was wrong, the file is
   corrupted and I discover it on the next read.

### When It Works

- Simple, one-shot edits to small files (< 50 lines).
- Situations where the edit target is unique across the entire file.
- Initial file creation and boilerplate setup.

### Maintained Status

These are built into the agent platform and maintained by the platform vendor.
They will always exist. They will not change to accommodate viewport-style editing.

---

## Anthropic Filesystem MCP Server (`@modelcontextprotocol/server-filesystem`)

The official filesystem server from the MCP specification repository. Provides
file operations including an `edit_file` tool.

### What the Agent Experiences

The `edit_file` tool accepts an array of edits, each with `oldText` and `newText`.
It supports dry-run mode and returns a git-style diff.

1. **I must still construct string matches.** The edit operation works by finding
   `oldText` in the file and replacing it. This is the same ambiguity problem as
   the built-in tools — repeated text causes failures.

2. **Dry-run helps, but adds a round trip.** I can call `edit_file` with
   `dryRun: true` to preview, then call again to apply. This is better than blind
   writes, but doubles my tool calls for every edit.

3. **No viewport concept.** I cannot say "only match within lines 30-50." The
   match scans the entire file.

4. **No per-viewport mode selection.** No buffered vs immediate. Every edit is
   immediate (with an optional dry-run preview).

5. **Hash-based conflict detection.** The server tracks the content hash at last
   read. If another process modified the file between my read and my edit, the
   edit fails. This is good, but the hash covers the entire file — any unrelated
   change elsewhere in the file blocks my edit.

### When It Works

- Edits where the target text is unique in the file.
- Workflows where the agent can afford the dry-run round trip.
- File-level operations (copy, move, search, directory tree) are well covered.

### Maintained Status

Official MCP specification repository. Regular updates, active maintenance.

---

## `mcp-text-editor` (tumf/mcp-text-editor)

A line-oriented text editor MCP server. Provides hash-verified line-range reads
and hash-verified patch operations.

### What the Agent Experiences

1. **I can read a line range.** I specify `file_path`, `line_start`, `line_end`,
   and I get only those lines. I also get a SHA-256 hash of the content range.
   This is token-efficient — I read only what I need.

2. **Patch-based editing is safe but verbose.** To edit, I must:
   - Read the target range to get the hash.
   - Construct a patch with `start`, `end`, `range_hash`, and `contents`.
   - Send the patch, which validates the hash before applying.
   This is three steps per edit. Safe, but high latency per operation.

3. **No viewport abstraction.** The agent manages line numbers and hashes
   manually. There is no "viewport" concept — just raw line ranges and hashes.
   The agent must track its own position in the file.

4. **No operational modes.** Every operation is immediate. No staging, no diff
   preview, no discard.

5. **Hash at the range level.** If I read lines 10-20 and someone modifies line
   12 elsewhere, my range hash mismatch blocks my edit. This is more granular
   than full-file hashes, but more fragile.

### When It Works

- Token-efficient reading (line-range reads are excellent).
- Single-edit operations where the agent can afford the read-hash-edit cycle.
- Scenarios requiring hash verification for safety.

### Maintained Status

Python-based project, MIT license, 191 stars, active development (240 commits).
Well-documented with test coverage at 90%. Appears actively maintained.

---

## `mcp-editor` (arathald/mcp-editor)

A TypeScript port of Anthropic's computer-use file editing demo.

### What the Agent Experiences

1. **String-replace editing.** Same `view` + `create` + `string_replace` pattern
   as the Anthropic demo. I view a file, then replace a unique string.

2. **No access control.** The README explicitly warns: "has no access control and
   relies entirely on the client's approval mechanism." I can edit any file the
   process has access to.

3. **No hash verification.** No conflict detection. If I read a file, then another
   process modifies it, my edit silently clobbers the change.

4. **Not actively maintained.** The README states: "This MCP server is not actively
   maintained and is provided only as a reference."

### When It Works

- Experimental or reference use.
- Single-user environments where access control and conflict detection
  are not concerns.

### Maintained Status

Not actively maintained. Per the author: "provided only as a reference."

---

## viewport-editor (this project)

An MCP server designed from the ground up for how AI agents edit files.

### What the Agent Experiences

1. **I open a viewport.** I say `viewport:open("src/main.py", 10, 40)` and
   I get a focused window. I see 30 lines. I know the file, the range, the
   timestamp, and the mode. I can name this viewport and work within it.

2. **Every edit is scoped.** When I call `edit:replace`, the match is against
   the viewport content, not the full file. No ambiguous matches. No "found
   in 3 places." The scope is explicit.

3. **I can stage and review.** In buffered mode, my edits accumulate in a buffer.
   I call `diff:show` and see a true delta against the original file on disk.
   I review. If it is wrong, I call `file:discard` and start over. If it is
   right, I call `file:save`.

4. **I can work in immediate mode.** If I am confident, I set the viewport to
   immediate mode. Every edit writes to disk atomically. No staging overhead.

5. **I can switch modes per-viewport.** `viewport:switch-mode` changes the mode.
   If the buffer is dirty, I get a clear message: "buffer has unsaved changes,
   save or discard before switching mode."

6. **I can navigate structurally.** `viewport:jump` goes to a line number,
   function name, markdown heading, table, or search result. I do not track
   line numbers manually.

7. **I can search and replace intelligently.** `search:find` returns structured
   results. `edit:replace-all` operates across a scope I choose. `edit:insert-lines`,
   `edit:delete-lines`, `edit:swap-lines`, `edit:move-lines` give me line-level
   operations that avoid string matching entirely.

8. **I can apply diffs safely.** `diff:apply` stages a unified diff into the
   buffer. The diff is never written directly to disk. I review with `diff:show`,
   then `file:save`.

9. **I have session isolation.** If another agent session is editing the same
   file, I get a soft warning on every operation. On save, if the file changed,
   I get a hard block (unless I use `force`).

10. **The interface speaks my language.** All tool descriptions, schemas, and
    responses use natural language prose and YAML. No JSON. I do not parse
    nested `$ref` schemas to understand a parameter.

### Maintained Status

New project, actively developed, MIT license.

---

## Summary

| Dimension | Built-in Read/Edit/Write | filesystem MCP | mcp-text-editor | mcp-editor | viewport-editor |
|-----------|--------------------------|----------------|-----------------|------------|-----------------|
| Edit scoping | full file | full file | line range | full file | viewport |
| Ambiguous match risk | high | high | none (line-based) | high | none |
| Edit staging | no | dry-run only | no | no | buffered mode |
| Diff preview | no | yes (dry-run) | no | no | yes (true delta) |
| Conflict detection | none | full-file hash | range hash | none | mtime+size |
| Multiple viewports | no | no | no | no | yes |
| Structural navigation | no | no | no | no | yes (jump) |
| Per-viewport modes | no | no | no | no | yes |
| Line operations | no | no | no | no | yes (6 actions) |
| Prose+YAML interface | schema default | JSON | JSON | JSON | designed for |
| Active maintenance | platform-vendor | active | active | not maintained | active |

---

*This document describes each tool from the perspective of an AI agent consuming
it via MCP. The analysis focuses on what the agent experiences during a typical
edit workflow, not on feature counts or implementation complexity.*

🤖 Co-authored with AI: OpenCode (ollama-cloud/deepseek-v4-flash)
