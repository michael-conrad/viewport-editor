# SPDX-FileCopyrightText: 2026 Michael Conrad
# SPDX-License-Identifier: MIT
# Provenance: AI-generated
"""File operation helpers for viewport-editor.

Co-authored with AI: OpenCode (deepseek-v4-flash)
"""

from __future__ import annotations

import os
import tempfile
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple

from .buffer import Buffer

if TYPE_CHECKING:
    from .viewport import ViewportEntry


def _resolve_path(file_path: str, project_root: str) -> Tuple[str, str]:
    if file_path.startswith("/"):
        return os.path.realpath(file_path), file_path
    resolved = os.path.realpath(os.path.join(project_root, file_path))
    return resolved, file_path


def create_new_file(file_path: str, project_root: str) -> str:
    resolved_path, _ = _resolve_path(file_path, project_root)
    if os.path.exists(resolved_path):
        raise FileExistsError(f"file already exists: {file_path}")
    parent = os.path.dirname(resolved_path)
    if parent and not os.path.isdir(parent):
        os.makedirs(parent, exist_ok=True)
    with open(resolved_path, "w", newline=""):
        pass
    return resolved_path


def save_as_file(
    source_file: str,
    target_file: str,
    project_root: str,
    buffer_content: str,
    force: bool = False,
) -> str:
    resolved_target, _ = _resolve_path(target_file, project_root)
    if os.path.exists(resolved_target) and not force:
        raise FileExistsError(f"target file already exists: {target_file}")
    parent = os.path.dirname(resolved_target)
    if parent and not os.path.isdir(parent):
        os.makedirs(parent, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(resolved_target))
    try:
        with os.fdopen(fd, "w", newline="") as f:
            f.write(buffer_content)
        os.replace(tmp, resolved_target)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise
    return resolved_target


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
    dominant = max(present, key=lambda k: present[k])
    return dominant.decode("ascii")


def _read_file_lines(
    resolved_path: str,
) -> Tuple[List[str], Optional[float], Optional[int]]:
    st = os.stat(resolved_path)
    mtime = st.st_mtime
    size = st.st_size
    with open(resolved_path, "r", newline="") as f:
        content = f.read()
    lines = content.splitlines(keepends=True)
    return lines, mtime, size


def flush_entry(buffer: Buffer, entry: "ViewportEntry", project_root: str) -> None:
    """Atomically write buffer content to disk and update entry metadata."""
    resolved_path, _ = _resolve_path(entry.file, project_root)
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(resolved_path))
    try:
        with os.fdopen(fd, "w", newline="") as f:
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


def delete_file(file_path: str, project_root: str) -> str:
    """Delete a file from disk after resolving its path within the project root."""
    resolved_path, _ = _resolve_path(file_path, project_root)
    os.remove(resolved_path)
    return resolved_path


def _find_sibling_agents_md(file_path: str, project_root: str) -> str | None:
    resolved_file = os.path.realpath(file_path)
    resolved_root = os.path.realpath(project_root)
    current = os.path.dirname(resolved_file)
    while current.startswith(resolved_root + os.sep) or current == resolved_root:
        candidate = os.path.join(current, "AGENTS.md")
        if os.path.isfile(candidate):
            if os.path.realpath(candidate) == resolved_file:
                return None
            try:
                with open(candidate) as f:
                    return f.read()
            except (OSError, UnicodeDecodeError):
                return None
        if current == resolved_root:
            break
        current = os.path.dirname(current)
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
