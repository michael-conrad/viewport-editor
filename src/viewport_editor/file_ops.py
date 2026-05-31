# SPDX-FileCopyrightText: 2026 Michael Conrad
# SPDX-License-Identifier: MIT
# Provenance: AI-generated
"""File operation helpers for viewport-editor.

Co-authored with AI: OpenCode (deepseek-v4-flash)
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple

from .buffer import Buffer
from .exceptions import AbsolutePathError, PathEscapeError

if TYPE_CHECKING:
    from .viewport import ViewportEntry


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
    present = {k: v for k, v in counts.items() if v > 0}
    if not present:
        return "\n"
    dominant = max(present, key=present.get)
    return dominant.decode("ascii")


def _read_file_lines(
    resolved_path: str,
) -> Tuple[List[str], Optional[float], Optional[int]]:
    st = os.stat(resolved_path)
    mtime = st.st_mtime
    size = st.st_size
    with open(resolved_path, "r") as f:
        content = f.read()
    lines = content.splitlines(keepends=True)
    return lines, mtime, size


def flush_entry(buffer: Buffer, entry: "ViewportEntry", project_root: str) -> None:
    """Atomically write buffer content to disk and update entry metadata."""
    resolved_path, _ = _resolve_path(entry.file, project_root)
    tmp = resolved_path + ".tmp"
    try:
        with open(tmp, "w") as f:
            f.write(buffer.content)
        os.replace(tmp, resolved_path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise
    st = os.stat(resolved_path)
    buffer.mtime = st.st_mtime
    buffer.size = st.st_size
    entry.mtime = buffer.mtime
    entry.size = buffer.size
    entry.dirty = False


def discard_buffer_changes(
    buffer: Buffer, entry: "ViewportEntry", project_root: str
) -> None:
    """Re-read file from disk into buffer, clearing dirty state."""
    resolved_path, _ = _resolve_path(entry.file, project_root)
    lines, mtime, size = _read_file_lines(resolved_path)
    buffer.content = "".join(lines)
    buffer.mtime = mtime
    buffer.size = size
    entry.dirty = False
    entry.mtime = mtime
    entry.size = size


def check_conflict(
    file_path: str,
    project_root: str,
    stored_mtime: Optional[float],
    stored_size: Optional[int],
) -> Optional[dict]:
    """Check whether the file on disk has changed since the last snapshot."""
    resolved_path, _ = _resolve_path(file_path, project_root)
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


def format_conflict_warning(warning: dict) -> str:
    """Format a conflict dict into a YAML warning string."""
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
