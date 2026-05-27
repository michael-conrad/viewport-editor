# SPDX-FileCopyrightText: 2026 Michael Conrad
# SPDX-License-Identifier: MIT
# Provenance: AI-generated
"""FastMCP server for viewport-editor.

Co-authored with AI: OpenCode (deepseek-v4-flash)
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, Optional

from mcp.server.fastmcp import FastMCP

from .exceptions import ViewportError
from .session import create_session, get_session, get_session_ids, remove_session
from .viewport import ViewportManager


def _get_project_root() -> str:
    return os.environ.get("VIEWPORT_PROJECT_ROOT", os.getcwd())


_manager: Optional[ViewportManager] = None


@asynccontextmanager
async def _server_lifespan(server: FastMCP) -> AsyncIterator[None]:
    """Startup: nothing extra beyond what create_server does.
    Shutdown: discard dirty buffers for all sessions (zero saves).
    """
    try:
        yield
    finally:
        mgr = _manager
        if mgr is not None:
            for session_id in list(get_session_ids()):
                mgr.destroy_session(session_id)
                remove_session(session_id)


def create_server(project_root: Optional[str] = None) -> FastMCP:
    global _manager
    root = project_root or _get_project_root()
    _manager = ViewportManager(project_root=root)

    mcp = FastMCP("viewport-editor", lifespan=_server_lifespan)

    @mcp.tool()
    def viewport(
        action: str,
        session_id: str,
        file_path: Optional[str] = None,
        start_line: Optional[int] = None,
        end_line: Optional[int] = None,
        autosave: Optional[bool] = None,
        viewport_id: Optional[str] = None,
        lines: Optional[int] = None,
        target: Optional[str] = None,
        enabled: Optional[bool] = None,
        display_mode: Optional[str] = None,
        ctx: Any = None,
    ) -> str:
        """Viewport text editor tool. Opens, navigates, and manages file viewports.

        Actions: open, close, list, scroll, page-up, page-down, jump, autosave, set-display-mode

        All responses use prose + YAML format. File paths must be relative to project root."""
        if _manager is None:
            return "error: server not initialized"

        session = get_session(session_id)
        if session is None:
            create_session(session_id)

        try:
            result = _handle_viewport_action(
                action=action,
                session_id=session_id,
                file_path=file_path,
                start_line=start_line,
                end_line=end_line,
                autosave=autosave,
                viewport_id=viewport_id,
                lines=lines,
                target=target,
                enabled=enabled,
                display_mode=display_mode,
            )
            return result
        except PermissionError as exc:
            return f"error: {exc}"

    @mcp.tool()
    def edit(
        ctx: Any = None,
        action: str = "",
        session_id: str = "",
        viewport_id: str = "",
        file_path: str = "",
        old_text: str = "",
        new_text: str = "",
        line_start: int = 0,
        line_end: int = 0,
        lines: Optional[list[str]] = None,
        target_line_start: int = 0,
        target_line_end: int = 0,
        target_line: int = 0,
    ) -> str:
        """Edit text content in an open viewport's buffer. All edits stage into buffer; flush to disk only on explicit save (file:save) or if autosave is enabled on the viewport.

        Actions: replace, replace-all, insert-lines, delete-lines, swap-lines, move-lines"""
        if _manager is None:
            return "error: server not initialized"

        session = get_session(session_id)
        if session is None:
            create_session(session_id)

        return _handle_edit_action(
            action=action,
            session_id=session_id,
            viewport_id=viewport_id,
            file_path=file_path,
            old_text=old_text,
            new_text=new_text,
            line_start=line_start,
            line_end=line_end,
            lines=lines,
            target_line_start=target_line_start,
            target_line_end=target_line_end,
            target_line=target_line,
        )

    @mcp.tool()
    def file(
        ctx: Any = None,
        action: str = "",
        session_id: str = "",
        viewport_id: str = "",
        file_path: str = "",
        force: bool = False,
    ) -> str:
        """File system operations for viewport-editor buffers. Persist pending edits to disk or discard them.

        Actions: save, discard"""
        if _manager is None:
            return "error: server not initialized"

        session = get_session(session_id)
        if session is None:
            create_session(session_id)

        return _handle_file_action(
            action=action,
            session_id=session_id,
            viewport_id=viewport_id,
            file_path=file_path,
            force=force,
        )

    @mcp.tool()
    def diff(
        ctx: Any = None,
        action: str = "",
        session_id: str = "",
        viewport_id: str = "",
        file_path: str = "",
    ) -> str:
        """Show unified diff of pending buffer changes vs disk content.

        Actions: show"""
        if _manager is None:
            return "error: server not initialized"

        session = get_session(session_id)
        if session is None:
            create_session(session_id)

        return _handle_diff_action(
            action=action,
            session_id=session_id,
            viewport_id=viewport_id,
            file_path=file_path,
        )

    @mcp.tool()
    def search(
        ctx: Any = None,
        action: str = "",
    ) -> str:
        """Search across files in the project. Not yet implemented.

        Actions: text, regex, filename"""
        return "search tool: not yet implemented"

    @mcp.tool()
    def regex(
        ctx: Any = None,
        action: str = "",
    ) -> str:
        """Regex operations for viewport-editor. Not yet implemented.

        Actions: match, replace, match-multi"""
        return "regex tool: not yet implemented"

    return mcp


def _handle_viewport_action(
    action: str,
    session_id: str,
    file_path: Optional[str] = None,
    start_line: Optional[int] = None,
    end_line: Optional[int] = None,
    autosave: Optional[bool] = None,
    viewport_id: Optional[str] = None,
    lines: Optional[int] = None,
    target: Optional[str] = None,
    enabled: Optional[bool] = None,
    display_mode: Optional[str] = None,
) -> str:
    if _manager is None:
        return "error: server not initialized"

    # Sweep stale sessions before handling the action
    stale_notice = _manager.sweep_stale_sessions()

    # Mark current session as active
    _manager.touch(session_id)

    actions = {
        "open": _action_open,
        "close": _action_close,
        "list": _action_list,
        "scroll": _action_scroll,
        "page-up": _action_page_up,
        "page-down": _action_page_down,
        "jump": _action_jump,
        "autosave": _action_autosave,
        "set-display-mode": _action_set_display_mode,
    }

    handler = actions.get(action)
    if handler is None:
        return f"error: unknown viewport action: {action}"

    result = handler(
        session_id=session_id,
        file_path=file_path,
        start_line=start_line,
        end_line=end_line,
        autosave=autosave,
        viewport_id=viewport_id,
        lines=lines,
        target=target,
        enabled=enabled,
        display_mode=display_mode,
    )

    if stale_notice:
        result = stale_notice + "\n" + result

    return result


def _check_file_conflict(file_path: str, entry: Any) -> Optional[str]:
    if _manager is None:
        return None
    warning = _manager.check_conflict(file_path, entry.mtime, entry.size)
    if warning:
        return _manager.format_conflict_warning(warning)
    return None


def _render_content_line(display_text: str, display_mode: str) -> str:
    """Render a single content line according to display mode.

    hide mode (default): show characters as-is.
    show mode: render non-printing Unicode chars as \\uNNNN, backslash as \\\\.
    Uses Unicode category (unicodedata) to determine printability — covers
    control (Cc), format (Cf), surrogate (Cs), private-use (Co), and
    unassigned (Cn) codepoints across the full Unicode range.
    """
    import unicodedata

    if display_mode == "hide":
        return display_text

    result: list[str] = []
    for ch in display_text:
        cp = ord(ch)
        if ch == "\\":
            result.append("\\\\")
        elif ch in ("\n", "\r"):
            # line terminators always pass through raw
            result.append(ch)
        else:
            if unicodedata.category(ch)[0] == "C":
                result.append(f"\\u{cp:04x}")
            else:
                result.append(ch)
    return "".join(result)


def _decode_unicode_escapes(text: str) -> str:
    """Decode \\uNNNN escape sequences in input text to actual Unicode characters.

    Handles:
    - \\\\uNNNN → \\uNNNN (escaped backslash produces literal backslash + text)
    - \\uNNNN  → actual Unicode character
    - All other text passes through unchanged.

    Processed left-to-right: escaped backslashes are consumed first so that
    \\\\u0041 decodes to literal \\u0041, not A.
    """
    result: list[str] = []
    i = 0
    while i < len(text):
        if text[i] == "\\" and i + 1 < len(text) and text[i + 1] == "\\":
            result.append("\\")
            i += 2
        elif text[i] == "\\" and i + 5 < len(text) and text[i + 1].lower() == "u":
            hex_str = text[i + 2 : i + 6]
            if all(c in "0123456789abcdefABCDEF" for c in hex_str):
                result.append(chr(int(hex_str, 16)))
                i += 6
            else:
                result.append(text[i])
                i += 1
        else:
            result.append(text[i])
            i += 1
    return "".join(result)


def _format_content_block(
    visible_lines: list[str], start_line: int, display_mode: str = "hide"
) -> str:
    """Format visible text content as a line-numbered content block (cat -n style)."""
    parts = ["  content:"]
    for i, line in enumerate(visible_lines):
        line_num = start_line + i
        # strip trailing newline for display; show blank lines as empty
        display = line.rstrip("\n").rstrip("\r")
        display = _render_content_line(display, display_mode)
        parts.append(f"    {line_num}: {display}")
    return "\n".join(parts)


def _action_open(
    session_id: str,
    file_path: Optional[str] = None,
    start_line: Optional[int] = None,
    end_line: Optional[int] = None,
    autosave: Optional[bool] = None,
    **kwargs: Any,
) -> str:
    if _manager is None:
        return "error: server not initialized"
    if file_path is None:
        return "error: file_path is required"
    result = _manager.open(
        session_id=session_id,
        file_path=file_path,
        start_line=start_line or 1,
        end_line=end_line or 100,
        autosave=autosave or False,
    )
    entry_data = result.to_dict()
    visible = _manager.get_visible_lines(session_id, result)
    content_block = _format_content_block(
        visible, result.start_line, result.display_mode
    )
    lines = [
        f"opened viewport for {entry_data['file']}:",
        f"  viewport_id: {entry_data['viewport_id']}",
        f"  file: {entry_data['file']}",
        f"  start_line: {entry_data['start_line']}",
        f"  end_line: {entry_data['end_line']}",
        f"  line_ending: {entry_data['line_ending']!r}",
        f"  display_mode: {entry_data['display_mode']}",
        f"  autosave: {entry_data['autosave']}",
        content_block,
    ]
    if entry_data["mtime"] is not None:
        lines.append(f"  mtime: {entry_data['mtime']}")
    if entry_data["size"] is not None:
        lines.append(f"  size: {entry_data['size']}")
    conflict_msg = _check_file_conflict(result.file, result)
    if conflict_msg:
        lines.append(f"  warning:\n{conflict_msg}")
    return "\n".join(lines)


def _action_close(
    session_id: str,
    viewport_id: Optional[str] = None,
    file_path: Optional[str] = None,
    **kwargs: Any,
) -> str:
    if _manager is None:
        return "error: server not initialized"
    if viewport_id is None:
        return "error: viewport_id is required"
    _manager.close(session_id, viewport_id)
    return f"closed viewport {viewport_id}"


def _action_list(
    session_id: str,
    **kwargs: Any,
) -> str:
    if _manager is None:
        return "error: server not initialized"
    entries = _manager.list(session_id)
    if not entries:
        return "no open viewports"
    parts = [f"viewports ({len(entries)}):"]
    for e in entries:
        parts.append(f"  - viewport_id: {e['viewport_id']}")
        parts.append(f"    file: {e['file']}")
        parts.append(f"    start_line: {e['start_line']}")
        parts.append(f"    end_line: {e['end_line']}")
        parts.append(f"    mtime: {e['mtime']}")
        parts.append(f"    size: {e['size']}")
        parts.append(f"    autosave: {e['autosave']}")
        parts.append(f"    dirty: {e['dirty']}")
        parts.append(f"    line_ending: {e['line_ending']!r}")
        parts.append(f"    display_mode: {e['display_mode']}")
    return "\n".join(parts)


def _action_scroll(
    session_id: str,
    viewport_id: Optional[str] = None,
    lines: Optional[int] = None,
    **kwargs: Any,
) -> str:
    if _manager is None:
        return "error: server not initialized"
    if viewport_id is None:
        return "error: viewport_id is required"
    if lines is None:
        return "error: lines is required"
    entry = _manager.scroll(session_id, viewport_id, lines)
    visible = _manager.get_visible_lines(session_id, entry)
    content_block = _format_content_block(visible, entry.start_line)
    conflict_msg = _check_file_conflict(entry.file, entry)
    parts = [
        f"scrolled viewport {viewport_id} by {lines} lines:",
        f"  start_line: {entry.start_line}",
        f"  end_line: {entry.end_line}",
        content_block,
    ]
    if conflict_msg:
        parts.append(f"  warning:\n{conflict_msg}")
    return "\n".join(parts)


def _action_page_up(
    session_id: str,
    viewport_id: Optional[str] = None,
    **kwargs: Any,
) -> str:
    if _manager is None:
        return "error: server not initialized"
    if viewport_id is None:
        return "error: viewport_id is required"
    entry = _manager.page_up(session_id, viewport_id)
    visible = _manager.get_visible_lines(session_id, entry)
    content_block = _format_content_block(visible, entry.start_line)
    conflict_msg = _check_file_conflict(entry.file, entry)
    parts = [
        f"paged up viewport {viewport_id}:",
        f"  start_line: {entry.start_line}",
        f"  end_line: {entry.end_line}",
        content_block,
    ]
    if conflict_msg:
        parts.append(f"  warning:\n{conflict_msg}")
    return "\n".join(parts)


def _action_page_down(
    session_id: str,
    viewport_id: Optional[str] = None,
    **kwargs: Any,
) -> str:
    if _manager is None:
        return "error: server not initialized"
    if viewport_id is None:
        return "error: viewport_id is required"
    entry = _manager.page_down(session_id, viewport_id)
    visible = _manager.get_visible_lines(session_id, entry)
    content_block = _format_content_block(visible, entry.start_line)
    conflict_msg = _check_file_conflict(entry.file, entry)
    parts = [
        f"paged down viewport {viewport_id}:",
        f"  start_line: {entry.start_line}",
        f"  end_line: {entry.end_line}",
        content_block,
    ]
    if conflict_msg:
        parts.append(f"  warning:\n{conflict_msg}")
    return "\n".join(parts)


def _action_jump(
    session_id: str,
    viewport_id: Optional[str] = None,
    target: Optional[str] = None,
    **kwargs: Any,
) -> str:
    if _manager is None:
        return "error: server not initialized"
    if viewport_id is None:
        return "error: viewport_id is required"
    if target is None:
        return "error: target is required"
    entry = _manager.jump(session_id, viewport_id, target)
    visible = _manager.get_visible_lines(session_id, entry)
    content_block = _format_content_block(visible, entry.start_line)
    conflict_msg = _check_file_conflict(entry.file, entry)
    parts = [
        f"jumped to '{target}' in viewport {viewport_id}:",
        f"  start_line: {entry.start_line}",
        f"  end_line: {entry.end_line}",
        content_block,
    ]
    if conflict_msg:
        parts.append(f"  warning:\n{conflict_msg}")
    return "\n".join(parts)


def _action_autosave(
    session_id: str,
    viewport_id: Optional[str] = None,
    enabled: Optional[bool] = None,
    **kwargs: Any,
) -> str:
    if _manager is None:
        return "error: server not initialized"
    if viewport_id is None:
        return "error: viewport_id is required"
    if enabled is None:
        return "error: enabled is required"
    entry = _manager.get_entry(session_id, viewport_id)
    conflict_msg = _check_file_conflict(entry.file, entry)
    _manager.set_autosave(session_id, viewport_id, enabled)
    parts = [f"autosave set to {enabled} for viewport {viewport_id}"]
    if conflict_msg:
        parts.append(f"  warning:\n{conflict_msg}")
    return "\n".join(parts)


def _action_set_display_mode(
    session_id: str,
    viewport_id: Optional[str] = None,
    display_mode: Optional[str] = None,
    **kwargs: Any,
) -> str:
    if _manager is None:
        return "error: server not initialized"
    if viewport_id is None:
        return "error: viewport_id is required"
    if display_mode is None:
        return "error: display_mode is required"
    entry = _manager.set_display_mode(session_id, viewport_id, display_mode)
    visible = _manager.get_visible_lines(session_id, entry)
    content_block = _format_content_block(visible, entry.start_line, entry.display_mode)
    conflict_msg = _check_file_conflict(entry.file, entry)
    parts = [
        f"display_mode set to {display_mode} for viewport {viewport_id}:",
        f"  viewport_id: {entry.viewport_id}",
        f"  display_mode: {entry.display_mode}",
        content_block,
    ]
    if conflict_msg:
        parts.append(f"  warning:\n{conflict_msg}")
    return "\n".join(parts)


def _handle_edit_action(
    action: str,
    session_id: str,
    viewport_id: str,
    file_path: str = "",
    old_text: str = "",
    new_text: str = "",
    line_start: int = 0,
    line_end: int = 0,
    lines: Optional[list[str]] = None,
    target_line_start: int = 0,
    target_line_end: int = 0,
    target_line: int = 0,
) -> str:
    if _manager is None:
        return "error: server not initialized"

    entry = _manager.get_entry(session_id, viewport_id)
    conflict_warning = _check_file_conflict(entry.file, entry)

    if action == "replace":
        result = _manager.apply_edit(session_id, viewport_id, old_text, new_text)
        parts = [
            f"replaced text in viewport {viewport_id}:",
            f"  found: {result['found']}",
            f"  count: {result['count']}",
        ]
    elif action == "replace-all":
        result = _manager.apply_replace_all(session_id, viewport_id, old_text, new_text)
        parts = [
            f"replaced all occurrences in viewport {viewport_id}:",
            f"  found: {result['found']}",
            f"  count: {result['count']}",
        ]
    elif action == "insert-lines":
        result = _manager.apply_insert_lines(session_id, viewport_id, line_start, lines or [])
        parts = [
            f"inserted lines in viewport {viewport_id}:",
            f"  line_start: {result['line_start']}",
            f"  line_end: {result['line_end']}",
            f"  count: {result['count']}",
        ]
    elif action == "delete-lines":
        result = _manager.apply_delete_lines(session_id, viewport_id, line_start, line_end)
        parts = [
            f"deleted lines in viewport {viewport_id}:",
            f"  line_start: {result['line_start']}",
            f"  line_count: {result['line_count']}",
        ]
    elif action == "swap-lines":
        _manager.apply_swap_lines(
            session_id, viewport_id, line_start, line_end,
            target_line_start, target_line_end,
        )
        parts = [f"swapped line ranges in viewport {viewport_id}:", "  swapped: True"]
    elif action == "move-lines":
        _manager.apply_move_lines(session_id, viewport_id, line_start, line_end, target_line)
        parts = [f"moved lines in viewport {viewport_id}:", "  moved: True"]
    else:
        raise ViewportError(f"unknown edit action: {action}")

    if conflict_warning:
        parts.append(f"  warning:\n{conflict_warning}")

    return "\n".join(parts)


def _handle_file_action(
    action: str,
    session_id: str,
    viewport_id: str,
    file_path: str = "",
    force: bool = False,
) -> str:
    if _manager is None:
        return "error: server not initialized"

    if action == "save":
        entry = _manager.get_entry(session_id, viewport_id)
        if file_path and entry.file != file_path:
            raise ViewportError(
                f"file '{file_path}' does not exist for viewport {viewport_id}"
            )
        conflict_warning = _manager.check_conflict(entry.file, entry.mtime, entry.size)
        if conflict_warning and not force:
            warning_str = _manager.format_conflict_warning(conflict_warning)
            raise ViewportError(f"stale mtime/size conflict\n{warning_str}")
        _manager._flush_entry(session_id, entry)
        return (
            f"saved viewport {viewport_id}:"
            f"\n  mtime: {entry.mtime}"
            f"\n  size: {entry.size}"
        )
    elif action == "discard":
        _manager.discard_buffer_changes(session_id, viewport_id)
        return f"discarded pending changes for viewport {viewport_id}"
    else:
        raise ViewportError(f"unknown file action: {action}")


def _handle_diff_action(
    action: str,
    session_id: str,
    viewport_id: str,
    file_path: str = "",
) -> str:
    if _manager is None:
        return "error: server not initialized"

    if action == "show":
        diff_str = _manager.get_buffer_diff(session_id, viewport_id)
        if not diff_str:
            return f"no pending changes for viewport {viewport_id}"
        return f"diff for {file_path}:\n{diff_str}"
    else:
        raise ViewportError(f"unknown diff action: {action}")
