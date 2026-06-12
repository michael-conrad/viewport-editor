# SPDX-FileCopyrightText: 2026 Michael Conrad
# SPDX-License-Identifier: MIT
# Provenance: AI-generated
"""RED-phase: SC-2 dedup — only first file under same AGENTS.md gets injection.

This will FAIL because _inject_agents_notice is not yet wired.

Co-authored with AI: OpenCode (deepseek-v4-flash)
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
async def test_sc2_dedup_same_session(
    client_session: any, test_project_root: Path
) -> None:
    sub = test_project_root / "sc2_subdir"
    sub.mkdir(parents=True, exist_ok=True)
    (sub / "AGENTS.md").write_text("SC-2 dedup instructions")
    (sub / "a.txt").write_text("content a\n")
    (sub / "b.txt").write_text("content b\n")

    # First open should have injection
    r1 = await client_session.call_tool(
        "viewport",
        arguments={"action": "open", "file_path": os.path.join("sc2_subdir", "a.txt")},
    )
    t1 = _get_text(r1)
    assert "<system-reminder>" in t1, "First open should have injection"

    # Second open under same AGENTS.md should NOT have injection (dedup)
    r2 = await client_session.call_tool(
        "viewport",
        arguments={"action": "open", "file_path": os.path.join("sc2_subdir", "b.txt")},
    )
    t2 = _get_text(r2)
    assert "<system-reminder>" not in t2, (
        "Second open under same AGENTS.md should not have injection (dedup)"
    )
