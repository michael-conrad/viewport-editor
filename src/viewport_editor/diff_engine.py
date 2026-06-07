# SPDX-FileCopyrightText: 2026 Michael Conrad
# SPDX-License-Identifier: MIT
# Provenance: AI-generated
"""Unified diff generation and application for viewport-editor buffers.

Co-authored with AI: OpenCode (ollama-cloud/deepseek-v4-flash)
"""

from __future__ import annotations

import difflib
import re
from dataclasses import dataclass, field
from typing import List, Optional

from .exceptions import DiffApplyError


def generate_unified_diff(original: str, modified: str, file_path: str = "") -> str:
    """Return a standard unified diff between original and modified strings.

    Uses Python's difflib.unified_diff internally. Returns empty string
    when there are no differences.
    """
    if original == modified:
        return ""

    orig_lines = original.splitlines(keepends=True)
    mod_lines = modified.splitlines(keepends=True)

    diff_lines = list(
        difflib.unified_diff(
            orig_lines,
            mod_lines,
            fromfile=file_path or "original",
            tofile=file_path or "modified",
        )
    )
    return "".join(diff_lines)


@dataclass
class DiffHunk:
    old_start: int
    old_count: int
    new_start: int
    new_count: int
    lines: List[str] = field(default_factory=list)


_HUNK_RE = re.compile(r"^@@\s+-(\d+)(?:,(\d+))?\s+\+(\d+)(?:,(\d+))?\s+@@")


def parse_unified_diff(patch: str) -> List[DiffHunk]:
    """Parse a unified diff string into a list of DiffHunk objects.

    Each hunk contains its line range metadata and the diff lines
    (context/removed/added) within that hunk.
    """
    hunks: List[DiffHunk] = []
    current_hunk: Optional[DiffHunk] = None

    for line in patch.splitlines(keepends=True):
        m = _HUNK_RE.match(line)
        if m:
            if current_hunk is not None:
                hunks.append(current_hunk)
            old_start = int(m.group(1))
            old_count = int(m.group(2)) if m.group(2) is not None else 1
            new_start = int(m.group(3))
            new_count = int(m.group(4)) if m.group(4) is not None else 1
            current_hunk = DiffHunk(
                old_start=old_start,
                old_count=old_count,
                new_start=new_start,
                new_count=new_count,
            )
            continue

        if line.startswith("---") or line.startswith("+++"):
            continue

        if current_hunk is not None and (
            line.startswith(" ") or line.startswith("+") or line.startswith("-")
        ):
            current_hunk.lines.append(line)

    if current_hunk is not None:
        hunks.append(current_hunk)

    return hunks


def _strip_line_ending(s: str) -> str:
    return s.rstrip("\n").rstrip("\r")


def apply_diff_to_content(content: str, patch: str) -> str:
    """Apply a unified diff patch to content string.

    Uses fuzzy context matching: context lines from the patch are matched
    by stripped content against stripped buffer lines, allowing for whitespace
    differences.

    Returns the new content string.
    Raises DiffApplyError if context lines cannot be matched.
    """
    hunks = parse_unified_diff(patch)
    if not hunks:
        raise DiffApplyError("no hunks found in patch")

    lines = content.splitlines(keepends=True)
    offset = 0

    for hunk in hunks:
        old_lines: List[str] = []
        for dl in hunk.lines:
            if dl.startswith(" "):
                old_lines.append(dl[1:])
            elif dl.startswith("-"):
                old_lines.append(dl[1:])

        search_start = max(0, hunk.old_start - 1 + offset - 2)
        match_pos = _find_hunk_position(lines, old_lines, search_start)

        if match_pos is None:
            match_pos = _find_hunk_position(lines, old_lines, 0)

        if match_pos is None:
            ctx_preview = [_strip_line_ending(ln) for ln in old_lines[:3]]
            raise DiffApplyError(
                f"cannot match context lines at hunk @@ -{hunk.old_start},{hunk.old_count}"
                f" +{hunk.new_start},{hunk.new_count} @@: "
                f"no match for {ctx_preview!r}"
            )

        new_lines_for_hunk: List[str] = []
        for dl in hunk.lines:
            if dl.startswith(" "):
                buf_idx = match_pos + sum(
                    1
                    for x in hunk.lines[: hunk.lines.index(dl)]
                    if x.startswith(" ") or x.startswith("-")
                )
                if buf_idx < len(lines):
                    new_lines_for_hunk.append(lines[buf_idx])
                else:
                    new_lines_for_hunk.append(dl[1:])
            elif dl.startswith("+"):
                line_text = dl[1:]
                if not line_text.endswith("\n") and not line_text.endswith("\r"):
                    le = _detect_line_ending(lines)
                    line_text += le
                new_lines_for_hunk.append(line_text)
            elif dl.startswith("-"):
                pass

        old_count = sum(
            1 for dl in hunk.lines if dl.startswith(" ") or dl.startswith("-")
        )
        lines[match_pos : match_pos + old_count] = new_lines_for_hunk
        offset += len(new_lines_for_hunk) - old_count

    return "".join(lines)


def _detect_line_ending(lines: List[str]) -> str:
    if not lines:
        return "\n"
    first = lines[0]
    if first.endswith("\r\n"):
        return "\r\n"
    if first.endswith("\r"):
        return "\r"
    return "\n"


def _find_hunk_position(
    lines: List[str],
    context_lines: List[str],
    start: int,
) -> Optional[int]:
    """Find the position in lines where the context lines match (fuzzy).

    Strips leading whitespace from both sides for fuzzy matching.
    Returns 0-based line index or None if no match found.
    """
    if not context_lines:
        return start if start < len(lines) else None

    for pos in range(max(0, start), len(lines)):
        if _context_matches(lines, pos, context_lines):
            return pos

    return None


def _context_matches(
    lines: List[str],
    pos: int,
    context_lines: List[str],
) -> bool:
    """Check if context lines match starting at position pos (fuzzy)."""
    ctx_idx = 0
    line_idx = pos

    while ctx_idx < len(context_lines) and line_idx < len(lines):
        ctx_stripped = context_lines[ctx_idx].strip()
        line_stripped = _strip_line_ending(lines[line_idx]).strip()

        if ctx_stripped == line_stripped:
            ctx_idx += 1
            line_idx += 1
        else:
            return False

    return ctx_idx == len(context_lines)
