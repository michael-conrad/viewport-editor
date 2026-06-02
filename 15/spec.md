---
id: 15
title: '[SPEC-FIX] Decompose viewport.py into buffer.py, editor.py, file_ops.py'
state: closed
state_reason: completed
author: michael-conrad
labels: []
created: '2026-05-31T18:37:36Z'
updated: '2026-05-31T20:08:13Z'
closed_at: '2026-05-31T20:08:13Z'
closed_by: michael-conrad
remote_url: https://github.com/michael-conrad/viewport-editor/issues/15
---

# [SPEC-FIX] Decompose viewport.py into buffer.py, editor.py, file_ops.py

## Problem

File `src/viewport_editor/viewport.py` (531 lines) consolidates all buffer management, edit operations, and file operations into the `ViewportManager` class. The plan declares separate modules (`buffer.py`, `editor.py`, `file_ops.py`) but these were never created. This creates a monolithic blast radius: any ViewportManager change affects all subsystems, and there is no interface boundary between phases.

## Solution

Extract three modules from viewport.py:

### 1. `buffer.py` — Buffer + BufferManager

Move `Buffer` dataclass and buffer lifecycle methods into a new `BufferManager` class:

```python
class BufferManager:
    def __init__(self) -> None: ...
    def get_or_create(self, session_id, file_path, resolved_path) -> Buffer: ...
    def get_lines(self, session_id, file_path) -> list[str]: ...
    def refresh_if_changed(self, session_id, file_path, resolved_path) -> None: ...
    def get_diff(self, session_id, file_path, project_root) -> str: ...
    def destroy_session(self, session_id) -> None: ...
    def get_raw_content(self, session_id, file_path) -> str: ...
    def set_content(self, session_id, file_path, content) -> None: ...
```

### 2. `file_ops.py` — Module-level file operation functions

```python
def _resolve_path(file_path, project_root) -> tuple[str, str]: ...
def _detect_line_ending(file_path) -> str: ...
def _read_file_lines(resolved_path) -> tuple[list[str], float | None, int | None]: ...
def flush_entry(buffer, entry_file_path, entry, project_root) -> None: ...
def maybe_autosave(manager, session_id, entry) -> None: ...
def discard_buffer_changes(manager, session_id, entry) -> ViewportEntry: ...
def check_conflict(file_path, project_root, stored_mtime, stored_size) -> dict | None: ...
def format_conflict_warning(warning) -> str: ...
```

### 3. `editor.py` — Pure functions for edit operations

```python
def apply_edit(content, old_text, new_text) -> tuple[str, dict]: ...
def apply_replace_all(content, old_text, new_text) -> tuple[str, dict]: ...
def apply_insert_lines(content, line_start, lines, line_ending) -> tuple[str, dict]: ...
def apply_delete_lines(content, line_start, line_end) -> tuple[str, dict]: ...
def apply_swap_lines(content, line_start, line_end, target_line_start, target_line_end) -> tuple[str, dict]: ...
def apply_move_lines(content, line_start, line_end, target_line) -> tuple[str, dict]: ...
```

### 4. `viewport.py` — Reduced coordinator

`ViewportManager` drops `_buffers` dict and delegates to `BufferManager`. Edit methods become thin wrappers that get content from BufferManager, call editor pure function, store result back, and call `maybe_autosave`. File methods delegate to `file_ops`. `destroy_session` also calls `buffer_mgr.destroy_session()`.

### Changes to server.py

Line 678: `_manager._flush_entry(session_id, entry)` → expose a public `flush_entry` method on ViewportManager that routes to `file_ops.flush_entry`.

## Success Criteria

| ID | Criterion | Evidence Type |
|----|-----------|---------------|
| SC-1 | buffer.py exists with Buffer dataclass and BufferManager class | behavioral |
| SC-2 | editor.py exists with 6 pure edit functions | behavioral |
| SC-3 | file_ops.py exists with file operation functions | behavioral |
| SC-4 | viewport.py drops _buffers dict, uses BufferManager instead | behavioral |
| SC-5 | ViewportManager edit methods are thin wrappers delegating to editor.py | behavioral |
| SC-6 | viewport.py delegates flush/discard/conflict/format to file_ops.py | behavioral |
| SC-7 | server.py does not access _manager._flush_entry (private) | behavioral |
| SC-8 | All 51 existing tests pass without modification | behavioral |
| SC-9 | No new imports added to server.py — only viewport.py imports change | behavioral |

## Implementation Order

1. Create `buffer.py` with Buffer + BufferManager
2. Create `file_ops.py` with file operation functions  
3. Create `editor.py` with pure edit functions
4. Rewrite `viewport.py` ViewportManager to delegate
5. Fix server.py private access
6. Run full test suite (51 tests)

---

🤖 Co-authored with AI: OpenCode (ollama-cloud/deepseek-v4-flash)