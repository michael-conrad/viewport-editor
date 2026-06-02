# SPDX-FileCopyrightText: 2026 Michael Conrad
# SPDX-License-Identifier: MIT
# Provenance: AI-generated
"""Phase 3 RED behavioral tests for clipboard stash tools of viewport-editor MCP server.

These tests assert GREEN-phase behavior for SC-43 (stash copies clipboard to named
slot), SC-44 (pop replaces clipboard from named slot), SC-45 (swap exchanges clipboard
and named slot), and SC-47 (stash list returns metadata). They MUST FAIL against
current code because clipboard stash actions do not exist yet.

Co-authored with AI: OpenCode (ollama-cloud/glm-5.1)
"""

from __future__ import annotations

import tempfile
import uuid
from pathlib import Path
from typing import AsyncIterator

import pytest
from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client
from mcp.types import CallToolResult


@pytest.fixture(scope="module")
def test_project_root() -> Path:
    tmpdir = Path(tempfile.mkdtemp(prefix="ve-test-"))
    (tmpdir / "stash_src.txt").write_text("alpha\nbeta\ngamma\ndelta\nepsilon\n")
    (tmpdir / "stash_other.txt").write_text("foo\nbar\nbaz\nqux\nquux\n")
    return tmpdir


@pytest.fixture(scope="module")
def server_params(test_project_root: Path) -> StdioServerParameters:
    return StdioServerParameters(
        command="uv",
        args=[
            "run",
            "python",
            "-m",
            "viewport_editor",
            "--project-root",
            str(test_project_root),
        ],
    )


@pytest.fixture
async def client_session(
    server_params: StdioServerParameters,
) -> AsyncIterator[ClientSession]:
    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                yield session
    except RuntimeError as exc:
        msg = str(exc)
        if "Attempted to exit cancel scope in a different task" not in msg:
            raise


def _get_text(result: CallToolResult) -> str:
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


def _unique_sid() -> str:
    return f"test-p3s-{uuid.uuid4().hex[:8]}"


# ── SC-43: stash copies clipboard contents to named storage slot ─────────────


@pytest.mark.phase3
@pytest.mark.asyncio
async def test_stash_copies_clipboard(
    client_session: ClientSession, test_project_root: Path
) -> None:
    """SC-43: stash copies clipboard contents to named slot; clipboard stays intact.

    RED: clipboard stash action does not exist; call_tool will fail.
    GREEN: after stash, clipboard:show still has content and stash slot has content.
    """
    sid = _unique_sid()
    file_path = "stash_src.txt"

    result_open = await client_session.call_tool(
        "viewport",
        arguments={
            "action": "open",
            "session_id": sid,
            "file_path": file_path,
        },
    )
    assert "error" not in _get_text(result_open)
    vpid = _extract_vpid(_get_text(result_open))

    result = await client_session.call_tool(
        "clipboard",
        arguments={
            "action": "copy",
            "session_id": sid,
            "viewport_id": vpid,
            "start_line": 2,
            "end_line": 4,
        },
    )
    assert not result.isError, (
        f"Precondition: clipboard:copy must work: {_get_text(result)[:200]}"
    )

    stash_result = await client_session.call_tool(
        "clipboard",
        arguments={
            "action": "stash",
            "session_id": sid,
            "name": "slot_a",
        },
    )
    stash_text = _get_text(stash_result)

    assert not stash_result.isError, (
        f"RED FAIL: clipboard:stash not implemented: {stash_text[:200]}"
    )
    assert "error" not in stash_text.lower(), (
        f"RED FAIL: clipboard:stash returned error: {stash_text[:200]}"
    )

    show_result = await client_session.call_tool(
        "clipboard",
        arguments={"action": "show", "session_id": sid},
    )
    show_text = _get_text(show_result)
    assert "beta" in show_text, (
        f"SC-43: clipboard must remain intact after stash (beta still present): {show_text[:300]}"
    )
    assert "gamma" in show_text, (
        f"SC-43: clipboard must remain intact after stash (gamma still present): {show_text[:300]}"
    )

    stash_list_result = await client_session.call_tool(
        "clipboard",
        arguments={"action": "stash-list", "session_id": sid},
    )
    list_text = _get_text(stash_list_result)
    assert not stash_list_result.isError, (
        f"RED FAIL: clipboard:stash-list not implemented: {list_text[:200]}"
    )
    assert "slot_a" in list_text, (
        f"SC-43: stash-list must contain slot 'slot_a': {list_text[:300]}"
    )


@pytest.mark.phase3
@pytest.mark.asyncio
async def test_stash_overwrite(
    client_session: ClientSession, test_project_root: Path
) -> None:
    """SC-43: stash to same name overwrites previous slot content.

    RED: clipboard stash action does not exist; call_tool will fail.
    GREEN: second stash to 'slot_a' overwrites; stash-list shows new content.
    """
    sid = _unique_sid()
    file_path = "stash_src.txt"

    result_open = await client_session.call_tool(
        "viewport",
        arguments={
            "action": "open",
            "session_id": sid,
            "file_path": file_path,
        },
    )
    assert "error" not in _get_text(result_open)
    vpid = _extract_vpid(_get_text(result_open))

    await client_session.call_tool(
        "clipboard",
        arguments={
            "action": "copy",
            "session_id": sid,
            "viewport_id": vpid,
            "start_line": 1,
            "end_line": 1,
        },
    )

    stash1 = await client_session.call_tool(
        "clipboard",
        arguments={"action": "stash", "session_id": sid, "name": "slot_a"},
    )
    stash1_text = _get_text(stash1)
    assert not stash1.isError, (
        f"RED FAIL: clipboard:stash not implemented: {stash1_text[:200]}"
    )

    await client_session.call_tool(
        "clipboard",
        arguments={
            "action": "copy",
            "session_id": sid,
            "viewport_id": vpid,
            "start_line": 3,
            "end_line": 5,
        },
    )

    stash2 = await client_session.call_tool(
        "clipboard",
        arguments={"action": "stash", "session_id": sid, "name": "slot_a"},
    )
    stash2_text = _get_text(stash2)
    assert not stash2.isError, (
        f"SC-43: second stash to same name must succeed: {stash2_text[:200]}"
    )

    list_result = await client_session.call_tool(
        "clipboard",
        arguments={"action": "stash-list", "session_id": sid},
    )
    list_text = _get_text(list_result)
    assert not list_result.isError, (
        f"RED FAIL: clipboard:stash-list not implemented: {list_text[:200]}"
    )

    pop_result = await client_session.call_tool(
        "clipboard",
        arguments={"action": "pop", "session_id": sid, "name": "slot_a"},
    )
    pop_text = _get_text(pop_result)
    assert not pop_result.isError, (
        f"RED FAIL: clipboard:pop not implemented: {pop_text[:200]}"
    )
    assert "gamma" in pop_text, (
        f"SC-43: overwritten slot_a must contain SECOND stash content (gamma): {pop_text[:300]}"
    )


@pytest.mark.phase3
@pytest.mark.asyncio
async def test_stash_empty_clipboard_is_error(
    client_session: ClientSession, test_project_root: Path
) -> None:
    """SC-43: stash with empty clipboard returns isError.

    RED: clipboard stash action does not exist; call_tool will fail.
    GREEN: stash on a fresh session (no clipboard) returns isError=true.
    """
    sid = _unique_sid()

    result = await client_session.call_tool(
        "clipboard",
        arguments={"action": "stash", "session_id": sid, "name": "empty_slot"},
    )
    result_text = _get_text(result)

    assert result.isError, (
        f"SC-43: stash with empty clipboard must return isError=true: {result_text[:200]}"
    )


# ── SC-44: pop replaces clipboard contents with named slot contents ──────────


@pytest.mark.phase3
@pytest.mark.asyncio
async def test_pop_replaces_clipboard(
    client_session: ClientSession, test_project_root: Path
) -> None:
    """SC-44: pop replaces clipboard contents with named slot contents; slot remains intact.

    RED: clipboard pop action does not exist; call_tool will fail.
    GREEN: after pop, clipboard has slot content, and stash-list still shows slot.
    """
    sid = _unique_sid()
    file_path = "stash_other.txt"

    result_open = await client_session.call_tool(
        "viewport",
        arguments={
            "action": "open",
            "session_id": sid,
            "file_path": file_path,
        },
    )
    assert "error" not in _get_text(result_open)
    vpid = _extract_vpid(_get_text(result_open))

    await client_session.call_tool(
        "clipboard",
        arguments={
            "action": "copy",
            "session_id": sid,
            "viewport_id": vpid,
            "start_line": 1,
            "end_line": 2,
        },
    )

    stash_result = await client_session.call_tool(
        "clipboard",
        arguments={"action": "stash", "session_id": sid, "name": "my_slot"},
    )
    assert not stash_result.isError, (
        f"Precondition: stash must work: {_get_text(stash_result)[:200]}"
    )

    await client_session.call_tool(
        "clipboard",
        arguments={
            "action": "copy",
            "session_id": sid,
            "viewport_id": vpid,
            "start_line": 4,
            "end_line": 5,
        },
    )

    pop_result = await client_session.call_tool(
        "clipboard",
        arguments={"action": "pop", "session_id": sid, "name": "my_slot"},
    )
    pop_text = _get_text(pop_result)

    assert not pop_result.isError, (
        f"RED FAIL: clipboard:pop not implemented: {pop_text[:200]}"
    )
    assert "error" not in pop_text.lower(), (
        f"RED FAIL: clipboard:pop returned error: {pop_text[:200]}"
    )

    show_result = await client_session.call_tool(
        "clipboard",
        arguments={"action": "show", "session_id": sid},
    )
    show_text = _get_text(show_result)
    assert "foo" in show_text, (
        f"SC-44: after pop, clipboard must contain slot content (foo): {show_text[:300]}"
    )
    assert "bar" in show_text, (
        f"SC-44: after pop, clipboard must contain slot content (bar): {show_text[:300]}"
    )

    list_result = await client_session.call_tool(
        "clipboard",
        arguments={"action": "stash-list", "session_id": sid},
    )
    list_text = _get_text(list_result)
    assert "my_slot" in list_text, (
        f"SC-44: stash slot must remain intact after pop (my_slot still in list): {list_text[:300]}"
    )


@pytest.mark.phase3
@pytest.mark.asyncio
async def test_pop_nonexistent_slot_is_error(
    client_session: ClientSession, test_project_root: Path
) -> None:
    """SC-44: pop with nonexistent slot returns isError.

    RED: clipboard pop action does not exist; call_tool will fail.
    GREEN: pop with a name that was never stashed returns isError=true.
    """
    sid = _unique_sid()

    result = await client_session.call_tool(
        "clipboard",
        arguments={"action": "pop", "session_id": sid, "name": "no_such_slot"},
    )
    result_text = _get_text(result)

    assert result.isError, (
        f"SC-44: pop with nonexistent slot must return isError=true: {result_text[:200]}"
    )


# ── SC-45: swap exchanges clipboard and named slot ────────────────────────────


@pytest.mark.phase3
@pytest.mark.asyncio
async def test_swap_exchanges(
    client_session: ClientSession, test_project_root: Path
) -> None:
    """SC-45: swap exchanges clipboard and named slot.

    RED: clipboard swap action does not exist; call_tool will fail.
    GREEN: after swap, clipboard has former slot content and slot has former clipboard content.
    """
    sid = _unique_sid()
    file_path = "stash_src.txt"

    result_open = await client_session.call_tool(
        "viewport",
        arguments={
            "action": "open",
            "session_id": sid,
            "file_path": file_path,
        },
    )
    assert "error" not in _get_text(result_open)
    vpid = _extract_vpid(_get_text(result_open))

    await client_session.call_tool(
        "clipboard",
        arguments={
            "action": "copy",
            "session_id": sid,
            "viewport_id": vpid,
            "start_line": 1,
            "end_line": 2,
        },
    )

    stash_result = await client_session.call_tool(
        "clipboard",
        arguments={"action": "stash", "session_id": sid, "name": "swap_slot"},
    )
    assert not stash_result.isError, (
        f"Precondition: stash must work: {_get_text(stash_result)[:200]}"
    )

    await client_session.call_tool(
        "clipboard",
        arguments={
            "action": "copy",
            "session_id": sid,
            "viewport_id": vpid,
            "start_line": 4,
            "end_line": 5,
        },
    )

    swap_result = await client_session.call_tool(
        "clipboard",
        arguments={"action": "swap", "session_id": sid, "name": "swap_slot"},
    )
    swap_text = _get_text(swap_result)

    assert not swap_result.isError, (
        f"RED FAIL: clipboard:swap not implemented: {swap_text[:200]}"
    )
    assert "error" not in swap_text.lower(), (
        f"RED FAIL: clipboard:swap returned error: {swap_text[:200]}"
    )

    show_result = await client_session.call_tool(
        "clipboard",
        arguments={"action": "show", "session_id": sid},
    )
    show_text = _get_text(show_result)

    assert "alpha" in show_text, (
        f"SC-45: after swap, clipboard must have former slot content (alpha): {show_text[:300]}"
    )
    assert "beta" in show_text, (
        f"SC-45: after swap, clipboard must have former slot content (beta): {show_text[:300]}"
    )

    pop_result = await client_session.call_tool(
        "clipboard",
        arguments={"action": "pop", "session_id": sid, "name": "swap_slot"},
    )
    pop_text = _get_text(pop_result)
    assert "delta" in pop_text, (
        f"SC-45: after swap, slot must have former clipboard content (delta): {pop_text[:300]}"
    )
    assert "epsilon" in pop_text, (
        f"SC-45: after swap, slot must have former clipboard content (epsilon): {pop_text[:300]}"
    )


@pytest.mark.phase3
@pytest.mark.asyncio
async def test_swap_empty_clipboard_is_error(
    client_session: ClientSession, test_project_root: Path
) -> None:
    """SC-45: swap with empty clipboard returns isError.

    RED: clipboard swap action does not exist; call_tool will fail.
    GREEN: swap on a fresh session (no clipboard, even with a stashed slot) returns isError.
    """
    sid = _unique_sid()
    file_path = "stash_other.txt"

    result_open = await client_session.call_tool(
        "viewport",
        arguments={
            "action": "open",
            "session_id": sid,
            "file_path": file_path,
        },
    )
    assert "error" not in _get_text(result_open)
    vpid = _extract_vpid(_get_text(result_open))

    await client_session.call_tool(
        "clipboard",
        arguments={
            "action": "copy",
            "session_id": sid,
            "viewport_id": vpid,
            "start_line": 1,
            "end_line": 1,
        },
    )

    stash_result = await client_session.call_tool(
        "clipboard",
        arguments={"action": "stash", "session_id": sid, "name": "filled_slot"},
    )
    assert not stash_result.isError

    show_result = await client_session.call_tool(
        "clipboard",
        arguments={"action": "show", "session_id": sid},
    )
    _get_text(show_result)
    await client_session.call_tool(
        "clipboard",
        arguments={
            "action": "cut",
            "session_id": sid,
            "viewport_id": vpid,
            "start_line": 1,
            "end_line": 1,
        },
    )

    another_open = await client_session.call_tool(
        "viewport",
        arguments={
            "action": "open",
            "session_id": sid,
            "file_path": file_path,
            "autosave": False,
        },
    )
    assert "error" not in _get_text(another_open)
    _extract_vpid(_get_text(another_open))

    swap_result = await client_session.call_tool(
        "clipboard",
        arguments={"action": "swap", "session_id": sid, "name": "filled_slot"},
    )
    _get_text(swap_result)

    # After cut, clipboard will have content. For a true empty-clipboard test,
    # we need a session with no clipboard at all. Use a fresh separate session
    # via a different _unique_sid. Instead, test with a session where we
    # never copy/cut anything.
    sid_fresh = _unique_sid()

    swap_fresh = await client_session.call_tool(
        "clipboard",
        arguments={"action": "swap", "session_id": sid_fresh, "name": "any_name"},
    )
    swap_fresh_text = _get_text(swap_fresh)

    assert swap_fresh.isError, (
        f"SC-45: swap with empty clipboard must return isError=true: {swap_fresh_text[:200]}"
    )


# ── SC-47: stash list returns metadata ───────────────────────────────────────


@pytest.mark.phase3
@pytest.mark.asyncio
async def test_stash_list_shows_metadata(
    client_session: ClientSession, test_project_root: Path
) -> None:
    """SC-47: stash-list returns name, source_file, line_range, line_count, first_line_preview.

    RED: clipboard stash-list action does not exist; call_tool will fail.
    GREEN: stash-list output includes all required metadata fields.
    """
    sid = _unique_sid()
    file_path = "stash_src.txt"

    result_open = await client_session.call_tool(
        "viewport",
        arguments={
            "action": "open",
            "session_id": sid,
            "file_path": file_path,
        },
    )
    assert "error" not in _get_text(result_open)
    vpid = _extract_vpid(_get_text(result_open))

    await client_session.call_tool(
        "clipboard",
        arguments={
            "action": "copy",
            "session_id": sid,
            "viewport_id": vpid,
            "start_line": 2,
            "end_line": 4,
        },
    )

    stash_result = await client_session.call_tool(
        "clipboard",
        arguments={"action": "stash", "session_id": sid, "name": "meta_slot"},
    )
    assert not stash_result.isError, (
        f"Precondition: stash must work: {_get_text(stash_result)[:200]}"
    )

    list_result = await client_session.call_tool(
        "clipboard",
        arguments={"action": "stash-list", "session_id": sid},
    )
    list_text = _get_text(list_result)

    assert not list_result.isError, (
        f"RED FAIL: clipboard:stash-list not implemented: {list_text[:200]}"
    )
    assert "error" not in list_text.lower(), (
        f"RED FAIL: clipboard:stash-list returned error: {list_text[:200]}"
    )

    assert "meta_slot" in list_text, (
        f"SC-47: stash-list must include slot name (meta_slot): {list_text[:300]}"
    )
    assert "source_file" in list_text, (
        f"SC-47: stash-list must include source_file: {list_text[:300]}"
    )
    assert "line_range" in list_text or "start_line" in list_text, (
        f"SC-47: stash-list must include line_range: {list_text[:300]}"
    )
    assert "line_count" in list_text, (
        f"SC-47: stash-list must include line_count: {list_text[:300]}"
    )
    assert "first_line" in list_text or "preview" in list_text, (
        f"SC-47: stash-list must include first_line_preview: {list_text[:300]}"
    )

    assert "beta" in list_text, (
        f"SC-47: first_line_preview must show first line content (beta): {list_text[:300]}"
    )


@pytest.mark.phase3
@pytest.mark.asyncio
async def test_stash_list_empty_returns_empty(
    client_session: ClientSession, test_project_root: Path
) -> None:
    """SC-47: stash-list with no stashes returns empty list.

    RED: clipboard stash-list action does not exist; call_tool will fail.
    GREEN: fresh session returns empty list or no-slot message (not error).
    """
    sid = _unique_sid()

    list_result = await client_session.call_tool(
        "clipboard",
        arguments={"action": "stash-list", "session_id": sid},
    )
    list_text = _get_text(list_result)

    assert not list_result.isError, (
        f"RED FAIL: clipboard:stash-list not implemented: {list_text[:200]}"
    )

    has_no_slots = (
        "no stash" in list_text.lower()
        or "empty" in list_text.lower()
        or "0 stash" in list_text.lower()
        or list_text.strip() == ""
    )
    assert has_no_slots, (
        f"SC-47: stash-list with no stashes must indicate empty/no slots: {list_text[:300]}"
    )


@pytest.mark.phase3
@pytest.mark.asyncio
async def test_stash_list_after_multiple_stash(
    client_session: ClientSession, test_project_root: Path
) -> None:
    """SC-47: multiple stashes all appear in stash-list.

    RED: clipboard stash action does not exist; call_tool will fail.
    GREEN: after stashing to 'alpha' and 'beta', stash-list shows both.
    """
    sid = _unique_sid()
    file_path = "stash_other.txt"

    result_open = await client_session.call_tool(
        "viewport",
        arguments={
            "action": "open",
            "session_id": sid,
            "file_path": file_path,
        },
    )
    assert "error" not in _get_text(result_open)
    vpid = _extract_vpid(_get_text(result_open))

    await client_session.call_tool(
        "clipboard",
        arguments={
            "action": "copy",
            "session_id": sid,
            "viewport_id": vpid,
            "start_line": 1,
            "end_line": 2,
        },
    )

    stash_a = await client_session.call_tool(
        "clipboard",
        arguments={"action": "stash", "session_id": sid, "name": "slot_alpha"},
    )
    assert not stash_a.isError, (
        f"Precondition: stash must work: {_get_text(stash_a)[:200]}"
    )

    await client_session.call_tool(
        "clipboard",
        arguments={
            "action": "copy",
            "session_id": sid,
            "viewport_id": vpid,
            "start_line": 3,
            "end_line": 5,
        },
    )

    stash_b = await client_session.call_tool(
        "clipboard",
        arguments={"action": "stash", "session_id": sid, "name": "slot_beta"},
    )
    assert not stash_b.isError, (
        f"Precondition: second stash must work: {_get_text(stash_b)[:200]}"
    )

    list_result = await client_session.call_tool(
        "clipboard",
        arguments={"action": "stash-list", "session_id": sid},
    )
    list_text = _get_text(list_result)

    assert not list_result.isError, (
        f"RED FAIL: clipboard:stash-list not implemented: {list_text[:200]}"
    )

    assert "slot_alpha" in list_text, (
        f"SC-47: stash-list must show first slot (slot_alpha): {list_text[:300]}"
    )
    assert "slot_beta" in list_text, (
        f"SC-47: stash-list must show second slot (slot_beta): {list_text[:300]}"
    )
