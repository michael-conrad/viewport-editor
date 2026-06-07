# SPDX-FileCopyrightText: 2026 Michael Conrad
# SPDX-License-Identifier: MIT
# Provenance: AI-generated
"""SC-3: Two viewports opened via the same Client share the same session.

RED phase — Tests PASS currently because server.py derives session_id from
ctx.session_id, which is consistent for all tool calls within one Client
connection.

GREEN phase — After Phase B removes session_id from manager signatures and
test args, these tests continue to PASS because ctx.session_id still provides
correct session sharing within a connection.

Behavioral evidence: clipboard content copied via one viewport is available
for paste via another viewport on the same Client connection.

Co-authored with AI: OpenCode (deepseek-v4-flash)
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any

import pytest


@pytest.fixture(scope="module")
def test_project_root() -> Path:
    tmpdir = Path(tempfile.mkdtemp(prefix="ve-test-"))
    (tmpdir / "test.txt").write_text("line 1\nline 2\nline 3\nline 4\nline 5\n")
    (tmpdir / "other.txt").write_text("alpha\nbeta\ngamma\n")
    return tmpdir


def _get_text(result: Any) -> str:
    parts: list[str] = []
    if result.content:
        for item in result.content:
            if hasattr(item, "text") and item.text:
                parts.append(item.text)
    return "\n".join(parts)


def _extract_vpid(text: str) -> str:
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("viewport_id:"):
            return line.split("viewport_id:")[1].strip()
    return ""


@pytest.mark.asyncio
async def test_sc3_same_client_clipboard_shared(client_session: Any) -> None:
    """Copy via one viewport, paste via another — same Client, shared clipboard.

    RED phase: PASSES. Both viewport calls go through the same ctx.session_id,
    so clipboard content stored on the Session object is accessible from both.

    GREEN phase: PASSES. ctx.session_id still provides correct sharing.
    """
    open1 = await client_session.call_tool(
        "viewport", arguments={"action": "open", "file_path": "test.txt"}
    )
    assert not open1.isError, f"first open: {_get_text(open1)}"
    vpid1 = _extract_vpid(_get_text(open1))
    assert vpid1

    copy_result = await client_session.call_tool(
        "clipboard",
        arguments={
            "action": "copy",
            "viewport_id": vpid1,
            "line_start": 1,
            "line_end": 1,
        },
    )
    assert not copy_result.isError, f"copy: {_get_text(copy_result)}"
    assert "copied to clipboard" in _get_text(copy_result).lower()

    open2 = await client_session.call_tool(
        "viewport", arguments={"action": "open", "file_path": "other.txt"}
    )
    assert not open2.isError, f"second open: {_get_text(open2)}"
    vpid2 = _extract_vpid(_get_text(open2))
    assert vpid2
    assert vpid1 != vpid2, "should have distinct viewport IDs"

    paste_result = await client_session.call_tool(
        "clipboard",
        arguments={"action": "paste", "viewport_id": vpid2, "target_line": 2},
    )
    assert not paste_result.isError, (
        f"paste should work (same session): {_get_text(paste_result)}"
    )
    assert "pasted from clipboard" in _get_text(paste_result).lower()


@pytest.mark.asyncio
async def test_sc3_same_client_stash_shared(client_session: Any) -> None:
    """Stash via one viewport, unstash via another — same Client, shared session.

    RED phase: PASSES. ctx.session_id is consistent within one connection.
    """
    open1 = await client_session.call_tool(
        "viewport", arguments={"action": "open", "file_path": "test.txt"}
    )
    vpid1 = _extract_vpid(_get_text(open1))

    await client_session.call_tool(
        "clipboard",
        arguments={
            "action": "copy",
            "viewport_id": vpid1,
            "line_start": 1,
            "line_end": 2,
        },
    )

    stash_result = await client_session.call_tool(
        "clipboard",
        arguments={"action": "stash", "viewport_id": vpid1, "name": "shared_slot"},
    )
    assert not stash_result.isError, f"stash: {_get_text(stash_result)}"

    open2 = await client_session.call_tool(
        "viewport", arguments={"action": "open", "file_path": "other.txt"}
    )
    vpid2 = _extract_vpid(_get_text(open2))

    pop_result = await client_session.call_tool(
        "clipboard",
        arguments={"action": "pop", "viewport_id": vpid2, "name": "shared_slot"},
    )
    assert not pop_result.isError, (
        f"pop from other viewport should work (same session): {_get_text(pop_result)}"
    )
    text = _get_text(pop_result).lower()
    assert "popped" in text, f"expected pop confirmation: {text}"
