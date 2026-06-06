# SPDX-FileCopyrightText: 2026 Michael Conrad
# SPDX-License-Identifier: MIT
# Provenance: AI-generated
"""RED-phase tests for #39: tool parameter naming normalization.

These tests use the TARGET parameter names (line_start, line_end,
autosave_enabled, ctx-first). They MUST FAIL against current code
because server.py still uses start_line/end_line/enabled.

Co-authored with AI: OpenCode (deepseek-v4-flash)
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import AsyncIterator, Any

import pytest


@pytest.fixture(scope="module")
def test_project_root() -> Path:
    tmpdir = Path(tempfile.mkdtemp(prefix="ve-red39-"))
    (tmpdir / "red_test.txt").write_text("line 1\nline 2\nline 3\nline 4\nline 5\n")
    return tmpdir


def _get_text(result: Any) -> str:
    parts: list[str] = []
    if result.content:
        for item in result.content:
            if hasattr(item, "text") and item.text:
                parts.append(item.text)
    return "\n".join(parts)


# SC-1: viewport uses line_start/line_end (RED — will fail with old code)
@pytest.mark.phase1
@pytest.mark.asyncio
async def test_red_sc1_viewport_line_start_end(client_session: Any) -> None:
    """Call viewport with line_start/line_end — fails on old code, passes on new."""
    result = await client_session.call_tool(
        "viewport",
        arguments={
            "action": "open",
            "session_id": "red-sc1",
            "file_path": "red_test.txt",
            "line_start": 1,
            "line_end": 3,
        },
    )
    text = _get_text(result)
    # On GREEN code: response uses line_start:/line_end: keys
    assert "line_start:" in text
    assert "line_end:" in text


# SC-2: viewport uses autosave_enabled (RED — will fail with old code)
@pytest.mark.phase1
@pytest.mark.asyncio
async def test_red_sc2_autosave_enabled(client_session: Any) -> None:
    """Call viewport autosave action with autosave_enabled — fails on old code."""
    result_open = await client_session.call_tool(
        "viewport",
        arguments={
            "action": "open",
            "session_id": "red-sc2",
            "file_path": "red_test.txt",
        },
    )
    open_text = _get_text(result_open)
    vpid = ""
    for line in open_text.splitlines():
        line = line.strip()
        if line.startswith("viewport_id:"):
            vpid = line.split("viewport_id:")[1].strip()
            break
    assert vpid, "could not extract viewport_id"
    result = await client_session.call_tool(
        "viewport",
        arguments={
            "action": "autosave",
            "session_id": "red-sc2",
            "viewport_id": vpid,
            "autosave_enabled": True,
        },
    )
    text = _get_text(result)
    assert "autosave set to True" in text


# SC-3: clipboard uses line_start/line_end (RED — will fail with old code)
@pytest.mark.phase1
@pytest.mark.asyncio
async def test_red_sc3_clipboard_line_start_end(client_session: Any) -> None:
    """Call clipboard with line_start/line_end — fails on old code."""
    result_open = await client_session.call_tool(
        "viewport",
        arguments={
            "action": "open",
            "session_id": "red-sc3",
            "file_path": "red_test.txt",
        },
    )
    open_text = _get_text(result_open)
    vpid = ""
    for line in open_text.splitlines():
        line = line.strip()
        if line.startswith("viewport_id:"):
            vpid = line.split("viewport_id:")[1].strip()
            break
    assert vpid, "could not extract viewport_id"
    result = await client_session.call_tool(
        "clipboard",
        arguments={
            "action": "copy",
            "session_id": "red-sc3",
            "viewport_id": vpid,
            "line_start": 1,
            "line_end": 3,
        },
    )
    text = _get_text(result)
    assert "copied" in text.lower()


# SC-4: ctx is first parameter in all 7 tools (RED — viewport/clipboard have it last)
@pytest.mark.phase1
@pytest.mark.asyncio
async def test_red_sc4_ctx_is_first_param(client_session: Any) -> None:
    """Check inputSchema property order — ctx should be first in all tools."""
    result = await client_session.list_tools()
    tools_by_name = {t.name: t for t in result.tools}
    expected_tools = {
        "viewport",
        "edit",
        "file",
        "diff",
        "clipboard",
        "search",
        "regex",
    }
    for name in sorted(expected_tools):
        t = tools_by_name[name]
        props = list(t.inputSchema.get("properties", {}).keys())
        # On RED: viewport and clipboard have ctx at end — this check fails
        # On GREEN: viewport and clipboard have ctx at front — this passes
        assert props[0] == "ctx", (
            f"{name}: ctx is not first param. First param is {props[0]}. "
            f"Params: {props}"
        )


# SC-5: ctx_pattern removed from regex (RED — it still exists)
@pytest.mark.phase1
@pytest.mark.asyncio
async def test_red_sc5_no_ctx_pattern(client_session: Any) -> None:
    """ctx_pattern should not be in regex tool properties."""
    result = await client_session.list_tools()
    tools_by_name = {t.name: t for t in result.tools}
    regex_tool = tools_by_name["regex"]
    props = list(regex_tool.inputSchema.get("properties", {}).keys())
    # On RED: ctx_pattern still exists — this fails
    # On GREEN: ctx_pattern removed — this passes
    assert "ctx_pattern" not in props, (
        f"regex tool still has ctx_pattern param. Params: {props}"
    )


# SC-6: file_path removed from edit (RED — it still exists)
@pytest.mark.phase1
@pytest.mark.asyncio
async def test_red_sc6_no_file_path_edit(client_session: Any) -> None:
    """file_path should not be in edit tool properties."""
    result = await client_session.list_tools()
    tools_by_name = {t.name: t for t in result.tools}
    edit_tool = tools_by_name["edit"]
    props = list(edit_tool.inputSchema.get("properties", {}).keys())
    # On RED: file_path still exists in edit — this fails
    # On GREEN: file_path removed from edit — this passes
    assert "file_path" not in props, (
        f"edit tool still has file_path param. Params: {props}"
    )
