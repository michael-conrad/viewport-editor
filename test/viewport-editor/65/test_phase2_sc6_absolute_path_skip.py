# SPDX-FileCopyrightText: 2026 Michael Conrad
# SPDX-License-Identifier: MIT
# Provenance: AI-generated
"""RED-phase: SC-6 absolute path skip — opening /etc/passwd should not inject.

This will FAIL because _inject_agents_notice is not yet wired.

Co-authored with AI: OpenCode (deepseek-v4-flash)
"""

from __future__ import annotations


import pytest


def _get_text(result: any) -> str:
    parts: list[str] = []
    if result.content:
        for item in result.content:
            if hasattr(item, "text") and item.text:
                parts.append(item.text)
    return "\n".join(parts)


@pytest.mark.asyncio
async def test_sc6_absolute_path_skip(client_session: any) -> None:
    """Absolute paths are rejected by _resolve_path before injection even fires."""
    result = await client_session.call_tool(
        "viewport",
        arguments={"action": "open", "file_path": "/etc/passwd"},
    )
    text = _get_text(result)
    # The server rejects absolute paths — no <system-reminder> should appear
    assert "<system-reminder>" not in text, (
        "SC-6 FAIL: absolute path should not produce injection"
    )
    assert result.isError, "SC-6 FAIL: absolute path should produce isError"
