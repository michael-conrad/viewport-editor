# SPDX-FileCopyrightText: 2026 Michael Conrad
# SPDX-License-Identifier: MIT
# Provenance: AI-generated
"""Generator for clipboard stress test sequences.

Co-authored with AI: OpenCode (deepseek-v4-flash)
"""

from __future__ import annotations

from test.stress.models import Sequence, ToolCall

CLIPBOARD_SEED = "alpha\nbeta\ngamma\ndelta\nepsilon\nzeta\neta\ntheta\n"


def generate_clipboard_sequences() -> list[Sequence]:
    return [
        # copy(A) -> edit -> paste(B) — clipboard retains original through edits
        Sequence(
            id="clipboard-001",
            category="clipboard",
            seed_content=CLIPBOARD_SEED,
            steps=[
                ToolCall(
                    tool="clipboard",
                    params={
                        "action": "copy",
                        "viewport_id": "",
                        "line_start": 1,
                        "line_end": 2,
                    },
                ),
                ToolCall(
                    tool="edit",
                    params={
                        "action": "replace",
                        "viewport_id": "",
                        "old_text": "gamma",
                        "new_text": "GAMMA",
                    },
                ),
                ToolCall(
                    tool="clipboard",
                    params={"action": "paste", "viewport_id": "", "target_line": 5},
                ),
            ],
            expected_save_success=True,
            description="copy A then edit then paste — clipboard retains original through edits",
        ),
        # cut(range) -> paste(different position) — offset correctness
        Sequence(
            id="clipboard-002",
            category="clipboard",
            seed_content=CLIPBOARD_SEED,
            steps=[
                ToolCall(
                    tool="clipboard",
                    params={
                        "action": "cut",
                        "viewport_id": "",
                        "line_start": 2,
                        "line_end": 3,
                    },
                ),
                ToolCall(
                    tool="clipboard",
                    params={"action": "paste", "viewport_id": "", "target_line": 6},
                ),
            ],
            expected_save_success=True,
            description="cut lines 2-3 then paste at line 6 — offset correctness",
        ),
        # cut -> cut -> paste — sequential cut offset accounting
        Sequence(
            id="clipboard-003",
            category="clipboard",
            seed_content=CLIPBOARD_SEED,
            steps=[
                ToolCall(
                    tool="clipboard",
                    params={
                        "action": "cut",
                        "viewport_id": "",
                        "line_start": 1,
                        "line_end": 1,
                    },
                ),
                ToolCall(
                    tool="clipboard",
                    params={
                        "action": "cut",
                        "viewport_id": "",
                        "line_start": 2,
                        "line_end": 2,
                    },
                ),
                ToolCall(
                    tool="clipboard",
                    params={"action": "paste", "viewport_id": "", "target_line": 6},
                ),
            ],
            expected_save_success=True,
            description="cut 1 then cut 2 (offset shifted after first cut) then paste — sequential cut accounting",
        ),
        # copy -> stash -> cut -> pop -> paste — stash lifecycle
        Sequence(
            id="clipboard-004",
            category="clipboard",
            seed_content=CLIPBOARD_SEED,
            steps=[
                ToolCall(
                    tool="clipboard",
                    params={
                        "action": "copy",
                        "viewport_id": "",
                        "line_start": 1,
                        "line_end": 2,
                    },
                ),
                ToolCall(
                    tool="clipboard",
                    params={"action": "stash", "viewport_id": "", "name": "slot_a"},
                ),
                ToolCall(
                    tool="clipboard",
                    params={
                        "action": "cut",
                        "viewport_id": "",
                        "line_start": 3,
                        "line_end": 4,
                    },
                ),
                ToolCall(
                    tool="clipboard",
                    params={"action": "pop", "viewport_id": "", "name": "slot_a"},
                ),
                ToolCall(
                    tool="clipboard",
                    params={"action": "paste", "viewport_id": "", "target_line": 7},
                ),
            ],
            expected_save_success=True,
            description="copy -> stash -> cut -> pop -> paste — stash lifecycle",
        ),
        # copy -> stash -> swap -> paste — swap semantics
        Sequence(
            id="clipboard-005",
            category="clipboard",
            seed_content=CLIPBOARD_SEED,
            steps=[
                ToolCall(
                    tool="clipboard",
                    params={
                        "action": "copy",
                        "viewport_id": "",
                        "line_start": 1,
                        "line_end": 2,
                    },
                ),
                ToolCall(
                    tool="clipboard",
                    params={"action": "stash", "viewport_id": "", "name": "slot_b"},
                ),
                ToolCall(
                    tool="clipboard",
                    params={"action": "swap", "viewport_id": "", "name": "slot_b"},
                ),
                ToolCall(
                    tool="clipboard",
                    params={"action": "paste", "viewport_id": "", "target_line": 5},
                ),
            ],
            expected_save_success=True,
            description="copy -> stash -> swap -> paste — swap semantics",
        ),
        # paste with empty clipboard — error path
        Sequence(
            id="clipboard-006",
            category="clipboard",
            seed_content=CLIPBOARD_SEED,
            steps=[
                ToolCall(
                    tool="clipboard",
                    params={"action": "paste", "viewport_id": "", "target_line": 1},
                ),
            ],
            expected_save_success=False,
            description="paste with empty clipboard — expected error",
        ),
        # stash with empty clipboard — error path
        Sequence(
            id="clipboard-007",
            category="clipboard",
            seed_content=CLIPBOARD_SEED,
            steps=[
                ToolCall(
                    tool="clipboard",
                    params={"action": "stash", "viewport_id": "", "name": "slot_err"},
                ),
            ],
            expected_save_success=False,
            description="stash with empty clipboard — expected error",
        ),
        # pop nonexistent slot — error path
        Sequence(
            id="clipboard-008",
            category="clipboard",
            seed_content=CLIPBOARD_SEED,
            steps=[
                ToolCall(
                    tool="clipboard",
                    params={
                        "action": "copy",
                        "viewport_id": "",
                        "line_start": 1,
                        "line_end": 1,
                    },
                ),
                ToolCall(
                    tool="clipboard",
                    params={
                        "action": "pop",
                        "viewport_id": "",
                        "name": "nonexistent_slot",
                    },
                ),
            ],
            expected_save_success=False,
            description="pop nonexistent slot — expected error",
        ),
    ]
