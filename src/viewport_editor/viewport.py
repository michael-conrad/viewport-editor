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

import os
import time
from dataclasses import dataclass, field
from itertools import count
from typing import Dict, Iterator, List, Optional

from .buffer import BufferManager
from . import editor
from .exceptions import (
    FileNotFoundError_,
    InvalidDisplayModeError,
    JumpLineOutOfRangeError,
    JumpTargetNotFoundError,
    SessionNotFoundError,
    ViewportError,
    ViewportNotFoundError,
)
from . import file_ops

_viewport_id_counter: Iterator[int] = count(1)
IDLE_TIMEOUT: float = 14400.0  # 4 hours


@dataclass
class ViewportEntry:
    file: str
    line_start: int
    line_end: int
    mtime: Optional[float] = None
    size: Optional[int] = None
    autosave: bool = False
    dirty: bool = False
    line_ending: str = "\n"
    display_mode: str = "hide"
    viewport_id: str = field(
        default_factory=lambda: f"viewport_{next(_viewport_id_counter)}"
    )

    def to_dict(self) -> dict:
        return {
            "viewport_id": self.viewport_id,
            "file": self.file,
            "line_start": self.line_start,
            "line_end": self.line_end,
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
        line_start: int = 1,
        line_end: int = 100,
        autosave: bool = False,
    ) -> ViewportEntry:
        resolved_path, _ = file_ops._resolve_path(file_path, self.project_root)
        if not __import__("os").path.isfile(resolved_path):
            raise FileNotFoundError_(file_path)
        if session_id not in self._entries:
            self._entries[session_id] = {}
        buffer = self._buffer_mgr.get_or_create(session_id, file_path, resolved_path)
        total_lines = len(buffer.content.splitlines(keepends=True))
        start = max(1, line_start)
        end = min(line_end, total_lines) if line_end <= total_lines else total_lines
        detected = file_ops._detect_line_ending(resolved_path)
        if session_id not in self.line_endings:
            self.line_endings[session_id] = {}
        self.line_endings[session_id][file_path] = detected
        entry = ViewportEntry(
            file=file_path,
            line_start=start,
            line_end=end,
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
        start = max(0, entry.line_start - 1)
        end = min(entry.line_end, total)
        return file_lines[start:end]

    def scroll(self, session_id: str, viewport_id: str, lines: int) -> ViewportEntry:
        entry = self.get_entry(session_id, viewport_id)
        file_lines = self._buffer_mgr.get_lines(session_id, entry.file)
        height = entry.line_end - entry.line_start
        total = len(file_lines)
        new_start = max(1, entry.line_start + lines)
        if new_start + height > total:
            new_start = max(1, total - height)
        entry.line_start = new_start
        entry.line_end = min(new_start + height, total)
        return entry

    def page_up(self, session_id: str, viewport_id: str) -> ViewportEntry:
        entry = self.get_entry(session_id, viewport_id)
        height = entry.line_end - entry.line_start
        return self.scroll(session_id, viewport_id, -height)

    def page_down(self, session_id: str, viewport_id: str) -> ViewportEntry:
        entry = self.get_entry(session_id, viewport_id)
        height = entry.line_end - entry.line_start
        return self.scroll(session_id, viewport_id, height)

    def jump(self, session_id: str, viewport_id: str, target: str) -> ViewportEntry:
        entry = self.get_entry(session_id, viewport_id)
        file_lines = self._buffer_mgr.get_lines(session_id, entry.file)
        total = len(file_lines)
        height = entry.line_end - entry.line_start
        target_str = target.strip().lower()
        if target_str == "top":
            new_start = 1
        elif target_str == "bottom":
            if total == 0:
                new_start = 1
            else:
                new_start = max(1, total - height)
        elif target_str.isdigit():
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
        entry.line_start = new_start
        entry.line_end = min(new_start + height, total)
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

    def open_new(
        self,
        session_id: str,
        file_path: str,
    ) -> ViewportEntry:
        resolved_path = file_ops.create_new_file(file_path, self.project_root)
        if session_id not in self._entries:
            self._entries[session_id] = {}
        buffer = self._buffer_mgr.get_or_create(session_id, file_path, resolved_path)
        if session_id not in self.line_endings:
            self.line_endings[session_id] = {}
        self.line_endings[session_id][file_path] = "\n"
        entry = ViewportEntry(
            file=file_path,
            line_start=1,
            line_end=0,
            mtime=buffer.mtime,
            size=0,
            autosave=False,
            line_ending="\n",
            display_mode="hide",
        )
        self._entries[session_id][entry.viewport_id] = entry
        return entry

    def save_as(
        self,
        session_id: str,
        viewport_id: str,
        target_file: str,
        force: bool = False,
    ) -> ViewportEntry:
        entry = self.get_entry(session_id, viewport_id)
        buf = self._buffer_mgr.get_buffer_ref(session_id, entry.file)
        resolved_target = file_ops.save_as_file(
            entry.file, target_file, self.project_root, buf.content, force=force
        )
        old_file = entry.file
        self.line_endings[session_id][target_file] = self.get_line_ending(
            session_id, old_file
        )
        self._buffer_mgr._buffers[session_id][target_file] = self._buffer_mgr._buffers[
            session_id
        ].pop(old_file)
        self._buffer_mgr._buffers[session_id][target_file].path = target_file
        st = os.stat(resolved_target)
        buf = self._buffer_mgr._buffers[session_id][target_file]
        buf.mtime = st.st_mtime
        buf.size = st.st_size
        entry.file = target_file
        entry.mtime = st.st_mtime
        entry.size = st.st_size
        entry.dirty = False
        return entry

    def delete_entry(self, session_id: str, viewport_id: str) -> str:
        """Delete the file on disk and close the viewport.

        Rejects if the buffer has uncommitted changes (dirty).
        Returns the resolved file path on success.
        """
        if session_id not in self._entries:
            raise SessionNotFoundError(session_id)
        if viewport_id not in self._entries[session_id]:
            raise ViewportNotFoundError(viewport_id)
        entry = self._entries[session_id][viewport_id]
        if entry.dirty:
            raise ViewportError(
                f"cannot delete file with uncommitted changes: {entry.file}"
            )
        file_ops.delete_file(entry.file, self.project_root)
        self._buffer_mgr.destroy_buffer(session_id, entry.file)
        del self._entries[session_id][viewport_id]
        if (
            session_id in self.line_endings
            and entry.file in self.line_endings[session_id]
        ):
            del self.line_endings[session_id][entry.file]
        return entry.file

    def format_conflict_warning(self, warning: dict) -> str:
        return file_ops.format_conflict_warning(warning)

    def apply_diff(self, session_id: str, viewport_id: str, patch: str) -> dict:
        """Apply a unified diff patch to the buffer for the given viewport.

        Uses autosave gate: switches to buffered mode on autosave=on viewports
        so the agent can review before saving.
        """
        from .diff_engine import apply_diff_to_content

        entry = self.get_entry(session_id, viewport_id)
        buf = self._buffer_mgr.get_buffer_ref(session_id, entry.file)
        new_content = apply_diff_to_content(buf.content, patch)
        buf.content = new_content
        gate_notice = self._autosave_gate(session_id, entry)

        hunks_count = len(
            [line for line in patch.splitlines() if line.startswith("@@")]
        )

        return {
            "hunks_applied": hunks_count,
            "gate_notice": gate_notice,
        }

    def find_viewport_for_file(
        self, session_id: str, file_path: str
    ) -> Optional[ViewportEntry]:
        """Find a viewport for the given file in the session."""
        if session_id not in self._entries:
            return None
        for entry in self._entries[session_id].values():
            if entry.file == file_path:
                return entry
        return None
