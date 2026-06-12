# SPDX-FileCopyrightText: 2026 Michael Conrad
# SPDX-License-Identifier: MIT
# Provenance: AI-generated
"""RED-phase: SC-4 nearest ancestor AGENTS.md wins over shallower one.

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
async def test_sc4_nearest_ancestor_wins(
    client_session: any, test_project_root: Path
) -> None:
    a = test_project_root / "sc4_a"
    b = a / "b"
    b.mkdir(parents=True, exist_ok=True)
    (a / "AGENTS.md").write_text("SHALLOW instructions")
    (b / "AGENTS.md").write_text("DEEP instructions")
    (b / "target.txt").write_text("content\n")
    result = await client_session.call_tool(
        "viewport",
        arguments={
            "action": "open",
            "file_path": os.path.join("sc4_a", "b", "target.txt"),
        },
    )
    text = _get_text(result)
    assert "<system-reminder>" in text, "SC-4 FAIL: expected injection"
    assert "DEEP instructions" in text, (
        f"SC-4 FAIL: expected deepest AGENTS.md content, got:\n{text}"
    )
