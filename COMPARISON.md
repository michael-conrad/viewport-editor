<!-- SPDX-FileCopyrightText: 2026 Michael Conrad -->
<!-- SPDX-License-Identifier: MIT -->
<!-- Provenance: AI-generated -->

# Comparison: How AI Agents Experience Editor Tooling

*This document is written from the perspective of an AI agent using each tool.
It describes what the agent sees, what it must do to accomplish a task, and where
each approach creates friction. Links verified as of 2026-05-25.*

---

## Quick Comparison Table

| Dimension | Built-in R/E/W | filesystem MCP | mcp-text-editor | mcp-editor | texted | viewport-editor |
|-----------|----------------|----------------|-----------------|------------|--------|-----------------|
| Edit paradigm | string match | string match | line patch | string match | script commands | viewport-scoped edit |
| Ambiguous match risk | high | high | none | high | medium | none |
| Edit staging | no | dry-run only | no | no | no | yes (buffered) |
| Diff preview | no | yes (dry-run) | no | no | no | yes (true delta) |
| Conflict detection | none | full-file hash | range hash | none | none | mtime+size |
| Multiple viewports | no | no | no | no | no | yes |
| Structural navigation | no | no | no | no | no | yes (jump) |
| Per-viewport modes | no | no | no | no | no | yes |
| Line operations | no | no | no | no | yes (scripted) | yes (native) |
| Discoverability | tool list | tool list | tool list | tool list | list_tools + texted_doc | list_tools |
| Prose+YAML | no | no | no | no | no | yes |
| Active maintenance | platform | active | active | not maintained | stable | active |
| Stars / community | — | 86.2k (servers) | 191 | 8 | — | new |

---

## Detailed Analysis

### The Built-in Read/Edit/Write Tools

These are the default tools present in most AI agent environments. The agent has
three operations: read a file, replace a string in a file, write a file.

#### What the Agent Experiences

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

#### When It Works

- Simple, one-shot edits to small files (< 50 lines).
- Situations where the edit target is unique across the entire file.
- Initial file creation and boilerplate setup.

#### Maintained Status

Built into the agent platform and maintained by the platform vendor.
They will always exist. [Source](https://opencode.ai)

---

### `@modelcontextprotocol/server-filesystem`

The official filesystem server from the MCP specification repository.
[GitHub](https://github.com/modelcontextprotocol/servers/tree/main/src/filesystem) |
[npm](https://www.npmjs.com/package/@modelcontextprotocol/server-filesystem) |
Latest: 2026.1.14 (published 2026-01, verified API response).

#### Tools Exposed

`read_text_file`, `read_media_file`, `read_multiple_files`, `write_file`,
`edit_file`, `create_directory`, `list_directory`, `list_directory_with_sizes`,
`directory_tree`, `search_files`, `get_file_info`, `move_file`,
`list_allowed_directories` (npm verified, 13 tools)

#### What the Agent Experiences

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

5. **Full-file hash for conflict detection.** The `edit_file` tool tracks content
   state at the file level. If any unrelated change occurs elsewhere in the file,
   the edit fails.

#### When It Works

- Edits where the target text is unique in the file.
- Workflows where the agent can afford the dry-run round trip.
- File-level operations (copy, move, search, directory tree) are well covered.

#### Maintained Status

Official MCP specification repository. Regular updates, active maintenance.
86.2k stars, 10.8k forks on the servers monorepo.

---

### `mcp-text-editor` (tumf/mcp-text-editor)

A line-oriented text editor MCP server.
[GitHub](https://github.com/tumf/mcp-text-editor) |
191 stars, 21 forks, 240 commits, Python, MIT.

#### Tools Exposed

`get_text_file_contents` (with line-range + hash), `patch_text_file_contents`
(with range_hash validation). Two focused tools.

#### What the Agent Experiences

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

5. **Range-level hash for conflict detection.** More granular than file-level,
   but also more fragile. Any change in the range invalidates the hash.

#### When It Works

- Token-efficient reading (line-range reads are excellent).
- Single-edit operations where the agent can afford the read-hash-edit cycle.
- Scenarios requiring hash verification for safety.

#### Maintained Status

Actively maintained. 191 stars, 240 commits, 90% test coverage per GitHub.

---

### `mcp-editor` (arathald/mcp-editor)

A TypeScript port of Anthropic's computer-use file editing demo.
[GitHub](https://github.com/arathald/mcp-editor) |
8 stars, 6 forks, 9 commits, TypeScript, MIT.

#### Tools Exposed

`view` (read file with optional range), `create` (write new file),
`string_replace` (find and replace unique string). Three tools.

#### What the Agent Experiences

1. **String-replace editing.** Same pattern as the Anthropic demo: view a file,
   then replace a unique string. Ambiguity risk on repeated text.

2. **No access control.** The README states: "This MCP server has NO access
   controls and relies entirely on your client's approval mechanisms."

3. **No hash verification.** No conflict detection. If I read a file, then
   another process modifies it, my edit silently clobbers the change.

4. **Not actively maintained.** The README states: "This MCP server is NOT
   actively maintained, and is provided for reference."

#### When It Works

- Experimental or reference use.
- Single-user environments where access control and conflict detection
  are not concerns.

#### Maintained Status

Not actively maintained. Per the author: "provided only as a reference."

---

### texted (dhamidi/texted)

A compiled (Go) script-based text editor exposing Emacs Lisp-style editing
commands via MCP.
[GitHub](https://github.com/dhamidi/texted) |
Analysis based on live `tools/list` response from compiled binary
(commit 2a9d1b04e7ac0e5a98dd648534f438626a9437a1).

#### Tools Exposed

`edit_file` — applies a script of editing commands to multiple files.
`texted_doc` — queries function documentation programmatically.
`texted_eval` — tests scripts on input text before applying.

Three tools total.

#### What the Agent Experiences

The edit paradigm is fundamentally different from line-based or string-match
editors. I write a **script** — a sequence of Emacs Lisp-style commands — and
texted applies it to one or more files.

To change line 5 of a file, I must write:

```texted
goto-line 5
replace-match "new content\n"
```

1. **I write code to edit code.** Every edit requires me to compose a script
   in texted's command language. For a simple replacement, I write:
   `search-forward "old text"` then `replace-match "new text"`.
   For a multi-step edit across different locations, the script grows
   correspondingly. Each step must be correct; if the file doesn't match my
   script's assumptions (e.g., search-forward can't find the anchor because
   the file was modified since I last read it), the entire script fails.

2. **I can test scripts before applying.** The `texted_eval` tool lets me run
   a script against input text and see the result. This is a significant
   advantage over blind string-replace — I can verify my logic before
   committing to a file.

3. **I can query available commands.** The `texted_doc` tool lets me look up
   function signatures and descriptions. This helps me discover what
   operations are available. However, it is an additional context load
   compared to tools with self-describing schemas.

4. **No structural awareness.** texted's model is an Emacs-style buffer
   with a cursor. Commands operate on this cursor position and buffer
   state. There is no concept of function boundaries, markdown sections,
   or other file structure.

5. **No conflict detection.** texted applies the script unconditionally.
   If the file has changed between when I last read it and when I apply
   the script, texted does not detect this.

6. **No viewport concept.** texted's buffer model is fundamentally
   different — it loads the entire buffer into an editing context and
   operates through cursor movement, not scoped windows.

#### When It Works

- Complex multi-file transformations where the script can be verified
  with `texted_eval` before application.
- Patterns that benefit from texted's command language (e.g., find a
  pattern and insert around it).
- Batch operations across many files.

#### Maintained Status

Stable project. Go-based, compiled binary. 7.3 MB binary size.
Not frequently updated but functional.

---

### viewport-editor (this project)

[GitHub](https://github.com/michael-conrad/viewport-editor) |
Designed from the ground up for how AI agents edit files.

#### What the Agent Experiences

1. **I open a viewport.** I use `viewport:open` with a file, line range,
   and optional mode. I get a focused window with full context — file path,
   range, timestamp, size, and operational mode.

2. **Every edit is scoped.** When I call `edit:replace`, the match is against
   the viewport content, not the full file. No ambiguous matches. No "found
   in 3 places." The scope is explicit.

3. **I can stage and review.** In buffered mode, my edits accumulate in a
   buffer. I call `diff:show` and see a true delta against the original file
   on disk. I review. If it is wrong, I call `file:discard` and start over.
   If it is right, I call `file:save`.

4. **I can work in immediate mode.** If I am confident, I set the viewport to
   immediate mode. Every edit writes to disk atomically.

5. **I can switch modes per-viewport.** `viewport:switch-mode` changes the
   mode. If the buffer is dirty, I get a clear refusal message.

6. **I can navigate structurally.** `viewport:jump` goes to a line number,
   function name, markdown heading, table, or search result. I do not track
   line numbers manually.

7. **I can search and replace with rich operations.** `search:find` returns
   structured results. `edit:replace-all` operates across a scope I choose.
   Line-level operations (`insert-lines`, `delete-lines`, `swap-lines`,
   `move-lines`) avoid string matching entirely.

8. **I can apply diffs safely.** `diff:apply` stages a unified diff into the
   buffer. The diff is never written directly to disk. I review with
   `diff:show`, then `file:save`.

9. **I have session isolation.** If another agent session is editing the same
   file, I get a soft warning on every operation. On save, if the file changed,
   I get a hard block (unless I use `force`).

10. **The interface speaks my language.** All tool descriptions, schemas, and
    responses use natural language prose and YAML. No JSON.

#### Maintained Status

New project, actively developed, MIT license.

---

## Summary Table Notes

- **Built-in R/E/W**: present in every agent platform. No choice, no change.
- **filesystem MCP**: the official Anthropic MCP server. Strong for file
  management, weak for string-match editing.
- **mcp-text-editor**: best hash-verified approach. Token-efficient reads.
  High latency on edit cycle (read-hash-patch).
- **mcp-editor**: reference implementation. Not for production use.
- **texted**: script-based paradigm. Powerful for batch operations, no
  conflict detection, no structural awareness.
- **viewport-editor**: designed for the agent's editing workflow.
  Viewport-scoping eliminates ambiguous matches. Buffered staging provides
  safety. Mode selection provides workflow choice.

---

*This document describes each tool from the perspective of an AI agent consuming
it via MCP. The analysis focuses on what the agent experiences during a typical
edit workflow, not on feature counts or implementation complexity.*

🤖 Co-authored with AI: OpenCode (ollama-cloud/deepseek-v4-flash)
