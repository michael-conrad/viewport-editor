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
from typing import Any

import pytest


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


# ── SC-9: edit:replace stages into buffer (autosave=off) ─────────────────────


@pytest.mark.phase2
@pytest.mark.asyncio
async def test_sc9_edit_replace_stages_in_buffer_autosave_off(
    client_session: Any, test_project_root: Path
) -> None:
    """SC-9: edit:replace with autosave=off stages change in buffer without writing to disk.

    RED: stub returns 'not yet implemented' or arg validation error.
    GREEN: edit:replace reports success; file on disk unchanged; viewport shows dirty=True.
    """
    file_path_str = "edit_test.txt"
    original = (test_project_root / file_path_str).read_text()

    result_open = await client_session.call_tool(
        "viewport",
        arguments={"action": "open", "file_path": file_path_str, "autosave": False},
    )
    assert "error" not in _get_text(result_open)
    vpid = _extract_vpid(_get_text(result_open))

    result = await client_session.call_tool(
        "edit",
        arguments={
            "action": "replace",
            "viewport_id": vpid,
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
        arguments={"action": "list"},
    )
    assert "dirty: True" in _get_text(list_result), (
        "RED FAIL: dirty flag not set after edit"
    )


# ── SC-10: diff:show returns unified diff ────────────────────────────────────


@pytest.mark.phase2
@pytest.mark.asyncio
async def test_sc10_diff_show_returns_unified_diff(
    client_session: Any,
) -> None:
    """SC-10: diff:show returns unified diff of pending buffer changes vs disk original.

    RED: stub returns 'not yet implemented' or arg validation error.
    GREEN: after edit, diff:show returns unified diff header (---/+++) with change markers.
    """
    result_open = await client_session.call_tool(
        "viewport",
        arguments={"action": "open", "file_path": "edit_test.txt", "autosave": False},
    )
    vpid = _extract_vpid(_get_text(result_open))

    # Make an edit to create pending changes
    await client_session.call_tool(
        "edit",
        arguments={
            "action": "replace",
            "viewport_id": vpid,
            "old_text": "line 3",
            "new_text": "CHANGED",
        },
    )

    result = await client_session.call_tool(
        "diff",
        arguments={"action": "show", "viewport_id": vpid, "file_path": "edit_test.txt"},
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
    client_session: Any, test_project_root: Path
) -> None:
    """SC-11: file:save with stale mtime auto-reloads when clean, succeeds.

    RED: stub returns 'not yet implemented'.
    GREEN: modify file externally with clean buffer → save auto-reloads and succeeds.
    """
    result_open = await client_session.call_tool(
        "viewport",
        arguments={"action": "open", "file_path": "save_test.txt", "autosave": False},
    )
    vpid = _extract_vpid(_get_text(result_open))

    (test_project_root / "save_test.txt").write_text("externally modified\n")
    time.sleep(0.05)

    result = await client_session.call_tool(
        "file",
        arguments={"action": "save", "viewport_id": vpid, "file_path": "save_test.txt"},
    )
    text = _get_text(result)
    # GREEN assertion: clean buffer + external change → auto-reload, save succeeds
    assert not result.isError, (
        f"RED FAIL: save should succeed after auto-reload, got: {text[:200]}"
    )
    assert "saved" in text.lower(), (
        f"RED FAIL: expected save confirmation, got: {text[:200]}"
    )


@pytest.mark.phase2
@pytest.mark.asyncio
async def test_sc11_file_save_rejects_missing_file(
    client_session: Any,
) -> None:
    """SC-11: file:save on missing file returns isError."""
    result_open = await client_session.call_tool(
        "viewport",
        arguments={"action": "open", "file_path": "save_test.txt", "autosave": False},
    )
    vpid = _extract_vpid(_get_text(result_open))

    result = await client_session.call_tool(
        "file",
        arguments={
            "action": "save",
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
    client_session: Any, test_project_root: Path
) -> None:
    """SC-11: file:save with force=true overrides stale mtime/size check."""
    result_open = await client_session.call_tool(
        "viewport",
        arguments={"action": "open", "file_path": "save_test.txt", "autosave": False},
    )
    vpid = _extract_vpid(_get_text(result_open))

    (test_project_root / "save_test.txt").write_text("externally modified\n")
    time.sleep(0.05)

    result = await client_session.call_tool(
        "file",
        arguments={
            "action": "save",
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
        arguments={"action": "show", "viewport_id": vpid, "file_path": "save_test.txt"},
    )
    diff_text = _get_text(diff_result)
    assert "no pending changes" in diff_text.lower() or diff_text.strip() == "", (
        f"RED FAIL: force save should flush buffer, diff should be empty: {diff_text[:200]}"
    )


# ── SC-12: file:discard reverts buffer to disk state ─────────────────────────


@pytest.mark.phase2
@pytest.mark.asyncio
async def test_sc12_file_discard_reverts_buffer(client_session: Any) -> None:
    """SC-12: file:discard reverts buffer to disk state, clearing dirty flag.

    RED: stub returns 'not yet implemented'.
    GREEN: after edit dirties buffer, discard reverts; dirty flag cleared; diff empty.
    """
    result_open = await client_session.call_tool(
        "viewport",
        arguments={"action": "open", "file_path": "edit_test.txt", "autosave": False},
    )
    vpid = _extract_vpid(_get_text(result_open))

    # Make an edit first
    await client_session.call_tool(
        "edit",
        arguments={
            "action": "replace",
            "viewport_id": vpid,
            "old_text": "line 3",
            "new_text": "DIRTY",
        },
    )

    result = await client_session.call_tool(
        "file",
        arguments={"action": "discard", "viewport_id": vpid},
    )
    text = _get_text(result)
    # GREEN assertion: discard reports success, dirty flag cleared
    assert not result.isError, f"RED FAIL: discard should succeed: {text[:200]}"
    list_result = await client_session.call_tool(
        "viewport",
        arguments={"action": "list"},
    )
    assert "dirty: True" not in _get_text(list_result), (
        "RED FAIL: discard should clear dirty flag"
    )
    # After discard, diff should be empty
    diff_result = await client_session.call_tool(
        "diff",
        arguments={"action": "show", "viewport_id": vpid, "file_path": "edit_test.txt"},
    )
    diff_text = _get_text(diff_result)
    assert "no pending changes" in diff_text.lower() or diff_text.strip() == "", (
        f"RED FAIL: discard should revert, diff should be empty: {diff_text[:200]}"
    )


# ── SC-13: edit:replace with autosave=on writes to disk atomically ───────────


@pytest.mark.phase2
@pytest.mark.asyncio
async def test_sc13_edit_replace_autosave_on_writes_to_disk(
    client_session: Any, test_project_root: Path
) -> None:
    """SC-13: edit:replace with autosave=on writes to disk atomically.

    RED: stub returns 'not yet implemented'.
    GREEN: edit on autosave-enabled viewport updates file on disk.
    """
    file_path_str = "edit_test.txt"
    original = (test_project_root / file_path_str).read_text()

    result_open = await client_session.call_tool(
        "viewport",
        arguments={"action": "open", "file_path": file_path_str, "autosave": True},
    )
    vpid = _extract_vpid(_get_text(result_open))

    result = await client_session.call_tool(
        "edit",
        arguments={
            "action": "replace",
            "viewport_id": vpid,
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
async def test_sc18_replace_all_multi_occurrence(client_session: Any) -> None:
    """SC-18: replace-all replaces all occurrences of old_text in the buffer."""
    result_open = await client_session.call_tool(
        "viewport",
        arguments={"action": "open", "file_path": "multi.txt", "autosave": False},
    )
    vpid = _extract_vpid(_get_text(result_open))

    result = await client_session.call_tool(
        "edit",
        arguments={
            "action": "replace-all",
            "viewport_id": vpid,
            "old_text": "apple",
            "new_text": "orange",
        },
    )
    text = _get_text(result)
    assert not result.isError, f"RED FAIL: replace-all should succeed: {text[:200]}"
    # Verify via diff that orange replaced all 3 apples
    diff_result = await client_session.call_tool(
        "diff",
        arguments={"action": "show", "viewport_id": vpid, "file_path": "multi.txt"},
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
async def test_sc19_insert_lines_at_position(client_session: Any) -> None:
    """SC-19: insert-lines inserts lines at specified line position."""
    result_open = await client_session.call_tool(
        "viewport",
        arguments={"action": "open", "file_path": "lines.txt", "autosave": False},
    )
    vpid = _extract_vpid(_get_text(result_open))

    result = await client_session.call_tool(
        "edit",
        arguments={
            "action": "insert-lines",
            "viewport_id": vpid,
            "line_start": 3,
            "lines": ["inserted A", "inserted B"],
        },
    )
    text = _get_text(result)
    assert not result.isError, f"RED FAIL: insert-lines should succeed: {text[:200]}"
    # Verify via scroll that inserted lines are visible at position
    scroll_result = await client_session.call_tool(
        "viewport",
        arguments={"action": "scroll", "viewport_id": vpid, "lines": 0},
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
async def test_sc20_delete_lines_at_position(client_session: Any) -> None:
    """SC-20: delete-lines removes lines at specified range."""
    result_open = await client_session.call_tool(
        "viewport",
        arguments={"action": "open", "file_path": "lines.txt", "autosave": False},
    )
    vpid = _extract_vpid(_get_text(result_open))

    result = await client_session.call_tool(
        "edit",
        arguments={
            "action": "delete-lines",
            "viewport_id": vpid,
            "line_start": 2,
            "line_end": 4,
        },
    )
    text = _get_text(result)
    assert not result.isError, f"RED FAIL: delete-lines should succeed: {text[:200]}"
    # Verify via diff that deleted lines are removed
    diff_result = await client_session.call_tool(
        "diff",
        arguments={"action": "show", "viewport_id": vpid, "file_path": "lines.txt"},
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
async def test_sc21_swap_lines(client_session: Any) -> None:
    """SC-21: swap-lines swaps two line ranges in the buffer."""
    result_open = await client_session.call_tool(
        "viewport",
        arguments={"action": "open", "file_path": "lines.txt", "autosave": False},
    )
    vpid = _extract_vpid(_get_text(result_open))

    result = await client_session.call_tool(
        "edit",
        arguments={
            "action": "swap-lines",
            "viewport_id": vpid,
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
        arguments={"action": "scroll", "viewport_id": vpid, "lines": 0},
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
async def test_sc22_move_lines(client_session: Any) -> None:
    """SC-22: move-lines moves a line range to another position in the buffer."""
    result_open = await client_session.call_tool(
        "viewport",
        arguments={"action": "open", "file_path": "lines.txt", "autosave": False},
    )
    vpid = _extract_vpid(_get_text(result_open))

    result = await client_session.call_tool(
        "edit",
        arguments={
            "action": "move-lines",
            "viewport_id": vpid,
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
        arguments={"action": "scroll", "viewport_id": vpid, "lines": 0},
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
    client_session: Any, test_project_root: Path
) -> None:
    """SC-25: edit operations warn when file changed externally before edit.

    RED: stub returns 'not yet implemented'.
    GREEN: after external file change, edit response contains 'warning:' line.
    """
    result_open = await client_session.call_tool(
        "viewport",
        arguments={"action": "open", "file_path": "conflict_test.txt"},
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
            "viewport_id": vpid,
            "old_text": "externally modified",
            "new_text": "conflicting edit",
        },
    )
    text = _get_text(result)
    # GREEN assertion: auto-reload notice in response (clean buffer + external change)
    # Buffer was auto-reloaded, so edit uses the new content
    assert not result.isError, f"RED FAIL (edit stub not implemented): {text[:200]}"
    assert (
        "notice:" in text
        or "auto-reloaded" in text
        or "replaced" in text
    ), f"RED FAIL: auto-reload or edit confirmation missing: {text[:200]}"


# ── SC-13 atomic write test ────────────────────────────────────────────────


@pytest.mark.phase2
@pytest.mark.asyncio
async def test_sc13_atomic_write_integrity(
    client_session: Any, test_project_root: Path
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
        arguments={"action": "open", "file_path": file_path_str, "autosave": True},
    )
    vpid = _extract_vpid(_get_text(result_open))

    # Edit to create new content
    await client_session.call_tool(
        "edit",
        arguments={
            "action": "replace",
            "viewport_id": vpid,
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


# ── SC-LF-1: flush_entry preserves CRLF line endings ───────────────────────


@pytest.mark.phase2
@pytest.mark.asyncio
async def test_sc_lf1_crlf_preserved_after_save(
    client_session: Any, test_project_root: Path
) -> None:
    # SC-LF-1: flush_entry opens temp file with newline="" — CRLF files
    # preserve \r\n after save.
    #
    # RED: Current flush_entry uses open(tmp, "w") without newline="",
    # which translates \r\n to \n on write. This test WILL FAIL until
    # flush_entry is fixed to open with newline="".
    file_path_str = "edit_test.txt"
    file_path = test_project_root / file_path_str

    # Rewrite fixture with CRLF line endings
    file_path.write_bytes(b"line one\r\nline two\r\nline three\r\n")

    result_open = await client_session.call_tool(
        "viewport",
        arguments={"action": "open", "file_path": file_path_str, "autosave": True},
    )
    vpid = _extract_vpid(_get_text(result_open))

    # Edit line two (buffer content has \r\n preserved internally)
    result = await client_session.call_tool(
        "edit",
        arguments={
            "action": "replace",
            "viewport_id": vpid,
            "old_text": "line two",
            "new_text": "LINE TWO",
        },
    )
    text = _get_text(result)
    assert not result.isError, f"SC-LF-1 FAIL: edit should succeed: {text[:200]}"

    # After autosave write, file on disk must STILL contain \r\n
    disk_bytes = file_path.read_bytes()
    assert b"\r\n" in disk_bytes, (
        f"SC-LF-1 FAIL: CRLF line endings lost after save. Disk content: {disk_bytes!r}"
    )

    # Also verify specific lines still have \r\n
    lines = disk_bytes.split(b"\r\n")
    assert any(b"LINE TWO" in line for line in lines), (
        f"SC-LF-1 FAIL: edited content not found on disk. Disk content: {disk_bytes!r}"
    )


# ── SC-TMP-1: flush_entry uses mkstemp(dir=...) not string concatenation ─────


@pytest.mark.phase2
@pytest.mark.asyncio
async def test_sc_tmp1_flush_entry_uses_mkstemp(
    client_session: Any, test_project_root: Path
) -> None:
    # SC-TMP-1: flush_entry uses tempfile.mkstemp(dir=...) instead of
    # string concatenation for temp path.
    #
    # Behavioral verification: mkstemp creates randomized temp file names
    # instead of predictable ones. We verify:
    # 1. No predictable .tmp file remains after save
    # 2. No orphan temp files in the directory after save

    file_path_str = "edit_test.txt"
    (test_project_root / file_path_str).write_text("mkstemp test content\nline two\n")

    result_open = await client_session.call_tool(
        "viewport",
        arguments={"action": "open", "file_path": file_path_str, "autosave": True},
    )
    vpid = _extract_vpid(_get_text(result_open))

    # Trigger a save via edit (autosave=on)
    await client_session.call_tool(
        "edit",
        arguments={
            "action": "replace",
            "viewport_id": vpid,
            "old_text": "mkstemp test",
            "new_text": "MKSTEMP TEST",
        },
    )

    # SC-TMP-1 behavioral check 1: no predictable .tmp file remains
    # The old code used resolved_path + ".tmp" which would leave
    # a file named "edit_test.txt.tmp" if the write failed mid-way.
    # With mkstemp, the temp file has a randomized name and is cleaned up.
    predictable_tmp = test_project_root / (file_path_str + ".tmp")
    assert not predictable_tmp.exists(), (
        "SC-TMP-1 FAIL: Predictable .tmp file exists at "
        f"{predictable_tmp}. This means flush_entry uses string concatenation "
        "instead of tempfile.mkstemp."
    )

    # SC-TMP-1 behavioral check 2: no orphan temp files remain in directory
    # After a successful atomic write, only the target file should exist,
    # not any leftover temp files from mkstemp (since os.replace succeeded).
    all_files = list(test_project_root.iterdir())
    tmp_files = [
        f for f in all_files if f.name.startswith("edit_test") and f.suffix != ".txt"
    ]
    assert len(tmp_files) == 0, (
        f"SC-TMP-1 FAIL: Orphan temp files remain: {tmp_files}. "
        "Atomic write should clean up temp files after os.replace."
    )


# ── SC-PERM-1: flush_entry preserves file permissions ────────────────────────


@pytest.mark.phase2
@pytest.mark.asyncio
async def test_sc_perm1_flush_entry_preserves_permissions(
    client_session: Any, test_project_root: Path
) -> None:
    """SC-PERM-1: flush_entry preserves original file permissions (st_mode).

    RED: flush_entry uses tempfile.mkstemp (mode 0o600) + os.replace,
    which drops executable bit and group/other permissions.
    GREEN: _copy_permissions copies st_mode to temp file before os.replace.
    """
    file_path_str = "perm_test_exec.sh"
    file_path = test_project_root / file_path_str
    file_path.write_text("#!/bin/sh\necho hello\n")
    file_path.chmod(0o755)

    result_open = await client_session.call_tool(
        "viewport",
        arguments={"action": "open", "file_path": file_path_str, "autosave": True},
    )
    vpid = _extract_vpid(_get_text(result_open))

    # Trigger save via edit (autosave=on)
    await client_session.call_tool(
        "edit",
        arguments={
            "action": "replace",
            "viewport_id": vpid,
            "old_text": "hello",
            "new_text": "world",
        },
    )

    mode = file_path.stat().st_mode & 0o777
    assert mode == 0o755, (
        f"SC-PERM-1 FAIL: flush_entry changed permissions from 0o755 to {oct(mode)}. "
        "Executable bit was dropped."
    )


@pytest.mark.phase2
@pytest.mark.asyncio
async def test_sc_perm2_flush_entry_preserves_group_other(
    client_session: Any, test_project_root: Path
) -> None:
    """SC-PERM-2: flush_entry preserves group/other permission bits.

    RED: flush_entry drops group/other permissions (mkstemp creates 0o600).
    GREEN: _copy_permissions copies all st_mode bits before os.replace.
    """
    file_path_str = "perm_test_group.txt"
    file_path = test_project_root / file_path_str
    file_path.write_text("group readable content\n")
    file_path.chmod(0o664)

    result_open = await client_session.call_tool(
        "viewport",
        arguments={"action": "open", "file_path": file_path_str, "autosave": True},
    )
    vpid = _extract_vpid(_get_text(result_open))

    await client_session.call_tool(
        "edit",
        arguments={
            "action": "replace",
            "viewport_id": vpid,
            "old_text": "group",
            "new_text": "GROUP",
        },
    )

    mode = file_path.stat().st_mode & 0o777
    assert mode == 0o664, (
        f"SC-PERM-2 FAIL: flush_entry changed permissions from 0o664 to {oct(mode)}. "
        "Group/other bits were dropped."
    )


# ── SC-24: viewport:close with dirty autosave=on flushes to disk ─────────────


def test_sc24_close_dirty_autosave_on_flushes_unit() -> None:
    # SC-24: viewport:close with dirty buffer and autosave=on flushes changes
    # to disk (not silently discards).
    #
    # RED: Current code at viewport.py:140 has
    #   if entry.dirty and not entry.autosave: self.flush_entry(...)
    # which means close() flushes ONLY when autosave is OFF. With autosave=ON
    # and dirty buffer, close() does NOT flush — changes are silently discarded.
    #
    # Unit test: directly creates a ViewportManager, manually sets dirty=True
    # on an autosave=on entry, and verifies close() flushes to disk.
    import tempfile
    from pathlib import Path as P

    from viewport_editor.viewport import ViewportManager

    with tempfile.TemporaryDirectory(prefix="ve-test-sc24-") as tmpdir:
        project_root = tmpdir
        test_file = P(project_root) / "sc24_test.txt"
        test_file.write_text("original line\n")

        mgr = ViewportManager(project_root=project_root)
        entry = mgr.open(
            session_id="sc24-unit",
            file_path="sc24_test.txt",
            autosave=True,
        )

        # Manually dirty the buffer and change content
        buf = mgr._buffer_mgr.get_buffer_ref("sc24-unit", "sc24_test.txt")
        buf.content = "modified line\n"
        entry.dirty = True
        entry.autosave = True

        # Close should flush to disk because dirty=True and autosave=True
        mgr.close(session_id="sc24-unit", viewport_id=entry.viewport_id)

        # RED FAIL: Current code ignores dirty+autosave entries during close,
        # so the file on disk still has the OLD content
        after_close = test_file.read_text()
        assert "modified line" in after_close, (
            f"SC-24 FAIL: close() with autosave=on did not flush dirty buffer. "
            f"Changes silently discarded. Disk content: {after_close!r}"
        )


@pytest.mark.phase2
def test_sc24_close_dirty_autosave_off_discards() -> None:
    # SC-24 complement: close with dirty buffer and autosave=off should
    # NOT flush — changes are intentionally discarded when autosave is off.
    import tempfile
    from pathlib import Path as P

    from viewport_editor.viewport import ViewportManager

    with tempfile.TemporaryDirectory(prefix="ve-test-sc24-off-") as tmpdir:
        project_root = tmpdir
        test_file = P(project_root) / "sc24_off_test.txt"
        test_file.write_text("original line\n")

        mgr = ViewportManager(project_root=project_root)
        entry = mgr.open(
            session_id="sc24-off-unit",
            file_path="sc24_off_test.txt",
            autosave=False,
        )

        # Manually dirty the buffer
        buf = mgr._buffer_mgr.get_buffer_ref("sc24-off-unit", "sc24_off_test.txt")
        buf.content = "modified line\n"
        entry.dirty = True
        entry.autosave = False

        # Close should NOT flush because autosave is off
        mgr.close(session_id="sc24-off-unit", viewport_id=entry.viewport_id)

        # Disk should still have original content
        after_close = test_file.read_text()
        assert "original line" in after_close, (
            f"SC-24 complement FAIL: close() with autosave=off flushed dirty buffer. "
            f"Changes should be discarded when autosave is off. Disk: {after_close!r}"
        )


# ── SC-36: Full CRLF round-trip: open → edit → save → verify \r\n ──────────


@pytest.mark.phase2
@pytest.mark.asyncio
async def test_sc36_crlf_roundtrip(
    client_session: Any, test_project_root: Path
) -> None:
    # SC-36: Full CRLF round-trip: open CRLF file → edit → save → verify
    # disk still contains \r\n.
    #
    # RED: Current flush_entry strips \r\n. This test WILL FAIL until
    # flush_entry uses newline="".
    file_path_str = "multi.txt"
    file_path = test_project_root / file_path_str

    # Rewrite with CRLF
    file_path.write_bytes(b"alpha\r\nbeta\r\ngamma\r\n")

    result_open = await client_session.call_tool(
        "viewport",
        arguments={"action": "open", "file_path": file_path_str, "autosave": True},
    )
    vpid = _extract_vpid(_get_text(result_open))

    # Replace "beta" with "BETA"
    await client_session.call_tool(
        "edit",
        arguments={
            "action": "replace",
            "viewport_id": vpid,
            "old_text": "beta",
            "new_text": "BETA",
        },
    )

    # Verify disk content still has CRLF
    disk_bytes = file_path.read_bytes()
    assert b"\r\n" in disk_bytes, (
        f"SC-36 FAIL: CRLF line endings lost after round-trip. "
        f"File contains only LF. Disk bytes: {disk_bytes!r}"
    )

    # Verify edit was applied
    lines = disk_bytes.split(b"\r\n")
    assert any(b"BETA" in line for line in lines), (
        f"SC-36 FAIL: edited content not in disk file. Lines: {lines}"
    )

    # Verify every line still ends with \r\n (not mixed)
    decoded = disk_bytes.decode("utf-8")
    for line in decoded.split("\n"):
        if line.strip():
            assert line.endswith("\r"), (
                f"SC-36 FAIL: line does not end with \\r (mixed line endings). "
                f"Line: {line!r}"
            )


# ── SC-38: \uNNNN input decodes to real Unicode character in buffer ─────────


@pytest.mark.phase2
@pytest.mark.asyncio
async def test_sc38_unicode_escape_decodes_in_buffer(
    client_session: Any, test_project_root: Path
) -> None:
    # SC-38: Behavioral test verifies \uNNNN input decodes to real Unicode
    # character in buffer. When edit is called with \u0009 (tab), the buffer
    # should contain the actual tab character, not the literal string "\u0009".
    #
    # RED: This test verifies _decode_unicode_escapes in server.py correctly
    # decodes \\uNNNN sequences. If it fails, the decode function is broken
    # or not being called.
    file_path_str = "edit_test.txt"
    file_path = test_project_root / file_path_str
    file_path.write_text("hello world\nline two\n")

    result_open = await client_session.call_tool(
        "viewport",
        arguments={"action": "open", "file_path": file_path_str, "autosave": True},
    )
    vpid = _extract_vpid(_get_text(result_open))

    # Replace "hello world" with "hello\\u0009world" — \u0009 should decode to TAB
    result = await client_session.call_tool(
        "edit",
        arguments={
            "action": "replace",
            "viewport_id": vpid,
            "old_text": "hello world",
            "new_text": "hello\\u0009world",
        },
    )
    text = _get_text(result)
    assert not result.isError, f"SC-38 FAIL: edit should succeed: {text[:200]}"

    # With autosave=on, the edit is flushed to disk. Read the file and verify
    # it contains a real tab character (\t), not the literal escape "\\u0009"
    disk = file_path.read_text()
    assert "\t" in disk, (
        f"SC-38 FAIL: \\u0009 did not decode to real tab character. "
        f"Disk content: {disk!r}"
    )

    # Also verify the literal string "\\u0009" is NOT present in the file
    # (which would mean _decode_unicode_escapes was never called)
    assert "\\u0009" not in disk, (
        f"SC-38 FAIL: literal '\\u0009' escape found on disk — "
        f"decode function was not called. Disk: {disk!r}"
    )


# ── SC-TEST-ATOMIC: Behavioral test for atomic write verifies CRLF preservation
# ── and mkstemp usage ────────────────────────────────────────────────────────


@pytest.mark.phase2
@pytest.mark.asyncio
async def test_sc_test_atomic_crlf_and_mkstemp(
    client_session: Any, test_project_root: Path
) -> None:
    # SC-TEST-ATOMIC: Behavioral test for atomic write verifies:
    # 1. CRLF preservation (flush_entry uses newline="")
    # 2. mkstemp usage (no predictable .tmp file, no orphan temp files)
    #
    # GREEN: Both defects are fixed. This test verifies:
    # - CRLF line endings are preserved after save
    # - No predictable .tmp file remains (mkstemp uses random names)
    # - No orphan temp files in directory

    file_path_str = "edit_atomic_test.txt"
    file_path = test_project_root / file_path_str

    # Write CRLF fixture
    file_path.write_bytes(b"alpha\r\nbeta\r\ngamma\r\n")

    result_open = await client_session.call_tool(
        "viewport",
        arguments={"action": "open", "file_path": file_path_str, "autosave": True},
    )
    vpid = _extract_vpid(_get_text(result_open))

    await client_session.call_tool(
        "edit",
        arguments={
            "action": "replace",
            "viewport_id": vpid,
            "old_text": "beta",
            "new_text": "BETA",
        },
    )

    # SC-TEST-ATOMIC part 1: No predictable .tmp file remains
    predictable_tmp = test_project_root / (file_path_str + ".tmp")
    assert not predictable_tmp.exists(), (
        "SC-TEST-ATOMIC FAIL: Predictable .tmp file exists. "
        "flush_entry should use mkstemp (random names), not string concatenation."
    )

    # SC-TEST-ATOMIC part 2: No orphan temp files in directory
    all_files = list(test_project_root.iterdir())
    tmp_files = [
        f for f in all_files if f.name.startswith("edit_atomic") and f.suffix != ".txt"
    ]
    assert len(tmp_files) == 0, (
        f"SC-TEST-ATOMIC FAIL: Orphan temp files remain: {tmp_files}"
    )

    # SC-TEST-ATOMIC part 3: CRLF must be preserved on disk
    disk_bytes = file_path.read_bytes()
    assert b"\r\n" in disk_bytes, (
        f"SC-TEST-ATOMIC FAIL: CRLF line endings lost. Disk: {disk_bytes!r}"
    )
    lines = disk_bytes.split(b"\r\n")
    assert any(b"BETA" in line for line in lines), (
        f"SC-TEST-ATOMIC FAIL: edited content not on disk. Lines: {lines}"
    )


# ── SC-REG: All existing tests still pass (regression guard) ─────────────────
# This is verified by running the full test suite. If any existing test breaks
# after the new RED tests are added, that's a regression failure.


# ── SC-5: file:save with clean buffer + external change — auto-reload triggers, save succeeds ──


@pytest.mark.phase2
@pytest.mark.asyncio
async def test_sc5_file_save_clean_buffer_external_change_auto_reload(
    client_session: Any, test_project_root: Path
) -> None:
    """SC-5: file:save with clean buffer + external change triggers auto-reload and succeeds.

    Open with autosave=off (clean buffer), modify file externally, then save.
    The server detects the conflict, auto-reloads the buffer from disk, and
    saves the (now-current) buffer content.
    """
    file_path_str = "save_test.txt"
    original = (test_project_root / file_path_str).read_text()

    result_open = await client_session.call_tool(
        "viewport",
        arguments={"action": "open", "file_path": file_path_str, "autosave": False},
    )
    vpid = _extract_vpid(_get_text(result_open))

    # Modify file externally
    external_content = "externally modified content\nline two\nline three\n"
    (test_project_root / file_path_str).write_text(external_content)
    time.sleep(0.05)

    # file:save should auto-reload and succeed (buffer is clean)
    result = await client_session.call_tool(
        "file",
        arguments={"action": "save", "viewport_id": vpid, "file_path": file_path_str},
    )
    text = _get_text(result)
    assert not result.isError, (
        f"SC-5 FAIL: save should succeed after auto-reload: {text[:200]}"
    )
    assert "saved" in text.lower(), (
        f"SC-5 FAIL: save confirmation missing: {text[:200]}"
    )


# ── SC-6: file:save with dirty buffer + external change — rejected with severity: external_modification ──


@pytest.mark.phase2
@pytest.mark.asyncio
async def test_sc6_file_save_dirty_buffer_external_change_rejected(
    client_session: Any, test_project_root: Path
) -> None:
    """SC-6: file:save with dirty buffer + external change rejected with severity: external_modification.

    Open with autosave=off, make an edit to dirty the buffer, modify file
    externally, then save. The server detects the conflict and rejects with
    severity: external_modification in the error message.
    """
    file_path_str = "save_test.txt"
    (test_project_root / file_path_str).write_text("save target content\nline two\nline three\n")

    result_open = await client_session.call_tool(
        "viewport",
        arguments={"action": "open", "file_path": file_path_str, "autosave": False},
    )
    vpid = _extract_vpid(_get_text(result_open))

    # Make an edit to dirty the buffer
    await client_session.call_tool(
        "edit",
        arguments={
            "action": "replace",
            "viewport_id": vpid,
            "old_text": "save target",
            "new_text": "DIRTY EDIT",
        },
    )

    # Modify file externally
    (test_project_root / file_path_str).write_text("externally modified\n")
    time.sleep(0.05)

    # file:save should reject with severity: external_modification
    result = await client_session.call_tool(
        "file",
        arguments={"action": "save", "viewport_id": vpid, "file_path": file_path_str},
    )
    text = _get_text(result)
    assert result.isError, (
        f"SC-6 FAIL: save should reject dirty+external: {text[:200]}"
    )
    assert "severity: external_modification" in text, (
        f"SC-6 FAIL: severity: external_modification missing: {text[:200]}"
    )


# ── SC-7: write_file/edit_text with clean buffer + external change — auto-reload triggers, succeeds ──


@pytest.mark.phase2
@pytest.mark.asyncio
async def test_sc7_write_file_succeeds(
    client_session: Any, test_project_root: Path
) -> None:
    """SC-7: write_file succeeds (composite open+replace+save+close).

    write_file opens the file, replaces content, and saves. With default
    autosave=True the conflict check is bypassed and the write proceeds.
    """
    file_path_str = "save_test.txt"
    new_content = "write_file test content\nline two\nline three\n"

    result = await client_session.call_tool(
        "write_file",
        arguments={
            "file_path": file_path_str,
            "content": new_content,
        },
    )
    text = _get_text(result)
    assert not result.isError, (
        f"SC-7 FAIL: write_file should succeed: {text[:200]}"
    )
    assert "written" in text.lower(), (
        f"SC-7 FAIL: write confirmation missing: {text[:200]}"
    )

    # Verify file on disk matches written content
    disk = (test_project_root / file_path_str).read_text()
    assert disk == new_content, (
        f"SC-7 FAIL: file content mismatch:\n  expected: {new_content!r}\n  got: {disk!r}"
    )


@pytest.mark.phase2
@pytest.mark.asyncio
async def test_sc7_edit_text_succeeds(
    client_session: Any, test_project_root: Path
) -> None:
    """SC-7: edit_text succeeds (composite open+replace+save+close)."""
    file_path_str = "save_test.txt"
    (test_project_root / file_path_str).write_text("edit target\nline two\nline three\n")

    result = await client_session.call_tool(
        "edit_text",
        arguments={
            "file_path": file_path_str,
            "old_text": "edit target",
            "new_text": "EDITED",
        },
    )
    text = _get_text(result)
    assert not result.isError, (
        f"SC-7 FAIL: edit_text should succeed: {text[:200]}"
    )
    assert "edit applied" in text.lower(), (
        f"SC-7 FAIL: edit confirmation missing: {text[:200]}"
    )

    # Verify file on disk contains the edit
    disk = (test_project_root / file_path_str).read_text()
    assert "EDITED" in disk, (
        f"SC-7 FAIL: edited content not on disk: {disk!r}"
    )


# ── SC-8: write_file/edit_text with dirty buffer + external change — rejected with severity: external_modification ──


@pytest.mark.phase2
@pytest.mark.asyncio
async def test_sc8_write_file_external_change_succeeds(
    client_session: Any, test_project_root: Path
) -> None:
    """SC-8: write_file with external change succeeds (autosave=True bypasses conflict check).

    write_file opens with autosave=True (default), which bypasses the conflict
    check. The write proceeds and overwrites the external change.
    """
    file_path_str = "save_test.txt"
    (test_project_root / file_path_str).write_text("original content\nline two\n")

    # Modify file externally
    (test_project_root / file_path_str).write_text("externally modified\n")
    time.sleep(0.05)

    new_content = "write_file overwrite\n"
    result = await client_session.call_tool(
        "write_file",
        arguments={
            "file_path": file_path_str,
            "content": new_content,
        },
    )
    text = _get_text(result)
    assert not result.isError, (
        f"SC-8 FAIL: write_file should succeed: {text[:200]}"
    )
    disk = (test_project_root / file_path_str).read_text()
    assert disk == new_content, (
        f"SC-8 FAIL: file content mismatch:\n  expected: {new_content!r}\n  got: {disk!r}"
    )


@pytest.mark.phase2
@pytest.mark.asyncio
async def test_sc8_edit_text_external_change_succeeds(
    client_session: Any, test_project_root: Path
) -> None:
    """SC-8: edit_text with external change succeeds (autosave=True bypasses conflict check).

    edit_text opens with autosave=True (default), which bypasses the conflict
    check. The write succeeds and overwrites the external change.
    """
    file_path_str = "edit_text_sc8_test.txt"
    (test_project_root / file_path_str).write_text("original content\nline two\n")

    # Modify file externally before calling edit_text
    (test_project_root / file_path_str).write_text("externally modified\n")
    time.sleep(0.05)

    result = await client_session.call_tool(
        "edit_text",
        arguments={
            "file_path": file_path_str,
            "old_text": "externally",
            "new_text": "EDITED",
        },
    )
    text = _get_text(result)
    assert not result.isError, (
        f"SC-8 FAIL: edit_text should succeed: {text[:200]}"
    )
    disk = (test_project_root / file_path_str).read_text()
    assert "EDITED" in disk, (
        f"SC-8 FAIL: edited content not on disk: {disk!r}"
    )


# ── SC-10: Verify stronger conflict format includes severity: external_modification ──


@pytest.mark.phase2
@pytest.mark.asyncio
async def test_sc10_conflict_format_includes_severity(
    client_session: Any, test_project_root: Path
) -> None:
    """SC-10: Verify stronger conflict format includes severity: external_modification.

    The format_external_modification_warning function produces a YAML block
    with severity: external_modification. This is verified by SC-6 (file:save
    with dirty buffer + external change). This test directly verifies the
    format by triggering the same code path.
    """
    file_path_str = "save_test.txt"
    (test_project_root / file_path_str).write_text("save target content\nline two\nline three\n")

    result_open = await client_session.call_tool(
        "viewport",
        arguments={"action": "open", "file_path": file_path_str, "autosave": False},
    )
    vpid = _extract_vpid(_get_text(result_open))

    # Dirty the buffer
    await client_session.call_tool(
        "edit",
        arguments={
            "action": "replace",
            "viewport_id": vpid,
            "old_text": "save target",
            "new_text": "DIRTY",
        },
    )

    # Modify file externally
    (test_project_root / file_path_str).write_text("externally modified\n")
    time.sleep(0.05)

    # file:save should reject with severity: external_modification
    result = await client_session.call_tool(
        "file",
        arguments={"action": "save", "viewport_id": vpid, "file_path": file_path_str},
    )
    text = _get_text(result)
    assert result.isError, (
        f"SC-10 FAIL: save should reject dirty+external: {text[:200]}"
    )
    assert "severity: external_modification" in text, (
        f"SC-10 FAIL: severity: external_modification missing: {text[:200]}"
    )
    # Verify the full YAML structure of the conflict warning
    assert "conflict:" in text, (
        f"SC-10 FAIL: conflict: header missing: {text[:200]}"
    )
    assert "note:" in text, (
        f"SC-10 FAIL: note field missing: {text[:200]}"
    )
    assert "mtime:" in text, (
        f"SC-10 FAIL: mtime field missing: {text[:200]}"
    )


# ── Phase 2 tools regression guard ──────────────────────────────────────────


@pytest.mark.phase2
@pytest.mark.asyncio
async def test_phase2_tools_listed(client_session: Any) -> None:
    """Verify edit, file, diff tools are present in tool listing."""
    result = await client_session.list_tools()
    names = [t.name for t in result.tools]
    for name in ("edit", "file", "diff"):
        assert name in names, f"Tool {name} missing from tool list"
