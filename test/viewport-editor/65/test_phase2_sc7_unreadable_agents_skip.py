# SPDX-FileCopyrightText: 2026 Michael Conrad
# SPDX-License-Identifier: MIT
# Provenance: AI-generated
"""RED-phase: SC-7 unreadable AGENTS.md silently skips injection.

Since injection is not wired, this test will PASS. Other tests should fail.

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
async def test_sc7_unreadable_agents_skip(
    client_session: any, test_project_root: Path
) -> None:
    sub = test_project_root / "sc7_unreadable"
    sub.mkdir(parents=True, exist_ok=True)
    agents_file = sub / "AGENTS.md"
    agents_file.write_text("SENSITIVE instructions")
    agents_file.chmod(0o000)
    (sub / "target.txt").write_text("content\n")
    try:
        result = await client_session.call_tool(
            "viewport",
            arguments={
                "action": "open",
                "file_path": os.path.join("sc7_unreadable", "target.txt"),
            },
        )
        text = _get_text(result)
        assert "<system-reminder>" not in text, (
            "SC-7 FAIL: unreadable AGENTS.md should not inject"
        )
    finally:
        agents_file.chmod(0o644)
