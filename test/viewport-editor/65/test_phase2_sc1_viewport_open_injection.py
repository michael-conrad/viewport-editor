# SPDX-FileCopyrightText: 2026 Michael Conrad
# SPDX-License-Identifier: MIT
# Provenance: AI-generated
"""RED-phase: SC-1 viewport:open injection of AGENTS.md content.

SC-1: Opening a file under a directory with AGENTS.md injects <system-reminder>.
This will FAIL because _inject_agents_notice is not yet wired into viewport:open.

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
async def test_sc1_viewport_open_injects_agents_md(
    client_session: any, test_project_root: Path
) -> None:
    sub = test_project_root / "sc1_subdir"
    sub.mkdir(parents=True, exist_ok=True)
    (sub / "AGENTS.md").write_text("SC-1 test instructions")
    (sub / "target.txt").write_text("content\n")
    result = await client_session.call_tool(
        "viewport",
        arguments={
            "action": "open",
            "file_path": os.path.join("sc1_subdir", "target.txt"),
        },
    )
    text = _get_text(result)
    assert "<system-reminder>" in text, (
        f"SC-1 FAIL: expected <system-reminder> injection, got:\n{text}"
    )
