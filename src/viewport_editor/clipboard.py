# SPDX-FileCopyrightText: 2026 Michael Conrad
# SPDX-License-Identifier: MIT
# Provenance: AI-generated
"""Clipboard data model and pure operations for viewport-editor.

Co-authored with AI: OpenCode (ollama-cloud/glm-5.1)
"""

from __future__ import annotations

import time
from dataclasses import dataclass


@dataclass
class ClipboardEntry:
    content: list[str]
    source_file: str
    line_range: tuple[int, int]
    timestamp: float
    line_ending: str


def apply_copy(
    file_lines: list[str],
    line_start: int,
    line_end: int,
    source_file: str,
    line_ending: str,
) -> tuple[list[str], ClipboardEntry]:
    idx_start = max(0, line_start - 1)
    idx_end = min(line_end, len(file_lines))
    copied = file_lines[idx_start:idx_end]
    entry = ClipboardEntry(
        content=copied,
        source_file=source_file,
        line_range=(line_start, line_end),
        timestamp=time.time(),
        line_ending=line_ending,
    )
    return copied, entry


def apply_cut(
    file_lines: list[str],
    line_start: int,
    line_end: int,
    source_file: str,
    line_ending: str,
) -> tuple[list[str], ClipboardEntry]:
    copied, entry = apply_copy(
        file_lines, line_start, line_end, source_file, line_ending
    )
    idx_start = max(0, line_start - 1)
    idx_end = min(line_end, len(file_lines))
    remaining = file_lines[:idx_start] + file_lines[idx_end:]
    return remaining, entry


def apply_paste(
    file_lines: list[str],
    target_line: int,
    clipboard_lines: list[str],
    line_ending: str,
) -> list[str]:
    """Insert clipboard lines before target_line (insert-before semantics).

    target_line is 1-based. Lines are inserted before line at target_line.
    Returns new file_lines with clipboard content inserted. Does NOT clear clipboard.
    """
    insert_idx = max(0, min(target_line - 1, len(file_lines)))
    normalized = [
        ln if ln.endswith(line_ending) else ln + line_ending for ln in clipboard_lines
    ]
    return file_lines[:insert_idx] + normalized + file_lines[insert_idx:]
