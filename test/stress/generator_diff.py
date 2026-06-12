# SPDX-FileCopyrightText: 2026 Michael Conrad
# SPDX-License-Identifier: MIT
# Provenance: AI-generated
"""Generator for diff apply stress test sequences.

Co-authored with AI: OpenCode (deepseek-v4-flash)
"""

from __future__ import annotations

from test.stress.models import Sequence, ToolCall

DIFF_SEED = "line 1\nline 2\nline 3\nline 4\nline 5\nline 6\nline 7\nline 8\n"


def generate_diff_sequences() -> list[Sequence]:
    return [
        # Single hunk, middle of file
        Sequence(
            id="diff-001",
            category="diff",
            seed_content=DIFF_SEED,
            steps=[
                ToolCall(
                    tool="diff",
                    params={
                        "action": "apply",
                        "viewport_id": "",
                        "patch": (
                            "--- a/test.txt\n+++ b/test.txt\n"
                            "@@ -3,3 +3,3 @@\n line 3\n-line 4\n+MODIFIED_4\n line 5\n"
                        ),
                    },
                ),
            ],
            expected_save_success=True,
            description="single hunk, middle of file",
        ),
        # Multi-hunk, non-overlapping
        Sequence(
            id="diff-002",
            category="diff",
            seed_content=DIFF_SEED,
            steps=[
                ToolCall(
                    tool="diff",
                    params={
                        "action": "apply",
                        "viewport_id": "",
                        "patch": (
                            "--- a/test.txt\n+++ b/test.txt\n"
                            "@@ -1,2 +1,2 @@\n-line 1\n+FIRST\n line 2\n"
                            "@@ -7,2 +7,2 @@\n line 7\n-line 8\n+LAST\n"
                        ),
                    },
                ),
            ],
            expected_save_success=True,
            description="multi-hunk, non-overlapping — offset tracking across hunks",
        ),
        # Multi-hunk with fuzzy context matching (whitespace tolerance)
        Sequence(
            id="diff-003",
            category="diff",
            seed_content=DIFF_SEED,
            steps=[
                ToolCall(
                    tool="diff",
                    params={
                        "action": "apply",
                        "viewport_id": "",
                        "patch": (
                            "--- a/test.txt\n+++ b/test.txt\n"
                            "@@ -4,3 +4,3 @@\n line 4\n-line 5\n+CHANGED_5\n line 6\n"
                        ),
                    },
                ),
            ],
            expected_save_success=True,
            description="single hunk with fuzzy context matching",
        ),
        # Hunk at line 1 (beginning boundary)
        Sequence(
            id="diff-004",
            category="diff",
            seed_content=DIFF_SEED,
            steps=[
                ToolCall(
                    tool="diff",
                    params={
                        "action": "apply",
                        "viewport_id": "",
                        "patch": (
                            "--- a/test.txt\n+++ b/test.txt\n"
                            "@@ -1,2 +1,2 @@\n-line 1\n+START\n line 2\n"
                        ),
                    },
                ),
            ],
            expected_save_success=True,
            description="hunk at line 1 — beginning boundary",
        ),
        # Hunk at last line (end boundary)
        Sequence(
            id="diff-005",
            category="diff",
            seed_content=DIFF_SEED,
            steps=[
                ToolCall(
                    tool="diff",
                    params={
                        "action": "apply",
                        "viewport_id": "",
                        "patch": (
                            "--- a/test.txt\n+++ b/test.txt\n"
                            "@@ -7,2 +7,2 @@\n line 7\n-line 8\n+END\n"
                        ),
                    },
                ),
            ],
            expected_save_success=True,
            description="hunk at last line — end boundary",
        ),
        # Overlapping hunks — intentionally invalid, expect error
        Sequence(
            id="diff-006",
            category="diff",
            seed_content=DIFF_SEED,
            steps=[
                ToolCall(
                    tool="diff",
                    params={
                        "action": "apply",
                        "viewport_id": "",
                        "patch": (
                            "--- a/test.txt\n+++ b/test.txt\n"
                            "@@ -2,4 +2,4 @@\n line 2\n-line 3\n+X\n line 4\n"
                            "@@ -3,4 +3,4 @@\n-X\n+Z\n line 4\n line 5\n"
                        ),
                    },
                ),
            ],
            expected_save_success=False,
            description="overlapping hunks — expected error",
        ),
        # Apply on unsaved viewport (autosave gate)
        Sequence(
            id="diff-007",
            category="diff",
            seed_content=DIFF_SEED,
            steps=[
                ToolCall(
                    tool="edit",
                    params={
                        "action": "replace",
                        "viewport_id": "",
                        "old_text": "line 1",
                        "new_text": "EDITED_1",
                    },
                ),
                ToolCall(
                    tool="diff",
                    params={
                        "action": "apply",
                        "viewport_id": "",
                        "patch": (
                            "--- a/test.txt\n+++ b/test.txt\n"
                            "@@ -3,2 +3,2 @@\n line 3\n-line 4\n+PATCHED_4\n"
                        ),
                    },
                ),
            ],
            expected_save_success=True,
            description="apply diff on already-edited buffer — accumulated changes",
        ),
    ]
