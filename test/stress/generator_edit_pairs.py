# SPDX-FileCopyrightText: 2026 Michael Conrad
# SPDX-License-Identifier: MIT
# Provenance: AI-generated
"""Generator for edit pair stress test sequences.

Produces all ordered pairs of edit operations at overlapping, non-overlapping,
and same-position variants, plus high-risk triple chains.

Co-authored with AI: OpenCode (deepseek-v4-flash)
"""

from __future__ import annotations

from typing import Literal

from test.stress.models import ContentCheck, Sequence, ToolCall

SINGLE_SEED = "line 1\nline 2\nline 3\nline 4\nline 5\n"
MULTI_SEED = (
    "line 1\nline 2\nline 3\nline 4\nline 5\nline 6\nline 7\nline 8\nline 9\nline 10\n"
)

OPERATIONS = [
    "replace",
    "replace-all",
    "insert-lines",
    "delete-lines",
    "swap-lines",
    "move-lines",
]

Position = Literal["non-overlapping", "overlapping", "same_position"]
ContentSize = Literal["single_line", "multi_line"]


def _make_seed(size: ContentSize) -> str:
    return SINGLE_SEED if size == "single_line" else MULTI_SEED


def _total_lines(size: ContentSize) -> int:
    return 5 if size == "single_line" else 10


def _make_tool_call(
    op: str, region_start: int, region_end: int, size: ContentSize
) -> ToolCall:
    """Build a ToolCall for an edit operation targeting a region.

    Params are generated so that operations at the same region interact:
    - replace: swaps 'line N' text inside the region
    - replace-all: changes ALL occurrences of a word in the region
    - insert-lines: inserts marker lines at region start
    - delete-lines: deletes the region
    - swap-lines: swaps two halves of the region
    - move-lines: moves the region elsewhere
    """
    total = _total_lines(size)

    if op == "replace":
        old = f"line {region_start}"
        new = f"REPLACED_{region_start}"
        return ToolCall(
            tool="edit",
            params={
                "action": "replace",
                "viewport_id": "",
                "old_text": old,
                "new_text": new,
            },
        )
    elif op == "replace-all":
        return ToolCall(
            tool="edit",
            params={
                "action": "replace-all",
                "viewport_id": "",
                "old_text": "line",
                "new_text": "ROW",
            },
        )
    elif op == "insert-lines":
        return ToolCall(
            tool="edit",
            params={
                "action": "insert-lines",
                "viewport_id": "",
                "line_start": region_start,
                "lines": [f"INSERTED_{region_start}"],
            },
        )
    elif op == "delete-lines":
        return ToolCall(
            tool="edit",
            params={
                "action": "delete-lines",
                "viewport_id": "",
                "line_start": region_start,
                "line_end": region_end,
            },
        )
    elif op == "swap-lines":
        mid = (region_start + region_end) // 2
        return ToolCall(
            tool="edit",
            params={
                "action": "swap-lines",
                "viewport_id": "",
                "line_start": region_start,
                "line_end": mid,
                "target_line_start": mid + 1,
                "target_line_end": region_end,
            },
        )
    elif op == "move-lines":
        target = total  # move to end of file
        return ToolCall(
            tool="edit",
            params={
                "action": "move-lines",
                "viewport_id": "",
                "line_start": region_start,
                "line_end": region_end,
                "target_line": target,
            },
        )
    else:
        raise ValueError(f"unknown operation: {op}")


def _region_a(position: Position, size: ContentSize) -> tuple[int, int]:
    if position == "non-overlapping":
        return (1, 2)
    elif position == "overlapping":
        return (2, 4)
    else:  # same_position
        return (2, 3)


def _region_b(position: Position, size: ContentSize) -> tuple[int, int]:
    if position == "non-overlapping":
        return (4, 5) if size == "single_line" else (4, 5)
    elif position == "overlapping":
        return (3, 5)
    else:  # same_position
        return (2, 3)


def _expected_checks(
    id_str: str, ops: list[str], position: Position, size: ContentSize
) -> list[ContentCheck]:
    """Generate expected content checks based on the operation sequence.

    These are basic sanity checks — precise correctness is verified
    by the audit pass.
    """
    checks: list[ContentCheck] = []
    last_op = ops[-1]
    # If last operation deletes every remaining line, file could be short
    # But we don't know the exact line count after prior ops, so skip line_count checks
    if last_op == "insert-lines":
        checks.append(ContentCheck(type="contains", target="INSERTED"))
    elif last_op in ("replace",):
        checks.append(ContentCheck(type="contains", target="REPLACED"))
    return checks


def _build_sequence(
    seq_id: str,
    ops: list[str],
    position: Position,
    size: ContentSize,
    description: str,
) -> Sequence:
    seed = _make_seed(size)
    steps: list[ToolCall] = []
    for i, op in enumerate(ops):
        if i == 0:
            r_start, r_end = _region_a(position, size)
        else:
            r_start, r_end = _region_b(position, size)
        steps.append(_make_tool_call(op, r_start, r_end, size))

    checks = _expected_checks(seq_id, ops, position, size)
    save_ok = ops[-1] not in ("delete-lines",) or position != "same_position"
    return Sequence(
        id=seq_id,
        category="edit_pairs",
        seed_content=seed,
        steps=steps,
        expected_save_success=save_ok,
        expected_content_checks=checks,
        description=description,
    )


def generate_edit_pair_sequences(
    density: str = "dense",
) -> list[Sequence]:
    """Generate edit pair stress test sequences.

    Args:
        density: "sparse" (~40 seqs) or "dense" (~266 seqs).

    Returns:
        List of Sequence objects.
    """
    sequences: list[Sequence] = []
    seq_counter = 0

    positions: list[Position]
    sizes: list[ContentSize]

    if density == "sparse":
        positions = ["non-overlapping", "same_position"]
        sizes = ["single_line"]
    else:
        positions = ["non-overlapping", "overlapping", "same_position"]
        sizes = ["single_line", "multi_line"]

    # Double operations: every ordered pair
    for op_a in OPERATIONS:
        for op_b in OPERATIONS:
            for position in positions:
                for size in sizes:
                    seq_counter += 1
                    seq_id = f"edit-pair-{seq_counter:04d}"
                    desc = f"{op_a} -> {op_b} ({position}, {size})"
                    sequences.append(
                        _build_sequence(seq_id, [op_a, op_b], position, size, desc)
                    )

    # Triple chain high-risk sequences
    triple_chains = [
        ("replace", "replace", "replace"),
        ("delete-lines", "insert-lines", "delete-lines"),
        ("move-lines", "replace", "move-lines"),
        ("swap-lines", "replace-all", "swap-lines"),
        ("replace-all", "delete-lines", "insert-lines"),
        ("insert-lines", "insert-lines", "insert-lines"),
    ]
    for chain in triple_chains:
        for position in positions:
            for size in sizes:
                seq_counter += 1
                seq_id = f"edit-pair-{seq_counter:04d}"
                op_names = " -> ".join(chain)
                desc = f"{op_names} ({position}, {size}) [triple]"
                sequences.append(
                    _build_sequence(seq_id, list(chain), position, size, desc)
                )

    return sequences
