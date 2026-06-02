# SPDX-FileCopyrightText: 2026 Michael Conrad
# SPDX-License-Identifier: MIT
# Provenance: AI-generated
"""Phase 3 RED behavioral tests for autosave gate of viewport-editor MCP server.

These tests assert GREEN-phase behavior for SC-14 (autosave=on gate for
file:save/diff:show/file:discard returning no-op) and SC-24 (viewport:close
with dirty+autosave flushes to disk, already-closed is no-op, clean close
doesn't write unnecessarily).

SC-14 tests MUST FAIL against current code because there is no autosave=on
gate in the file:save, diff:show, or file:discard handlers.

SC-24 tests may already PASS if issue #18 fixed the close logic.

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
    tmpdir = Path(tempfile.mkdtemp(prefix="ve-p3-autosave-test-"))
    (tmpdir / "autosave_gate.txt").write_text("alpha\nbeta\ngamma\ndelta\nepsilon\n")
    (tmpdir / "autosave_close.txt").write_text("original line one\noriginal line two\n")
    (tmpdir / "autosave_clean.txt").write_text("clean content\nmore content\n")
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
    return f"test-p3a-{uuid.uuid4().hex[:8]}"


# ── SC-14: With autosave=on, file:save returns no-op / empty state ────────────


@pytest.mark.phase3
@pytest.mark.asyncio
async def test_autosave_on_file_save_noop(
    client_session: ClientSession, test_project_root: Path
) -> None:
    """SC-14: With autosave=on, file:save returns "no pending changes".

    RED: Current file:save has no autosave gate — it performs a full save
    even when autosave=on, which is a no-op (changes already flushed).
    GREEN: file:save with autosave=on returns "no pending changes" or
    equivalent no-op response instead of performing a redundant flush.
    """
    sid = _unique_sid()
    file_path = "autosave_gate.txt"
    original = (test_project_root / file_path).read_text()

    result_open = await client_session.call_tool(
        "viewport",
        arguments={
            "action": "open",
            "session_id": sid,
            "file_path": file_path,
            "autosave": True,
        },
    )
    text_open = _get_text(result_open)
    vpid = _extract_vpid(text_open)
    assert vpid, f"Failed to open viewport: {text_open[:300]}"

    await client_session.call_tool(
        "edit",
        arguments={
            "action": "replace",
            "session_id": sid,
            "viewport_id": vpid,
            "file_path": file_path,
            "old_text": "beta",
            "new_text": "BETA",
        },
    )

    after_edit = (test_project_root / file_path).read_text()
    assert after_edit != original, (
        "Precondition: autosave=on should have flushed edit to disk"
    )

    result = await client_session.call_tool(
        "file",
        arguments={
            "action": "save",
            "session_id": sid,
            "viewport_id": vpid,
        },
    )
    text = _get_text(result)

    assert not result.isError, f"SC-14: file:save should not error: {text[:300]}"

    has_noop = (
        "no pending changes" in text.lower()
        or "no changes" in text.lower()
        or "already saved" in text.lower()
        or "nothing to save" in text.lower()
        or "autosave" in text.lower()
    )
    assert has_noop, (
        f"SC-14 FAIL: file:save with autosave=on should return no-op/empty state, "
        f"got: {text[:300]}"
    )


# ── SC-14: With autosave=on, diff:show returns empty diff ─────────────────────


@pytest.mark.phase3
@pytest.mark.asyncio
async def test_autosave_on_diff_show_empty(
    client_session: ClientSession,
) -> None:
    """SC-14: With autosave=on, diff:show returns explicit autosave gate response.

    The handler must check autosave=on BEFORE computing the diff and return
    "no pending changes (autosave: on)" explicitly — not just rely on the
    natural side effect that buffer and disk stay in sync.
    """
    sid = _unique_sid()
    file_path = "autosave_gate.txt"

    result_open = await client_session.call_tool(
        "viewport",
        arguments={
            "action": "open",
            "session_id": sid,
            "file_path": file_path,
            "autosave": True,
        },
    )
    text_open = _get_text(result_open)
    vpid = _extract_vpid(text_open)
    assert vpid, f"Failed to open viewport: {text_open[:300]}"

    await client_session.call_tool(
        "edit",
        arguments={
            "action": "replace",
            "session_id": sid,
            "viewport_id": vpid,
            "file_path": file_path,
            "old_text": "gamma",
            "new_text": "GAMMA",
        },
    )

    result = await client_session.call_tool(
        "diff",
        arguments={
            "action": "show",
            "session_id": sid,
            "viewport_id": vpid,
        },
    )
    text = _get_text(result)

    assert "autosave" in text.lower(), (
        f"SC-14 FAIL: diff:show with autosave=on must return explicit autosave gate "
        f"response (not just empty diff from natural side effect), got: {text[:300]}"
    )
    assert "no pending changes" in text.lower(), (
        f"SC-14 FAIL: diff:show with autosave=on must indicate no pending changes, "
        f"got: {text[:300]}"
    )


# ── SC-14: With autosave=on, file:discard returns empty state ─────────────────


@pytest.mark.phase3
@pytest.mark.asyncio
async def test_autosave_on_discard_empty(
    client_session: ClientSession,
) -> None:
    """SC-14: With autosave=on, file:discard returns empty/no-op state.

    RED: Current file:discard has no autosave gate — it still re-reads
    from disk even when autosave=on (which is semantically incorrect;
    there's nothing to discard if autosave just flushed).
    GREEN: file:discard with autosave=on returns "no pending changes" or
    equivalent no-op because autosave already keeps buffer and disk in sync.
    """
    sid = _unique_sid()
    file_path = "autosave_gate.txt"

    result_open = await client_session.call_tool(
        "viewport",
        arguments={
            "action": "open",
            "session_id": sid,
            "file_path": file_path,
            "autosave": True,
        },
    )
    text_open = _get_text(result_open)
    vpid = _extract_vpid(text_open)
    assert vpid, f"Failed to open viewport: {text_open[:300]}"

    result = await client_session.call_tool(
        "file",
        arguments={
            "action": "discard",
            "session_id": sid,
            "viewport_id": vpid,
        },
    )
    text = _get_text(result)

    assert not result.isError, f"SC-14: file:discard should not error: {text[:300]}"

    has_noop = (
        "no pending changes" in text.lower()
        or "no changes" in text.lower()
        or "nothing to discard" in text.lower()
        or "autosave" in text.lower()
    )
    assert has_noop, (
        f"SC-14 FAIL: file:discard with autosave=on should return no-op/empty state, "
        f"got: {text[:300]}"
    )


# ── SC-24: viewport:close with dirty buffer and autosave=on flushes to disk ──


@pytest.mark.phase3
@pytest.mark.asyncio
async def test_viewport_close_dirty_auto_saves(
    client_session: ClientSession, test_project_root: Path
) -> None:
    """SC-24: viewport:close with dirty buffer and autosave=on flushes to disk.

    Uses an integration test via the MCP server (not just unit test).
    Opens a file with autosave=on, edits it, then closes. Verifies the
    modified content is on disk after close (not silently discarded).
    """
    sid = _unique_sid()
    file_path = "autosave_close.txt"
    original = (test_project_root / file_path).read_text()

    result_open = await client_session.call_tool(
        "viewport",
        arguments={
            "action": "open",
            "session_id": sid,
            "file_path": file_path,
            "autosave": True,
        },
    )
    text_open = _get_text(result_open)
    vpid = _extract_vpid(text_open)
    assert vpid, f"Failed to open viewport: {text_open[:300]}"

    await client_session.call_tool(
        "edit",
        arguments={
            "action": "replace",
            "session_id": sid,
            "viewport_id": vpid,
            "file_path": file_path,
            "old_text": "original line one",
            "new_text": "MODIFIED LINE ONE",
        },
    )

    await client_session.call_tool(
        "viewport",
        arguments={
            "action": "close",
            "session_id": sid,
            "viewport_id": vpid,
        },
    )

    after_close = (test_project_root / file_path).read_text()
    assert "MODIFIED LINE ONE" in after_close, (
        f"SC-24 FAIL: close() with autosave=on did not flush dirty buffer. "
        f"Changes silently discarded. Disk: {after_close!r}"
    )

    (test_project_root / file_path).write_text(original)


# ── SC-24: closing already-closed viewport is no-op (returns error) ───────────


@pytest.mark.phase3
@pytest.mark.asyncio
async def test_viewport_close_already_closed_noop(
    client_session: ClientSession,
) -> None:
    """SC-24: closing an already-closed viewport raises ViewportNotFoundError.

    The second close on the same viewport_id should return isError=true
    because the viewport no longer exists in the session. This is the
    correct no-op behavior — you can't close what's already closed.
    """
    sid = _unique_sid()
    file_path = "autosave_gate.txt"

    result_open = await client_session.call_tool(
        "viewport",
        arguments={
            "action": "open",
            "session_id": sid,
            "file_path": file_path,
        },
    )
    text_open = _get_text(result_open)
    vpid = _extract_vpid(text_open)
    assert vpid, f"Failed to open viewport: {text_open[:300]}"

    result_close = await client_session.call_tool(
        "viewport",
        arguments={
            "action": "close",
            "session_id": sid,
            "viewport_id": vpid,
        },
    )
    assert "error" not in _get_text(result_close).lower(), (
        f"First close should succeed: {_get_text(result_close)[:200]}"
    )

    result_double_close = await client_session.call_tool(
        "viewport",
        arguments={
            "action": "close",
            "session_id": sid,
            "viewport_id": vpid,
        },
    )
    text_double = _get_text(result_double_close)

    assert result_double_close.isError, (
        f"SC-24: closing already-closed viewport should return isError=true, "
        f"got: {text_double[:300]}"
    )
    assert (
        "not found" in text_double.lower() or "does not exist" in text_double.lower()
    ), f"SC-24: error should mention viewport not found: {text_double[:300]}"


# ── SC-24: close on a clean viewport doesn't write unnecessarily ───────────────


@pytest.mark.phase3
@pytest.mark.asyncio
async def test_viewport_close_clean_noop(
    client_session: ClientSession, test_project_root: Path
) -> None:
    """SC-24: closing a clean (non-dirty) viewport doesn't trigger a disk write.

    Verification: open a file without making any edits, then close.
    The file on disk must remain byte-identical to the original (no
    unnecessary write). Additionally, close should succeed without error.
    """
    sid = _unique_sid()
    file_path = "autosave_clean.txt"
    original = (test_project_root / file_path).read_bytes()

    result_open = await client_session.call_tool(
        "viewport",
        arguments={
            "action": "open",
            "session_id": sid,
            "file_path": file_path,
        },
    )
    text_open = _get_text(result_open)
    vpid = _extract_vpid(text_open)
    assert vpid, f"Failed to open viewport: {text_open[:300]}"

    list_result = await client_session.call_tool(
        "viewport",
        arguments={"action": "list", "session_id": sid},
    )
    list_text = _get_text(list_result)
    assert "dirty: True" not in list_text, (
        f"Precondition: viewport should be clean (dirty=False): {list_text[:300]}"
    )

    result_close = await client_session.call_tool(
        "viewport",
        arguments={
            "action": "close",
            "session_id": sid,
            "viewport_id": vpid,
        },
    )
    close_text = _get_text(result_close)
    assert "error" not in close_text.lower(), (
        f"SC-24: closing clean viewport should succeed: {close_text[:200]}"
    )

    after_close = (test_project_root / file_path).read_bytes()
    assert after_close == original, (
        f"SC-24: closing clean viewport should not write to disk. "
        f"File changed unexpectedly. Original: {original!r}, After: {after_close!r}"
    )


# ── Unit test: SC-24 close with dirty+autosave flushes (direct ViewportManager) ─


@pytest.mark.phase3
def test_viewport_close_dirty_autosave_unit() -> None:
    """SC-24: unit test — ViewportManager.close() flushes dirty autosave buffer."""
    import tempfile as _tf
    from pathlib import Path as P

    from viewport_editor.viewport import ViewportManager

    with _tf.TemporaryDirectory(prefix="ve-p3a-sc24-") as tmpdir:
        test_file = P(tmpdir) / "sc24_unit.txt"
        test_file.write_text("original content\n")

        mgr = ViewportManager(project_root=tmpdir)
        entry = mgr.open(
            session_id="p3a-sc24-unit",
            file_path="sc24_unit.txt",
            autosave=True,
        )

        buf = mgr._buffer_mgr.get_buffer_ref("p3a-sc24-unit", "sc24_unit.txt")
        buf.content = "modified content\n"
        entry.dirty = True
        entry.autosave = True

        mgr.close(session_id="p3a-sc24-unit", viewport_id=entry.viewport_id)

        after_close = test_file.read_text()
        assert "modified content" in after_close, (
            f"SC-24 unit FAIL: close() with autosave=on did not flush. "
            f"Disk: {after_close!r}"
        )


# ── Unit test: SC-24 close clean viewport doesn't write (direct ViewportManager) ─


@pytest.mark.phase3
def test_viewport_close_clean_no_write_unit() -> None:
    """SC-24: unit test — ViewportManager.close() on clean buffer doesn't flush."""
    import tempfile as _tf
    from pathlib import Path as P

    from viewport_editor.viewport import ViewportManager

    with _tf.TemporaryDirectory(prefix="ve-p3a-sc24-clean-") as tmpdir:
        test_file = P(tmpdir) / "sc24_clean_unit.txt"
        test_file.write_text("unchanged content\n")
        original_bytes = test_file.read_bytes()

        mgr = ViewportManager(project_root=tmpdir)
        entry = mgr.open(
            session_id="p3a-sc24-clean",
            file_path="sc24_clean_unit.txt",
            autosave=True,
        )

        assert not entry.dirty, "Precondition: entry should be clean"

        mgr.close(session_id="p3a-sc24-clean", viewport_id=entry.viewport_id)

        after_bytes = test_file.read_bytes()
        assert after_bytes == original_bytes, (
            f"SC-24 unit FAIL: close() on clean buffer wrote unnecessarily. "
            f"Original: {original_bytes!r}, After: {after_bytes!r}"
        )


# ── Regression guard ───────────────────────────────────────────────────────────


@pytest.mark.phase3
@pytest.mark.asyncio
async def test_phase3_autosave_tools_listed(client_session: ClientSession) -> None:
    """Verify viewport, file, diff tools are present (regression guard)."""
    result = await client_session.list_tools()
    names = [t.name for t in result.tools]
    for name in ("viewport", "file", "diff"):
        assert name in names, f"Tool '{name}' missing from tool list"
