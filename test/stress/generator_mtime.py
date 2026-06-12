# SPDX-FileCopyrightText: 2026 Michael Conrad
# SPDX-License-Identifier: MIT
# Provenance: AI-generated
"""Generator for mtime/cross-session conflict stress test sequences.

Co-authored with AI: OpenCode (deepseek-v4-flash)
"""

from __future__ import annotations

from test.stress.models import Sequence, ToolCall

MTIME_SEED = "original line 1\noriginal line 2\noriginal line 3\n"


def generate_mtime_sequences() -> list[Sequence]:
    return [
        # Open -> externally modify -> open again (refresh_if_changed)
        Sequence(
            id="mtime-001",
            category="mtime",
            seed_content=MTIME_SEED,
            steps=[
                ToolCall(
                    tool="viewport",
                    params={
                        "action": "open",
                        "file_path": "mtime_file.txt",
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
                        "file_path": "mtime_file.txt",
                        "autosave": False,
                    },
                ),
            ],
            expected_save_success=True,
            description="open -> close -> reopen — buffer refresh",
        ),
        # Open -> externally modify -> save (no force) — mtime conflict
        Sequence(
            id="mtime-002",
            category="mtime",
            seed_content=MTIME_SEED,
            steps=[
                ToolCall(
                    tool="viewport",
                    params={
                        "action": "open",
                        "file_path": "mtime_file2.txt",
                        "autosave": False,
                    },
                ),
                # External modify happens in runner between steps
                ToolCall(
                    tool="file",
                    params={
                        "action": "save",
                        "viewport_id": "",
                        "file_path": "mtime_file2.txt",
                    },
                ),
            ],
            expected_save_success=False,
            description="open then external modify then save — expected mtime conflict",
        ),
        # Open -> externally modify -> save (force=true) — force override
        Sequence(
            id="mtime-003",
            category="mtime",
            seed_content=MTIME_SEED,
            steps=[
                ToolCall(
                    tool="viewport",
                    params={
                        "action": "open",
                        "file_path": "mtime_file3.txt",
                        "autosave": False,
                    },
                ),
                # External modify in runner
                ToolCall(
                    tool="file",
                    params={
                        "action": "save",
                        "viewport_id": "",
                        "file_path": "mtime_file3.txt",
                        "force": True,
                    },
                ),
            ],
            expected_save_success=True,
            description="open -> external modify -> force save — override conflict",
        ),
    ]
