# SPDX-FileCopyrightText: 2026 Michael Conrad
# SPDX-License-Identifier: MIT
# Provenance: AI-generated
"""RED-phase: SC-11 injection format — <system-reminder>\nInstructions from: pattern.

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
async def test_sc11_injection_format(
    client_session: any, test_project_root: Path
) -> None:
    sub = test_project_root / "sc11_format"
    sub.mkdir(parents=True, exist_ok=True)
    (sub / "AGENTS.md").write_text("SC-11 format instructions")
    (sub / "target.txt").write_text("content\n")
    result = await client_session.call_tool(
        "viewport",
        arguments={
            "action": "open",
            "file_path": os.path.join("sc11_format", "target.txt"),
        },
    )
    text = _get_text(result)
    assert "<system-reminder>\nInstructions from:" in text, (
        f"SC-11 FAIL: expected '<system-reminder>\\nInstructions from:' format, got:\n{text}"
    )
