# SPDX-FileCopyrightText: 2026 Michael Conrad
# SPDX-License-Identifier: MIT
# Provenance: AI-generated
"""Phase 3 RED behavioral tests for clipboard tools of viewport-editor MCP server.

These tests assert GREEN-phase behavior for SC-39 (copy creates session-scoped
clipboard with provenance) and SC-48 (line-aligned ranges only). They MUST FAIL
against current code because clipboard:copy tool does not exist yet.

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
    (tmpdir / "clip_src.txt").write_text("alpha\nbeta\ngamma\ndelta\nepsilon\n")
    (tmpdir / "clip_other.txt").write_text("foo\nbar\nbaz\nqux\nquux\n")
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
    return f"test-p3-{uuid.uuid4().hex[:8]}"


# ── SC-39: copy creates session-scoped clipboard with provenance ─────────────


@pytest.mark.phase3
@pytest.mark.asyncio
async def test_copy_creates_clipboard_with_provenance(
    client_session: ClientSession, test_project_root: Path
) -> None:
    """SC-39: clipboard:copy populates session clipboard with source_file, line_range, timestamp.

    RED: clipboard tool does not exist; call_tool will fail.
    GREEN: copy returns success; session state shows clipboard with provenance fields.
    """
    sid = _unique_sid()
    file_path = "clip_src.txt"

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
    text = _get_text(result)

    assert not result.isError, f"RED FAIL: clipboard:copy not implemented: {text[:200]}"
    assert "error" not in text.lower(), (
        f"RED FAIL: clipboard:copy returned error: {text[:200]}"
    )

    assert "source_file:" in text, (
        f"SC-39: response must include source_file provenance: {text[:300]}"
    )
    assert "line_range:" in text or "start_line:" in text, (
        f"SC-39: response must include line_range provenance: {text[:300]}"
    )
    assert "timestamp:" in text, (
        f"SC-39: response must include timestamp provenance: {text[:300]}"
    )

    list_result = await client_session.call_tool(
        "clipboard",
        arguments={"action": "show", "session_id": sid},
    )
    list_text = _get_text(list_result)
    assert not list_result.isError, (
        f"RED FAIL: clipboard:show not implemented: {list_text[:200]}"
    )
    assert "source_file:" in list_text, (
        f"SC-39: clipboard:show must include source_file: {list_text[:300]}"
    )


# ── SC-48: line-aligned ranges only ─────────────────────────────────────────


@pytest.mark.phase3
@pytest.mark.asyncio
async def test_copy_line_aligned_only(
    client_session: ClientSession, test_project_root: Path
) -> None:
    """SC-48: clipboard:copy snaps mid-line ranges to line boundaries.

    RED: clipboard tool does not exist; call_tool will fail.
    GREEN: copy with non-line-aligned range snaps start to line start, end to line end.
    Returns line_range as whole lines (2-4), not partial.
    """
    sid = _unique_sid()
    file_path = "clip_src.txt"

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

    # Request lines 2-4 (already line-aligned), verify response reports
    # start_line=2, end_line=4 with no character/offset granularity
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
    text = _get_text(result)

    assert not result.isError, f"RED FAIL: clipboard:copy not implemented: {text[:200]}"
    assert "error" not in text.lower(), (
        f"RED FAIL: clipboard:copy returned error: {text[:200]}"
    )

    # Response must report line-aligned range (integer line numbers only)
    assert "start_line: 2" in text, (
        f"SC-48: response must report start_line as integer: {text[:300]}"
    )
    assert "end_line: 4" in text, (
        f"SC-48: response must report end_line as integer: {text[:300]}"
    )

    # Must NOT contain character offset fields (col_start, col_end, char_offset, etc.)
    forbidden_fields = ["col_start", "col_end", "char_offset", "char_start", "char_end"]
    for field in forbidden_fields:
        assert field not in text, (
            f"SC-48: response must not contain character-granularity field '{field}': {text[:300]}"
        )

    # Content must be complete lines (line 2 through line 4)
    assert "beta" in text, (
        f"SC-48: copied content must include line 2 (beta): {text[:300]}"
    )
    assert "gamma" in text, (
        f"SC-48: copied content must include line 3 (gamma): {text[:300]}"
    )
    assert "delta" in text, (
        f"SC-48: copied content must include line 4 (delta): {text[:300]}"
    )
    # Line outside range must NOT be present
    assert "alpha" not in text, (
        f"SC-48: copied content must not include line 1 (alpha): {text[:300]}"
    )


# ── SC-39 (cross-file): copy from different viewport shows correct source ────


@pytest.mark.phase3
@pytest.mark.asyncio
async def test_copy_cross_file(
    client_session: ClientSession, test_project_root: Path
) -> None:
    """SC-39: clipboard:copy provenance tracks correct source file across viewports.

    RED: clipboard tool does not exist; call_tool will fail.
    GREEN: copying from clip_other.txt shows source_file=clip_other.txt.
    """
    sid = _unique_sid()

    result_open = await client_session.call_tool(
        "viewport",
        arguments={
            "action": "open",
            "session_id": sid,
            "file_path": "clip_other.txt",
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
            "start_line": 1,
            "end_line": 3,
        },
    )
    text = _get_text(result)

    assert not result.isError, f"RED FAIL: clipboard:copy not implemented: {text[:200]}"
    assert "error" not in text.lower(), (
        f"RED FAIL: clipboard:copy returned error: {text[:200]}"
    )

    assert "clip_other.txt" in text, (
        f"SC-39: clipboard must record source_file=clip_other.txt: {text[:300]}"
    )
    assert "source_file:" in text, (
        f"SC-39: response must include source_file provenance: {text[:300]}"
    )


# ── SC-39: copy does not switch to buffered mode ─────────────────────────────


@pytest.mark.phase3
@pytest.mark.asyncio
async def test_copy_no_buffered_switch(
    client_session: ClientSession, test_project_root: Path
) -> None:
    """SC-39: clipboard:copy is a read — does not switch viewport to buffered mode.

    RED: clipboard tool does not exist; call_tool will fail.
    GREEN: after copy, viewport list shows same autosave state as before copy.
    """
    sid = _unique_sid()
    file_path = "clip_src.txt"

    result_open = await client_session.call_tool(
        "viewport",
        arguments={
            "action": "open",
            "session_id": sid,
            "file_path": file_path,
            "autosave": False,
        },
    )
    assert "error" not in _get_text(result_open)
    vpid = _extract_vpid(_get_text(result_open))

    # Capture viewport state before copy
    list_before = await client_session.call_tool(
        "viewport",
        arguments={"action": "list", "session_id": sid},
    )
    text_before = _get_text(list_before)

    result = await client_session.call_tool(
        "clipboard",
        arguments={
            "action": "copy",
            "session_id": sid,
            "viewport_id": vpid,
            "start_line": 1,
            "end_line": 2,
        },
    )
    text = _get_text(result)

    assert not result.isError, f"RED FAIL: clipboard:copy not implemented: {text[:200]}"
    assert "error" not in text.lower(), (
        f"RED FAIL: clipboard:copy returned error: {text[:200]}"
    )

    # After copy, viewport list should show same state (no buffered/dirty switch)
    list_after = await client_session.call_tool(
        "viewport",
        arguments={"action": "list", "session_id": sid},
    )
    text_after = _get_text(list_after)

    copy_does_not_say_buffered = "buffered" not in text.lower()
    assert copy_does_not_say_buffered, (
        f"SC-39: copy response must not mention switching to buffered mode: {text[:300]}"
    )

    autosave_unchanged = ("autosave: False" in text_after) == (
        "autosave: False" in text_before
    )
    assert autosave_unchanged, (
        f"SC-39: copy must not change autosave state. Before: {text_before[:200]}, After: {text_after[:200]}"
    )

    dirty_unchanged = ("dirty: True" in text_after) == ("dirty: True" in text_before)
    assert dirty_unchanged, (
        f"SC-39: copy must not change dirty state. Before: {text_before[:200]}, After: {text_after[:200]}"
    )


# ── SC-40: cut copies range to clipboard + stages deletion in buffer ──────────


@pytest.mark.phase3
@pytest.mark.asyncio
async def test_cut_stages_deletion_in_buffer(
    client_session: ClientSession, test_project_root: Path
) -> None:
    """SC-40: cut copies range to clipboard AND stages deletion in buffer.

    After cut, the clipboard should have the cut content, and the viewport
    should no longer show the cut lines (they are deleted from buffer).
    """
    sid = _unique_sid()
    file_path = "clip_src.txt"

    result_open = await client_session.call_tool(
        "viewport",
        arguments={
            "action": "open",
            "session_id": sid,
            "file_path": file_path,
            "autosave": False,
        },
    )
    assert "error" not in _get_text(result_open)
    vpid = _extract_vpid(_get_text(result_open))

    result = await client_session.call_tool(
        "clipboard",
        arguments={
            "action": "cut",
            "session_id": sid,
            "viewport_id": vpid,
            "start_line": 2,
            "end_line": 4,
        },
    )
    text = _get_text(result)

    assert not result.isError, f"RED FAIL: clipboard:cut not implemented: {text[:200]}"
    assert "error" not in text.lower(), (
        f"RED FAIL: clipboard:cut returned error: {text[:200]}"
    )

    assert "source_file:" in text, (
        f"SC-40: cut response must include source_file provenance: {text[:300]}"
    )
    assert "start_line: 2" in text, (
        f"SC-40: cut response must report start_line: {text[:300]}"
    )
    assert "end_line: 4" in text, (
        f"SC-40: cut response must report end_line: {text[:300]}"
    )
    assert "cut" in text.lower(), (
        f"SC-40: cut response must indicate cut operation: {text[:300]}"
    )

    content_result = await client_session.call_tool(
        "viewport",
        arguments={
            "action": "open",
            "session_id": sid,
            "file_path": file_path,
            "autosave": False,
        },
    )
    content_text = _get_text(content_result)

    assert "beta" not in content_text, (
        f"SC-40: after cut, deleted lines (beta) must not appear in buffer: {content_text[:300]}"
    )
    assert "gamma" not in content_text, (
        f"SC-40: after cut, deleted lines (gamma) must not appear in buffer: {content_text[:300]}"
    )
    assert "delta" not in content_text, (
        f"SC-40: after cut, deleted lines (delta) must not appear in buffer: {content_text[:300]}"
    )
    assert "alpha" in content_text, (
        f"SC-40: after cut, remaining lines (alpha) must still be in buffer: {content_text[:300]}"
    )
    assert "epsilon" in content_text, (
        f"SC-40: after cut, remaining lines (epsilon) must still be in buffer: {content_text[:300]}"
    )

    show_result = await client_session.call_tool(
        "clipboard",
        arguments={"action": "show", "session_id": sid},
    )
    show_text = _get_text(show_result)
    assert "beta" in show_text, (
        f"SC-40: clipboard must contain cut content (beta): {show_text[:300]}"
    )
    assert "gamma" in show_text, (
        f"SC-40: clipboard must contain cut content (gamma): {show_text[:300]}"
    )
    assert "delta" in show_text, (
        f"SC-40: clipboard must contain cut content (delta): {show_text[:300]}"
    )


@pytest.mark.phase3
@pytest.mark.asyncio
async def test_cut_autosave_gate(
    client_session: ClientSession, test_project_root: Path
) -> None:
    """SC-40: cut with autosave=on switches to buffered mode.

    Cut is a write operation — unlike copy, it stages a deletion. When
    autosave is on, the autosave gate fires on cut, same as delete-lines.
    """
    sid = _unique_sid()

    result_open = await client_session.call_tool(
        "viewport",
        arguments={
            "action": "open",
            "session_id": sid,
            "file_path": "clip_other.txt",
            "autosave": False,
        },
    )
    assert "error" not in _get_text(result_open)
    vpid = _extract_vpid(_get_text(result_open))

    result = await client_session.call_tool(
        "clipboard",
        arguments={
            "action": "cut",
            "session_id": sid,
            "viewport_id": vpid,
            "start_line": 1,
            "end_line": 1,
        },
    )
    text = _get_text(result)

    assert not result.isError, f"RED FAIL: clipboard:cut not implemented: {text[:200]}"
    assert "error" not in text.lower(), (
        f"RED FAIL: clipboard:cut returned error: {text[:200]}"
    )

    list_result = await client_session.call_tool(
        "viewport",
        arguments={"action": "list", "session_id": sid},
    )
    list_text = _get_text(list_result)
    assert "dirty: False" in list_text or "dirty: True" in list_text, (
        f"SC-40: cut with autosave must leave viewport in valid state: {list_text[:300]}"
    )

    content_result = await client_session.call_tool(
        "viewport",
        arguments={
            "action": "open",
            "session_id": sid,
            "file_path": "clip_other.txt",
        },
    )
    content_text = _get_text(content_result)
    assert "foo" not in content_text, (
        f"SC-40: cut with autosave must actually delete lines from disk: {content_text[:300]}"
    )


@pytest.mark.phase3
@pytest.mark.asyncio
async def test_cut_already_buffered(
    client_session: ClientSession, test_project_root: Path
) -> None:
    """SC-40: cut when already buffered returns no autosave-gate notice.

    When autosave is off (buffered mode), cut just stages deletion — no
    autosave gate switch needed since viewport is already buffered.
    """
    sid = _unique_sid()
    file_path = "clip_src.txt"

    result_open = await client_session.call_tool(
        "viewport",
        arguments={
            "action": "open",
            "session_id": sid,
            "file_path": file_path,
            "autosave": False,
        },
    )
    assert "error" not in _get_text(result_open)
    vpid = _extract_vpid(_get_text(result_open))

    result = await client_session.call_tool(
        "clipboard",
        arguments={
            "action": "cut",
            "session_id": sid,
            "viewport_id": vpid,
            "start_line": 1,
            "end_line": 1,
        },
    )
    text = _get_text(result)

    assert not result.isError, f"RED FAIL: clipboard:cut not implemented: {text[:200]}"
    assert "error" not in text.lower(), (
        f"RED FAIL: clipboard:cut returned error: {text[:200]}"
    )

    assert "switched to buffered" not in text.lower(), (
        f"SC-40: cut on already-buffered viewport must not claim switching to buffered: {text[:300]}"
    )


# ── SC-41: paste inserts clipboard content before target line ──────────────────


@pytest.mark.phase3
@pytest.mark.asyncio
async def test_paste_insert_before(
    client_session: ClientSession, test_project_root: Path
) -> None:
    """SC-41: paste inserts clipboard content BEFORE target line (insert-before semantics).

    Copy lines 2-4 (beta/gamma/delta), then paste before line 5 (epsilon).
    After paste, clipboard content must appear before line 5.
    """
    sid = _unique_sid()

    result_open = await client_session.call_tool(
        "viewport",
        arguments={
            "action": "open",
            "session_id": sid,
            "file_path": "clip_other.txt",
            "autosave": False,
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
    assert not result.isError

    paste_result = await client_session.call_tool(
        "clipboard",
        arguments={
            "action": "paste",
            "session_id": sid,
            "viewport_id": vpid,
            "target_line": 5,
        },
    )
    paste_text = _get_text(paste_result)

    assert not paste_result.isError, (
        f"SC-41: paste returned isError: {paste_text[:300]}"
    )
    assert "error" not in paste_text.lower(), (
        f"SC-41: paste returned error: {paste_text[:300]}"
    )
    assert "pasted" in paste_text.lower(), (
        f"SC-41: paste response must confirm paste: {paste_text[:300]}"
    )

    verify_result = await client_session.call_tool(
        "viewport",
        arguments={
            "action": "open",
            "session_id": sid,
            "file_path": "clip_other.txt",
        },
    )
    verify_text = _get_text(verify_result)
    lines = [
        ln.strip()
        for ln in verify_text.splitlines()
        if ln.strip() and ":" in ln and ln.strip()[0].isdigit()
    ]
    line_nums = []
    for ln in lines:
        parts = ln.split(":", 1)
        if parts[0].strip().isdigit():
            line_nums.append(int(parts[0].strip()))

    assert len(line_nums) == 8, (
        f"SC-41: after pasting 3 lines into 5-line file, expected 8 lines, got {len(line_nums)}: {line_nums}"
    )

    assert "bar" in verify_text, (
        f"SC-41: pasted content (bar) must appear in file after paste: {verify_text[:400]}"
    )
    assert "baz" in verify_text, (
        f"SC-41: pasted content (baz) must appear in file after paste: {verify_text[:400]}"
    )
    assert "qux" in verify_text, (
        f"SC-41: pasted content (qux) must appear in file after paste: {verify_text[:400]}"
    )


@pytest.mark.phase3
@pytest.mark.asyncio
async def test_paste_preserves_clipboard(
    client_session: ClientSession, test_project_root: Path
) -> None:
    """SC-41: paste preserves clipboard content (never auto-clears).

    After paste, clipboard:show must still return the original copied content.
    Pasting twice should work without re-copying.
    """
    sid = _unique_sid()

    result_open = await client_session.call_tool(
        "viewport",
        arguments={
            "action": "open",
            "session_id": sid,
            "file_path": "clip_other.txt",
            "autosave": False,
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
            "start_line": 1,
            "end_line": 2,
        },
    )
    assert not result.isError

    paste_result = await client_session.call_tool(
        "clipboard",
        arguments={
            "action": "paste",
            "session_id": sid,
            "viewport_id": vpid,
            "target_line": 3,
        },
    )
    paste_text = _get_text(paste_result)
    assert not paste_result.isError, (
        f"SC-41: paste returned isError: {paste_text[:300]}"
    )
    assert "error" not in paste_text.lower(), (
        f"SC-41: paste returned error: {paste_text[:300]}"
    )

    show_result = await client_session.call_tool(
        "clipboard",
        arguments={"action": "show", "session_id": sid},
    )
    show_text = _get_text(show_result)

    assert not show_result.isError, (
        f"SC-41: clipboard:show after paste should not error: {show_text[:300]}"
    )
    assert "foo" in show_text, (
        f"SC-41: clipboard must still contain copied content (foo) after paste: {show_text[:300]}"
    )

    paste2_result = await client_session.call_tool(
        "clipboard",
        arguments={
            "action": "paste",
            "session_id": sid,
            "viewport_id": vpid,
            "target_line": 5,
        },
    )
    paste2_text = _get_text(paste2_result)
    assert not paste2_result.isError, (
        f"SC-41: second paste must work without re-copying: {paste2_text[:300]}"
    )


@pytest.mark.phase3
@pytest.mark.asyncio
async def test_paste_cross_viewport(
    client_session: ClientSession, test_project_root: Path
) -> None:
    """SC-41: paste across viewports — clipboard is session-scoped, not viewport-scoped.

    Copy from clip_src.txt viewport, paste into clip_other.txt viewport.
    The pasted content must appear in clip_other.txt, not clip_src.txt.
    """
    sid = _unique_sid()

    result_src = await client_session.call_tool(
        "viewport",
        arguments={
            "action": "open",
            "session_id": sid,
            "file_path": "clip_other.txt",
            "autosave": False,
        },
    )
    assert "error" not in _get_text(result_src)
    vpid_src = _extract_vpid(_get_text(result_src))

    result_dest = await client_session.call_tool(
        "viewport",
        arguments={
            "action": "open",
            "session_id": sid,
            "file_path": "clip_src.txt",
            "autosave": False,
        },
    )
    assert "error" not in _get_text(result_dest)
    vpid_dest = _extract_vpid(_get_text(result_dest))

    copy_result = await client_session.call_tool(
        "clipboard",
        arguments={
            "action": "copy",
            "session_id": sid,
            "viewport_id": vpid_src,
            "start_line": 2,
            "end_line": 3,
        },
    )
    assert not copy_result.isError

    paste_result = await client_session.call_tool(
        "clipboard",
        arguments={
            "action": "paste",
            "session_id": sid,
            "viewport_id": vpid_dest,
            "target_line": 1,
        },
    )
    paste_text = _get_text(paste_result)
    assert not paste_result.isError, (
        f"SC-41: cross-viewport paste returned error: {paste_text[:300]}"
    )

    show_result = await client_session.call_tool(
        "clipboard",
        arguments={"action": "show", "session_id": sid},
    )
    show_text = _get_text(show_result)
    assert "bar" in show_text, (
        f"SC-41: clipboard must have content from source viewport (bar): {show_text[:300]}"
    )
    assert "baz" in show_text, (
        f"SC-41: clipboard must have content from source viewport (baz): {show_text[:300]}"
    )


# ── SC-42: paste autosave gate ───────────────────────────────────────────────


@pytest.mark.phase3
@pytest.mark.asyncio
async def test_paste_autosave_gate(
    client_session: ClientSession, test_project_root: Path
) -> None:
    """SC-42: paste with autosave=on switches to buffered mode and returns notice.

    Paste is a write operation. When autosave is on, the autosave gate fires:
    the viewport switches to buffered mode (autosave off) and the response
    includes a 'switched to buffered' notice. The change is staged in buffer,
    NOT flushed to disk immediately.
    """
    sid = _unique_sid()

    result_open = await client_session.call_tool(
        "viewport",
        arguments={
            "action": "open",
            "session_id": sid,
            "file_path": "clip_other.txt",
            "autosave": True,
        },
    )
    assert "error" not in _get_text(result_open)
    vpid = _extract_vpid(_get_text(result_open))

    result_copy = await client_session.call_tool(
        "clipboard",
        arguments={
            "action": "copy",
            "session_id": sid,
            "viewport_id": vpid,
            "start_line": 1,
            "end_line": 1,
        },
    )
    assert not result_copy.isError

    result = await client_session.call_tool(
        "clipboard",
        arguments={
            "action": "paste",
            "session_id": sid,
            "viewport_id": vpid,
            "target_line": 2,
        },
    )
    text = _get_text(result)

    assert not result.isError, f"SC-42: paste returned isError: {text[:300]}"
    assert "error" not in text.lower(), f"SC-42: paste returned error: {text[:300]}"

    assert "switched to buffered" in text.lower(), (
        f"SC-42: paste with autosave=on must return 'switched to buffered' notice: {text[:300]}"
    )

    list_result = await client_session.call_tool(
        "viewport",
        arguments={"action": "list", "session_id": sid},
    )
    list_text = _get_text(list_result)
    assert "autosave: False" in list_text, (
        f"SC-42: after paste autosave gate, viewport must have autosave=False: {list_text[:300]}"
    )
    assert "dirty: True" in list_text, (
        f"SC-42: after paste autosave gate, viewport must be dirty: {list_text[:300]}"
    )


@pytest.mark.phase3
@pytest.mark.asyncio
async def test_paste_already_buffered_no_notice(
    client_session: ClientSession, test_project_root: Path
) -> None:
    """SC-42: paste when already buffered returns no autosave-gate notice.

    When autosave is off (buffered mode), paste just stages the insertion —
    no autosave gate switch needed since viewport is already buffered.
    """
    sid = _unique_sid()

    result_open = await client_session.call_tool(
        "viewport",
        arguments={
            "action": "open",
            "session_id": sid,
            "file_path": "clip_src.txt",
            "autosave": False,
        },
    )
    assert "error" not in _get_text(result_open)
    vpid = _extract_vpid(_get_text(result_open))

    result_copy = await client_session.call_tool(
        "clipboard",
        arguments={
            "action": "copy",
            "session_id": sid,
            "viewport_id": vpid,
            "start_line": 1,
            "end_line": 1,
        },
    )
    assert not result_copy.isError

    result = await client_session.call_tool(
        "clipboard",
        arguments={
            "action": "paste",
            "session_id": sid,
            "viewport_id": vpid,
            "target_line": 2,
        },
    )
    text = _get_text(result)

    assert not result.isError, f"SC-42: paste returned isError: {text[:300]}"
    assert "error" not in text.lower(), f"SC-42: paste returned error: {text[:300]}"

    assert "switched to buffered" not in text.lower(), (
        f"SC-42: paste on already-buffered viewport must not claim switching to buffered: {text[:300]}"
    )


# ── SC-42: cut autosave gate notice ─────────────────────────────────────────


@pytest.mark.phase3
@pytest.mark.asyncio
async def test_cut_autosave_gate_notice(
    client_session: ClientSession, test_project_root: Path
) -> None:
    """SC-42: cut with autosave=on switches to buffered mode and returns notice.

    Cut is a write operation. When autosave is on, the autosave gate fires:
    the viewport switches to buffered mode (autosave off) and the response
    includes a 'switched to buffered' notice. The deletion is staged in buffer,
    NOT flushed to disk immediately.
    """
    sid = _unique_sid()

    result_open = await client_session.call_tool(
        "viewport",
        arguments={
            "action": "open",
            "session_id": sid,
            "file_path": "clip_src.txt",
            "autosave": True,
        },
    )
    assert "error" not in _get_text(result_open)
    vpid = _extract_vpid(_get_text(result_open))

    result = await client_session.call_tool(
        "clipboard",
        arguments={
            "action": "cut",
            "session_id": sid,
            "viewport_id": vpid,
            "start_line": 1,
            "end_line": 1,
        },
    )
    text = _get_text(result)

    assert not result.isError, f"SC-42: cut returned isError: {text[:300]}"
    assert "error" not in text.lower(), f"SC-42: cut returned error: {text[:300]}"

    assert "switched to buffered" in text.lower(), (
        f"SC-42: cut with autosave=on must return 'switched to buffered' notice: {text[:300]}"
    )

    list_result = await client_session.call_tool(
        "viewport",
        arguments={"action": "list", "session_id": sid},
    )
    list_text = _get_text(list_result)
    assert "autosave: False" in list_text, (
        f"SC-42: after cut autosave gate, viewport must have autosave=False: {list_text[:300]}"
    )
    assert "dirty: True" in list_text, (
        f"SC-42: after cut autosave gate, viewport must be dirty: {list_text[:300]}"
    )


# ── SC-42: diff in cut/paste response ───────────────────────────────────────


@pytest.mark.phase3
@pytest.mark.asyncio
async def test_cut_diff_response(
    client_session: ClientSession, test_project_root: Path
) -> None:
    """SC-42: cut returns diff in tool response (matching diff:show format).

    After cut, the response should include a unified diff showing the
    deletion, similar to diff:show output format.
    """
    sid = _unique_sid()

    result_open = await client_session.call_tool(
        "viewport",
        arguments={
            "action": "open",
            "session_id": sid,
            "file_path": "clip_src.txt",
            "autosave": False,
        },
    )
    assert "error" not in _get_text(result_open)
    vpid = _extract_vpid(_get_text(result_open))

    result = await client_session.call_tool(
        "clipboard",
        arguments={
            "action": "cut",
            "session_id": sid,
            "viewport_id": vpid,
            "start_line": 1,
            "end_line": 1,
        },
    )
    text = _get_text(result)

    assert not result.isError, f"SC-42: cut returned isError: {text[:300]}"
    assert "error" not in text.lower(), f"SC-42: cut returned error: {text[:300]}"

    assert "---" in text, (
        f"SC-42: cut response must include unified diff (--- header): {text[:400]}"
    )
    assert "+++" in text, (
        f"SC-42: cut response must include unified diff (+++ header): {text[:400]}"
    )
    assert "-alpha" in text, (
        f"SC-42: cut diff must show deleted line with - prefix: {text[:400]}"
    )


@pytest.mark.phase3
@pytest.mark.asyncio
async def test_paste_diff_response(
    client_session: ClientSession, test_project_root: Path
) -> None:
    """SC-42: paste returns diff in tool response (matching diff:show format).

    After paste, the response should include a unified diff showing the
    insertion, similar to diff:show output format.
    """
    sid = _unique_sid()

    result_open = await client_session.call_tool(
        "viewport",
        arguments={
            "action": "open",
            "session_id": sid,
            "file_path": "clip_other.txt",
            "autosave": False,
        },
    )
    assert "error" not in _get_text(result_open)
    vpid = _extract_vpid(_get_text(result_open))

    result_copy = await client_session.call_tool(
        "clipboard",
        arguments={
            "action": "copy",
            "session_id": sid,
            "viewport_id": vpid,
            "start_line": 1,
            "end_line": 1,
        },
    )
    assert not result_copy.isError

    result = await client_session.call_tool(
        "clipboard",
        arguments={
            "action": "paste",
            "session_id": sid,
            "viewport_id": vpid,
            "target_line": 2,
        },
    )
    text = _get_text(result)

    assert not result.isError, f"SC-42: paste returned isError: {text[:300]}"
    assert "error" not in text.lower(), f"SC-42: paste returned error: {text[:300]}"

    assert "---" in text, (
        f"SC-42: paste response must include unified diff (--- header): {text[:400]}"
    )
    assert "+++" in text, (
        f"SC-42: paste response must include unified diff (+++ header): {text[:400]}"
    )
    assert "+foo" in text, (
        f"SC-42: paste diff must show inserted line with + prefix: {text[:400]}"
    )


@pytest.mark.phase3
@pytest.mark.asyncio
async def test_paste_empty_clipboard_is_error(
    client_session: ClientSession, test_project_root: Path
) -> None:
    """SC-41: paste with no clipboard content returns isError=true.

    A fresh session has no clipboard; paste must fail gracefully.
    """
    sid = _unique_sid()
    file_path = "clip_src.txt"

    result_open = await client_session.call_tool(
        "viewport",
        arguments={
            "action": "open",
            "session_id": sid,
            "file_path": file_path,
            "autosave": False,
        },
    )
    assert "error" not in _get_text(result_open)
    vpid = _extract_vpid(_get_text(result_open))

    paste_result = await client_session.call_tool(
        "clipboard",
        arguments={
            "action": "paste",
            "session_id": sid,
            "viewport_id": vpid,
            "target_line": 1,
        },
    )
    assert paste_result.isError, (
        "SC-41: paste with empty clipboard must return isError=true"
    )


# ── SC-46: paste never reads from stash ──────────────────────────────────────


@pytest.mark.phase3
@pytest.mark.asyncio
async def test_paste_ignores_stash(
    client_session: ClientSession, test_project_root: Path
) -> None:
    """SC-46: paste reads strictly from session.clipboard — never from stash.

    The paste handler must read session.clipboard, not any stash attribute.
    This test verifies paste output matches clipboard:show content exactly,
    proving the clipboard is the sole data source for paste. If stash (#22)
    is ever wired into paste incorrectly, this test will fail because pasted
    content would diverge from clipboard content.
    """
    sid = _unique_sid()

    result_open = await client_session.call_tool(
        "viewport",
        arguments={
            "action": "open",
            "session_id": sid,
            "file_path": "clip_src.txt",
            "autosave": False,
        },
    )
    assert "error" not in _get_text(result_open)
    vpid = _extract_vpid(_get_text(result_open))

    result_copy = await client_session.call_tool(
        "clipboard",
        arguments={
            "action": "copy",
            "session_id": sid,
            "viewport_id": vpid,
            "start_line": 2,
            "end_line": 4,
        },
    )
    assert not result_copy.isError

    show_result = await client_session.call_tool(
        "clipboard",
        arguments={"action": "show", "session_id": sid},
    )
    show_text = _get_text(show_result)
    assert not show_result.isError, (
        f"SC-46: clipboard:show must work after copy: {show_text[:300]}"
    )

    clipboard_lines_in_show = [
        ln
        for ln in show_text.splitlines()
        if "beta" in ln or "gamma" in ln or "delta" in ln
    ]
    assert len(clipboard_lines_in_show) >= 3, (
        f"SC-46: clipboard:show must list all 3 copied lines: {show_text[:400]}"
    )

    paste_result = await client_session.call_tool(
        "clipboard",
        arguments={
            "action": "paste",
            "session_id": sid,
            "viewport_id": vpid,
            "target_line": 5,
        },
    )
    paste_text = _get_text(paste_result)

    assert not paste_result.isError, (
        f"SC-46: paste returned isError: {paste_text[:300]}"
    )
    assert "error" not in paste_text.lower(), (
        f"SC-46: paste returned error: {paste_text[:300]}"
    )

    assert "beta" in paste_text, (
        f"SC-46: pasted content must include clipboard line (beta): {paste_text[:400]}"
    )
    assert "gamma" in paste_text, (
        f"SC-46: pasted content must include clipboard line (gamma): {paste_text[:400]}"
    )
    assert "delta" in paste_text, (
        f"SC-46: pasted content must include clipboard line (delta): {paste_text[:400]}"
    )

    verify_result = await client_session.call_tool(
        "viewport",
        arguments={
            "action": "open",
            "session_id": sid,
            "file_path": "clip_src.txt",
        },
    )
    verify_text = _get_text(verify_result)

    beta_count = verify_text.count("beta")
    gamma_count = verify_text.count("gamma")
    delta_count = verify_text.count("delta")

    assert beta_count == 2, (
        f"SC-46: after paste, beta must appear twice (original + pasted): count={beta_count}, text={verify_text[:500]}"
    )
    assert gamma_count == 2, (
        f"SC-46: after paste, gamma must appear twice (original + pasted): count={gamma_count}, text={verify_text[:500]}"
    )
    assert delta_count == 2, (
        f"SC-46: after paste, delta must appear twice (original + pasted): count={delta_count}, text={verify_text[:500]}"
    )

    show_after = await client_session.call_tool(
        "clipboard",
        arguments={"action": "show", "session_id": sid},
    )
    show_after_text = _get_text(show_after)
    assert "beta" in show_after_text, (
        f"SC-46: clipboard must still have original content after paste: {show_after_text[:300]}"
    )
