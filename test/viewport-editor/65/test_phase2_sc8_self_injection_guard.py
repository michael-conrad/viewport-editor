# SPDX-FileCopyrightText: 2026 Michael Conrad
# SPDX-License-Identifier: MIT
# Provenance: AI-generated
"""RED-phase: SC-8 self-injection guard — opening AGENTS.md itself should not inject.

This test may PASS even in RED-phase because the dedup/self-guard logic isn't wired.

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
async def test_sc8_self_injection_guard(
    client_session: any, test_project_root: Path
) -> None:
    sub = test_project_root / "sc8_self"
    sub.mkdir(parents=True, exist_ok=True)
    agents_file = sub / "AGENTS.md"
    agents_file.write_text("SELF instructions")
    result = await client_session.call_tool(
        "viewport",
        arguments={
            "action": "open",
            "file_path": os.path.join("sc8_self", "AGENTS.md"),
        },
    )
    text = _get_text(result)
    assert "<system-reminder>" not in text, (
        "SC-8 FAIL: opening AGENTS.md should not self-inject"
    )
