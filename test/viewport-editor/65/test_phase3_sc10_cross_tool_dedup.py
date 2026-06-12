# SPDX-FileCopyrightText: 2026 Michael Conrad
# SPDX-License-Identifier: MIT
# Provenance: AI-generated
"""Phase 3: SC-10 cross-tool dedup between read_file and viewport:open.

SC-10: read_file then viewport:open on files under same AGENTS.md → single
injection total. Since injection wiring and session-based dedup are fully
implemented in Phases 1-2, this is expected to PASS.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest


def _get_text(result: any) -> str:
    parts: list[str] = []
    if result.content:
        for item in result.content:
            if hasattr(item, "text") and item.text:
                parts.append(item.text)
    return "\n".join(parts)


@pytest.mark.asyncio
async def test_sc10_cross_tool_dedup(
    client_session: any, test_project_root: Path
) -> None:
    sub = test_project_root / "sc10_subdir"
    sub.mkdir(parents=True, exist_ok=True)
    (sub / "AGENTS.md").write_text("SC-10 test instructions")
    (sub / "alpha.txt").write_text("alpha\n")
    (sub / "beta.txt").write_text("beta\n")

    # First: read_file on alpha.txt — should get injection
    result1 = await client_session.call_tool(
        "read_file",
        arguments={
            "file_path": os.path.join("sc10_subdir", "alpha.txt"),
        },
    )
    text1 = _get_text(result1)
    assert "<system-reminder>" in text1, (
        "SC-10 FAIL: read_file should inject <system-reminder>"
    )

    # Second: viewport:open on beta.txt — should NOT inject again (dedup)
    result2 = await client_session.call_tool(
        "viewport",
        arguments={
            "action": "open",
            "file_path": os.path.join("sc10_subdir", "beta.txt"),
        },
    )
    text2 = _get_text(result2)
    assert "<system-reminder>" not in text2, (
        "SC-10 FAIL: viewport:open should NOT inject again (dedup)"
    )
