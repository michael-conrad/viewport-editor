# Extend jump action with "top"/"bottom" symbolic targets

## Summary

Extend the existing `jump` viewport action to support `"top"` and `"bottom"` as symbolic target keywords. No new action verbs needed — this keeps the tool surface clean by reusing the existing `jump` dispatch.

## Background

The `jump` action (defined in `src/viewport_editor/viewport.py:208-233`) currently accepts:
- A numeric string (`"42"`) → jump to that line number
- Any other string → scan line-by-line for first line containing the target as substring

The `jump` + numeric-string path already covers "go to line N", but an AI agent has no efficient way to navigate to the beginning or end of a file without knowing the total line count. Adding `"top"`/`"bottom"` gives agents a direct, predictable way to anchor navigation.

## Success Criteria

| ID | Criterion | Evidence Type | Verification Method |
|----|-----------|---------------|---------------------|
| SC-1 | `jump` with target `"top"` sets viewport to start at line 1 | `behavioral` | Test: call `jump` with `"top"`, assert `line_start == 1` |
| SC-2 | `jump` with target `"bottom"` sets viewport to end of file (viewport end aligns with total lines) | `behavioral` | Test: call `jump` with `"bottom"` on file with known line count, assert `line_end == total_lines` |
| SC-3 | `"top"` and `"bottom"` only match the exact literal lowercase strings — text search fallback is NOT invoked for these keywords | `behavioral` | Test: file containing line `"top"` should NOT match via text search when target is `"top"`; full line count check proves symbolic routing worked |
| SC-4 | Existing numeric jump still works unchanged | `behavioral` | Test: `jump("42")` behaves identically to current behavior |
| SC-5 | Existing text-search jump still works unchanged for non-keyword targets | `behavioral` | Test: `jump("function foo")` behaves identically to current behavior |
| SC-6 | `jump` to `"bottom"` on an empty file (0 lines) positions viewport at line 1 with `line_end=0` | `behavioral` | Test: create empty file, open viewport, jump `"bottom"`, assert `line_start=1, line_end=0` |

## Implementation Notes

### viewport.py changes (only file to modify)

In `ViewportManager.jump()` (line 208), add keyword dispatch before the existing `isdigit()` check:

```python
def jump(self, session_id: str, viewport_id: str, target: str) -> ViewportEntry:
    entry = self.get_entry(session_id, viewport_id)
    file_lines = self._buffer_mgr.get_lines(session_id, entry.file)
    total = len(file_lines)
    height = entry.line_end - entry.line_start
    target_str = target.strip().lower()

    if target_str == "top":
        new_start = 1
    elif target_str == "bottom":
        new_start = max(1, total - height) if total > 0 else 1
    elif target_str.isdigit():
        # existing numeric logic
        ...
    else:
        # existing text search logic
        ...
```

The `lower()` normalization means `"TOP"`, `"Top"`, `"top"` all match — robust for LLM-generated target strings.

### server.py docstring update

Add a `jump` detail line to the MCP tool docstring so AI agents discover the feature:

```
- Jump target: a line number, text to search for, "top" (start of file), or "bottom" (end of file)
```

The docstring at `server.py:68-72` is what MCP surfaces as the tool description — this single line tells agents about all four jump modalities.

### Response message update

The `_action_jump` handler formats its response as `jumped to '<target>'` — for `"top"` and `"bottom"`, this reads naturally ("jumped to 'top'") so no change needed.

## Affected Files

| File | Change |
|------|--------|
| `src/viewport_editor/viewport.py:208-233` | Add `"top"`/`"bottom"` keyword dispatch |
| `src/viewport_editor/server.py:70` | Add jump target detail to tool docstring |
| `test/test_phase1_server_viewport.py` | Add 5-6 test cases |

## Design Considerations

- **Why not new actions?** Adding `goto-top`/`goto-bottom` as separate actions adds surface area (new dispatch table entries, new handler functions, new docs). The `jump` action already exists and accepts a string target — symbolic keywords are a natural extension of its design.
- **Why `"top"`/`"bottom"` and not `"start"`/`"end"`?** File-level navigation in text editors uses `top`/`bottom` (Ctrl+Home → top of file, Ctrl+End → bottom of file). `start`/`end` conventionally refer to line or selection boundaries.
- **Why `.lower()` normalization?** AI agents may produce `"Top"`, `"TOP"`, or `"top"` — case-insensitive matching prevents false text-search fallback for what should be a symbolic jump.

<!-- SPDX-FileCopyrightText: 2026 Michael Conrad -->
<!-- SPDX-License-Identifier: MIT -->
<!-- Provenance: AI-generated -->
<!-- Co-authored with AI: OpenCode (deepseek-v4-flash) -->