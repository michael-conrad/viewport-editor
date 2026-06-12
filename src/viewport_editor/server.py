# SPDX-FileCopyrightText: 2026 Michael Conrad
# SPDX-License-Identifier: MIT
# Provenance: AI-generated
"""FastMCP server for viewport-editor.

Co-authored with AI: OpenCode (deepseek-v4-flash)
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, AsyncIterator, Optional

from fastmcp import Context, FastMCP

from .clipboard import ClipboardEntry, apply_copy, apply_cut, apply_paste
from .exceptions import (
    DiffApplyError,
    EditTargetNotFoundError,
    FileNotFoundError_,
    ViewportError,
)
from .file_ops import _find_sibling_agents_md, _resolve_path
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
        ctx: Context,
        action: str = "",
        file_path: Optional[str] = None,
        line_start: Optional[int] = None,
        line_end: Optional[int] = None,
        autosave: Optional[bool] = None,
        viewport_id: Optional[str] = None,
        lines: Optional[int] = None,
        target: Optional[str] = None,
        autosave_enabled: Optional[bool] = None,
        display_mode: Optional[str] = None,
    ) -> str:
        """Open a file into a staged buffer viewport with undo and conflict detection.
        Supports open, close, list, scroll, page-up, page-down, jump, autosave,
        and display-mode actions. All edits stage into memory — nothing reaches
        disk until file:save confirms the change. Use this for all file navigation
        and multi-edit workflows where review before save is important.

        Jump target: a line number, text to search for, "top" (start of file),
        or "bottom" (end of file).

        Actions: open, close, list, scroll, page-up, page-down, jump, autosave,
        set-display-mode

        All responses use prose + YAML format. File paths must be relative to
        project root."""
        session_id = ctx.session_id
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
                line_start=line_start,
                line_end=line_end,
                autosave=autosave,
                viewport_id=viewport_id,
                lines=lines,
                target=target,
                autosave_enabled=autosave_enabled,
                display_mode=display_mode,
            )
            return result
        except PermissionError as exc:
            return f"error: {exc}"

    @mcp.tool()
    def edit(
        ctx: Context,
        action: str = "",
        viewport_id: str = "",
        old_text: str = "",
        new_text: str = "",
        line_start: int = 0,
        line_end: int = 0,
        lines: Optional[list[str]] = None,
        target_line_start: int = 0,
        target_line_end: int = 0,
        target_line: int = 0,
    ) -> str:
        """Edit text inside an open viewport's staged buffer. Supports replace,
        replace-all, insert-lines, delete-lines, swap-lines, and move-lines
        actions. All edits accumulate in memory — no bytes reach disk until
        file:save or autosave flushes them. Use this for targeted changes
        where diff review before save is needed.

        Actions: replace, replace-all, insert-lines, delete-lines, swap-lines,
        move-lines"""
        session_id = ctx.session_id
        if _manager is None:
            return "error: server not initialized"

        session = get_session(session_id)
        if session is None:
            create_session(session_id)

        return _handle_edit_action(
            action=action,
            session_id=session_id,
            viewport_id=viewport_id,
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
        ctx: Context,
        action: str = "",
        viewport_id: str = "",
        file_path: str = "",
        force: bool = False,
    ) -> str:
        """Flush staged viewport buffer edits to disk. The save gate converts
        pending memory edits into permanent file content. Use file:save after
        diff:show review to commit changes. Supports save, discard, new, and
        save-as actions for full file lifecycle management.

        Actions: save, discard, new, save-as"""
        session_id = ctx.session_id
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
        ctx: Context,
        action: str = "",
        viewport_id: str = "",
        file_path: str = "",
        patch: str = "",
    ) -> str:
        """Show unified diff of staged edits in a viewport buffer before they are
        committed to disk. Returns the diff as standard unified format with
        context lines, additions, and deletions. If no changes are pending,
        returns an empty result. Use this before file:save to verify edits are
        correct.

        Actions: show, apply"""
        session_id = ctx.session_id
        if _manager is None:
            return "error: server not initialized"

        session = get_session(session_id)
        if session is None:
            create_session(session_id)

        # Composite-style shortcut: no action + file_path = auto-discover viewport
        if not action and file_path:
            entry = _manager.find_viewport_for_file(session_id, file_path)
            if entry is None:
                return f"no pending changes for {file_path}"
            diff_str = _manager.get_buffer_diff(session_id, entry.viewport_id)
            if not diff_str:
                return f"no pending changes for {file_path}"
            return f"diff for {file_path}:\n{diff_str}"

        return _handle_diff_action(
            action=action,
            session_id=session_id,
            viewport_id=viewport_id,
            file_path=file_path,
            patch=patch,
        )

    @mcp.tool()
    def clipboard(
        ctx: Context,
        action: str = "",
        viewport_id: Optional[str] = None,
        line_start: Optional[int] = None,
        line_end: Optional[int] = None,
        target_line: Optional[int] = None,
        name: Optional[str] = None,
    ) -> str:
        """Cross-viewport clipboard with provenance tracking. Copy content from
        one viewport and paste into another with source-file and line-range
        metadata preserved. Supports stash slots for organizing multiple
        clipboard entries. Use this for moving text between files with
        traceable origin.

        Actions: copy, cut, paste, show, stash, pop, swap, stash-list"""
        session_id = ctx.session_id
        if _manager is None:
            return "error: server not initialized"

        session = get_session(session_id)
        if session is None:
            create_session(session_id)

        return _handle_clipboard_action(
            action=action,
            session_id=session_id,
            viewport_id=viewport_id or "",
            line_start=line_start or 0,
            line_end=line_end or 0,
            target_line=target_line or 0,
            name=name or "",
        )

    @mcp.tool()
    def search(
        ctx: Context,
        action: str = "",
        pattern: str = "",
        regex: Optional[bool] = None,
        scope: Optional[str] = None,
        file_path: Optional[str] = None,
        viewport_id: Optional[str] = None,
    ) -> str:
        """Search across files with structured results including pattern, line
        number, and file path in every match. Supports substring (default)
        and regex matching. Results are designed for direct navigation via
        viewport:jump. Use this for finding code patterns, debugging, and
        codebase exploration.

        Actions: find

        Scopes: file (single file), viewport (open viewport), all_open (all
        open viewports), or project-wide (default)"""
        session_id = ctx.session_id
        if _manager is None:
            return "error: server not initialized"

        session = get_session(session_id)
        if session is None:
            create_session(session_id)

        return _handle_search_action(
            action=action,
            session_id=session_id,
            pattern=pattern,
            regex=regex or False,
            scope=scope or "",
            file_path=file_path or "",
            viewport_id=viewport_id or "",
        )

    @mcp.tool()
    def regex(
        ctx: Context,
        action: str = "",
        pattern: Optional[str] = None,
        text: Optional[str] = None,
    ) -> str:
        """Test and escape regex patterns. regex:test matches a pattern against
        sample text and returns match positions with capture groups.
        regex:escape escapes metacharacters for literal matching. Use this
        before applying patterns in search:find to verify correctness.

        Actions: test (match pattern against text), escape (escape metacharacters)"""
        if _manager is None:
            return "error: server not initialized"

        return _handle_regex_action(
            action=action,
            pattern=pattern or "",
            text=text or "",
        )

    @mcp.tool()
    def read_file(
        ctx: Context,
        file_path: str,
        line_start: int = 1,
        line_end: int = 100,
    ) -> str:
        """Read file contents from the local filesystem into a staged buffer viewport.
        If the file path does not exist, an error is returned. Supports offset/limit
        for partial reads. The viewport remains open for follow-up edits. No content
        touches disk until explicitly confirmed via file:save. Use this for all file
        reading tasks including config files, source code, and logs."""
        session_id = ctx.session_id
        if _manager is None:
            return "error: server not initialized"

        session = get_session(session_id)
        if session is None:
            create_session(session_id)

        try:
            entry = _manager.open(
                session_id=session_id,
                file_path=file_path,
                line_start=line_start,
                line_end=line_end,
            )
        except (ViewportError, FileNotFoundError, PermissionError) as exc:
            return f"error: {exc}"

        visible = _manager.get_visible_lines(session_id, entry)
        entry_data = entry.to_dict()

        content_block = _format_content_block(
            visible, entry.line_start, entry.display_mode
        )
        lines = [
            f"opened viewport for {entry_data['file']}:",
            f"  viewport_id: {entry_data['viewport_id']}",
            f"  file: {entry_data['file']}",
            f"  line_start: {entry_data['line_start']}",
            f"  line_end: {entry_data['line_end']}",
            f"  line_ending: {entry_data['line_ending']!r}",
            f"  display_mode: {entry_data['display_mode']}",
            f"  autosave: {entry_data['autosave']}",
            content_block,
        ]
        if entry_data["mtime"] is not None:
            lines.append(f"  mtime: {entry_data['mtime']}")
        if entry_data["size"] is not None:
            lines.append(f"  size: {entry_data['size']}")
        response = "\n".join(lines)
        return _inject_agents_notice(file_path, session_id, response)

    @mcp.tool()
    def write_file(
        ctx: Context,
        file_path: str,
        content: str,
    ) -> str:
        """Write file contents to the local filesystem through a staged buffer with
        automated viewport lifecycle management. Opens a viewport, replaces the
        entire buffer content, saves to disk, and closes the viewport. Conflict
        detection catches external file modifications before overwrite. New files
        are created automatically. Use this for creating new files or full-file
        overwrites."""
        session_id = ctx.session_id
        if _manager is None:
            return "error: server not initialized"

        session = get_session(session_id)
        if session is None:
            create_session(session_id)

        # Open existing file or create new one
        try:
            entry = _manager.open(
                session_id=session_id,
                file_path=file_path,
            )
        except FileNotFoundError_:
            try:
                entry = _manager.open_new(session_id, file_path)
            except (ViewportError, FileExistsError) as exc:
                return f"error: {exc}"
        except (ViewportError, PermissionError) as exc:
            return f"error: {exc}"

        # Replace entire buffer content
        _manager._buffer_mgr.set_content(session_id, entry.file, content)
        entry.dirty = True

        # Check for external conflict before save
        conflict_warning = _manager.check_conflict(entry.file, entry.mtime, entry.size)
        if conflict_warning and not entry.autosave:
            warning_str = _manager.format_conflict_warning(conflict_warning)
            return f"error: conflict detected\n{warning_str}"

        # Flush to disk and close viewport
        _manager.flush_entry(session_id, entry)
        _manager.close(session_id, entry.viewport_id)

        return (
            f"written {len(content)} bytes to {file_path}:"
            f"\n  mtime: {entry.mtime}"
            f"\n  size: {entry.size}"
        )

    @mcp.tool()
    def edit_text(
        ctx: Context,
        file_path: str,
        old_text: str,
        new_text: str,
    ) -> str:
        """Perform exact string replacements in files through a staged buffer with
        automated viewport lifecycle management. Opens a viewport, applies the
        replacement, saves to disk, and closes the viewport. Conflict detection
        prevents overwriting externally modified files. For write/edit overlap,
        use edit_text for targeted changes under 100 characters — use write_file
        for full-file replacement."""
        session_id = ctx.session_id
        if _manager is None:
            return "error: server not initialized"

        session = get_session(session_id)
        if session is None:
            create_session(session_id)

        try:
            entry = _manager.open(
                session_id=session_id,
                file_path=file_path,
            )
        except (ViewportError, FileNotFoundError, PermissionError) as exc:
            return f"error: {exc}"

        try:
            result = _manager.apply_replace_all(
                session_id, entry.viewport_id, old_text, new_text
            )
        except (ViewportError, EditTargetNotFoundError) as exc:
            return f"error: {exc}"

        # Check for external conflict before save
        conflict_warning = _manager.check_conflict(entry.file, entry.mtime, entry.size)
        if conflict_warning and not entry.autosave:
            _manager.discard_buffer_changes(session_id, entry.viewport_id)
            warning_str = _manager.format_conflict_warning(conflict_warning)
            return f"error: conflict detected\n{warning_str}"

        # Flush to disk and close viewport
        _manager.flush_entry(session_id, entry)
        _manager.close(session_id, entry.viewport_id)

        return f"edit applied to {file_path}:\n  count: {result['count']}"

    @mcp.tool()
    def find_text(
        ctx: Context,
        pattern: str,
        file_path: str = "",
        regex: bool = False,
    ) -> str:
        """Fast content search tool that works with any project size. Searches file
        contents using substring (default) or regex matching. Returns structured
        results with line numbers, file paths, and matching text for navigation
        via viewport:jump. Supports scoping to a single file or project-wide
        search."""
        if _manager is None:
            return "error: server not initialized"

        session_id = ctx.session_id
        session = get_session(session_id)
        if session is None:
            create_session(session_id)

        return _handle_search_action(
            action="find",
            session_id=session_id,
            pattern=pattern,
            regex=regex,
            scope="file" if file_path else "",
            file_path=file_path,
        )

    return mcp


def _handle_regex_action(action: str, pattern: str, text: str) -> str:
    actions = {
        "test": _action_regex_test,
        "escape": _action_regex_escape,
    }
    handler = actions.get(action)
    if handler is None:
        raise ViewportError(f"unknown regex action: {action}")
    return handler(pattern=pattern, text=text)


def _action_regex_test(pattern: str, text: str) -> str:
    import re as _re

    if not pattern:
        raise ViewportError("pattern is required for test action")

    try:
        compiled = _re.compile(pattern)
    except _re.error as exc:
        raise ViewportError(f"invalid regex pattern: {exc}")

    matches: list[dict] = []
    for m in compiled.finditer(text):
        groups = {}
        if m.groups():
            groups = {f"group_{i}": g for i, g in enumerate(m.groups(), 1)}
        matches.append(
            {
                "start": m.start(),
                "end": m.end(),
                "matched": m.group(0),
                **groups,
            }
        )

    parts = [f"regex test results for pattern '{pattern}':"]
    parts.append(f"  matches: {len(matches)}")
    if matches:
        for i, m in enumerate(matches):
            parts.append(f"  match {i}:")
            parts.append(f"    start: {m['start']}")
            parts.append(f"    end: {m['end']}")
            parts.append(f"    matched: {m['matched']}")
            for gk, gv in m.items():
                if gk.startswith("group_") and gv is not None:
                    parts.append(f"    {gk}: {gv}")
    else:
        parts.append("  (no matches found)")
    return "\n".join(parts)


def _action_regex_escape(pattern: str, text: str) -> str:
    import re as _re

    if not text:
        raise ViewportError("text is required for escape action")

    escaped = _re.escape(text)
    parts = ["regex escape results:"]
    parts.append(f"  original: {text}")
    parts.append(f"  escaped: {escaped}")
    return "\n".join(parts)


def _handle_viewport_action(
    action: str,
    session_id: str,
    file_path: Optional[str] = None,
    line_start: Optional[int] = None,
    line_end: Optional[int] = None,
    autosave: Optional[bool] = None,
    viewport_id: Optional[str] = None,
    lines: Optional[int] = None,
    target: Optional[str] = None,
    autosave_enabled: Optional[bool] = None,
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
        line_start=line_start,
        line_end=line_end,
        autosave=autosave,
        viewport_id=viewport_id,
        lines=lines,
        target=target,
        autosave_enabled=autosave_enabled,
        display_mode=display_mode,
    )

    if stale_notice:
        result = stale_notice + "\n" + result

    return result


def _inject_agents_notice(file_path: str, session_id: str, response_text: str) -> str:
    if _manager is None:
        return response_text
    project_root = _manager.project_root
    # Resolve file_path against project_root before detection, so that
    # relative paths work correctly in test environments with temp dirs
    resolved_abs = os.path.realpath(os.path.join(project_root, file_path))
    content = _find_sibling_agents_md(resolved_abs, project_root)
    if content is None:
        return response_text
    session = get_session(session_id)
    if session is None:
        return response_text
    resolved = os.path.realpath(os.path.join(project_root, file_path))
    agents_path = os.path.dirname(resolved) + "/AGENTS.md"
    if agents_path in session.injected_agents_files:
        return response_text
    session.injected_agents_files.add(agents_path)
    return (
        response_text
        + f"\n\n<system-reminder>\nInstructions from: {agents_path}\n{content}\n</system-reminder>"
    )


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
    visible_lines: list[str], line_start: int, display_mode: str = "hide"
) -> str:
    """Format visible text content as a line-numbered content block (cat -n style)."""
    parts = ["  content:"]
    for i, line in enumerate(visible_lines):
        line_num = line_start + i
        # strip trailing newline for display; show blank lines as empty
        display = line.rstrip("\n").rstrip("\r")
        display = _render_content_line(display, display_mode)
        parts.append(f"    {line_num}: {display}")
    return "\n".join(parts)


def _action_open(
    session_id: str,
    file_path: Optional[str] = None,
    line_start: Optional[int] = None,
    line_end: Optional[int] = None,
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
        line_start=line_start or 1,
        line_end=line_end or 100,
        autosave=autosave or False,
    )
    entry_data = result.to_dict()
    visible = _manager.get_visible_lines(session_id, result)
    content_block = _format_content_block(
        visible, result.line_start, result.display_mode
    )
    lines = [
        f"opened viewport for {entry_data['file']}:",
        f"  viewport_id: {entry_data['viewport_id']}",
        f"  file: {entry_data['file']}",
        f"  line_start: {entry_data['line_start']}",
        f"  line_end: {entry_data['line_end']}",
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
    response = "\n".join(lines)
    return _inject_agents_notice(file_path, session_id, response)


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
        parts.append(f"    line_start: {e['line_start']}")
        parts.append(f"    line_end: {e['line_end']}")
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
    content_block = _format_content_block(visible, entry.line_start)
    conflict_msg = _check_file_conflict(entry.file, entry)
    parts = [
        f"scrolled viewport {viewport_id} by {lines} lines:",
        f"  line_start: {entry.line_start}",
        f"  line_end: {entry.line_end}",
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
    content_block = _format_content_block(visible, entry.line_start)
    conflict_msg = _check_file_conflict(entry.file, entry)
    parts = [
        f"paged up viewport {viewport_id}:",
        f"  line_start: {entry.line_start}",
        f"  line_end: {entry.line_end}",
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
    content_block = _format_content_block(visible, entry.line_start)
    conflict_msg = _check_file_conflict(entry.file, entry)
    parts = [
        f"paged down viewport {viewport_id}:",
        f"  line_start: {entry.line_start}",
        f"  line_end: {entry.line_end}",
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
    content_block = _format_content_block(visible, entry.line_start)
    conflict_msg = _check_file_conflict(entry.file, entry)
    parts = [
        f"jumped to '{target}' in viewport {viewport_id}:",
        f"  line_start: {entry.line_start}",
        f"  line_end: {entry.line_end}",
        content_block,
    ]
    if conflict_msg:
        parts.append(f"  warning:\n{conflict_msg}")
    return "\n".join(parts)


def _action_autosave(
    session_id: str,
    viewport_id: Optional[str] = None,
    autosave_enabled: Optional[bool] = None,
    **kwargs: Any,
) -> str:
    if _manager is None:
        return "error: server not initialized"
    if viewport_id is None:
        return "error: viewport_id is required"
    if autosave_enabled is None:
        return "error: autosave_enabled is required"
    entry = _manager.get_entry(session_id, viewport_id)
    conflict_msg = _check_file_conflict(entry.file, entry)
    _manager.set_autosave(session_id, viewport_id, autosave_enabled)
    parts = [f"autosave set to {autosave_enabled} for viewport {viewport_id}"]
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
    content_block = _format_content_block(visible, entry.line_start, entry.display_mode)
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

    # Decode \\uNNNN escapes in text parameters so agents in show mode
    # can input \\uNNNN to match/insert real characters
    decoded_old = _decode_unicode_escapes(old_text)
    decoded_new = _decode_unicode_escapes(new_text)

    if action == "replace":
        result = _manager.apply_edit(session_id, viewport_id, decoded_old, decoded_new)
        parts = [
            f"replaced text in viewport {viewport_id}:",
            f"  found: {result['found']}",
            f"  count: {result['count']}",
        ]
    elif action == "replace-all":
        result = _manager.apply_replace_all(
            session_id, viewport_id, decoded_old, decoded_new
        )
        parts = [
            f"replaced all occurrences in viewport {viewport_id}:",
            f"  found: {result['found']}",
            f"  count: {result['count']}",
        ]
    elif action == "insert-lines":
        result = _manager.apply_insert_lines(
            session_id, viewport_id, line_start, lines or []
        )
        parts = [
            f"inserted lines in viewport {viewport_id}:",
            f"  line_start: {result['line_start']}",
            f"  line_end: {result['line_end']}",
            f"  count: {result['count']}",
        ]
    elif action == "delete-lines":
        result = _manager.apply_delete_lines(
            session_id, viewport_id, line_start, line_end
        )
        parts = [
            f"deleted lines in viewport {viewport_id}:",
            f"  line_start: {result['line_start']}",
            f"  line_count: {result['line_count']}",
        ]
    elif action == "swap-lines":
        _manager.apply_swap_lines(
            session_id,
            viewport_id,
            line_start,
            line_end,
            target_line_start,
            target_line_end,
        )
        parts = [f"swapped line ranges in viewport {viewport_id}:", "  swapped: True"]
    elif action == "move-lines":
        _manager.apply_move_lines(
            session_id, viewport_id, line_start, line_end, target_line
        )
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
        if entry.autosave:
            return f"no pending changes for viewport {viewport_id} (autosave: on)"
        if file_path and entry.file != file_path:
            raise ViewportError(
                f"file '{file_path}' does not exist for viewport {viewport_id}"
            )
        conflict_warning = _manager.check_conflict(entry.file, entry.mtime, entry.size)
        if conflict_warning and not force:
            warning_str = _manager.format_conflict_warning(conflict_warning)
            raise ViewportError(f"stale mtime/size conflict\n{warning_str}")
        _manager.flush_entry(session_id, entry)
        return (
            f"saved viewport {viewport_id}:"
            f"\n  mtime: {entry.mtime}"
            f"\n  size: {entry.size}"
        )
    elif action == "discard":
        entry = _manager.get_entry(session_id, viewport_id)
        if entry.autosave:
            return f"no pending changes for viewport {viewport_id} (autosave: on)"
        _manager.discard_buffer_changes(session_id, viewport_id)
        return f"discarded pending changes for viewport {viewport_id}"
    elif action == "new":
        if not file_path:
            raise ViewportError("file_path is required for new action")
        try:
            entry = _manager.open_new(session_id, file_path)
        except FileExistsError as exc:
            raise ViewportError(str(exc))
        entry_data = entry.to_dict()
        lines = [
            "created new file and opened viewport:",
            f"  viewport_id: {entry_data['viewport_id']}",
            f"  file: {entry_data['file']}",
            f"  autosave: {entry_data['autosave']}",
        ]
        return "\n".join(lines)
    elif action == "save-as":
        if not viewport_id:
            raise ViewportError("viewport_id is required for save-as action")
        if not file_path:
            raise ViewportError("file_path is required for save-as action")
        try:
            entry = _manager.save_as(session_id, viewport_id, file_path, force=force)
        except FileExistsError as exc:
            raise ViewportError(str(exc))
        entry_data = entry.to_dict()
        lines = [
            f"saved as new file for viewport {viewport_id}:",
            f"  viewport_id: {entry_data['viewport_id']}",
            f"  file: {entry_data['file']}",
        ]
        return "\n".join(lines)
    elif action == "delete":
        if not viewport_id:
            raise ViewportError("viewport_id is required for delete action")
        deleted_file = _manager.delete_entry(session_id, viewport_id)
        return f"deleted file: {deleted_file}"
    else:
        raise ViewportError(f"unknown file action: {action}")


def _handle_diff_action(
    action: str,
    session_id: str,
    viewport_id: str,
    file_path: str = "",
    patch: str = "",
) -> str:
    if _manager is None:
        return "error: server not initialized"

    if action == "show":
        entry = _manager.get_entry(session_id, viewport_id)
        if entry.autosave:
            return f"no pending changes for viewport {viewport_id} (autosave: on)"
        diff_str = _manager.get_buffer_diff(session_id, viewport_id)
        if not diff_str:
            return f"no pending changes for viewport {viewport_id}"
        return f"diff for {file_path}:\n{diff_str}"
    elif action == "apply":
        if not patch:
            raise ViewportError("patch is required for apply action")

        vpid = viewport_id
        if vpid:
            entry = _manager.get_entry(session_id, vpid)
        elif file_path:
            entry = _manager.find_viewport_for_file(session_id, file_path)
            if entry is None:
                new_entry = _manager.open(
                    session_id=session_id,
                    file_path=file_path,
                )
                vpid = new_entry.viewport_id
                entry = new_entry
            else:
                vpid = entry.viewport_id
        else:
            raise ViewportError("viewport_id or file_path is required for apply action")

        try:
            result = _manager.apply_diff(session_id, vpid, patch)
        except DiffApplyError as exc:
            raise ViewportError(exc.message)

        entry_after = _manager.get_entry(session_id, vpid)
        diff_str = _manager.get_buffer_diff(session_id, vpid)
        visible = _manager.get_visible_lines(session_id, entry_after)
        content_block = _format_content_block(
            visible, entry_after.line_start, entry_after.display_mode
        )

        parts = [
            f"applied diff to viewport {vpid}:",
            f"  hunks_applied: {result['hunks_applied']}",
        ]
        if result.get("gate_notice"):
            parts.append(f"  notice: {result['gate_notice']}")
        if diff_str:
            parts.append("  diff:")
            for dline in diff_str.splitlines():
                parts.append(f"    {dline}")
        parts.append(content_block)
        return "\n".join(parts)
    else:
        raise ViewportError(f"unknown diff action: {action}")


def _handle_clipboard_action(
    action: str,
    session_id: str,
    viewport_id: str,
    line_start: int = 0,
    line_end: int = 0,
    target_line: int = 0,
    name: str = "",
) -> str:
    if _manager is None:
        return "error: server not initialized"

    stale_notice = _manager.sweep_stale_sessions()
    _manager.touch(session_id)

    if action == "copy":
        if not viewport_id:
            return "error: viewport_id is required"
        if line_start <= 0 or line_end <= 0:
            return "error: line_start and line_end are required"
        if line_end < line_start:
            return "error: line_end must be >= line_start"

        entry = _manager.get_entry(session_id, viewport_id)
        file_lines = _manager._buffer_mgr.get_lines(session_id, entry.file)
        line_ending = _manager.get_line_ending(session_id, entry.file)

        copied_lines, clip_entry = apply_copy(
            file_lines=file_lines,
            line_start=line_start,
            line_end=line_end,
            source_file=entry.file,
            line_ending=line_ending,
        )

        session = get_session(session_id)
        if session is not None:
            session.clipboard = clip_entry

        content_block = _format_content_block(
            copied_lines, line_start, entry.display_mode
        )
        parts = [
            "copied to clipboard:",
            f"  source_file: {entry.file}",
            f"  line_start: {line_start}",
            f"  line_end: {line_end}",
            f"  line_range: {line_start}-{line_end}",
            f"  timestamp: {clip_entry.timestamp}",
            content_block,
        ]
        result = "\n".join(parts)
        if stale_notice:
            result = stale_notice + "\n" + result
        return result

    elif action == "cut":
        if not viewport_id:
            return "error: viewport_id is required"
        if line_start <= 0 or line_end <= 0:
            return "error: line_start and line_end are required"
        if line_end < line_start:
            return "error: line_end must be >= line_start"

        entry = _manager.get_entry(session_id, viewport_id)
        buf = _manager._buffer_mgr.get_buffer_ref(session_id, entry.file)
        file_lines = _manager._buffer_mgr.get_lines(session_id, entry.file)
        line_ending = _manager.get_line_ending(session_id, entry.file)

        remaining_lines, clip_entry = apply_cut(
            file_lines=file_lines,
            line_start=line_start,
            line_end=line_end,
            source_file=entry.file,
            line_ending=line_ending,
        )

        line_ending_str = line_ending
        new_content = line_ending_str.join(
            line.rstrip("\n").rstrip("\r") for line in remaining_lines
        )
        if remaining_lines:
            new_content += line_ending_str
        buf.content = new_content

        session = get_session(session_id)
        if session is not None:
            session.clipboard = clip_entry

        gate_notice = _manager._autosave_gate(session_id, entry)
        diff_str = _manager.get_buffer_diff(session_id, viewport_id)

        content_block = _format_content_block(
            clip_entry.content, line_start, entry.display_mode
        )
        parts = [
            "cut to clipboard:",
            f"  source_file: {entry.file}",
            f"  line_start: {line_start}",
            f"  line_end: {line_end}",
            f"  line_range: {line_start}-{line_end}",
            f"  timestamp: {clip_entry.timestamp}",
            content_block,
        ]
        if gate_notice:
            parts.append(f"  notice: {gate_notice}")
        if diff_str:
            parts.append("  diff:")
            for dline in diff_str.splitlines():
                parts.append(f"    {dline}")
        result = "\n".join(parts)
        if stale_notice:
            result = stale_notice + "\n" + result
        return result

    elif action == "paste":
        session = get_session(session_id)
        if session is None or session.clipboard is None:
            raise ViewportError("clipboard is empty — copy or cut before pasting")

        if not viewport_id:
            return "error: viewport_id is required for paste"
        if target_line <= 0:
            return "error: target_line is required for paste"

        entry = _manager.get_entry(session_id, viewport_id)
        buf = _manager._buffer_mgr.get_buffer_ref(session_id, entry.file)
        file_lines = _manager._buffer_mgr.get_lines(session_id, entry.file)
        line_ending = _manager.get_line_ending(session_id, entry.file)

        new_lines = apply_paste(
            file_lines=file_lines,
            target_line=target_line,
            clipboard_lines=session.clipboard.content,
            line_ending=line_ending,
        )

        line_ending_str = line_ending
        new_content = line_ending_str.join(
            line.rstrip("\n").rstrip("\r") for line in new_lines
        )
        if new_lines:
            new_content += line_ending_str
        buf.content = new_content

        gate_notice = _manager._autosave_gate(session_id, entry)
        diff_str = _manager.get_buffer_diff(session_id, viewport_id)

        clip = session.clipboard
        content_block = _format_content_block(
            clip.content, clip.line_range[0], entry.display_mode
        )
        parts = [
            "pasted from clipboard:",
            f"  source_file: {clip.source_file}",
            f"  target_line: {target_line}",
            f"  lines_pasted: {len(clip.content)}",
            f"  line_range: {target_line}-{target_line + len(clip.content) - 1}",
            content_block,
        ]
        if gate_notice:
            parts.append(f"  notice: {gate_notice}")
        if diff_str:
            parts.append("  diff:")
            for dline in diff_str.splitlines():
                parts.append(f"    {dline}")
        result = "\n".join(parts)
        if stale_notice:
            result = stale_notice + "\n" + result
        return result

    elif action == "show":
        session = get_session(session_id)
        if session is None or session.clipboard is None:
            return "clipboard is empty"

        clip = session.clipboard
        content_block = _format_content_block(clip.content, clip.line_range[0])
        parts = [
            "clipboard:",
            f"  source_file: {clip.source_file}",
            f"  line_range: {clip.line_range[0]}-{clip.line_range[1]}",
            f"  timestamp: {clip.timestamp}",
            content_block,
        ]
        return "\n".join(parts)

    elif action == "stash":
        session = get_session(session_id)
        if session is None or session.clipboard is None:
            raise ViewportError("clipboard is empty — copy or cut before stashing")
        if not name:
            return "error: name is required for stash"

        clip = session.clipboard
        session.stash_slots[name] = ClipboardEntry(
            content=list(clip.content),
            source_file=clip.source_file,
            line_range=clip.line_range,
            timestamp=clip.timestamp,
            line_ending=clip.line_ending,
        )

        content_block = _format_content_block(clip.content, clip.line_range[0])
        parts = [
            f"stashed clipboard to '{name}':",
            f"  source_file: {clip.source_file}",
            f"  line_range: {clip.line_range[0]}-{clip.line_range[1]}",
            f"  line_count: {len(clip.content)}",
            content_block,
        ]
        result = "\n".join(parts)
        if stale_notice:
            result = stale_notice + "\n" + result
        return result

    elif action == "pop":
        session = get_session(session_id)
        if session is None:
            raise ViewportError(f"stash slot '{name}' not found")
        if not name:
            return "error: name is required for pop"
        slot = session.stash_slots.get(name)
        if slot is None:
            raise ViewportError(f"stash slot '{name}' not found")

        session.clipboard = ClipboardEntry(
            content=list(slot.content),
            source_file=slot.source_file,
            line_range=slot.line_range,
            timestamp=slot.timestamp,
            line_ending=slot.line_ending,
        )

        clip = session.clipboard
        content_block = _format_content_block(clip.content, clip.line_range[0])
        parts = [
            f"popped '{name}' to clipboard:",
            f"  source_file: {clip.source_file}",
            f"  line_range: {clip.line_range[0]}-{clip.line_range[1]}",
            f"  line_count: {len(clip.content)}",
            content_block,
        ]
        result = "\n".join(parts)
        if stale_notice:
            result = stale_notice + "\n" + result
        return result

    elif action == "swap":
        session = get_session(session_id)
        if session is None or session.clipboard is None:
            raise ViewportError("clipboard is empty — copy or cut before swapping")
        if not name:
            return "error: name is required for swap"
        slot = session.stash_slots.get(name) if session is not None else None
        if slot is None:
            raise ViewportError(f"stash slot '{name}' not found")

        clip = session.clipboard
        session.stash_slots[name] = ClipboardEntry(
            content=list(clip.content),
            source_file=clip.source_file,
            line_range=clip.line_range,
            timestamp=clip.timestamp,
            line_ending=clip.line_ending,
        )
        session.clipboard = ClipboardEntry(
            content=list(slot.content),
            source_file=slot.source_file,
            line_range=slot.line_range,
            timestamp=slot.timestamp,
            line_ending=slot.line_ending,
        )

        new_clip = session.clipboard
        content_block = _format_content_block(new_clip.content, new_clip.line_range[0])
        parts = [
            f"swapped clipboard with '{name}':",
            f"  clipboard now: {new_clip.source_file} lines {new_clip.line_range[0]}-{new_clip.line_range[1]}",
            f"  slot '{name}' now: {clip.source_file} lines {clip.line_range[0]}-{clip.line_range[1]}",
            content_block,
        ]
        result = "\n".join(parts)
        if stale_notice:
            result = stale_notice + "\n" + result
        return result

    elif action == "stash-list":
        session = get_session(session_id)
        if session is None or not session.stash_slots:
            return "no stash slots"

        parts = [f"stash slots ({len(session.stash_slots)}):"]
        for slot_name, slot in session.stash_slots.items():
            first_line = (
                slot.content[0].rstrip("\n").rstrip("\r") if slot.content else ""
            )
            parts.append(f"  - name: {slot_name}")
            parts.append(f"    source_file: {slot.source_file}")
            parts.append(f"    line_range: {slot.line_range[0]}-{slot.line_range[1]}")
            parts.append(f"    line_count: {len(slot.content)}")
            parts.append(f"    first_line: {first_line}")
        result = "\n".join(parts)
        if stale_notice:
            result = stale_notice + "\n" + result
        return result

    else:
        return f"error: unknown clipboard action: {action}"


def _handle_search_action(
    action: str,
    session_id: str,
    pattern: str = "",
    regex: bool = False,
    scope: str = "",
    file_path: str = "",
    viewport_id: str = "",
) -> str:
    if _manager is None:
        return "error: server not initialized"

    if action == "find":
        return _action_find(
            session_id=session_id,
            pattern=pattern,
            regex=regex,
            scope=scope,
            file_path=file_path,
            viewport_id=viewport_id,
        )
    else:
        return f"error: unknown search action: {action}"


def _search_in_content(content: str, pattern: str, use_regex: bool) -> list[dict]:
    results: list[dict] = []
    lines = content.splitlines()
    if use_regex:
        import re as _re

        try:
            compiled = _re.compile(pattern)
        except _re.error as exc:
            raise ViewportError(f"invalid regex pattern: {exc}")
        for i, line in enumerate(lines, 1):
            if compiled.search(line):
                results.append({"line": i, "text": line})
    else:
        for i, line in enumerate(lines, 1):
            if pattern in line:
                results.append({"line": i, "text": line})
    return results


def _format_find_results(matches: list[dict], file_label: str) -> list[str]:
    parts: list[str] = []
    for m in matches:
        text_preview = m["text"][:120]
        parts.append(f"    - line: {m['line']}")
        parts.append(f"      text: {text_preview}")
    return parts


def _action_find(
    session_id: str,
    pattern: str,
    regex: bool,
    scope: str,
    file_path: str,
    viewport_id: str,
) -> str:
    if _manager is None:
        return "error: server not initialized"
    if not pattern:
        return "error: pattern is required for find action"

    if scope == "file":
        if not file_path:
            return "error: file_path is required for scope=file"
        resolved, _ = _resolve_path(file_path, _manager.project_root)
        if not os.path.isfile(resolved):
            return f"error: file not found: {file_path}"
        with open(resolved, "r", newline="") as f:
            content = f.read()
        matches = _search_in_content(content, pattern, regex)
        parts = [f"find results for '{pattern}' in {file_label_from_path(file_path)}:"]
        if matches:
            parts.append(f"  matches: {len(matches)}")
            parts.append(f"  file: {file_path}")
            for m in matches:
                text_preview = m["text"][:120]
                parts.append(f"  - line: {m['line']}")
                parts.append(f"    text: {text_preview}")
        else:
            parts.append("  matches: 0")
        parts.append("  scope: file")
        return "\n".join(parts)

    elif scope == "viewport":
        if not viewport_id:
            return "error: viewport_id is required for scope=viewport"
        entry = _manager.get_entry(session_id, viewport_id)
        content = _manager._buffer_mgr.get_raw_content(session_id, entry.file)
        matches = _search_in_content(content, pattern, regex)
        parts = [f"find results for '{pattern}' in viewport {viewport_id}:"]
        if matches:
            parts.append(f"  matches: {len(matches)}")
            parts.append(f"  file: {entry.file}")
            for m in matches:
                text_preview = m["text"][:120]
                parts.append(f"  - line: {m['line']}")
                parts.append(f"    text: {text_preview}")
        else:
            parts.append("  matches: 0")
        parts.append("  scope: viewport")
        return "\n".join(parts)

    elif scope == "all_open":
        if session_id not in _manager._entries or not _manager._entries[session_id]:
            return f"find results for '{pattern}': no open viewports"
        total_matches: list[dict] = []
        file_results: dict[str, list[dict]] = {}
        for vp_id, vp_entry in _manager._entries[session_id].items():
            try:
                content = _manager._buffer_mgr.get_raw_content(
                    session_id, vp_entry.file
                )
            except KeyError:
                continue
            file_matches = _search_in_content(content, pattern, regex)
            if file_matches:
                file_results[vp_entry.file] = file_matches
                total_matches.extend(file_matches)
        parts = [f"find results for '{pattern}' across all open viewports:"]
        if file_results:
            parts.append(f"  matches: {len(total_matches)}")
            for fp, fmatches in file_results.items():
                parts.append(f"  file: {fp}")
                for m in fmatches:
                    text_preview = m["text"][:120]
                    parts.append(f"  - line: {m['line']}")
                    parts.append(f"    text: {text_preview}")
        else:
            parts.append("  matches: 0")
        parts.append("  scope: all_open")
        return "\n".join(parts)

    else:
        resolved, _ = _resolve_path(
            file_path if file_path else ".", _manager.project_root
        )
        all_files = _collect_project_files(_manager.project_root)
        total_matches: list[dict] = []
        file_results: dict[str, list[dict]] = {}
        for fp in all_files:
            full_path = os.path.join(_manager.project_root, fp)
            try:
                with open(full_path, "r", newline="") as f:
                    content = f.read()
            except (OSError, UnicodeDecodeError):
                continue
            file_matches = _search_in_content(content, pattern, regex)
            if file_matches:
                file_results[fp] = file_matches
                total_matches.extend(file_matches)
        parts = [f"find results for '{pattern}':"]
        if file_results:
            parts.append(f"  matches: {len(total_matches)}")
            for fp, fmatches in file_results.items():
                parts.append(f"  file: {fp}")
                for m in fmatches:
                    text_preview = m["text"][:120]
                    parts.append(f"  - line: {m['line']}")
                    parts.append(f"    text: {text_preview}")
        else:
            parts.append("  matches: 0")
        return "\n".join(parts)


def _collect_project_files(project_root: str) -> list[str]:
    result: list[str] = []
    for dirpath, _dirnames, filenames in os.walk(project_root):
        skip = False
        for part in Path(dirpath).relative_to(project_root).parts:
            if part.startswith(".") or part == "__pycache__":
                skip = True
                break
        if skip:
            continue
        for fname in filenames:
            rel = str(Path(dirpath).relative_to(project_root) / fname)
            result.append(rel)
    return result


def file_label_from_path(fp: str) -> str:
    return fp
