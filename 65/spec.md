# [SPEC] MCP-Level AGENTS.md Injection for Sibling File Operations

**Issue:** https://github.com/michael-conrad/viewport-editor/issues/65
**Status:** DRAFT
**Author:** OpenCode (deepseek-v4-flash:cloud)

## Problem

The agent (`opencode-cli`) injects sibling `AGENTS.md` content into the conversation when the agent uses built-in `read`/`edit`/`write` tools. This is how model-timeout mandates (120s → 3600s) and model-set constraints reach the model's context.

When file operations go through MCP tools (`viewport:open`, `file:save`, `search:find`, etc.), the injection never fires. MCP bypasses the agent's built-in tool-injection layer entirely. The model operating files via viewport-editor never sees the AGENTS.md constraints that reside in the same directory as the files being operated on.

This produces wrong behavior: default 120s timeouts apply, wrong models get selected, and AGENTS.md mandates are silently absent during MCP-mediated file operations.

**Root cause:** The injection mechanism lives in the agent's tool-handling layer (opencode-cli's `read`/`write`/`edit` handlers). MCP tools bypass this layer entirely — they receive a file path from the LLM and operate on it directly, with no intermediate AGENTS.md scanning. The MCP server has no equivalent of the sibling AGENTS.md injection that the built-in tools provide.

## Solution

The MCP server detects sibling `AGENTS.md` files when resolving file paths for any file-touching tool. When found, the AGENTS.md content is prepended to the tool response. Per-session tracking prevents duplicate injection.

This mirrors the behavior of the built-in `read`/`edit`/`write` tools, which inject AGENTS.md content from the file's parent directory into the conversation. The MCP server does the same thing, but at the tool-response level rather than the conversation level.

## Design

### AGENTS.md Detection

On every file path resolution (for any file-touching tool), walk up from the file's directory to the project root, checking each parent directory for an `AGENTS.md` file. The first one found is the sibling AGENTS.md for that file. Return the **first-found** (nearest ancestor) AGENTS.md content.

```python
def _find_sibling_agents_md(file_path: str, project_root: str) -> str | None:
    """Walk up from file_path's directory to project_root looking for AGENTS.md.
    Returns the content of the first AGENTS.md found, or None."""
    current = os.path.dirname(os.path.abspath(file_path))
    root = os.path.abspath(project_root)
    while current.startswith(root + os.sep) or current == root:
        candidate = os.path.join(current, "AGENTS.md")
        if os.path.isfile(candidate):
            with open(candidate) as f:
                return f.read()
        if current == root:
            break
        current = os.path.dirname(current)
    return None
```

### Injection Format

When AGENTS.md content is found and has not been injected for the current session, prepend it to the tool response:

```
[AGENTS.md injection from /path/to/AGENTS.md]
<content>
---
<normal tool response>
```

The content is **raw AGENTS.md text** — no summarization, no truncation. The model needs to see the exact mandates.

### Per-Session Deduplication

Each session tracks which AGENTS.md paths have been injected. On subsequent file operations under the same AGENTS.md, the injection is silently skipped.

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
| `file` | `save` | On save (file_path resolved) |
| `file` | `save-as` | On save-as (new file_path resolved) |
| `file` | `delete` | On delete (file_path resolved) |
| `edit` | all | No (viewport already open) |
| `search` | `find` scope=file | On file match (file_path resolved against disk) |
| `search` | `find` scope=project | First file match triggers check |
| `clipboard` | `copy`, `cut` | On source file resolution |
| `clipboard` | `paste` | No (target viewport already open) |
| `read_file` (composite, from #63) | all | On file_path resolve |
| `write_file` (composite, from #63) | all | On file_path resolve |
| `edit_text` (composite, from #63) | all | On file_path resolve |
| `find_text` (composite, from #63) | all | On file_path resolve |

### Implementation Location

**New function** in `src/viewport_editor/file_ops.py`:
- `_find_sibling_agents_md(file_path, project_root) → str | None`

**Modify** `src/viewport_editor/session.py`:
- Add `injected_agents_files: set[str]` field to `Session`

**Modify** `src/viewport_editor/server.py`:
- Add helper `_inject_agents_notice(file_path, session_id, response)` that calls `_find_sibling_agents_md`, checks dedup, prepends content if found, and records in session
- Call from: `_action_open`, `_handle_file_action` (save, save-as, delete), `_handle_search_action` (find-scope-file), `_handle_clipboard_action` (copy, cut), and composite tool handlers (read_file, write_file, edit_text, find_text from #63)

The injection happens AFTER the tool handler produces its normal response, prepending the notice.

## Spec Requirements

### R1: Composite tool coverage (#63 integration)

The five composite tools from spec #63 (`read_file`, `write_file`, `edit_text`, `find_text`, `diff`) also need AGENTS.md injection. Since `diff` has no file_path parameter (it operates on viewport state), it is exempt. The other four composite tools resolve file paths and must trigger injection.

### R2: Session dedup across tool types

If `viewport:open` injects AGENTS.md for a file, then `file:save-as` to the same AGENTS.md directory, the injection must NOT fire again. Dedup is by AGENTS.md path, not by tool type. The set `injected_agents_files` is session-scoped and shared across all tools.

### R3: Project root boundary

Files outside the project root (absolute paths like `/etc/passwd`) must not trigger AGENTS.md injection. The walk-up algorithm terminates at the project root — it never ascends above it. This prevents leaking system-wide AGENTS.md files or unrelated parent directories.

### R4: Error handling for unreadable AGENTS.md

If an AGENTS.md file exists but is unreadable (permissions, binary content, encoding error), the server must silently skip injection (no crash, no partial content, no error message to the model).

### R5: Composite tool `read_file` and `find_text` viewport lifecycle

For the `read_file` composite tool (opens viewport, returns content, keeps viewport open), the AGENTS.md injection must happen on the first call. If the model subsequently calls `edit_text` on the same file, no duplicate injection.

## Success Criteria

| ID | Criterion | Evidence Type | Verification Method |
|----|-----------|---------------|---------------------|
| SC-1 | `viewport:open` on a file under a directory with AGENTS.md prepends AGENTS.md content to the response | `behavioral` | Test: open a file in a directory with AGENTS.md → response contains AGENTS.md content |
| SC-2 | Same AGENTS.md is NOT injected twice in the same session | `behavioral` | Test: open two files under same AGENTS.md → only first response has injection |
| SC-3 | AGENTS.md from a different parent (project root) injects when no closer AGENTS.md exists | `behavioral` | Test: open a file in a dir without AGENTS.md but with one at project root → root AGENTS.md injected |
| SC-4 | `file:save-as` with new path under a different AGENTS.md triggers new injection | `behavioral` | Test: save-as to directory under different AGENTS.md → new AGENTS.md content injected |
| SC-5 | `search:find` scope=file injects AGENTS.md for matched file's directory | `behavioral` | Test: find in a file under AGENTS.md → response contains AGENTS.md content |
| SC-6 | `clipboard:copy` from a file under AGENTS.md injects AGENTS.md content | `behavioral` | Test: copy from file under AGENTS.md → response contains AGENTS.md content |
| SC-7 | Injection format includes `[AGENTS.md injection from ...]` header and `---` separator | `string` | grep response for the header pattern |
| SC-8 | Nearest-ancestor rule: deepest AGENTS.md wins over shallower one | `behavioral` | Test: file under `a/b/AGENTS.md` where `a/AGENTS.md` also exists → `a/b/AGENTS.md` is injected |
| SC-9 | `injected_agents_files` field exists on Session dataclass | `structural` | Check `session.py` for `injected_agents_files: set[str]` |
| SC-10 | Files outside project root (absolute paths) skip AGENTS.md check | `behavioral` | Test: open `/etc/passwd` → no AGENTS.md injection |
| SC-11 | Unreadable AGENTS.md silently skipped (no crash, no partial content) | `behavioral` | Test: AGENTS.md with 000 permissions → injection silently skipped |
| SC-12 | Composite `read_file` triggers injection on first call, not on subsequent edits | `behavioral` | Test: read_file then edit_text on same file → single injection |
| SC-13 | `diff` composite tool does not trigger AGENTS.md injection (no file_path) | `behavioral` | Test: call diff → no AGENTS.md header in response |

## Implementation Plan

### Phase 1: Core Detection + Session Tracking

1. Implement `_find_sibling_agents_md()` in `src/viewport_editor/file_ops.py`
2. Add `injected_agents_files: set[str]` to `Session` in `src/viewport_editor/session.py`
3. Implement `_inject_agents_notice()` helper in `src/viewport_editor/server.py`

### Phase 2: Tool Integration

4. Wire injection into `_action_open()` (viewport open)
5. Wire injection into `_handle_file_action()` (save, save-as, delete)
6. Wire injection into `_handle_search_action()` (find-scope-file, find-scope-project)
7. Wire injection into `_handle_clipboard_action()` (copy, cut)
8. Wire injection into composite tool handlers (read_file, write_file, edit_text, find_text from #63)

### Phase 3: Behavioral Tests

9. Create test fixture directory structure with AGENTS.md files
10. Set up test AGENTS.md with known content per fixture
11. Behavioral test: open file under AGENTS.md → injection seen (SC-1)
12. Behavioral test: second open → no duplicate injection (SC-2)
13. Behavioral test: nearest-ancestor precedence (SC-8)
14. Behavioral test: absolute-path files → no injection (SC-10)
15. Behavioral test: unreadable AGENTS.md → silent skip (SC-11)
16. Behavioral test: composite tool path → single injection (SC-12)

## Evaluation Methodology

### Per-Tool Injection Verification

Each tool handler that resolves a file path must be tested independently. A test fixture directory tree with AGENTS.md at two levels establishes the nearest-ancestor behavior:

```
tmp/test-agents/
  AGENTS.md           → "ROOT AGENTS"
  subdir/
    AGENTS.md          → "SUBDIR AGENTS"
    target_file.txt
```

### Dedup Verification

One session, two file operations under the same AGENTS.md. Only the first response contains the injection header. The second response is tool output only.

### Session Isolation

Different sessions receive independent injection tracking. Opening a file under the same AGENTS.md in session A and session B produces injection in both sessions.

## Branch and Tagging Strategy

Tracking on `feature/65-agents-injection` (or as sub-phase of `feature/63-composite-tools` since they share the same server.py file and test framework).

## Cross-References

- **Spec #63** — Composite action tools. The 5 composite tools share the same `server.py` handlers and need AGENTS.md injection wired in.
- **Test framework** (`test/tool_selection/`) — The MCP test server and runner scripts can verify injection behavior.
- **`test/tool_selection/AGENTS.md`** — The actual AGENTS.md that needs injection for tool selection test runs.

## SC Coverage

| ID | Status | Notes |
|----|--------|-------|
| SC-1 to SC-13 | PENDING | Implementation + behavioral tests |