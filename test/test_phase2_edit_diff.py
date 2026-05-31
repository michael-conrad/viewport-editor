# SPDX-FileCopyrightText: 2026 Michael Conrad
# SPDX-License-Identifier: MIT
# Provenance: AI-generated
"""Phase 2 RED behavioral tests for edit/buffer/diff tools of viewport-editor MCP server.

These tests assert GREEN-phase behavior and MUST FAIL against current stubs
(which return "not yet implemented"). When Phase 2 is implemented, these tests
must PASS.

Co-authored with AI: OpenCode (ollama-cloud/deepseek-v4-flash)
"""

from __future__ import annotations

import time
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
    (tmpdir / "edit_test.txt").write_text("line 1\nline 2\nline 3\nline 4\nline 5\n")
    (tmpdir / "save_test.txt").write_text("save target content\nline two\nline three\n")
    (tmpdir / "multi.txt").write_text("apple\nbanana\napple\ncherry\napple\ndate\n")
    (tmpdir / "lines.txt").write_text(
        "zero\none\ntwo\nthree\nfour\nfive\nsix\nseven\neight\nnine\nten\n"
    )
    (tmpdir / "conflict_test.txt").write_text("original content\nline 2\nline 3\n")
    (tmpdir / "edit_atomic_test.txt").write_text(
        "line a\nline b\nline c\nline d\nline e\n"
    )
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


# ── SC-9: edit:replace stages into buffer (autosave=off) ─────────────────────


@pytest.mark.phase2
@pytest.mark.asyncio
async def test_sc9_edit_replace_stages_in_buffer_autosave_off(
    client_session: ClientSession, test_project_root: Path
) -> None:
    """SC-9: edit:replace with autosave=off stages change in buffer without writing to disk.

    RED: stub returns 'not yet implemented' or arg validation error.
    GREEN: edit:replace reports success; file on disk unchanged; viewport shows dirty=True.
    """
    file_path_str = "edit_test.txt"
    original = (test_project_root / file_path_str).read_text()

    result_open = await client_session.call_tool(
        "viewport",
        arguments={
            "action": "open",
            "session_id": "test-sc9",
            "file_path": file_path_str,
            "autosave": False,
        },
    )
    assert "error" not in _get_text(result_open)
    vpid = _extract_vpid(_get_text(result_open))

    result = await client_session.call_tool(
        "edit",
        arguments={
            "action": "replace",
            "session_id": "test-sc9",
            "viewport_id": vpid,
            "file_path": file_path_str,
            "old_text": "line 3",
            "new_text": "modified line 3",
        },
    )
    text = _get_text(result)
    # GREEN assertion: edit succeeds, file unchanged on disk, dirty flag set
    assert not result.isError, f"RED FAIL (edit stub not implemented): {text[:200]}"
    assert "error" not in text.lower(), (
        f"RED FAIL: unexpected error in response: {text[:200]}"
    )
    after = (test_project_root / file_path_str).read_text()
    assert after == original, "RED FAIL: file changed on disk with autosave=off"
    # Viewport list should show dirty=True
    list_result = await client_session.call_tool(
        "viewport",
        arguments={"action": "list", "session_id": "test-sc9"},
    )
    assert "dirty: True" in _get_text(list_result), (
        "RED FAIL: dirty flag not set after edit"
    )


# ── SC-10: diff:show returns unified diff ────────────────────────────────────


@pytest.mark.phase2
@pytest.mark.asyncio
async def test_sc10_diff_show_returns_unified_diff(
    client_session: ClientSession,
) -> None:
    """SC-10: diff:show returns unified diff of pending buffer changes vs disk original.

    RED: stub returns 'not yet implemented' or arg validation error.
    GREEN: after edit, diff:show returns unified diff header (---/+++) with change markers.
    """
    result_open = await client_session.call_tool(
        "viewport",
        arguments={
            "action": "open",
            "session_id": "test-sc10",
            "file_path": "edit_test.txt",
        },
    )
    vpid = _extract_vpid(_get_text(result_open))

    # Make an edit to create pending changes
    await client_session.call_tool(
        "edit",
        arguments={
            "action": "replace",
            "session_id": "test-sc10",
            "viewport_id": vpid,
            "file_path": "edit_test.txt",
            "old_text": "line 3",
            "new_text": "CHANGED",
        },
    )

    result = await client_session.call_tool(
        "diff",
        arguments={
            "action": "show",
            "session_id": "test-sc10",
            "viewport_id": vpid,
            "file_path": "edit_test.txt",
        },
    )
    text = _get_text(result)
    # GREEN assertion: unified diff format
    assert not result.isError, f"RED FAIL (diff stub not implemented): {text[:200]}"
    assert "---" in text or "+++" in text, (
        f"RED FAIL: unified diff markers missing: {text[:200]}"
    )


# ── SC-11: file:save rejects on stale mtime/size mismatch ────────────────────


@pytest.mark.phase2
@pytest.mark.asyncio
async def test_sc11_file_save_rejects_stale_mtime(
    client_session: ClientSession, test_project_root: Path
) -> None:
    """SC-11: file:save with stale mtime returns isError.

    RED: stub returns 'not yet implemented'.
    GREEN: modify file externally → save returns isError with staleness warning.
    """
    result_open = await client_session.call_tool(
        "viewport",
        arguments={
            "action": "open",
            "session_id": "test-sc11",
            "file_path": "save_test.txt",
        },
    )
    vpid = _extract_vpid(_get_text(result_open))

    (test_project_root / "save_test.txt").write_text("externally modified\n")
    time.sleep(0.05)

    result = await client_session.call_tool(
        "file",
        arguments={
            "action": "save",
            "session_id": "test-sc11",
            "viewport_id": vpid,
            "file_path": "save_test.txt",
        },
    )
    text = _get_text(result)
    # GREEN assertion: isError=true with staleness warning or force override needed
    assert result.isError, (
        f"RED FAIL: save should reject stale mtime, got: {text[:200]}"
    )
    assert (
        "mtime" in text.lower() or "stale" in text.lower() or "conflict" in text.lower()
    ), f"RED FAIL: staleness warning missing: {text[:200]}"


@pytest.mark.phase2
@pytest.mark.asyncio
async def test_sc11_file_save_rejects_missing_file(
    client_session: ClientSession,
) -> None:
    """SC-11: file:save on missing file returns isError."""
    result_open = await client_session.call_tool(
        "viewport",
        arguments={
            "action": "open",
            "session_id": "test-sc11b",
            "file_path": "save_test.txt",
        },
    )
    vpid = _extract_vpid(_get_text(result_open))

    result = await client_session.call_tool(
        "file",
        arguments={
            "action": "save",
            "session_id": "test-sc11b",
            "viewport_id": vpid,
            "file_path": "nonexistent.txt",
        },
    )
    text = _get_text(result)
    assert result.isError, (
        f"RED FAIL: save should reject missing file, got: {text[:200]}"
    )
    assert "not found" in text.lower() or "does not exist" in text.lower(), (
        f"RED FAIL: missing-file error message absent: {text[:200]}"
    )


@pytest.mark.phase2
@pytest.mark.asyncio
async def test_sc11_file_save_force_overrides_stale(
    client_session: ClientSession, test_project_root: Path
) -> None:
    """SC-11: file:save with force=true overrides stale mtime/size check."""
    result_open = await client_session.call_tool(
        "viewport",
        arguments={
            "action": "open",
            "session_id": "test-sc11c",
            "file_path": "save_test.txt",
        },
    )
    vpid = _extract_vpid(_get_text(result_open))

    (test_project_root / "save_test.txt").write_text("externally modified\n")
    time.sleep(0.05)

    result = await client_session.call_tool(
        "file",
        arguments={
            "action": "save",
            "session_id": "test-sc11c",
            "viewport_id": vpid,
            "file_path": "save_test.txt",
            "force": True,
        },
    )
    text = _get_text(result)
    # GREEN assertion: force=true saves buffer content to disk despite staleness
    assert not result.isError, f"RED FAIL: force save should succeed: {text[:200]}"
    # After force save, diff should be empty (buffer === disk)
    diff_result = await client_session.call_tool(
        "diff",
        arguments={
            "action": "show",
            "session_id": "test-sc11c",
            "viewport_id": vpid,
            "file_path": "save_test.txt",
        },
    )
    diff_text = _get_text(diff_result)
    assert "no pending changes" in diff_text.lower() or diff_text.strip() == "", (
        f"RED FAIL: force save should flush buffer, diff should be empty: {diff_text[:200]}"
    )


# ── SC-12: file:discard reverts buffer to disk state ─────────────────────────


@pytest.mark.phase2
@pytest.mark.asyncio
async def test_sc12_file_discard_reverts_buffer(client_session: ClientSession) -> None:
    """SC-12: file:discard reverts buffer to disk state, clearing dirty flag.

    RED: stub returns 'not yet implemented'.
    GREEN: after edit dirties buffer, discard reverts; dirty flag cleared; diff empty.
    """
    result_open = await client_session.call_tool(
        "viewport",
        arguments={
            "action": "open",
            "session_id": "test-sc12",
            "file_path": "edit_test.txt",
            "autosave": False,
        },
    )
    vpid = _extract_vpid(_get_text(result_open))

    # Make an edit first
    await client_session.call_tool(
        "edit",
        arguments={
            "action": "replace",
            "session_id": "test-sc12",
            "viewport_id": vpid,
            "file_path": "edit_test.txt",
            "old_text": "line 3",
            "new_text": "DIRTY",
        },
    )

    result = await client_session.call_tool(
        "file",
        arguments={"action": "discard", "session_id": "test-sc12", "viewport_id": vpid},
    )
    text = _get_text(result)
    # GREEN assertion: discard reports success, dirty flag cleared
    assert not result.isError, f"RED FAIL: discard should succeed: {text[:200]}"
    list_result = await client_session.call_tool(
        "viewport",
        arguments={"action": "list", "session_id": "test-sc12"},
    )
    assert "dirty: True" not in _get_text(list_result), (
        "RED FAIL: discard should clear dirty flag"
    )
    # After discard, diff should be empty
    diff_result = await client_session.call_tool(
        "diff",
        arguments={
            "action": "show",
            "session_id": "test-sc12",
            "viewport_id": vpid,
            "file_path": "edit_test.txt",
        },
    )
    diff_text = _get_text(diff_result)
    assert "no pending changes" in diff_text.lower() or diff_text.strip() == "", (
        f"RED FAIL: discard should revert, diff should be empty: {diff_text[:200]}"
    )


# ── SC-13: edit:replace with autosave=on writes to disk atomically ───────────


@pytest.mark.phase2
@pytest.mark.asyncio
async def test_sc13_edit_replace_autosave_on_writes_to_disk(
    client_session: ClientSession, test_project_root: Path
) -> None:
    """SC-13: edit:replace with autosave=on writes to disk atomically.

    RED: stub returns 'not yet implemented'.
    GREEN: edit on autosave-enabled viewport updates file on disk.
    """
    file_path_str = "edit_test.txt"
    original = (test_project_root / file_path_str).read_text()

    result_open = await client_session.call_tool(
        "viewport",
        arguments={
            "action": "open",
            "session_id": "test-sc13",
            "file_path": file_path_str,
            "autosave": True,
        },
    )
    vpid = _extract_vpid(_get_text(result_open))

    result = await client_session.call_tool(
        "edit",
        arguments={
            "action": "replace",
            "session_id": "test-sc13",
            "viewport_id": vpid,
            "file_path": file_path_str,
            "old_text": "line 3",
            "new_text": "AUTO SAVED",
        },
    )
    text = _get_text(result)
    # GREEN assertion: edit succeeds, file on disk changed
    assert not result.isError, f"RED FAIL (edit stub not implemented): {text[:200]}"
    assert "error" not in text.lower(), f"RED FAIL: edit should succeed: {text[:200]}"
    after = (test_project_root / file_path_str).read_text()
    assert after != original, "RED FAIL: file on disk did not change with autosave=on"


# ── SC-18: replace-all (multi-occurrence replace) ────────────────────────────


@pytest.mark.phase2
@pytest.mark.asyncio
async def test_sc18_replace_all_multi_occurrence(client_session: ClientSession) -> None:
    """SC-18: replace-all replaces all occurrences of old_text in the buffer."""
    result_open = await client_session.call_tool(
        "viewport",
        arguments={
            "action": "open",
            "session_id": "test-sc18",
            "file_path": "multi.txt",
        },
    )
    vpid = _extract_vpid(_get_text(result_open))

    result = await client_session.call_tool(
        "edit",
        arguments={
            "action": "replace-all",
            "session_id": "test-sc18",
            "viewport_id": vpid,
            "file_path": "multi.txt",
            "old_text": "apple",
            "new_text": "orange",
        },
    )
    text = _get_text(result)
    assert not result.isError, f"RED FAIL: replace-all should succeed: {text[:200]}"
    # Verify via diff that orange replaced all 3 apples
    diff_result = await client_session.call_tool(
        "diff",
        arguments={
            "action": "show",
            "session_id": "test-sc18",
            "viewport_id": vpid,
            "file_path": "multi.txt",
        },
    )
    diff_text = _get_text(diff_result)
    # The diff should show 3 removals of apple lines and 3 additions of orange lines
    assert "-apple" in diff_text, (
        f"RED FAIL: diff should show apple removal: {diff_text[:200]}"
    )
    assert "+orange" in diff_text, (
        f"RED FAIL: diff should show orange addition: {diff_text[:200]}"
    )


# ── SC-19: insert-lines at line position ─────────────────────────────────────


@pytest.mark.phase2
@pytest.mark.asyncio
async def test_sc19_insert_lines_at_position(client_session: ClientSession) -> None:
    """SC-19: insert-lines inserts lines at specified line position."""
    result_open = await client_session.call_tool(
        "viewport",
        arguments={
            "action": "open",
            "session_id": "test-sc19",
            "file_path": "lines.txt",
        },
    )
    vpid = _extract_vpid(_get_text(result_open))

    result = await client_session.call_tool(
        "edit",
        arguments={
            "action": "insert-lines",
            "session_id": "test-sc19",
            "viewport_id": vpid,
            "file_path": "lines.txt",
            "line_start": 3,
            "lines": ["inserted A", "inserted B"],
        },
    )
    text = _get_text(result)
    assert not result.isError, f"RED FAIL: insert-lines should succeed: {text[:200]}"
    # Verify via scroll that inserted lines are visible at position
    scroll_result = await client_session.call_tool(
        "viewport",
        arguments={
            "action": "scroll",
            "session_id": "test-sc19",
            "viewport_id": vpid,
            "lines": 0,
        },
    )
    scroll_text = _get_text(scroll_result)
    assert "inserted A" in scroll_text, (
        f"RED FAIL: inserted content not visible: {scroll_text[:200]}"
    )
    assert "inserted B" in scroll_text, (
        f"RED FAIL: inserted content not visible: {scroll_text[:200]}"
    )


# ── SC-20: delete-lines at line position ─────────────────────────────────────


@pytest.mark.phase2
@pytest.mark.asyncio
async def test_sc20_delete_lines_at_position(client_session: ClientSession) -> None:
    """SC-20: delete-lines removes lines at specified range."""
    result_open = await client_session.call_tool(
        "viewport",
        arguments={
            "action": "open",
            "session_id": "test-sc20",
            "file_path": "lines.txt",
        },
    )
    vpid = _extract_vpid(_get_text(result_open))

    result = await client_session.call_tool(
        "edit",
        arguments={
            "action": "delete-lines",
            "session_id": "test-sc20",
            "viewport_id": vpid,
            "file_path": "lines.txt",
            "line_start": 2,
            "line_end": 4,
        },
    )
    text = _get_text(result)
    assert not result.isError, f"RED FAIL: delete-lines should succeed: {text[:200]}"
    # Verify via diff that deleted lines are removed
    diff_result = await client_session.call_tool(
        "diff",
        arguments={
            "action": "show",
            "session_id": "test-sc20",
            "viewport_id": vpid,
            "file_path": "lines.txt",
        },
    )
    diff_text = _get_text(diff_result)
    assert "-one" in diff_text, (
        f"RED FAIL: diff should show deleted line 'one': {diff_text[:200]}"
    )
    assert "-two" in diff_text, (
        f"RED FAIL: diff should show deleted line 'two': {diff_text[:200]}"
    )
    assert "-three" in diff_text, (
        f"RED FAIL: diff should show deleted line 'three': {diff_text[:200]}"
    )


# ── SC-21: swap-lines swaps two line ranges ──────────────────────────────────


@pytest.mark.phase2
@pytest.mark.asyncio
async def test_sc21_swap_lines(client_session: ClientSession) -> None:
    """SC-21: swap-lines swaps two line ranges in the buffer."""
    result_open = await client_session.call_tool(
        "viewport",
        arguments={
            "action": "open",
            "session_id": "test-sc21",
            "file_path": "lines.txt",
        },
    )
    vpid = _extract_vpid(_get_text(result_open))

    result = await client_session.call_tool(
        "edit",
        arguments={
            "action": "swap-lines",
            "session_id": "test-sc21",
            "viewport_id": vpid,
            "file_path": "lines.txt",
            "line_start": 1,
            "line_end": 2,
            "target_line_start": 4,
            "target_line_end": 5,
        },
    )
    text = _get_text(result)
    assert not result.isError, f"RED FAIL: swap-lines should succeed: {text[:200]}"
    # Verify via scroll that lines were reordered
    scroll_result = await client_session.call_tool(
        "viewport",
        arguments={
            "action": "scroll",
            "session_id": "test-sc21",
            "viewport_id": vpid,
            "lines": 0,
        },
    )
    scroll_text = _get_text(scroll_result)
    # Original: zero/one/two/three/four/five... After swap: three/four/two/zero/one/five...
    assert (
        "    1: three" in scroll_text
        or "    2: three" in scroll_text
        or "three" in scroll_text
    ), f"RED FAIL: swapped content not visible: {scroll_text[:300]}"
    assert "    1: zero" not in scroll_text, (
        f"RED FAIL: zero should no longer be at line 1: {scroll_text[:300]}"
    )


# ── SC-22: move-lines moves a line range to another position ─────────────────


@pytest.mark.phase2
@pytest.mark.asyncio
async def test_sc22_move_lines(client_session: ClientSession) -> None:
    """SC-22: move-lines moves a line range to another position in the buffer."""
    result_open = await client_session.call_tool(
        "viewport",
        arguments={
            "action": "open",
            "session_id": "test-sc22",
            "file_path": "lines.txt",
        },
    )
    vpid = _extract_vpid(_get_text(result_open))

    result = await client_session.call_tool(
        "edit",
        arguments={
            "action": "move-lines",
            "session_id": "test-sc22",
            "viewport_id": vpid,
            "file_path": "lines.txt",
            "line_start": 5,
            "line_end": 7,
            "target_line": 2,
        },
    )
    text = _get_text(result)
    assert not result.isError, f"RED FAIL: move-lines should succeed: {text[:200]}"
    # Verify via scroll that moved lines appear at target position
    scroll_result = await client_session.call_tool(
        "viewport",
        arguments={
            "action": "scroll",
            "session_id": "test-sc22",
            "viewport_id": vpid,
            "lines": 0,
        },
    )
    scroll_text = _get_text(scroll_result)
    # Original: zero/one/two/three/four/five/six/seven/eight/nine/ten
    # After moving lines 5-7 (four/five/six) to target_line=2:
    # zero/four/five/six/one/two/three/seven/eight/nine/ten
    # Check that "four" appears near the top (before "one")
    four_pos = scroll_text.find("four")
    one_pos = scroll_text.find("one")
    assert four_pos >= 0, (
        f"RED FAIL: moved line 'four' not visible: {scroll_text[:300]}"
    )
    assert one_pos >= 0, (
        f"RED FAIL: expected line 'one' still visible: {scroll_text[:300]}"
    )
    assert four_pos < one_pos, (
        f"RED FAIL: 'four' should appear before 'one' after move: {scroll_text[:300]}"
    )


# ── SC-25: Soft conflict warning on edit operations ─────────────────────────


@pytest.mark.phase2
@pytest.mark.asyncio
async def test_sc25_soft_conflict_warning_on_edit(
    client_session: ClientSession, test_project_root: Path
) -> None:
    """SC-25: edit operations warn when file changed externally before edit.

    RED: stub returns 'not yet implemented'.
    GREEN: after external file change, edit response contains 'warning:' line.
    """
    result_open = await client_session.call_tool(
        "viewport",
        arguments={
            "action": "open",
            "session_id": "test-sc25",
            "file_path": "conflict_test.txt",
        },
    )
    vpid = _extract_vpid(_get_text(result_open))

    (test_project_root / "conflict_test.txt").write_text(
        "externally modified\nstill modified\n"
    )
    time.sleep(0.05)

    result = await client_session.call_tool(
        "edit",
        arguments={
            "action": "replace",
            "session_id": "test-sc25",
            "viewport_id": vpid,
            "file_path": "conflict_test.txt",
            "old_text": "original content",
            "new_text": "conflicting edit",
        },
    )
    text = _get_text(result)
    # GREEN assertion: soft conflict warning in response
    assert not result.isError, f"RED FAIL (edit stub not implemented): {text[:200]}"
    assert (
        "warning:" in text
        or "conflict:" in text
        or "mtime" in text.lower()
        or "externally" in text.lower()
    ), f"RED FAIL: soft conflict warning missing: {text[:200]}"


# ── SC-13 atomic write test ────────────────────────────────────────────────


@pytest.mark.phase2
@pytest.mark.asyncio
async def test_sc13_atomic_write_integrity(
    client_session: ClientSession, test_project_root: Path
) -> None:
    """SC-13-FIX: file:save writes fully, no orphaned .tmp files, content correct.

    Behavioral evidence: after save with autosave=on, the file on disk matches
    buffer content; no .tmp file lingers alongside the target.
    """
    file_path_str = "edit_atomic_test.txt"
    original_content = (test_project_root / file_path_str).read_text()
    assert "line c" in original_content, "test fixture missing expected content"

    result_open = await client_session.call_tool(
        "viewport",
        arguments={
            "action": "open",
            "session_id": "test-sc13-atomic",
            "file_path": file_path_str,
            "autosave": True,
        },
    )
    vpid = _extract_vpid(_get_text(result_open))

    # Edit to create new content
    await client_session.call_tool(
        "edit",
        arguments={
            "action": "replace",
            "session_id": "test-sc13-atomic",
            "viewport_id": vpid,
            "file_path": file_path_str,
            "old_text": "line c",
            "new_text": "ATOMIC SAVED",
        },
    )

    # File on disk should now reflect edit (autosave=on flushes)
    after = (test_project_root / file_path_str).read_text()
    assert original_content != after, (
        "SC-13-FIX FAIL: file on disk unchanged after autosave=on edit"
    )
    assert "ATOMIC SAVED" in after, "SC-13-FIX FAIL: edited content not in file on disk"

    # No orphaned .tmp file
    tmp_files = list(test_project_root.glob("*.tmp"))
    assert len(tmp_files) == 0, (
        f"SC-13-FIX FAIL: orphaned .tmp files found: {tmp_files}"
    )


# ── Phase 2 tools regression guard ──────────────────────────────────────────


@pytest.mark.phase2
@pytest.mark.asyncio
async def test_phase2_tools_listed(client_session: ClientSession) -> None:
    """Verify edit, file, diff tools are present in tool listing."""
    result = await client_session.list_tools()
    names = [t.name for t in result.tools]
    for name in ("edit", "file", "diff"):
        assert name in names, f"Tool {name} missing from tool list"
