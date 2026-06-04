# SPDX-FileCopyrightText: 2026 Michael Conrad
# SPDX-License-Identifier: MIT
# Provenance: AI-generated
"""RED test: viewport_id collision from hex(id(object()))[2:].

SC-1: Two consecutive viewport opens produce different viewport_ids.
SC-2: viewport_id follows viewport_ format with incrementing integers.

This test MUST FAIL against current code (hex(id(object()))[2:]) and
MUST PASS after the fix (itertools.count with viewport_ prefix).

Co-authored with AI: OpenCode (deepseek-v4-flash)
"""

from __future__ import annotations


def test_sc1_viewport_id_no_collision() -> None:
    """SC-1: Two consecutive viewport opens produce different viewport_ids.

    RED: current hex(id(object()))[2:] produces duplicates because the
    throwaway object() is immediately GC'd and the memory address is reused.
    """
    from viewport_editor.viewport import ViewportEntry

    ids: list[str] = []
    for _ in range(100):
        # Create and immediately delete to trigger GC memory address reuse
        entry = ViewportEntry(file="/dev/null", start_line=1, end_line=1)
        ids.append(entry.viewport_id)
        del entry

    unique = set(ids)
    assert len(unique) == len(ids), (
        f"SC-1 FAIL: viewport_id collision detected — "
        f"{len(ids) - len(unique)} duplicates out of {len(ids)} IDs. "
        f"First 5 duplicates: "
        f"{[i for i in ids if ids.count(i) > 1][:5]}"
    )


def test_sc2_viewport_id_format() -> None:
    """SC-2: viewport_id follows viewport_<N> format with incrementing integers.

    RED: current hex(id(object()))[2:] produces hex format, not viewport_<N>.
    """
    from viewport_editor.viewport import ViewportEntry

    ids: list[str] = []
    for _ in range(20):
        entry = ViewportEntry(file="/dev/null", start_line=1, end_line=1)
        ids.append(entry.viewport_id)

    # After fix, IDs should start with "viewport_" and increment
    for vid in ids:
        assert vid.startswith("viewport_"), (
            f"SC-2 FAIL: viewport_id '{vid}' does not start with 'viewport_'. "
            f"Fix not yet applied — current format is hex(id(object()))[2:]"
        )

    # Verify they're strictly sequential integers (no gaps, no duplicates)
    nums = [int(vid.removeprefix("viewport_")) for vid in ids]
    expected = list(range(nums[0], nums[0] + 20))
    assert nums == expected, (
        f"SC-2 FAIL: viewport_ids not sequentially incrementing. "
        f"Got {nums[0]}..{nums[-1]}, expected 20 consecutive integers"
    )
