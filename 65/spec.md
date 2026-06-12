# [SPEC] MCP-Level AGENTS.md Injection for Sibling File Operations

**Issue:** https://github.com/michael-conrad/viewport-editor/issues/65
**Status:** DRAFT
**Author:** OpenCode (deepseek-v4-flash:cloud)

## Problem

The agent (`opencode-cli`) injects sibling `AGENTS.md` content into the conversation
when the agent uses the built-in `read` tool. This is how model-timeout mandates
(120s → 3600s) and model-set constraints reach the model's context.

When file operations go through MCP tools (`viewport:open`, composite `read_file`),
the injection never fires. MCP bypasses the agent's built-in tool-injection layer
entirely. The model operating files via viewport-editor never sees the AGENTS.md
constraints that reside in the same directory as the files being operated on.

This produces wrong behavior: default 120s timeouts apply, wrong models get selected,
and AGENTS.md mandates are silently absent during MCP-mediated file read operations.

**Root cause:** The injection mechanism lives in the agent's tool-handling layer
(opencode-cli's `read` handler). MCP tools bypass this layer entirely — they receive
a file path from the LLM and operate on it directly, with no intermediate AGENTS.md
scanning. The MCP server has no equivalent of the sibling AGENTS.md injection that
the built-in `read` tool provides.

## Solution

The MCP server detects sibling `AGENTS.md` files when opening a file for reading
(`viewport:open`, composite `read_file`). When found, the AGENTS.md content is
appended to the tool response wrapped in a `<system-reminder>` block, matching
the built-in `read` tool's injection format exactly. Per-session tracking prevents
duplicate injection.

This mirrors the behavior of the built-in `read` tool, which injects AGENTS.md
content from the file's ancestor directories into the conversation. The MCP server
does the same thing, but at the tool-response level rather than the conversation level.

## Design

### AGENTS.md Detection

On every file path resolution for read-equivalent tools (`viewport:open`,
composite `read_file`), walk up from the file's directory to the project root
(CWD at server start), checking each parent directory for an `AGENTS.md` file.
Return the **first-found** (nearest ancestor) AGENTS.md content. If the file
being opened IS the AGENTS.md itself, skip injection.

```python
def _find_sibling_agents_md(file_path: str, project_root: str) -> str | None:
    """Walk up from file_path's directory to project_root looking for AGENTS.md.
    Skips if file_path IS the AGENTS.md. Returns content of the first (nearest)
    AGENTS.md found, or None."""
    resolved_file = os.path.realpath(file_path)
    resolved_root = os.path.realpath(project_root)
    current = os.path.dirname(resolved_file)
    while current.startswith(resolved_root + os.sep) or current == resolved_root:
        candidate = os.path.join(current, "AGENTS.md")
        if os.path.isfile(candidate):
            # Skip if the file being opened IS the AGENTS.md itself
            if os.path.realpath(candidate) == resolved_file:
                return None
            with open(candidate) as f:
                return f.read()
        if current == resolved_root:
            break
        current = os.path.dirname(current)
    return None
```

### Injection Format

Match the built-in `read` tool exactly. Appended after the normal tool response
text, in the same `content[0].text` string:

```
<system-reminder>
Instructions from: /path/to/AGENTS.md
<raw AGENTS.md content>
</system-reminder>
```

The built-in produces this by appending to the output string:
```python
output += f"\n\n<system-reminder>\nInstructions from: {agents_path}\n{content}\n</system-reminder>"
```

The content is **raw AGENTS.md text** — no summarization, no truncation.
The model needs to see the exact mandates. The `<system-reminder>` wrapping is
the built-in's authority-signal mechanism — losing it loses the signal.

### Per-Session Deduplication

Each session tracks which AGENTS.md paths have been injected. On subsequent read
operations under the same AGENTS.md, the injection is silently skipped.

```python
# Per-session set of injected AGENTS.md absolute paths
session.injected_agents_files: set[str]
```

Check before injection: `if agents_path not in session.injected_agents_files`

### Tools Covered

| Tool | Action | AGENTS.md Check Trigger |
|------|--------|-------------------------|
| `viewport` | `open` | On open (file_path resolved against disk) |
| `viewport` | `scroll`, `jump`, `page-up`, `page-down` | No (file already open, already injected) |
| `edit` | all | No (not a read operation; built-in edit doesn't inject) |
| `file` | all | No (not a read operation) |
| `search` | all | No (not a read operation) |
| `clipboard` | all | No (not a read operation) |
| `diff` | all | No (no file_path parameter) |
| `read_file` (composite, from #63) | all | On file_path resolve — same injection as viewport:open |

Only read-equivalent operations trigger injection. This matches the built-in
behavior where only the `read` tool (not `write` or `edit`) injects sibling
AGENTS.md content.

### Self-Injection Guard

If the file_path being opened resolves to `*/AGENTS.md`, skip injection.
The agent is reading the AGENTS.md itself — injecting duplicate content is
redundant noise. Matches the built-in `if (found === target) continue` guard.

### Symlink-Safe Path Comparison

Both the file path and project root are resolved via `os.path.realpath()` before
the walk-up loop. This prevents early termination on macOS where `/tmp` resolves
to `/private/tmp`.

### Implementation Location

**New function** in `src/viewport_editor/file_ops.py`:
- `_find_sibling_agents_md(file_path, project_root) -> str | None`

**Modify** `src/viewport_editor/session.py`:
- Add `injected_agents_files: set[str]` field to `Session`

**Modify** `src/viewport_editor/server.py`:
- Add `_inject_agents_notice(file_path, session_id, response_text) -> str` that
  calls `_find_sibling_agents_md`, checks dedup, appends `<system-reminder>` block
  if found, and records in session. Returns the (possibly modified) response text.
- Call from: `_action_open` handler and composite `read_file` handler

The injection happens AFTER the normal response text is built, appending the
`<system-reminder>` block to the same text string before returning.

## Spec Requirements

### R1: Read-equivalent tool coverage only

Only tools that read file content trigger injection: `viewport:open` and composite
`read_file`. Write/edit/file/search/clipboard/diff tools do not trigger injection,
matching the built-in `read`-only behavior.

### R2: Session dedup across tool types

If `viewport:open` injects AGENTS.md for a file, then composite `read_file` for
the same file, the injection must NOT fire again. Dedup is by AGENTS.md path,
not by tool type. The set `injected_agents_files` is session-scoped and shared
across all tools.

### R3: Project root boundary (CWD)

The walk-up algorithm uses CWD at server start as the upper boundary. It never
ascends above the project root. `os.path.realpath()` ensures symlink-safe
comparison. Files outside the project root are caught by the existing
`_resolve_path` validation and never reach the injection check.

### R4: Error handling for unreadable AGENTS.md

If an AGENTS.md file exists but is unreadable (permissions, binary content,
encoding error), the server must silently skip injection (no crash, no partial
content, no error message to the model).

### R5: Self-injection guard

If the file path being opened IS the AGENTS.md itself, skip injection. The
agent reading the AGENTS.md file doesn't need the same content injected as a
system-reminder.

### R6: Composite `read_file` inherits injection

The composite `read_file` tool from spec #63 delegates to the viewport open path
internally. It must trigger the same AGENTS.md injection as `viewport:open`.

### R7: Injection format matches built-in exactly

Format: `<system-reminder>\nInstructions from: {path}\n{content}\n</system-reminder>`
appended to the response text. Single `content[0].text` string (not separate
content array items — opencode's MCP result parser drops all but the first text
item).

## Success Criteria

| ID | Criterion | Evidence Type | Verification Method |
|----|-----------|---------------|---------------------|
| SC-1 | `viewport:open` on a file under a directory with AGENTS.md appends `<system-reminder>` with AGENTS.md content to the response | `behavioral` | Test: open a file in a directory with AGENTS.md → response contains `<system-reminder>` with AGENTS.md content |
| SC-2 | Same AGENTS.md is NOT injected twice in the same session | `behavioral` | Test: open two files under same AGENTS.md → only first response has injection |
| SC-3 | AGENTS.md at project root injects when no closer AGENTS.md exists | `behavioral` | Test: open a file in a dir without AGENTS.md but with one at project root → root AGENTS.md injected |
| SC-4 | Nearest-ancestor rule: deepest AGENTS.md wins over shallower one | `behavioral` | Test: file under `a/b/AGENTS.md` where `a/AGENTS.md` also exists → `a/b/AGENTS.md` is injected |
| SC-5 | `injected_agents_files` field exists on Session dataclass | `structural` | Check `session.py` for `injected_agents_files: set[str]` |
| SC-6 | Files outside project root (absolute paths) skip AGENTS.md check | `behavioral` | Test: open `/etc/passwd` → no `<system-reminder>` in response |
| SC-7 | Unreadable AGENTS.md silently skipped (no crash, no partial content) | `behavioral` | Test: AGENTS.md with 000 permissions → injection silently skipped |
| SC-8 | File that IS the AGENTS.md itself does not trigger self-injection | `behavioral` | Test: open `AGENTS.md` → response does not contain `<system-reminder>` |
| SC-9 | Composite `read_file` triggers same AGENTS.md injection as `viewport:open` | `behavioral` | Test: read_file on a file under AGENTS.md → response contains AGENTS.md content in `<system-reminder>` |
| SC-10 | Composite `read_file` + `viewport:open` in same session share dedup | `behavioral` | Test: read_file then viewport:open on files under same AGENTS.md → single injection total |
| SC-11 | Injection format matches `<system-reminder>\nInstructions from: ...\n` built-in pattern | `string` | grep response for `<system-reminder>\nInstructions from:` |
| SC-12 | `os.path.realpath()` is used for symlink-safe path comparison | `structural` | Check `_find_sibling_agents_md` for `os.path.realpath` calls on both file_path and project_root |

## Implementation Plan

### Phase 1: Core Detection + Session Tracking

1. Implement `_find_sibling_agents_md()` in `src/viewport_editor/file_ops.py`
   - Uses `os.path.realpath()` on file_path and project_root
   - Nearest-ancestor walk-up (returns first found)
   - Self-injection guard (skip if file_path IS the AGENTS.md)
   - Returns `str | None`

2. Add `injected_agents_files: set[str]` to `Session` in `src/viewport_editor/session.py`

3. Implement `_inject_agents_notice()` helper in `src/viewport_editor/server.py`
   - Calls `_find_sibling_agents_md`, checks dedup against `session.injected_agents_files`
   - Builds `<system-reminder>` block in built-in format
   - Appends to response text
   - Records in session

### Phase 2: Tool Integration

4. Wire injection into `_action_open()` handler — the primary read-equivalent tool
5. Wire injection into composite `read_file` handler (spec #63) — delegates to same helper

### Phase 3: Behavioral Tests

6. Create test fixture directory structure with AGENTS.md files
7. Set up test AGENTS.md with known content per fixture
8. Behavioral test: open file under AGENTS.md → injection seen (SC-1)
9. Behavioral test: second open → no duplicate injection (SC-2)
10. Behavioral test: nearest-ancestor precedence (SC-4)
11. Behavioral test: absolute-path files → no injection (SC-6)
12. Behavioral test: unreadable AGENTS.md → silent skip (SC-7)
13. Behavioral test: self-injection guard (SC-8)
14. Behavioral test: composite read_file injection (SC-9)
15. Behavioral test: cross-tool dedup read_file + viewport:open (SC-10)

## Evaluation Methodology

### Per-Tool Injection Verification

Each read-equivalent tool handler must be tested independently. A test fixture
directory tree with AGENTS.md at two levels establishes the nearest-ancestor
behavior:

```
tmp/test-agents/
  AGENTS.md           → "ROOT AGENTS"
  subdir/
    AGENTS.md          → "SUBDIR AGENTS"
    target_file.txt
```

### Dedup Verification

One session, two read operations under the same AGENTS.md. Only the first
response contains the `<system-reminder>` block. The second response is tool
output only.

### Session Isolation

Different sessions receive independent injection tracking. Opening a file under
the same AGENTS.md in session A and session B produces injection in both sessions.

## Branch and Tagging Strategy

Tracking on `feature/65-agents-injection`.

## Cross-References

- **Spec #63** — Composite action tools. `read_file` composite tool inherits
  AGENTS.md injection from the same `_inject_agents_notice` helper.
- **Test framework** (`test/tool_selection/`) — The MCP test server and runner
  scripts can verify injection behavior.
- **`test/tool_selection/AGENTS.md`** — The actual AGENTS.md that needs injection
  for tool selection test runs.

## SC Coverage

| ID | Status | Notes |
|----|--------|-------|
| SC-1 | PENDING | viewport:open injection |
| SC-2 | PENDING | dedup in session |
| SC-3 | PENDING | root fallback |
| SC-4 | PENDING | nearest ancestor wins |
| SC-5 | PENDING | structural check |
| SC-6 | PENDING | absolute path skip |
| SC-7 | PENDING | unreadable skip |
| SC-8 | PENDING | self-injection guard |
| SC-9 | PENDING | composite read_file |
| SC-10 | PENDING | cross-tool dedup |
| SC-11 | PENDING | format match |
| SC-12 | PENDING | realpath symlink safety |