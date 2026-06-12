# SPDX-FileCopyrightText: 2026 Michael Conrad
# SPDX-License-Identifier: MIT
# Provenance: AI-generated
"""RED-phase: SC-3 root AGENTS.md fallback when no ancestor has AGENTS.md.

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
async def test_sc3_root_agents_fallback(
    client_session: any, test_project_root: Path
) -> None:
    (test_project_root / "AGENTS.md").write_text("SC-3 root instructions")
    deep = test_project_root / "sc3_deep" / "nested" / "path"
    deep.mkdir(parents=True, exist_ok=True)
    (deep / "target.txt").write_text("content\n")
    result = await client_session.call_tool(
        "viewport",
        arguments={
            "action": "open",
            "file_path": os.path.join("sc3_deep", "nested", "path", "target.txt"),
        },
    )
    text = _get_text(result)
    assert "<system-reminder>" in text, (
        "SC-3 FAIL: expected root AGENTS.md fallback injection"
    )


@pytest.mark.asyncio
async def test_sc3_root_agents_cleanup(
    client_session: any, test_project_root: Path
) -> None:
    """Cleanup the root AGENTS.md so other tests aren't affected."""
    root_md = test_project_root / "AGENTS.md"
    if root_md.exists():
        root_md.unlink()
