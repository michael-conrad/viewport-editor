# SPDX-FileCopyrightText: 2026 Michael Conrad
# SPDX-License-Identifier: MIT
# Provenance: AI-generated
"""Phase 3: SC-9 composite read_file triggers AGENTS.md injection.

SC-9: read_file on a file under AGENTS.md → response contains AGENTS.md
content in <system-reminder>. Since _inject_agents_notice is already wired
into the read_file handler (Phase 2), this is expected to PASS.
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
async def test_sc9_read_file_injects_agents_md(
    client_session: any, test_project_root: Path
) -> None:
    sub = test_project_root / "sc9_subdir"
    sub.mkdir(parents=True, exist_ok=True)
    (sub / "AGENTS.md").write_text("SC-9 test instructions")
    (sub / "target.txt").write_text("content\n")
    result = await client_session.call_tool(
        "read_file",
        arguments={
            "file_path": os.path.join("sc9_subdir", "target.txt"),
        },
    )
    text = _get_text(result)
    assert "<system-reminder>" in text, (
        f"SC-9 FAIL: read_file should inject <system-reminder>, got:\n{text}"
    )
