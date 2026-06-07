# Codebase Investigation — Session ID References

**Date:** 2026-06-07
**Method:** Full source search via srclight + grep across `src/`

## Overview

Six files in `src/` contain `session_id` references. Three supporting files (`editor.py`, `file_ops.py`, `diff_engine.py`, `clipboard.py`) have zero. 16 test files contain ~303 references.

## server.py — Tool Entry Points

All 6 tool stubs receive `session_id: str = ""` as user-supplied param:

| Tool | Line | Signature |
|------|------|-----------|
| `viewport` | 54 | `def viewport(ctx: Context, action: str = "", session_id: str = "", ...)` |
| `edit` | 99 | `def edit(ctx: Context, action: str = "", session_id: str = "", ...)` |
| `file` | 138 | `def file(ctx: Context, action: str = "", session_id: str = "", ...)` |
| `diff` | 165 | `def diff(ctx: Context, action: str = "", session_id: str = "", ...)` |
| `clipboard` | 192 | `def clipboard(ctx: Context, action: str = "", session_id: str = "", ...)` |
| `search` | 223 | `def search(ctx: Context, action: str = "", session_id: str = "", ...)` |
| `regex` | 256 | `def regex(ctx: Context, action: str = "", ...)` — NO session_id |

**Key finding:** `ctx: Context` annotation already present (from #46). `ctx.session_id` is never extracted or used anywhere in `src/`.

### Handler Functions (Pass 1 scope: remove session_id param)

| Handler | Line | Takes session_id |
|---------|------|------------------|
| `_handle_viewport_action` | 343 | YES |
| `_handle_edit_action` | 717 | YES |
| `_handle_file_action` | 800 | YES |
| `_handle_diff_action` | 874 | YES |
| `_handle_clipboard_action` | 941 | YES |
| `_handle_search_action` | 1252 | YES |
| `_handle_regex_action` | 278 | NO |

### Action Functions (Pass 1 scope: remove session_id param)

| Action | Line | Takes session_id |
|--------|------|------------------|
| `_action_open` | 484 | YES |
| `_action_close` | 529 | YES |
| `_action_list` | 543 | YES |
| `_action_scroll` | 567 | YES |
| `_action_page_up` | 594 | YES |
| `_action_page_down` | 618 | YES |
| `_action_jump` | 642 | YES |
| `_action_autosave` | 669 | YES |
| `_action_set_display_mode` | 690 | YES |
| `_action_find` | 1306 | YES |
| `_action_regex_test` | 289 | NO |
| `_action_regex_escape` | 330 | NO |

## viewport.py — ViewportManager (left unchanged after feasibility analysis)

29 methods all take `session_id: str` as first positional param:

| Method | Line |
|--------|------|
| `touch` | 79 |
| `open` | 106 |
| `close` | 140 |
| `flush_entry` | 150 |
| `_maybe_autosave` | 155 |
| `_autosave_gate` | 161 |
| `list` | 174 |
| `get_visible_lines` | 179 |
| `scroll` | 186 |
| `page_up` | 198 |
| `page_down` | 203 |
| `jump` | 208 |
| `set_autosave` | 235 |
| `set_display_mode` | 244 |
| `destroy_session` | 253 |
| `get_entry` | 258 |
| `get_line_ending` | 265 |
| `apply_edit` | 275 |
| `apply_replace_all` | 285 |
| `apply_insert_lines` | 295 |
| `apply_delete_lines` | 308 |
| `apply_swap_lines` | 320 |
| `apply_move_lines` | 338 |
| `discard_buffer_changes` | 357 |
| `get_buffer_diff` | 365 |
| `open_new` | 376 |
| `save_as` | 401 |
| `delete_entry` | 431 |
| `apply_diff` | 459 |
| `find_viewport_for_file` | 482 |

**NOT taking session_id:** `sweep_stale_sessions` (83), `check_conflict` (369), `format_conflict_warning` (456)

## buffer.py — BufferManager (left unchanged after feasibility analysis)

9 methods all take `session_id: str`:

| Method | Line |
|--------|------|
| `get_or_create` | 31 |
| `get_lines` | 46 |
| `get_raw_content` | 49 |
| `set_content` | 52 |
| `refresh_if_changed` | 55 |
| `get_diff` | 67 |
| `get_buffer_ref` | 76 |
| `destroy_buffer` | 79 |
| `destroy_session` | 84 |

## session.py — Session Management

4 module-level functions and `Session.__init__`:

| Function | Line | Signature |
|----------|------|-----------|
| `Session.__init__` | 18 | `(self, session_id: str) -> None` |
| `create_session` | 28 | `(session_id: str) -> Session` |
| `get_session` | 34 | `(session_id: str) -> Optional[Session]` |
| `remove_session` | 38 | `(session_id: str) -> None` |
| `get_session_ids` | 42 | `() -> list[str]` |

**Decision:** Keep as-is. Session keys remain strings. Only the *source* of the string changes.

## exceptions.py

`SessionNotFoundError(session_id)` at line 42 — informational. Keep as-is.

## Architectural Insight

The current design has three layers each duplicating the session key concept:

```
server.py (gets session_id from agent) 
  → viewport.py ViewportManager._entries: Dict[str, Dict[str, ViewportEntry]]  (keyed by session_id)
  → buffer.py BufferManager._buffers: Dict[str, Dict[str, Buffer]]  (keyed by session_id)
  → session.py _sessions: Dict[str, Session]  (keyed by session_id)
```

After Pass 1 (server.py), the stack becomes:

```
server.py (extracts session_id from ctx.session_id)
  → viewport.py (receives session_id from caller, same string-keyed dicts)
  → buffer.py (receives session_id from caller, same string-keyed dicts)
  → session.py (unchanged)
```

The only change is the *source* of the session string. Dict keying patterns are unchanged. This minimizes risk.

Managers are left unchanged after feasibility analysis — every approach to remove `session_id` from manager signatures either breaks session isolation (contradicts SC-4), introduces thread-safety bugs, or changes nothing meaningful.

## Test File Count

Verified 16 test files contain `"session_id"` in `arguments={}`. A batch `texted` script with `search-forward "session_id":` → `delete-region` (with comma handling) is the correct approach for cleanup.