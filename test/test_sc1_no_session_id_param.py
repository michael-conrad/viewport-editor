# SPDX-FileCopyrightText: 2026 Michael Conrad
# SPDX-License-Identifier: MIT
# Provenance: AI-generated
"""SC-1: session_id parameter removed from all six tool stubs.

RED phase — Tests FAIL because session_id IS still present in inputSchema.
GREEN phase — After removing session_id from tool stubs, tests PASS.

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
async def test_sc1_schema_no_session_id(client_session: Any) -> None:
    """SC-1: session_id absent from all six tool inputSchemas.

    RED phase: FAILS — session_id IS present in each tool's inputSchema.
    GREEN phase: PASSES — session_id removed from all six stubs.
    """
    result = await client_session.list_tools()
    for t in result.tools:
        if t.name in SIX_TOOLS:
            props = t.inputSchema.get("properties", {})
            assert "session_id" not in props, (
                f"Tool '{t.name}' has session_id in inputSchema: {list(props.keys())}"
            )


@pytest.mark.asyncio
async def test_sc1_regex_no_session_id(client_session: Any) -> None:
    """regex tool never had session_id — always absent."""
    result = await client_session.list_tools()
    tools_by_name = {t.name: t for t in result.tools}
    regex_tool = tools_by_name.get("regex")
    assert regex_tool is not None
    props = regex_tool.inputSchema.get("properties", {})
    assert "session_id" not in props, "regex should never have session_id"


@pytest.mark.asyncio
async def test_sc1_behavioral_open_no_session_id(client_session: Any) -> None:
    """Open a viewport without session_id in arguments."""
    result = await client_session.call_tool(
        "viewport",
        arguments={"action": "open", "file_path": "test_file.txt"},
    )
    assert not result.isError, "Expected success, got error"
    assert "opened viewport" in _get_text(result).lower()


@pytest.mark.asyncio
async def test_sc1_behavioral_all_tools_without_session_id(
    client_session: Any,
) -> None:
    """Call all seven tools without session_id in arguments."""
    open_result = await client_session.call_tool(
        "viewport",
        arguments={"action": "open", "file_path": "test_file.txt"},
    )
    vpid = _extract_vpid(_get_text(open_result))
    assert vpid, "viewport_id not returned"

    edit_result = await client_session.call_tool(
        "edit",
        arguments={
            "action": "replace",
            "viewport_id": vpid,
            "old_text": "line 1",
            "new_text": "replaced",
        },
    )
    assert not edit_result.isError, f"edit failed: {_get_text(edit_result)}"

    save_result = await client_session.call_tool(
        "file",
        arguments={"action": "save", "viewport_id": vpid},
    )
    assert not save_result.isError, f"file:save failed: {_get_text(save_result)}"

    diff_result = await client_session.call_tool(
        "diff",
        arguments={"action": "show", "viewport_id": vpid, "file_path": "test_file.txt"},
    )
    assert (
        not diff_result.isError
        or "no pending changes" in _get_text(diff_result).lower()
    )

    clip_result = await client_session.call_tool(
        "clipboard",
        arguments={
            "action": "copy",
            "viewport_id": vpid,
            "line_start": 1,
            "line_end": 1,
        },
    )
    assert not clip_result.isError, f"clipboard failed: {_get_text(clip_result)}"

    search_result = await client_session.call_tool(
        "search",
        arguments={
            "action": "find",
            "pattern": "line",
            "scope": "file",
            "file_path": "test_file.txt",
        },
    )
    assert not search_result.isError, f"search failed: {_get_text(search_result)}"

    regex_result = await client_session.call_tool(
        "regex",
        arguments={"action": "test", "pattern": "line", "text": "line 1"},
    )
    assert not regex_result.isError, f"regex failed: {_get_text(regex_result)}"
