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

| ID | Criterion | Evidence Type | Verification Method | Test File | Phase Mapping |
|----|-----------|---------------|---------------------|-----------|---------------|
| SC-1 | `viewport:open` on a file under a directory with AGENTS.md appends `<system-reminder>` with AGENTS.md content to the response | `behavioral` | Test: open a file in a directory with AGENTS.md → response contains `<system-reminder>` with AGENTS.md content | `.opencode/tests/viewport-editor/65/test_viewport_open_injection.py` | Phase 2 |
| SC-2 | Same AGENTS.md is NOT injected twice in the same session | `behavioral` | Test: open two files under same AGENTS.md → only first response has injection | `.opencode/tests/viewport-editor/65/test_dedup_same_session.py` | Phase 2 |
| SC-3 | AGENTS.md at project root injects when no closer AGENTS.md exists | `behavioral` | Test: open a file in a dir without AGENTS.md but with one at project root → root AGENTS.md injected | `.opencode/tests/viewport-editor/65/test_root_agents_fallback.py` | Phase 2 |
| SC-4 | Nearest-ancestor rule: deepest AGENTS.md wins over shallower one | `behavioral` | Test: file under `a/b/AGENTS.md` where `a/AGENTS.md` also exists → `a/b/AGENTS.md` is injected | `.opencode/tests/viewport-editor/65/test_nearest_ancestor_wins.py` | Phase 2 |
| SC-5 | `injected_agents_files` field exists on Session dataclass | `structural` | Check `session.py` for `injected_agents_files: set[str]` | `.opencode/tests/viewport-editor/65/test_session_injected_agents_field.py` | Phase 1 |
| SC-6 | Files outside project root (absolute paths) skip AGENTS.md check | `behavioral` | Test: open `/etc/passwd` → no `<system-reminder>` in response | `.opencode/tests/viewport-editor/65/test_absolute_path_skip.py` | Phase 2 |
| SC-7 | Unreadable AGENTS.md silently skipped (no crash, no partial content) | `behavioral` | Test: AGENTS.md with 000 permissions → injection silently skipped | `.opencode/tests/viewport-editor/65/test_unreadable_agents_skip.py` | Phase 2 |
| SC-8 | File that IS the AGENTS.md itself does not trigger self-injection | `behavioral` | Test: open `AGENTS.md` → response does not contain `<system-reminder>` | `.opencode/tests/viewport-editor/65/test_self_injection_guard.py` | Phase 2 |
| SC-9 | Composite `read_file` triggers same AGENTS.md injection as `viewport:open` | `behavioral` | Test: read_file on a file under AGENTS.md → response contains AGENTS.md content in `<system-reminder>` | `.opencode/tests/viewport-editor/65/test_read_file_injection.py` | Phase 3 |
| SC-10 | Composite `read_file` + `viewport:open` in same session share dedup | `behavioral` | Test: read_file then viewport:open on files under same AGENTS.md → single injection total | `.opencode/tests/viewport-editor/65/test_cross_tool_dedup.py` | Phase 3 |
| SC-11 | Injection format matches `<system-reminder>\nInstructions from: ...\n` built-in pattern | `string` | grep response for `<system-reminder>\nInstructions from:` | `.opencode/tests/viewport-editor/65/test_injection_format.py` | Phase 2 |
| SC-12 | `os.path.realpath()` is used for symlink-safe path comparison | `structural` | Check `_find_sibling_agents_md` for `os.path.realpath` calls on both file_path and project_root | `.opencode/tests/viewport-editor/65/test_find_sibling_agents_realpath.py` | Phase 1 |

## Implementation Plan

The authoritative implementation plan is at `.issues/65/spec-artifacts/plan.md` — a 3-phase plan using the mandatory 14-gate enumerated checklist format with routing annotations per issue #1129.

Each phase produces test files at `.opencode/tests/viewport-editor/65/` and output artifacts at `./tmp/65/artifacts/`. Every gate in the 14-item checklist specifies a routing annotation (orchestrator routes to sub-agent type / orchestrator inline).

### Phase Summary

| Phase | Concern | SCs Covered | Key Deliverables |
|-------|---------|-------------|------------------|
| Phase 1 | Core detection + session tracking | SC-5, SC-12 | `_find_sibling_agents_md()`, `injected_agents_files`, `_inject_agents_notice()` |
| Phase 2 | Tool integration | SC-1, SC-2, SC-3, SC-4, SC-6, SC-7, SC-8, SC-11 | Injection wiring in `_action_open()` and `read_file` handler |
| Phase 3 | Behavioral tests | SC-9, SC-10 | Cross-tool dedup and composite read_file injection tests |

### Routing Annotations (from plan.md)

Each checklist item in `.issues/65/spec-artifacts/plan.md` specifies one of:
- **orchestrator routes to [sub-agent-type]** — orchestrator tasks a clean-room sub-agent (pre-analysis, exploration, RED, GREEN, VbC, resolve-models, regression, review-prep, finishing, git-workflow)
- **orchestrator inline** — orchestrator performs the action directly (git commits, artifact verification, cross-validate, exec summary)

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

| ID | Status | Test File | Phase | Notes |
|----|--------|-----------|-------|-------|
| SC-1 | PENDING | `.opencode/tests/viewport-editor/65/test_viewport_open_injection.py` | Phase 2 | viewport:open injection |
| SC-2 | PENDING | `.opencode/tests/viewport-editor/65/test_dedup_same_session.py` | Phase 2 | dedup in session |
| SC-3 | PENDING | `.opencode/tests/viewport-editor/65/test_root_agents_fallback.py` | Phase 2 | root fallback |
| SC-4 | PENDING | `.opencode/tests/viewport-editor/65/test_nearest_ancestor_wins.py` | Phase 2 | nearest ancestor wins |
| SC-5 | PENDING | `.opencode/tests/viewport-editor/65/test_session_injected_agents_field.py` | Phase 1 | structural check |
| SC-6 | PENDING | `.opencode/tests/viewport-editor/65/test_absolute_path_skip.py` | Phase 2 | absolute path skip |
| SC-7 | PENDING | `.opencode/tests/viewport-editor/65/test_unreadable_agents_skip.py` | Phase 2 | unreadable skip |
| SC-8 | PENDING | `.opencode/tests/viewport-editor/65/test_self_injection_guard.py` | Phase 2 | self-injection guard |
| SC-9 | PENDING | `.opencode/tests/viewport-editor/65/test_read_file_injection.py` | Phase 3 | composite read_file |
| SC-10 | PENDING | `.opencode/tests/viewport-editor/65/test_cross_tool_dedup.py` | Phase 3 | cross-tool dedup |
| SC-11 | PENDING | `.opencode/tests/viewport-editor/65/test_injection_format.py` | Phase 2 | format match |
| SC-12 | PENDING | `.opencode/tests/viewport-editor/65/test_find_sibling_agents_realpath.py` | Phase 1 | realpath symlink safety |