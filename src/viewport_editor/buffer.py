# SPDX-FileCopyrightText: 2026 Michael Conrad
# SPDX-License-Identifier: MIT
# Provenance: AI-generated
"""Buffer model and BufferManager for viewport-editor.

Co-authored with AI: OpenCode (deepseek-v4-flash)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

from .diff_engine import generate_unified_diff


@dataclass
class Buffer:
    path: str
    content: str
    mtime: Optional[float]
    size: Optional[int]


class BufferManager:
    """Manages in-memory line buffers per session and file path."""

    def __init__(self) -> None:
        self._buffers: Dict[str, Dict[str, Buffer]] = {}

    def get_or_create(
        self, session_id: str, file_path: str, resolved_path: str
    ) -> Buffer:
        from .file_ops import _read_file_lines

        if session_id not in self._buffers:
            self._buffers[session_id] = {}
        if file_path not in self._buffers[session_id]:
            lines, mtime, size = _read_file_lines(resolved_path)
            content = "".join(lines)
            self._buffers[session_id][file_path] = Buffer(
                path=file_path, content=content, mtime=mtime, size=size
            )
        return self._buffers[session_id][file_path]

    def get_lines(self, session_id: str, file_path: str) -> List[str]:
        return self._buffers[session_id][file_path].content.splitlines(keepends=True)

    def get_raw_content(self, session_id: str, file_path: str) -> str:
        return self._buffers[session_id][file_path].content

    def set_content(self, session_id: str, file_path: str, content: str) -> None:
        self._buffers[session_id][file_path].content = content

    def refresh_if_changed(
        self, session_id: str, file_path: str, resolved_path: str
    ) -> None:
        from .file_ops import _read_file_lines

        if session_id in self._buffers and file_path in self._buffers[session_id]:
            lines, mtime, size = _read_file_lines(resolved_path)
            buf = self._buffers[session_id][file_path]
            buf.content = "".join(lines)
            buf.mtime = mtime
            buf.size = size

    def get_diff(self, session_id: str, file_path: str, project_root: str) -> str:
        from .file_ops import _read_file_lines, _resolve_path

        buf = self._buffers[session_id][file_path]
        resolved_path, _ = _resolve_path(file_path, project_root)
        lines, _, _ = _read_file_lines(resolved_path)
        disk_content = "".join(lines)
        return generate_unified_diff(disk_content, buf.content, file_path)

    def get_buffer_ref(
        self, session_id: str, file_path: str
    ) -> Buffer:
        return self._buffers[session_id][file_path]

    def destroy_session(self, session_id: str) -> None:
        self._buffers.pop(session_id, None)
