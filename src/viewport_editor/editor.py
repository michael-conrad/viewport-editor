# SPDX-FileCopyrightText: 2026 Michael Conrad
# SPDX-License-Identifier: MIT
# Provenance: AI-generated
"""Pure edit operations for viewport-editor.

All functions operate on raw string content and return (new_content, result_dict).
No side effects — callers manage buffer storage and autosave.

Co-authored with AI: OpenCode (deepseek-v4-flash)
"""

from __future__ import annotations

from typing import List, Tuple

from .exceptions import EditTargetNotFoundError, LineRangeError


def apply_edit(content: str, old_text: str, new_text: str) -> Tuple[str, dict]:
    """Single replace: replace first occurrence of old_text with new_text."""
    count = content.count(old_text)
    if count == 0:
        raise EditTargetNotFoundError(old_text)
    new_content = content.replace(old_text, new_text, 1)
    line_idx = new_content[: new_content.index(new_text)].splitlines(keepends=True)
    snippet_line = len(line_idx)
    lines = new_content.splitlines(keepends=True)
    snippet = (
        lines[snippet_line - 1].rstrip("\n").rstrip("\r")
        if snippet_line <= len(lines)
        else ""
    )
    return new_content, {"found": True, "count": count, "snippet": snippet}


def apply_replace_all(content: str, old_text: str, new_text: str) -> Tuple[str, dict]:
    """Replace all occurrences of old_text with new_text."""
    count = content.count(old_text)
    if count == 0:
        raise EditTargetNotFoundError(old_text)
    new_content = content.replace(old_text, new_text)
    snippet_start = new_content[:50].rstrip("\n").rstrip("\r")
    return new_content, {"found": True, "count": count, "snippet": snippet_start}


def apply_insert_lines(
    content: str, line_start: int, lines: List[str], line_ending: str
) -> Tuple[str, dict]:
    """Insert lines at the specified 1-based line position."""
    file_lines = content.splitlines(keepends=True)
    total = len(file_lines)
    if line_start < 1 or line_start > max(total + 1, 1):
        raise LineRangeError(f"line_start {line_start} out of range (1-{total})")
    new_lines = [ln if ln.endswith(line_ending) else ln + line_ending for ln in lines]
    file_lines[line_start:line_start] = new_lines
    new_content = "".join(file_lines)
    return new_content, {
        "line_start": line_start + 1,
        "line_end": line_start + len(new_lines),
        "count": len(new_lines),
    }


def apply_delete_lines(
    content: str, line_start: int, line_end: int
) -> Tuple[str, dict]:
    """Delete lines in the range [line_start, line_end] (1-based)."""
    file_lines = content.splitlines(keepends=True)
    total = len(file_lines)
    if line_start < 1 or line_end > total or line_start > line_end:
        raise LineRangeError(
            f"invalid line range: {line_start}-{line_end} (total {total})"
        )
    del file_lines[line_start - 1 : line_end]
    new_content = "".join(file_lines)
    return new_content, {
        "line_start": line_start,
        "line_count": line_end - line_start + 1,
    }


def apply_swap_lines(
    content: str,
    line_start: int,
    line_end: int,
    target_line_start: int,
    target_line_end: int,
) -> Tuple[str, dict]:
    """Swap two line ranges."""
    file_lines = content.splitlines(keepends=True)
    total = len(file_lines)
    for a, b in [(line_start, line_end), (target_line_start, target_line_end)]:
        if a < 1 or b > total or a > b:
            raise LineRangeError(f"invalid range {a}-{b} (total {total})")
    range_a = file_lines[line_start - 1 : line_end]
    range_b = file_lines[target_line_start - 1 : target_line_end]
    file_lines[line_start - 1 : line_end] = range_b
    file_lines[target_line_start - 1 : target_line_end] = range_a
    new_content = "".join(file_lines)
    return new_content, {"swapped": True}


def apply_move_lines(
    content: str,
    line_start: int,
    line_end: int,
    target_line: int,
) -> Tuple[str, dict]:
    """Move lines in range [line_start, line_end] to target_line position."""
    file_lines = content.splitlines(keepends=True)
    total = len(file_lines)
    if line_start < 1 or line_end > total or line_start > line_end:
        raise LineRangeError(f"invalid range {line_start}-{line_end} (total {total})")
    if target_line < 1 or target_line > total + 1:
        raise LineRangeError(f"invalid target_line {target_line} (total {total})")
    moved = file_lines[line_start - 1 : line_end]
    del file_lines[line_start - 1 : line_end]
    if target_line > line_start:
        adjusted_target = target_line - len(moved)
    else:
        adjusted_target = target_line
    file_lines[adjusted_target - 1 : adjusted_target - 1] = moved
    new_content = "".join(file_lines)
    return new_content, {"moved": True}
