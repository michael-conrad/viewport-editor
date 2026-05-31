# SPDX-FileCopyrightText: 2026 Michael Conrad
# SPDX-License-Identifier: MIT
# Provenance: AI-generated
"""Phase 3 RED behavioral tests for file operations + autosave integration.

RED tests that MUST FAIL against current code (missing feature implementations).
GREEN phase implements the missing features to make these tests PASS.

Co-authored with AI: OpenCode (ollama-cloud/deepseek-v4-flash)
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import AsyncIterator

import pytest
from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client
from mcp.types import CallToolResult


@pytest.fixture(scope="module")
def test_project_root() -> Path:
    tmpdir = Path(tempfile.mkdtemp(prefix="ve-test-"))
    (tmpdir / "existing_save_as.txt").write_text("save-as target\n")
    (tmpdir / "delete_me.txt").write_text("will be deleted\n")
    (tmpdir / "close_test.txt").write_text("line 1\nline 2\nline 3\n")
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


# ── SC-14: autosave=on no-op for file:save, diff:show, file:discard ─────────


@pytest.mark.phase3
@pytest.mark.asyncio
async def test_sc14_autosave_on_file_save_noop(
    client_session: ClientSession, test_project_root: Path
) -> None:
    """SC-14: With autosave=on, file:save returns 'no pending changes'.

    RED: file:save always flushes (no autosave gate) — test FAILS (returns success).
    GREEN: autosave=on gate returns empty/no-pending-changes for file:save.
    """
    file_path_str = "close_test.txt"
    result_open = await client_session.call_tool(
        "viewport",
        arguments={
            "action": "open",
            "session_id": "test-sc14-save",
            "file_path": file_path_str,
            "autosave": True,
        },
    )
    assert "error" not in _get_text(result_open)
    vpid = _extract_vpid(_get_text(result_open))

    # With autosave=on, file:save should be a no-op (no pending changes to save)
    result = await client_session.call_tool(
        "file",
        arguments={
            "action": "save",
            "session_id": "test-sc14-save",
            "viewport_id": vpid,
            "file_path": file_path_str,
        },
    )
    text = _get_text(result)
    # GREEN assertion: save reports no-op / empty state
    assert not result.isError, f"RED FAIL: save should not error: {text[:200]}"
    assert (
        "no pending" in text.lower()
        or "nothing to save" in text.lower()
        or "up to date" in text.lower()
    ), f"RED FAIL: expected no-pending-changes message: {text[:200]}"


@pytest.mark.phase3
@pytest.mark.asyncio
async def test_sc14_autosave_on_diff_show_empty(client_session: ClientSession) -> None:
    """SC-14: With autosave=on, diff:show returns empty diff.

    RED: diff:show returns actual diff (no autosave gate) — test FAILS.
    GREEN: autosave=on gate returns empty/no-pending-changes for diff:show.
    """
    result_open = await client_session.call_tool(
        "viewport",
        arguments={
            "action": "open",
            "session_id": "test-sc14-diff",
            "file_path": "close_test.txt",
            "autosave": True,
        },
    )
    vpid = _extract_vpid(_get_text(result_open))

    # With autosave=on, diff should show no pending changes
    result = await client_session.call_tool(
        "diff",
        arguments={
            "action": "show",
            "session_id": "test-sc14-diff",
            "viewport_id": vpid,
            "file_path": "close_test.txt",
        },
    )
    text = _get_text(result)
    # GREEN assertion: diff shows no pending changes
    assert not result.isError, f"RED FAIL: diff:show should not error: {text[:200]}"
    assert "no pending" in text.lower(), (
        f"RED FAIL: expected no-pending-changes message for autosave=on: {text[:200]}"
    )


@pytest.mark.phase3
@pytest.mark.asyncio
async def test_sc14_autosave_on_discard_empty(client_session: ClientSession) -> None:
    """SC-14: With autosave=on, file:discard returns empty state.

    RED: file:discard always discards (no autosave gate) — test FAILS.
    GREEN: autosave=on gate returns empty/no-pending-changes for file:discard.
    """
    result_open = await client_session.call_tool(
        "viewport",
        arguments={
            "action": "open",
            "session_id": "test-sc14-discard",
            "file_path": "close_test.txt",
            "autosave": True,
        },
    )
    vpid = _extract_vpid(_get_text(result_open))

    # With autosave=on, discard should be a no-op
    result = await client_session.call_tool(
        "file",
        arguments={
            "action": "discard",
            "session_id": "test-sc14-discard",
            "viewport_id": vpid,
        },
    )
    text = _get_text(result)
    # GREEN assertion: discard reports no-op / empty state
    assert not result.isError, f"RED FAIL: discard should not error: {text[:200]}"
    assert (
        "no pending" in text.lower()
        or "nothing to discard" in text.lower()
        or "no changes" in text.lower()
    ), f"RED FAIL: expected no-pending-changes message: {text[:200]}"


# ── SC-15: file:new creates file and opens viewport ──────────────────────────


@pytest.mark.phase3
@pytest.mark.asyncio
async def test_sc15_file_new_creates_file(
    client_session: ClientSession, test_project_root: Path
) -> None:
    """SC-15: file:new creates file on disk and opens viewport with autosave=off.

    RED: file tool has no 'new' action — test FAILS with unknown action error.
    GREEN: file:new creates empty file, opens viewport, autosave=off.
    """
    new_file = "brand_new_file.txt"
    assert not (test_project_root / new_file).exists(), (
        "test fixture: file should not exist yet"
    )

    result = await client_session.call_tool(
        "file",
        arguments={"action": "new", "session_id": "test-sc15", "file_path": new_file},
    )
    text = _get_text(result)
    # GREEN assertion: file created, viewport opened, autosave=off
    assert not result.isError, f"RED FAIL: file:new should succeed: {text[:200]}"
    assert (test_project_root / new_file).exists(), (
        "RED FAIL: file was not created on disk"
    )
    assert "viewport_id:" in text, "RED FAIL: viewport not opened"
    assert "autosave: False" in text, "RED FAIL: autosave should be off for new files"


@pytest.mark.phase3
@pytest.mark.asyncio
async def test_sc15_file_new_existing_rejects(client_session: ClientSession) -> None:
    """SC-15: file:new on existing path returns isError.

    RED: file tool has no 'new' action — test FAILS with unknown action error (not specific).
    GREEN: file:new on existing file returns isError with appropriate message.
    """
    result = await client_session.call_tool(
        "file",
        arguments={
            "action": "new",
            "session_id": "test-sc15-existing",
            "file_path": "close_test.txt",
        },
    )
    text = _get_text(result)
    # GREEN assertion: isError when file already exists
    assert result.isError, (
        f"RED FAIL: file:new should reject existing file: {text[:200]}"
    )
    assert "already exists" in text.lower() or "exists" in text.lower(), (
        f"RED FAIL: expected 'already exists' error: {text[:200]}"
    )


# ── SC-16: file:save-as with force=false/true ────────────────────────────────


@pytest.mark.phase3
@pytest.mark.asyncio
async def test_sc16_file_save_as_rejects_existing(
    client_session: ClientSession,
) -> None:
    """SC-16: file:save-as with force=false rejects existing target.

    RED: file tool has no 'save-as' action — test FAILS.
    GREEN: save-as with force=false returns isError when target exists.
    """
    result_open = await client_session.call_tool(
        "viewport",
        arguments={
            "action": "open",
            "session_id": "test-sc16-reject",
            "file_path": "close_test.txt",
        },
    )
    vpid = _extract_vpid(_get_text(result_open))

    result = await client_session.call_tool(
        "file",
        arguments={
            "action": "save-as",
            "session_id": "test-sc16-reject",
            "viewport_id": vpid,
            "file_path": "existing_save_as.txt",
            "force": False,
        },
    )
    text = _get_text(result)
    # GREEN assertion: isError when target exists and force=false
    assert result.isError, (
        f"RED FAIL: save-as should reject existing file: {text[:200]}"
    )
    assert "already exists" in text.lower() or "exists" in text.lower(), (
        f"RED FAIL: expected 'already exists' error: {text[:200]}"
    )


@pytest.mark.phase3
@pytest.mark.asyncio
async def test_sc16_file_save_as_force_overwrites(
    client_session: ClientSession, test_project_root: Path
) -> None:
    """SC-16: file:save-as with force=true overwrites existing target.

    RED: file tool has no 'save-as' action — test FAILS.
    GREEN: save-as with force=true overwrites target file with buffer content.
    """
    result_open = await client_session.call_tool(
        "viewport",
        arguments={
            "action": "open",
            "session_id": "test-sc16-force",
            "file_path": "close_test.txt",
        },
    )
    vpid = _extract_vpid(_get_text(result_open))

    buffer_content = (test_project_root / "close_test.txt").read_text()

    result = await client_session.call_tool(
        "file",
        arguments={
            "action": "save-as",
            "session_id": "test-sc16-force",
            "viewport_id": vpid,
            "file_path": "existing_save_as.txt",
            "force": True,
        },
    )
    text = _get_text(result)
    # GREEN assertion: force=true overwrites target
    assert not result.isError, (
        f"RED FAIL: save-as with force=true should succeed: {text[:200]}"
    )
    assert "saved" in text.lower(), (
        f"RED FAIL: expected save confirmation: {text[:200]}"
    )
    after = (test_project_root / "existing_save_as.txt").read_text()
    assert after == buffer_content, (
        "RED FAIL: target file content does not match buffer"
    )


# ── SC-30: file:delete removes file on disk ─────────────────────────────────


@pytest.mark.phase3
@pytest.mark.asyncio
async def test_sc30_file_delete_removes_file(
    client_session: ClientSession, test_project_root: Path
) -> None:
    """SC-30: file:delete removes file on disk.

    RED: file tool has no 'delete' action — test FAILS.
    GREEN: file:delete removes the file from disk.
    """
    result = await client_session.call_tool(
        "file",
        arguments={
            "action": "delete",
            "session_id": "test-sc30",
            "file_path": "delete_me.txt",
        },
    )
    text = _get_text(result)
    # GREEN assertion: file removed from disk
    assert not result.isError, f"RED FAIL: file:delete should succeed: {text[:200]}"
    assert "deleted" in text.lower(), (
        f"RED FAIL: expected deletion confirmation: {text[:200]}"
    )
    assert not (test_project_root / "delete_me.txt").exists(), (
        "RED FAIL: file still exists on disk"
    )


@pytest.mark.phase3
@pytest.mark.asyncio
async def test_sc30_file_delete_dirty_buffer_rejects(
    client_session: ClientSession,
) -> None:
    """SC-30: file:delete with dirty buffer returns isError.

    RED: file tool has no 'delete' action — test FAILS.
    GREEN: file:delete on file with dirty buffer returns isError.
    """
    result_open = await client_session.call_tool(
        "viewport",
        arguments={
            "action": "open",
            "session_id": "test-sc30-dirty",
            "file_path": "close_test.txt",
        },
    )
    vpid = _extract_vpid(_get_text(result_open))

    # Dirty the buffer with an edit
    await client_session.call_tool(
        "edit",
        arguments={
            "action": "replace",
            "session_id": "test-sc30-dirty",
            "viewport_id": vpid,
            "file_path": "close_test.txt",
            "old_text": "line 1",
            "new_text": "DIRTY",
        },
    )

    result = await client_session.call_tool(
        "file",
        arguments={
            "action": "delete",
            "session_id": "test-sc30-dirty",
            "file_path": "close_test.txt",
        },
    )
    text = _get_text(result)
    # GREEN assertion: isError because buffer is dirty
    assert result.isError, f"RED FAIL: delete should reject dirty buffer: {text[:200]}"
    assert (
        "dirty" in text.lower()
        or "pending" in text.lower()
        or "unsaved" in text.lower()
    ), f"RED FAIL: expected dirty-buffer rejection message: {text[:200]}"


# ── SC-24: viewport:close with dirty buffer auto-saves ──────────────────────


@pytest.mark.phase3
@pytest.mark.asyncio
async def test_sc24_viewport_close_dirty_auto_saves(
    client_session: ClientSession, test_project_root: Path
) -> None:
    """SC-24: viewport:close with dirty buffer auto-saves to disk.

    RED: close currently auto-saves (already implemented) — this should PASS
    as a regression guard.
    GREEN: close flushes dirty buffer to disk when autosave=off.
    """
    file_path_str = "close_test.txt"
    original = (test_project_root / file_path_str).read_text()

    result_open = await client_session.call_tool(
        "viewport",
        arguments={
            "action": "open",
            "session_id": "test-sc24",
            "file_path": file_path_str,
            "autosave": False,
        },
    )
    vpid = _extract_vpid(_get_text(result_open))

    # Edit to dirty the buffer
    await client_session.call_tool(
        "edit",
        arguments={
            "action": "replace",
            "session_id": "test-sc24",
            "viewport_id": vpid,
            "file_path": file_path_str,
            "old_text": "line 1",
            "new_text": "AUTO-SAVED BY CLOSE",
        },
    )

    # Close the viewport — should auto-save dirty buffer
    result_close = await client_session.call_tool(
        "viewport",
        arguments={"action": "close", "session_id": "test-sc24", "viewport_id": vpid},
    )
    assert "error" not in _get_text(result_close)

    # File on disk should reflect the edit
    after = (test_project_root / file_path_str).read_text()
    assert after != original, (
        "RED FAIL: file on disk unchanged after close with dirty buffer"
    )
    assert "AUTO-SAVED BY CLOSE" in after, (
        "RED FAIL: edited content not in file on disk after close"
    )


@pytest.mark.phase3
@pytest.mark.asyncio
async def test_sc24_viewport_close_already_closed_noop(
    client_session: ClientSession,
) -> None:
    """SC-24: closing an already-closed viewport returns isError."""
    result_open = await client_session.call_tool(
        "viewport",
        arguments={
            "action": "open",
            "session_id": "test-sc24-noop",
            "file_path": "close_test.txt",
        },
    )
    vpid = _extract_vpid(_get_text(result_open))

    # Close once
    await client_session.call_tool(
        "viewport",
        arguments={
            "action": "close",
            "session_id": "test-sc24-noop",
            "viewport_id": vpid,
        },
    )

    # Close again — should error
    result = await client_session.call_tool(
        "viewport",
        arguments={
            "action": "close",
            "session_id": "test-sc24-noop",
            "viewport_id": vpid,
        },
    )
    assert result.isError, (
        "RED FAIL: closing already-closed viewport should return isError"
    )


# ── Phase 3 regression guard: tools still present ───────────────────────────


@pytest.mark.phase3
@pytest.mark.asyncio
async def test_phase3_tools_listed(client_session: ClientSession) -> None:
    """Verify all 6 tools are present in tool listing."""
    result = await client_session.list_tools()
    names = [t.name for t in result.tools]
    for name in ("viewport", "edit", "file", "diff", "search", "regex"):
        assert name in names, f"Tool {name} missing from tool list"
