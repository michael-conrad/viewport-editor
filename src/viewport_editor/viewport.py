# SPDX-FileCopyrightText: 2026 Michael Conrad
# SPDX-License-Identifier: MIT
# Provenance: AI-generated
"""ViewportEntry model and ViewportManager for viewport-editor.

ViewportManager is a coordinator that delegates to:
  - BufferManager for buffer lifecycle
  - editor.py for pure edit operations
  - file_ops.py for file I/O and conflict detection

Co-authored with AI: OpenCode (deepseek-v4-flash)
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .buffer import BufferManager
from . import editor
from .exceptions import (
    FileNotFoundError_,
    InvalidDisplayModeError,
    JumpLineOutOfRangeError,
    JumpTargetNotFoundError,
    SessionNotFoundError,
    ViewportNotFoundError,
)
from . import file_ops

IDLE_TIMEOUT: float = 14400.0  # 4 hours


@dataclass
class ViewportEntry:
    file: str
    start_line: int
    end_line: int
    mtime: Optional[float] = None
    size: Optional[int] = None
    autosave: bool = False
    dirty: bool = False
    line_ending: str = "\n"
    display_mode: str = "hide"
    viewport_id: str = field(default_factory=lambda: hex(id(object()))[2:])

    def to_dict(self) -> dict:
        return {
            "viewport_id": self.viewport_id,
            "file": self.file,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "mtime": self.mtime,
            "size": self.size,
            "autosave": self.autosave,
            "dirty": self.dirty,
            "line_ending": self.line_ending,
            "display_mode": self.display_mode,
        }


class ViewportManager:
    """Coordinates viewport state, delegating buffer/file/edit operations."""

    def __init__(self, project_root: str) -> None:
        self.project_root = project_root
        self._entries: Dict[str, Dict[str, ViewportEntry]] = {}
        self._last_active: Dict[str, float] = {}
        self.line_endings: Dict[str, Dict[str, str]] = {}
        self._buffer_mgr = BufferManager()

    def touch(self, session_id: str) -> None:
        """Mark session as active at current time."""
        self._last_active[session_id] = time.time()

    def sweep_stale_sessions(self) -> Optional[str]:
        """Evict sessions idle longer than IDLE_TIMEOUT. Dirty buffers discarded (zero saves)."""
        now = time.time()
        stale = []
        for session_id, last_active in list(self._last_active.items()):
            if now - last_active > IDLE_TIMEOUT:
                stale.append(session_id)
        if not stale:
            return None
        notices: list[str] = ["discarded stale sessions:"]
        for session_id in stale:
            entries = self._entries.get(session_id, {})
            summary = (
                ", ".join(
                    f"{e.file} {'[dirty]' if e.dirty else '[clean]'}"
                    for e in entries.values()
                )
                or "no open viewports"
            )
            notices.append(f"  - {session_id}: {summary}")
            self.destroy_session(session_id)
        return "\n".join(notices)

    def open(
        self,
        session_id: str,
        file_path: str,
        start_line: int = 1,
        end_line: int = 100,
        autosave: bool = False,
    ) -> ViewportEntry:
        resolved_path, _ = file_ops._resolve_path(file_path, self.project_root)
        if not __import__("os").path.isfile(resolved_path):
            raise FileNotFoundError_(file_path)
        if session_id not in self._entries:
            self._entries[session_id] = {}
        buffer = self._buffer_mgr.get_or_create(session_id, file_path, resolved_path)
        total_lines = len(buffer.content.splitlines(keepends=True))
        start = max(1, start_line)
        end = min(end_line, total_lines) if end_line <= total_lines else total_lines
        detected = file_ops._detect_line_ending(resolved_path)
        if session_id not in self.line_endings:
            self.line_endings[session_id] = {}
        self.line_endings[session_id][file_path] = detected
        entry = ViewportEntry(
            file=file_path,
            start_line=start,
            end_line=end,
            mtime=buffer.mtime,
            size=buffer.size,
            autosave=autosave,
            line_ending=detected,
            display_mode="hide",
        )
        self._entries[session_id][entry.viewport_id] = entry
        return entry

    def close(self, session_id: str, viewport_id: str) -> None:
        if session_id not in self._entries:
            raise SessionNotFoundError(session_id)
        if viewport_id not in self._entries[session_id]:
            raise ViewportNotFoundError(viewport_id)
        entry = self._entries[session_id][viewport_id]
        if entry.dirty and entry.autosave:
            self.flush_entry(session_id, entry)
        del self._entries[session_id][viewport_id]

    def flush_entry(self, session_id: str, entry: ViewportEntry) -> None:
        """Public flush: delegates to file_ops, writing buffer to disk atomically."""
        buf = self._buffer_mgr.get_buffer_ref(session_id, entry.file)
        file_ops.flush_entry(buf, entry, self.project_root)

    def _maybe_autosave(self, session_id: str, entry: ViewportEntry) -> None:
        """Set dirty flag; flush to disk if autosave enabled."""
        entry.dirty = True
        if entry.autosave:
            self.flush_entry(session_id, entry)

    def _autosave_gate(self, session_id: str, entry: ViewportEntry) -> Optional[str]:
        """Autosave gate for write operations that should switch to buffered mode.

        When autosave is on, switches to buffered mode (autosave off) and
        returns a notice string. When already buffered, returns None.
        Marks the entry dirty in either case.
        """
        entry.dirty = True
        if entry.autosave:
            entry.autosave = False
            return "autosave gate: switched to buffered mode (autosave off) — changes staged in buffer, not yet saved to disk"
        return None

    def list(self, session_id: str) -> List[dict]:
        if session_id not in self._entries:
            return []
        return [e.to_dict() for e in self._entries[session_id].values()]

    def get_visible_lines(self, session_id: str, entry: ViewportEntry) -> list[str]:
        file_lines = self._buffer_mgr.get_lines(session_id, entry.file)
        total = len(file_lines)
        start = max(0, entry.start_line - 1)
        end = min(entry.end_line, total)
        return file_lines[start:end]

    def scroll(self, session_id: str, viewport_id: str, lines: int) -> ViewportEntry:
        entry = self.get_entry(session_id, viewport_id)
        file_lines = self._buffer_mgr.get_lines(session_id, entry.file)
        height = entry.end_line - entry.start_line
        total = len(file_lines)
        new_start = max(1, entry.start_line + lines)
        if new_start + height > total:
            new_start = max(1, total - height)
        entry.start_line = new_start
        entry.end_line = min(new_start + height, total)
        return entry

    def page_up(self, session_id: str, viewport_id: str) -> ViewportEntry:
        entry = self.get_entry(session_id, viewport_id)
        height = entry.end_line - entry.start_line
        return self.scroll(session_id, viewport_id, -height)

    def page_down(self, session_id: str, viewport_id: str) -> ViewportEntry:
        entry = self.get_entry(session_id, viewport_id)
        height = entry.end_line - entry.start_line
        return self.scroll(session_id, viewport_id, height)

    def jump(self, session_id: str, viewport_id: str, target: str) -> ViewportEntry:
        entry = self.get_entry(session_id, viewport_id)
        file_lines = self._buffer_mgr.get_lines(session_id, entry.file)
        total = len(file_lines)
        height = entry.end_line - entry.start_line
        target_str = target.strip()
        if target_str.isdigit():
            line_num = int(target_str)
            if line_num < 1 or line_num > total:
                raise JumpLineOutOfRangeError(line_num, total)
            new_start = max(1, line_num)
        else:
            found = False
            new_start = 1
            for i, line in enumerate(file_lines):
                if target_str in line:
                    new_start = max(1, i + 1)
                    found = True
                    break
            if not found:
                raise JumpTargetNotFoundError(target)
        if new_start + height > total:
            new_start = max(1, total - height)
        entry.start_line = new_start
        entry.end_line = min(new_start + height, total)
        return entry

    def set_autosave(
        self, session_id: str, viewport_id: str, enabled: bool
    ) -> ViewportEntry:
        entry = self.get_entry(session_id, viewport_id)
        if enabled and not entry.autosave and entry.dirty:
            self.flush_entry(session_id, entry)
        entry.autosave = enabled
        return entry

    def set_display_mode(
        self, session_id: str, viewport_id: str, mode: str
    ) -> ViewportEntry:
        entry = self.get_entry(session_id, viewport_id)
        if mode not in ("hide", "show"):
            raise InvalidDisplayModeError(mode)
        entry.display_mode = mode
        return entry

    def destroy_session(self, session_id: str) -> None:
        """Remove a session and all its state. Dirty buffers are discarded (zero saves)."""
        self._entries.pop(session_id, None)
        self._buffer_mgr.destroy_session(session_id)

    def get_entry(self, session_id: str, viewport_id: str) -> ViewportEntry:
        if session_id not in self._entries:
            raise SessionNotFoundError(session_id)
        if viewport_id not in self._entries[session_id]:
            raise ViewportNotFoundError(viewport_id)
        return self._entries[session_id][viewport_id]

    def get_line_ending(self, session_id: str, file_path: str) -> str:
        if (
            session_id not in self.line_endings
            or file_path not in self.line_endings[session_id]
        ):
            return "\n"
        return self.line_endings[session_id][file_path]

    # --- Edit operations (thin wrappers delegating to editor.py) ---

    def apply_edit(
        self, session_id: str, viewport_id: str, old_text: str, new_text: str
    ) -> dict:
        entry = self.get_entry(session_id, viewport_id)
        buf = self._buffer_mgr.get_buffer_ref(session_id, entry.file)
        new_content, result = editor.apply_edit(buf.content, old_text, new_text)
        buf.content = new_content
        self._maybe_autosave(session_id, entry)
        return result

    def apply_replace_all(
        self, session_id: str, viewport_id: str, old_text: str, new_text: str
    ) -> dict:
        entry = self.get_entry(session_id, viewport_id)
        buf = self._buffer_mgr.get_buffer_ref(session_id, entry.file)
        new_content, result = editor.apply_replace_all(buf.content, old_text, new_text)
        buf.content = new_content
        self._maybe_autosave(session_id, entry)
        return result

    def apply_insert_lines(
        self, session_id: str, viewport_id: str, line_start: int, lines: list[str]
    ) -> dict:
        entry = self.get_entry(session_id, viewport_id)
        buf = self._buffer_mgr.get_buffer_ref(session_id, entry.file)
        le = self.get_line_ending(session_id, entry.file)
        new_content, result = editor.apply_insert_lines(
            buf.content, line_start, lines, le
        )
        buf.content = new_content
        self._maybe_autosave(session_id, entry)
        return result

    def apply_delete_lines(
        self, session_id: str, viewport_id: str, line_start: int, line_end: int
    ) -> dict:
        entry = self.get_entry(session_id, viewport_id)
        buf = self._buffer_mgr.get_buffer_ref(session_id, entry.file)
        new_content, result = editor.apply_delete_lines(
            buf.content, line_start, line_end
        )
        buf.content = new_content
        self._maybe_autosave(session_id, entry)
        return result

    def apply_swap_lines(
        self,
        session_id: str,
        viewport_id: str,
        line_start: int,
        line_end: int,
        target_line_start: int,
        target_line_end: int,
    ) -> dict:
        entry = self.get_entry(session_id, viewport_id)
        buf = self._buffer_mgr.get_buffer_ref(session_id, entry.file)
        new_content, result = editor.apply_swap_lines(
            buf.content, line_start, line_end, target_line_start, target_line_end
        )
        buf.content = new_content
        self._maybe_autosave(session_id, entry)
        return result

    def apply_move_lines(
        self,
        session_id: str,
        viewport_id: str,
        line_start: int,
        line_end: int,
        target_line: int,
    ) -> dict:
        entry = self.get_entry(session_id, viewport_id)
        buf = self._buffer_mgr.get_buffer_ref(session_id, entry.file)
        new_content, result = editor.apply_move_lines(
            buf.content, line_start, line_end, target_line
        )
        buf.content = new_content
        self._maybe_autosave(session_id, entry)
        return result

    # --- File operations (delegating to file_ops.py) ---

    def discard_buffer_changes(
        self, session_id: str, viewport_id: str
    ) -> ViewportEntry:
        entry = self.get_entry(session_id, viewport_id)
        buf = self._buffer_mgr.get_buffer_ref(session_id, entry.file)
        file_ops.discard_buffer_changes(buf, entry, self.project_root)
        return entry

    def get_buffer_diff(self, session_id: str, viewport_id: str) -> str:
        entry = self.get_entry(session_id, viewport_id)
        return self._buffer_mgr.get_diff(session_id, entry.file, self.project_root)

    def check_conflict(
        self, file_path: str, stored_mtime: Optional[float], stored_size: Optional[int]
    ) -> Optional[dict]:
        return file_ops.check_conflict(
            file_path, self.project_root, stored_mtime, stored_size
        )

    def format_conflict_warning(self, warning: dict) -> str:
        return file_ops.format_conflict_warning(warning)
