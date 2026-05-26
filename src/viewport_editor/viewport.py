# SPDX-FileCopyrightText: 2026 Michael Conrad
# SPDX-License-Identifier: MIT
# Provenance: AI-generated
"""ViewportEntry model and ViewportManager for viewport-editor.

Co-authored with AI: OpenCode (deepseek-v4-flash)
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from .exceptions import (
    AbsolutePathError,
    FileNotFoundError_,
    InvalidDisplayModeError,
    JumpLineOutOfRangeError,
    JumpTargetNotFoundError,
    PathEscapeError,
    SessionNotFoundError,
    ViewportNotFoundError,
)

IDLE_TIMEOUT: float = 14400.0  # 4 hours — abandoned sessions are evicted on next action


@dataclass
class Buffer:
    path: str
    content: str
    mtime: Optional[float]
    size: Optional[int]


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


def _resolve_path(file_path: str, project_root: str) -> Tuple[str, str]:
    if file_path.startswith("/"):
        raise AbsolutePathError(file_path)
    resolved = os.path.normpath(os.path.join(project_root, file_path))
    resolved_str = str(resolved)
    norm_root = os.path.normpath(project_root)
    if not resolved_str.startswith(str(norm_root)):
        raise PathEscapeError(file_path)
    return resolved_str, file_path


def _detect_line_ending(file_path: str) -> str:
    """Scan the first 100 lines in binary mode and return the dominant line terminator."""
    with open(file_path, "rb") as f:
        raw = f.read(32768)
    crlf = raw.count(b"\r\n")
    lf = raw.count(b"\n") - crlf
    cr = raw.count(b"\r") - crlf
    counts = {b"\r\n": crlf, b"\n": lf, b"\r": cr}
    # Filter to only terminators that actually appeared
    present = {k: v for k, v in counts.items() if v > 0}
    if not present:
        return "\n"
    dominant = max(present, key=present.get)
    return dominant.decode("ascii")


def _read_file_lines(resolved_path: str) -> Tuple[List[str], Optional[float], Optional[int]]:
    st = os.stat(resolved_path)
    mtime = st.st_mtime
    size = st.st_size
    with open(resolved_path, "r") as f:
        content = f.read()
    lines = content.splitlines(keepends=True)
    return lines, mtime, size


class ViewportManager:
    def __init__(self, project_root: str) -> None:
        self.project_root = project_root
        self._buffers: Dict[str, Dict[str, Buffer]] = {}
        self._entries: Dict[str, Dict[str, ViewportEntry]] = {}
        self._last_active: Dict[str, float] = {}
        self.line_endings: Dict[str, Dict[str, str]] = {}

    def touch(self, session_id: str) -> None:
        """Mark session as active at current time."""
        self._last_active[session_id] = time.time()

    def sweep_stale_sessions(self) -> Optional[str]:
        """Evict sessions idle longer than IDLE_TIMEOUT. Dirty buffers are discarded (zero saves).
        Returns a YAML notice string if any sessions were evicted, or None."""
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
            summary = ", ".join(
                f"{e.file} {'[dirty]' if e.dirty else '[clean]'}"
                for e in entries.values()
            ) or "no open viewports"
            notices.append(f"  - {session_id}: {summary}")
            self.destroy_session(session_id)

        return "\n".join(notices)

    def _get_or_create_buffer(self, session_id: str, file_path: str, resolved_path: str) -> Buffer:
        if session_id not in self._buffers:
            self._buffers[session_id] = {}
        if file_path not in self._buffers[session_id]:
            lines, mtime, size = _read_file_lines(resolved_path)
            content = "".join(lines)
            self._buffers[session_id][file_path] = Buffer(
                path=file_path, content=content, mtime=mtime, size=size
            )
        return self._buffers[session_id][file_path]

    def _file_lines(self, session_id: str, file_path: str) -> List[str]:
        buf = self._buffers[session_id][file_path]
        return buf.content.splitlines(keepends=True)

    def _refresh_buffer_if_changed(self, session_id: str, file_path: str, resolved_path: str) -> None:
        if session_id in self._buffers and file_path in self._buffers[session_id]:
            lines, mtime, size = _read_file_lines(resolved_path)
            buf = self._buffers[session_id][file_path]
            buf.content = "".join(lines)
            buf.mtime = mtime
            buf.size = size

    def open(
        self,
        session_id: str,
        file_path: str,
        start_line: int = 1,
        end_line: int = 100,
        autosave: bool = False,
    ) -> ViewportEntry:
        resolved_path, _ = _resolve_path(file_path, self.project_root)
        if not os.path.isfile(resolved_path):
            raise FileNotFoundError_(file_path)

        if session_id not in self._entries:
            self._entries[session_id] = {}

        buffer = self._get_or_create_buffer(session_id, file_path, resolved_path)
        total_lines = len(buffer.content.splitlines(keepends=True))

        start = max(1, start_line)
        end = min(end_line, total_lines) if end_line <= total_lines else total_lines

        detected = _detect_line_ending(resolved_path)
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
        if entry.dirty and not entry.autosave:
            self._flush_entry(session_id, entry)
        del self._entries[session_id][viewport_id]

    def _flush_entry(self, session_id: str, entry: ViewportEntry) -> None:
        if session_id not in self._buffers or entry.file not in self._buffers[session_id]:
            return
        buf = self._buffers[session_id][entry.file]
        resolved_path, _ = _resolve_path(entry.file, self.project_root)
        with open(resolved_path, "w") as f:
            f.write(buf.content)
        st = os.stat(resolved_path)
        buf.mtime = st.st_mtime
        buf.size = st.st_size
        entry.mtime = buf.mtime
        entry.size = buf.size
        entry.dirty = False

    def list(self, session_id: str) -> List[dict]:
        if session_id not in self._entries:
            return []
        return [e.to_dict() for e in self._entries[session_id].values()]

    def get_visible_lines(self, session_id: str, entry: ViewportEntry) -> list[str]:
        """Return buffer lines visible at the entry's current position."""
        file_lines = self._file_lines(session_id, entry.file)
        total = len(file_lines)
        # entry.start_line is 1-based; file_lines is 0-based
        start = max(0, entry.start_line - 1)
        end = min(entry.end_line, total)
        return file_lines[start:end]

    def scroll(self, session_id: str, viewport_id: str, lines: int) -> ViewportEntry:
        entry = self.get_entry(session_id, viewport_id)
        file_lines = self._file_lines(session_id, entry.file)
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
        file_lines = self._file_lines(session_id, entry.file)
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

    def set_autosave(self, session_id: str, viewport_id: str, enabled: bool) -> ViewportEntry:
        entry = self.get_entry(session_id, viewport_id)
        if enabled and not entry.autosave and entry.dirty:
            self._flush_entry(session_id, entry)
        entry.autosave = enabled
        return entry

    def set_display_mode(self, session_id: str, viewport_id: str, mode: str) -> ViewportEntry:
        entry = self.get_entry(session_id, viewport_id)
        if mode not in ("hide", "show"):
            raise InvalidDisplayModeError(mode)
        entry.display_mode = mode
        return entry

    def destroy_session(self, session_id: str) -> None:
        """Remove a session and all its state. Dirty buffers are discarded (zero saves)."""
        self._entries.pop(session_id, None)
        self._buffers.pop(session_id, None)

    def get_entry(self, session_id: str, viewport_id: str) -> ViewportEntry:
        if session_id not in self._entries:
            raise SessionNotFoundError(session_id)
        if viewport_id not in self._entries[session_id]:
            raise ViewportNotFoundError(viewport_id)
        return self._entries[session_id][viewport_id]

    def get_line_ending(self, session_id: str, file_path: str) -> str:
        if session_id not in self.line_endings or file_path not in self.line_endings[session_id]:
            return "\n"
        return self.line_endings[session_id][file_path]

    def check_conflict(self, file_path: str, stored_mtime: Optional[float], stored_size: Optional[int]) -> Optional[dict]:
        resolved_path, _ = _resolve_path(file_path, self.project_root)
        if not os.path.isfile(resolved_path):
            return {"file": file_path, "missing": True}
        st = os.stat(resolved_path)
        warnings: Dict[str, object] = {}
        if stored_mtime is not None and abs(st.st_mtime - stored_mtime) > 0.01:
            warnings["mtime"] = {"stored": stored_mtime, "current": st.st_mtime}
        if stored_size is not None and st.st_size != stored_size:
            warnings["size"] = {"stored": stored_size, "current": st.st_size}
        if warnings:
            return {"file": file_path, "conflicts": warnings}
        return None

    def format_conflict_warning(self, warning: dict) -> str:
        if warning.get("missing"):
            return f"conflict:\n  file: {warning['file']}\n  status: file no longer exists on disk"
        lines = [
            "conflict:",
            f"  file: {warning['file']}",
        ]
        for key, vals in warning.get("conflicts", {}).items():
            lines.append(f"  {key}:")
            lines.append(f"    stored: {vals['stored']}")
            lines.append(f"    current: {vals['current']}")
        return "\n".join(lines)
