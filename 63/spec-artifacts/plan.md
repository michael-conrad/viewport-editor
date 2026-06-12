# [PLAN] Composite Action Tools — Implementation Pipeline

## Authorization Context
```
authorization_scope: for_implementation
halt_at: verification_complete
pr_strategy: stacked
pipeline_phase: sc-coherence-gate
authorization_source: "User approved implementation on 2026-06-11"
```

## Item Decomposition

Six implementation items, processed sequentially through the 14-step pipeline. Each item follows a full RED → GREEN → VERIFY → AUDIT cycle. Items 1-5 are the composite tool handlers. Item 6 is the existing tool description rewrite.

| Item | Concerns | Spec SCs | Files Modified |
|------|----------|----------|----------------|
| **1. read_file** | Open viewport, return content + metadata, offset/limit partial reads, conflict warnings | SC-1, SC-2, SC-3 | `server.py` (+handler), `test/test_composite_tools.py` |
| **2. write_file** | Open viewport, replace-all content, save, close viewport, conflict detection, new file creation | SC-4, SC-5, SC-6, SC-10 | `server.py`, `test/test_composite_tools.py` |
| **3. edit_text** | Open viewport, replace(s), save, close viewport, old_text not found, ambiguous matches | SC-7, SC-8, SC-9, SC-10 | `server.py`, `test/test_composite_tools.py` |
| **4. find_text** | Substring search, regex search, structured results, file-scoped/project-wide | SC-11, SC-12 | `server.py`, `test/test_composite_tools.py` |
| **5. diff** | Unified diff of pending changes, empty state, no file_path param | SC-13, SC-14 | `server.py`, `test/test_composite_tools.py` |
| **6. Descriptions** | Rewrite 7 existing tool descriptions to agent-facing, positive-framing style | SC-18, SC-19 | `server.py` (docstrings only) |

## Tool Descriptions (Locked from V2)

```python
read_file = """Read file contents from the local filesystem into a staged buffer viewport.
If the file path does not exist, an error is returned. Supports offset/limit
for partial reads. The viewport remains open for follow-up edits. No content
touches disk until explicitly confirmed via file:save. Use this for all file
reading tasks including config files, source code, and logs."""

write_file = """Write file contents to the local filesystem through a staged buffer with
automated viewport lifecycle management. Opens a viewport, replaces the
entire buffer content, saves to disk, and closes the viewport. Conflict
detection catches external file modifications before overwrite. New files
are created automatically. Use this for creating new files or full-file
overwrites."""

edit_text = """Perform exact string replacements in files through a staged buffer with
automated viewport lifecycle management. Opens a viewport, applies the
replacement, saves to disk, and closes the viewport. Conflict detection
prevents overwriting externally modified files. For write/edit overlap,
use edit_text for targeted changes under 100 characters — use write_file
for full-file replacement."""

find_text = """Fast content search tool that works with any project size. Searches file
contents using substring (default) or regex matching. Returns structured
results with line numbers, file paths, and matching text for navigation
via viewport:jump. Supports scoping to a single file or project-wide
search."""

diff = """Show unified diff of staged edits in a viewport buffer before they are
committed to disk. Returns the diff as standard unified format with
context lines, additions, and deletions. If no changes are pending,
returns an empty result. Use this before file:save to verify edits are
correct."""
```

## Tool Parameters

| Tool | Parameters | Required |
|------|-----------|----------|
| `read_file` | `file_path: str`, `line_start: int = 1`, `line_end: int = 100` | file_path |
| `write_file` | `file_path: str`, `content: str` | both |
| `edit_text` | `file_path: str`, `old_text: str`, `new_text: str` | all |
| `find_text` | `pattern: str`, `file_path: str = ""`, `regex: bool = False` | pattern |
| `diff` | `file_path: str` | file_path |

## File Structure

**`src/viewport_editor/server.py`** — Add 5 `@mcp.tool()` registrations, each delegating to a handler function. Plus 5 handler functions. Plus update 7 existing tool docstrings.

**`test/test_composite_tools.py`** — Unit tests per SC-1 through SC-14 (new file).

## Pipeline Execution Order

Below is the item-level execution. Each item runs its own 14-step pipeline cycle. The pipeline is serial — items depend on previous items remaining unchanged.

### Initialization (before item 1)

```bash
mkdir -p ./tmp/63/state
.srclight/scripts/solve state init ./tmp/63/state/
rm -f ./tmp/63/artifacts/pipeline-*
```

### Per-Item Pipeline Cycle

For each item (1-6):

```
Step  1: sc-coherence-gate
Step  2: pre-red-baseline
Step  3: red-phase              → write unit test
Step  4: red-doublecheck        → verify test fails
Step  5: green-phase            → implement handler
Step  6: checkpoint-commit      → git commit
Step  7: structural-checks      → lint + typecheck
Step  8: green-doublecheck      → verify test passes
Step  9: green-vbc              → verify SC evidence
Step 10: adversarial-audit      → dual-auditor review
Step 11: cross-validate         → consensus check
Step 12: regression-check       → run full test suite
Step 13: review-prep            → prepare summary
Step 14: exec-summary           → log result
```

### Step 1: sc-coherence-gate

For each item, check:
- Spec coherence: Does the item's spec description match the current codebase state?
- Cross-reference: Do any other open issues modify the same `server.py` lines?
- Supersession: Has any later spec superseded this item?
- Execution-time coherence: If a prior item changed server.py, does item N's handler collide with those changes?

### Step 3-4: RED Phase (per item)

Unit test for the specific tool handler. Test file: `test/test_composite_tools.py`.

Example RED test for read_file:
```python
def test_read_file_returns_content():
    manager = ViewportManager(project_root="/tmp")
    # ...set up fixture file...
    # Test via server.create_server() to exercise the MCP tool registration
```

### Step 5: GREEN Phase (per item)

Implementation pattern for each composite tool:

```python
@mcp.tool()
def read_file(ctx: Context, file_path: str, line_start: int = 1, line_end: int = 100) -> str:
    """<locked description from V2>"""
    session_id = ctx.session_id
    session = get_session(session_id)
    if session is None:
        create_session(session_id)
    try:
        entry = _manager.open(session_id, file_path, line_start, line_end)
        visible = _manager.get_visible_lines(session_id, entry)
        # Format response with content block, metadata, conflict warnings
        ...
    except FileNotFoundError_ as e:
        return f"error: file not found: {e.file_path}"
```

### Step 6: checkpoint-commit

Tag: `63/checkpoint/item-{N}-{label}`

Example: `63/checkpoint/item-1-read-file`

### Step 10: Adversarial Audit

Dual-auditor (deepseek + qwen3.5 families) verifying:
- The handler matches the spec description
- Error cases are properly handled
- The agent-facing description is positive-framing, no negative comparisons
- Viewport lifecycle is correct (close on write/edit, open on read)

### Step 12: Regression Check

Run full test suite: `uv run pytest test/`

### Step 13: Review Prep

Compare URL for the branch.

## Viewport Lifecycle Per Tool

| Tool | Open Viewport? | Keep Open? | Close After? |
|------|---------------|-----------|-------------|
| `read_file` | Yes | Yes (for follow-up edits) | No — model decides via viewport:close |
| `write_file` | Yes | No | Yes — after save |
| `edit_text` | Yes | No | Yes — after save |
| `find_text` | No (uses search:find) | N/A | N/A |
| `diff` | Yes (if not already open via find_viewport_for_file) | Yes | No |

## Error Handling Matrix

| Failure Mode | Detection | Response |
|-------------|-----------|----------|
| File not found (read_file, edit_text) | FileNotFoundError_ from viewport:open | `"error: file not found: {path}"` |
| old_text not found (edit_text) | EditTargetNotFoundError from apply_replace_all | `"error: old text not found in {file}"` |
| Multiple ambiguous matches (edit_text) | Handled via replace-all (safe by design) | Returns count, not error |
| File changed externally | check_conflict on save | Conflict warning in response |
| Path escapes project root | PathEscapeError from resolve | `"error: path escapes project root"` |
| Absolute path provided | AbsolutePathError from resolve | `"error: use relative path, not absolute"` |
| Pattern not found (find_text) | Empty result set | `"found 0 matches"` (not an error) |
| No pending changes (diff) | Empty diff string | `"no pending changes for {path}"` |

## Dependency Contract

| Item | Depends On | Breaking Change Risk |
|------|-----------|---------------------|
| 1 (read_file) | Nothing | None |
| 2 (write_file) | Nothing | None |
| 3 (edit_text) | Nothing | None |
| 4 (find_text) | Nothing | None |
| 5 (diff) | Nothing | None |
| 6 (descriptions) | Items 1-5 | Low — docstrings only |

All items are independent — they add new tools without modifying existing ones. `server.py` changes are additive: 5 new `@mcp.tool()` blocks. No existing tool logic is modified. Item 6 edits existing docstrings in-place.

## Success Criteria Check

| SC ID | Criterion | Item | Evidence Type |
|-------|-----------|------|---------------|
| SC-1 | `read_file` returns file content with mtime/size/conflict | Item 1 | `behavioral` |
| SC-2 | `read_file` with offset/limit returns specified line range | Item 1 | `behavioral` |
| SC-3 | `read_file` returns error for non-existent file | Item 1 | `behavioral` |
| SC-4 | `write_file` creates a new file with content | Item 2 | `behavioral` |
| SC-5 | `write_file` overwrites existing file with content | Item 2 | `behavioral` |
| SC-6 | `write_file` detects external file modification | Item 2 | `behavioral` |
| SC-7 | `edit_text` replaces old_text with new_text | Item 3 | `behavioral` |
| SC-8 | `edit_text` returns error when old_text not found | Item 3 | `behavioral` |
| SC-9 | `edit_text` returns error on ambiguous matches | Item 3 | `behavioral` |
| SC-10 | After write_file/edit_text, viewport is closed | Item 2,3 | `behavioral` |
| SC-11 | `find_text` returns structured results with line numbers | Item 4 | `behavioral` |
| SC-12 | `find_text` with regex=true returns regex matches | Item 4 | `behavioral` |
| SC-13 | `diff` returns unified diff of pending buffer changes | Item 5 | `behavioral` |
| SC-14 | `diff` returns empty result when no pending changes | Item 5 | `behavioral` |
| SC-15 | All composite tools use verb_noun naming | Items 1-5 | `string` |
| SC-18 | 7 existing tool descriptions rewritten | Item 6 | `string` |
| SC-19 | All descriptions use positive framing only | Item 6 | `string` |
| SC-22 | Clean-room evaluation sub-agent for verification | Post-cycle | `behavioral` |

## Progress Tracking

Status is maintained via solve state at `./tmp/63/state/`. Pipeline artifacts at `./tmp/63/artifacts/`. Lifecycle events appended to `.issues/63/spec-artifacts/lifecycle.yaml`.

### State Transitions

```
  init
   ↓
  sc-coherence-gate  ──PASS──▶  pre-red-baseline  ──PASS──▶  red-phase  ──PASS──▶  red-doublecheck
                                                                                        |
                                                                                        ▼
                                                                                 (verify test FAILS)
                                                                                        |
                                                                                   PASS  |
                                                                                        ▼
                                                                                  green-phase
                                                                                        |
                                                                                        ▼
                                                                                  checkpoint-commit
                                                                                        |
                                                                                        ▼
                                                                                  structural-checks
                                                                                        |
                                                                                        ▼
                                                                                  green-doublecheck
                                                                                        |
                                                                                        ▼
                                                                                 (verify test PASSES)
                                                                                        |
                                                                                   PASS  |
                                                                                        ▼
                                                                                  green-vbc
                                                                                        |
                                                                                   PASS  |
                                                                                        ▼
                                                                                  adversarial-audit
                                                                                        |
                                                                                   PASS  |
                                                                                        ▼
                                                                                  cross-validate
                                                                                        |
                                                                                   PASS  |
                                                                                        ▼
                                                                                  regression-check
                                                                                        |
                                                                                   PASS  |
                                                                                        ▼
                                                                                  review-prep
                                                                                        |
                                                                                        ▼
                                                                                  exec-summary ──▶ next item
```

## Authorization Gate

This plan requires `for_implementation` scope to execute. The pipeline halts at each item boundary for checkpoint review if `halt_at` is set to `verification_complete`. With `pr_strategy: stacked`, all items accumulate on the same feature branch with one commit per item.