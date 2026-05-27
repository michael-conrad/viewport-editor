# SPDX-FileCopyrightText: 2026 Michael Conrad
# SPDX-License-Identifier: MIT
# Provenance: AI-generated
"""Unified diff generation for viewport-editor buffers.

Co-authored with AI: OpenCode (ollama-cloud/deepseek-v4-flash)
"""

from __future__ import annotations

import difflib


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
