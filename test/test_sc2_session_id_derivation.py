# SPDX-FileCopyrightText: 2026 Michael Conrad
# SPDX-License-Identifier: MIT
# Provenance: AI-generated
"""SC-2: ctx.session_id is used internally as the session key.

RED phase — Tests FAIL because:
- Schema still requires session_id (test_sc2_schema_session_id_absent)
- Two distinct Client instances share empty-string session (test_sc2_two_clients_separate_sessions)

GREEN phase — Refactored handlers use ctx.session_id internally:
- Schema lacks session_id param
- Each Client connection gets its own ctx.session_id → sessions isolated

Co-authored with AI: OpenCode (deepseek-v4-flash)
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any

import pytest


SIX_TOOLS = {"viewport", "edit", "file", "diff", "search", "clipboard"}


@pytest.fixture(scope="module")
def test_project_root() -> Path:
    tmpdir = Path(tempfile.mkdtemp(prefix="ve-test-"))
    (tmpdir / "test_file.txt").write_text("line 1\nline 2\nline 3\n")
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
async def test_sc2_schema_session_id_absent(client_session: Any) -> None:
    """SC-2: session_id absent from all six tool inputSchemas.

    RED phase: FAILS — session_id param IS present in schema.
    GREEN phase: PASSES — session_id removed from all six stubs.
    """
    result = await client_session.list_tools()
    for t in result.tools:
        if t.name in SIX_TOOLS:
            props = t.inputSchema.get("properties", {})
            assert "session_id" not in props, (
                f"Tool '{t.name}' still has session_id in inputSchema: {list(props.keys())}"
            )


@pytest.mark.asyncio
async def test_sc2_viewport_works_without_session_id(client_session: Any) -> None:
    """SC-2: viewport tool derives session from ctx.session_id.

    RED phase: PASSES (empty-string default works).
    GREEN phase: PASSES (uses ctx.session_id instead).
    """
    result = await client_session.call_tool(
        "viewport",
        arguments={"action": "open", "file_path": "test_file.txt"},
    )
    assert not result.isError, "Expected open to succeed, got error"
    text = _get_text(result)
    assert "opened viewport" in text.lower()
    vpid = _extract_vpid(text)
    assert vpid

    scroll = await client_session.call_tool(
        "viewport",
        arguments={"action": "scroll", "viewport_id": vpid, "lines": 1},
    )
    assert not scroll.isError, f"scroll failed: {_get_text(scroll)}"

    close = await client_session.call_tool(
        "viewport",
        arguments={"action": "close", "viewport_id": vpid},
    )
    assert not close.isError, f"close failed: {_get_text(close)}"


@pytest.mark.asyncio
async def test_sc2_two_clients_separate_sessions(
    _server: Any,
) -> None:
    """SC-2: two separate Client instances get isolated sessions.

    RED phase: FAILS — both clients use empty-string session_id="",
    so the first client's viewport leaks into the second client's list.

    GREEN phase: PASSES — each Client has its own ctx.session_id (UUID),
    so the second client starts with an empty session.
    """
    from fastmcp import Client

    async with Client(transport=_server) as client1:
        result1 = await client1.call_tool(
            "viewport",
            arguments={
                "action": "open",
                "file_path": "test_file.txt",
            },
        )
        assert "error" not in result1.content[0].text.lower()

    async with Client(transport=_server) as client2:
        result2 = await client2.call_tool(
            "viewport",
            arguments={
                "action": "list",
            },
        )
        text2 = result2.content[0].text

    # RED: both clients share "" session, so client2 sees client1's viewport → FAIL
    # GREEN: each client has unique ctx.session_id, so client2 sees empty session → PASS
    assert "no open viewports" in text2.lower(), (
        f"Expected empty session for second client, got viewport leak: {text2}"
    )


@pytest.mark.asyncio
async def test_sc2_edit_file_clipboard_work_without_session_id(
    client_session: Any,
) -> None:
    """Edit, file, clipboard, diff all derive session from ctx.session_id.

    RED phase: PASSES (empty-string default works).
    GREEN phase: PASSES (uses ctx.session_id instead).
    """
    result = await client_session.call_tool(
        "viewport",
        arguments={"action": "open", "file_path": "test_file.txt"},
    )
    vpid = _extract_vpid(_get_text(result))
    assert vpid

    edit_result = await client_session.call_tool(
        "edit",
        arguments={
            "action": "replace",
            "viewport_id": vpid,
            "old_text": "line 1",
            "new_text": "ALT",
        },
    )
    assert not edit_result.isError, f"edit: {_get_text(edit_result)}"

    save_result = await client_session.call_tool(
        "file",
        arguments={"action": "save", "viewport_id": vpid},
    )
    assert not save_result.isError, f"save: {_get_text(save_result)}"

    clip_result = await client_session.call_tool(
        "clipboard",
        arguments={
            "action": "copy",
            "viewport_id": vpid,
            "line_start": 1,
            "line_end": 1,
        },
    )
    assert not clip_result.isError, f"clipboard: {_get_text(clip_result)}"
