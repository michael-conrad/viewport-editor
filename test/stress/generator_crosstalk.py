# SPDX-FileCopyrightText: 2026 Michael Conrad
# SPDX-License-Identifier: MIT
# Provenance: AI-generated
"""Generator for crosstalk stress test sequences (multi-viewport, multi-session).

Co-authored with AI: OpenCode (deepseek-v4-flash)
"""

from __future__ import annotations

from test.stress.models import Sequence, ToolCall

CROSSTALK_SEED = "alpha\nbeta\ngamma\ndelta\nepsilon\n"


def generate_crosstalk_sequences() -> list[Sequence]:
    return [
        # Same file in 2 viewports, edit both, save both
        Sequence(
            id="crosstalk-001",
            category="crosstalk",
            seed_content=CROSSTALK_SEED,
            steps=[
                ToolCall(
                    tool="viewport",
                    params={
                        "action": "open",
                        "file_path": "file_a.txt",
                        "autosave": False,
                    },
                ),
                ToolCall(
                    tool="viewport",
                    params={
                        "action": "open",
                        "file_path": "file_a.txt",
                        "autosave": False,
                    },
                ),
                ToolCall(tool="viewport", params={"action": "list"}),
            ],
            expected_save_success=True,
            description="open same file in 2 viewports — verify both appear in list",
        ),
        # Open -> close -> reopen same file
        Sequence(
            id="crosstalk-002",
            category="crosstalk",
            seed_content=CROSSTALK_SEED,
            steps=[
                ToolCall(
                    tool="viewport",
                    params={
                        "action": "open",
                        "file_path": "file_b.txt",
                        "autosave": False,
                    },
                ),
                ToolCall(
                    tool="viewport", params={"action": "close", "viewport_id": ""}
                ),
                ToolCall(
                    tool="viewport",
                    params={
                        "action": "open",
                        "file_path": "file_b.txt",
                        "autosave": False,
                    },
                ),
            ],
            expected_save_success=True,
            description="open -> close -> reopen same file — buffer cleanup",
        ),
    ]
