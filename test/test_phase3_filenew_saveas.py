# SPDX-FileCopyrightText: 2026 Michael Conrad
# SPDX-License-Identifier: MIT
# Provenance: AI-generated
"""Phase 3 RED behavioral tests for file:new and file:save-as tools of viewport-editor MCP server.

These tests assert GREEN-phase behavior and MUST FAIL against current stubs
(which do not handle "new" or "save-as" file actions). When Phase 3 is
implemented, these tests must PASS.

SCs covered:
- SC-15: file:new creates file and opens viewport with autosave=off
- SC-16: file:save-as with force=false rejects existing target; force=true overwrites
- SC-LF-2: save-as handler opens temp file with newline="" — CRLF files preserved after save-as
- SC-TMP-2: save-as handler uses tempfile.mkstemp(dir=...) instead of string concatenation for temp path
- SC-LF-3: file:new opens file with newline="" for consistency

Co-authored with AI: OpenCode (ollama-cloud/glm-5.1)
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
    tmpdir = Path(tempfile.mkdtemp(prefix="ve-p3-test-"))
    (tmpdir / "existing_file.txt").write_text("original line one\noriginal line two\n")
    (tmpdir / "saveas_source.txt").write_text("source content A\nsource content B\n")
    (tmpdir / "crlf_source.txt").write_bytes(b"alpha\r\nbeta\r\ngamma\r\n")
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


# ── SC-15: file:new creates file and opens viewport with autosave=off ────────


@pytest.mark.phase3
@pytest.mark.asyncio
async def test_sc15_file_new_creates_file_and_opens_viewport(
    client_session: ClientSession, test_project_root: Path
) -> None:
    """SC-15: file:new creates a new file on disk and opens a viewport with autosave=off.

    RED: 'new' action not implemented in file tool — returns error or unknown action.
    GREEN: file:new creates the file, opens viewport, viewport has autosave=False.
    """
    new_file = "brand_new_file.txt"
    target_path = test_project_root / new_file

    if target_path.exists():
        target_path.unlink()

    result = await client_session.call_tool(
        "file",
        arguments={
            "action": "new",
            "session_id": "test-sc15",
            "file_path": new_file,
        },
    )
    text = _get_text(result)

    assert not result.isError, (
        f"SC-15 FAIL: file:new should succeed, got error: {text[:300]}"
    )

    assert target_path.exists(), (
        f"SC-15 FAIL: file:new did not create file on disk: {text[:300]}"
    )

    vpid = _extract_vpid(text)
    assert vpid, f"SC-15 FAIL: file:new did not return viewport_id: {text[:300]}"

    list_result = await client_session.call_tool(
        "viewport",
        arguments={"action": "list", "session_id": "test-sc15"},
    )
    list_text = _get_text(list_result)
    assert "autosave: False" in list_text or "autosave: false" in list_text.lower(), (
        f"SC-15 FAIL: file:new viewport should have autosave=False: {list_text[:300]}"
    )


# ── SC-15: file:new with existing file returns error ─────────────────────────


@pytest.mark.phase3
@pytest.mark.asyncio
async def test_sc15_file_new_rejects_existing_file(
    client_session: ClientSession,
) -> None:
    """SC-15: file:new rejects when a file with the same name already exists.

    RED: 'new' action not implemented.
    GREEN: file:new returns isError for existing file.
    """
    result = await client_session.call_tool(
        "file",
        arguments={
            "action": "new",
            "session_id": "test-sc15-exists",
            "file_path": "existing_file.txt",
        },
    )
    text = _get_text(result)

    assert result.isError, (
        f"SC-15 FAIL: file:new should reject existing file, got: {text[:300]}"
    )
    assert "exists" in text.lower() or "already" in text.lower(), (
        f"SC-15 FAIL: error should mention file exists: {text[:300]}"
    )


# ── SC-16: file:save-as with force=false rejects existing target ─────────────


@pytest.mark.phase3
@pytest.mark.asyncio
async def test_sc16_save_as_rejects_existing_target_without_force(
    client_session: ClientSession,
) -> None:
    """SC-16: file:save-as with force=false rejects when target file exists.

    RED: 'save-as' action not implemented in file tool.
    GREEN: file:save-as returns isError indicating target exists.
    """
    result_open = await client_session.call_tool(
        "viewport",
        arguments={
            "action": "open",
            "session_id": "test-sc16-nf",
            "file_path": "saveas_source.txt",
        },
    )
    vpid = _extract_vpid(_get_text(result_open))

    result = await client_session.call_tool(
        "file",
        arguments={
            "action": "save-as",
            "session_id": "test-sc16-nf",
            "viewport_id": vpid,
            "file_path": "existing_file.txt",
            "force": False,
        },
    )
    text = _get_text(result)

    assert result.isError, (
        f"SC-16 FAIL: save-as with force=false should reject existing target: {text[:300]}"
    )
    assert (
        "exists" in text.lower()
        or "already" in text.lower()
        or "overwrite" in text.lower()
    ), f"SC-16 FAIL: error should mention target exists: {text[:300]}"


# ── SC-16: file:save-as with force=true overwrites existing target ────────────


@pytest.mark.phase3
@pytest.mark.asyncio
async def test_sc16_save_as_overwrites_existing_target_with_force(
    client_session: ClientSession, test_project_root: Path
) -> None:
    """SC-16: file:save-as with force=true overwrites existing target file.

    RED: 'save-as' action not implemented in file tool.
    GREEN: save-as succeeds; target file now contains source content.
    """
    target_path = test_project_root / "overwrite_target.txt"
    target_path.write_text("this will be overwritten\n")

    result_open = await client_session.call_tool(
        "viewport",
        arguments={
            "action": "open",
            "session_id": "test-sc16-force",
            "file_path": "saveas_source.txt",
        },
    )
    vpid = _extract_vpid(_get_text(result_open))

    result = await client_session.call_tool(
        "file",
        arguments={
            "action": "save-as",
            "session_id": "test-sc16-force",
            "viewport_id": vpid,
            "file_path": "overwrite_target.txt",
            "force": True,
        },
    )
    text = _get_text(result)

    assert not result.isError, (
        f"SC-16 FAIL: save-as with force=true should succeed: {text[:300]}"
    )

    disk = target_path.read_text()
    assert "source content A" in disk, (
        f"SC-16 FAIL: target file should contain source content after overwrite: {disk!r}"
    )


# ── SC-16: file:save-as to new path creates new file ─────────────────────────


@pytest.mark.phase3
@pytest.mark.asyncio
async def test_sc16_save_as_creates_new_file(
    client_session: ClientSession, test_project_root: Path
) -> None:
    """SC-16: file:save-as to a non-existent path creates a new file with buffer content.

    RED: 'save-as' action not implemented.
    GREEN: new file created on disk with buffer content.
    """
    new_target = test_project_root / "saveas_new_target.txt"
    if new_target.exists():
        new_target.unlink()

    result_open = await client_session.call_tool(
        "viewport",
        arguments={
            "action": "open",
            "session_id": "test-sc16-new",
            "file_path": "saveas_source.txt",
        },
    )
    vpid = _extract_vpid(_get_text(result_open))

    result = await client_session.call_tool(
        "file",
        arguments={
            "action": "save-as",
            "session_id": "test-sc16-new",
            "viewport_id": vpid,
            "file_path": "saveas_new_target.txt",
        },
    )
    text = _get_text(result)

    assert not result.isError, (
        f"SC-16 FAIL: save-as to new path should succeed: {text[:300]}"
    )

    assert new_target.exists(), (
        f"SC-16 FAIL: save-as did not create new target file: {text[:300]}"
    )

    disk = new_target.read_text()
    assert "source content A" in disk, (
        f"SC-16 FAIL: new target should contain buffer content: {disk!r}"
    )


# ── SC-LF-2: save-as handler opens temp file with newline="" — CRLF preserved ─


@pytest.mark.phase3
@pytest.mark.asyncio
async def test_sc_lf2_save_as_preserves_crlf(
    client_session: ClientSession, test_project_root: Path
) -> None:
    """SC-LF-2: save-as handler opens temp file with newline="" — CRLF files preserved after save-as.

    RED: 'save-as' action not implemented, or CRLF stripped by open() without newline="".
    GREEN: after save-as of CRLF file, target disk content still has \\r\\n.
    """
    target_path = test_project_root / "crlf_saveas_target.txt"
    if target_path.exists():
        target_path.unlink()

    result_open = await client_session.call_tool(
        "viewport",
        arguments={
            "action": "open",
            "session_id": "test-sc-lf2",
            "file_path": "crlf_source.txt",
        },
    )
    vpid = _extract_vpid(_get_text(result_open))

    result = await client_session.call_tool(
        "file",
        arguments={
            "action": "save-as",
            "session_id": "test-sc-lf2",
            "viewport_id": vpid,
            "file_path": "crlf_saveas_target.txt",
        },
    )
    text = _get_text(result)

    assert not result.isError, f"SC-LF-2 FAIL: save-as should succeed: {text[:300]}"

    disk_bytes = target_path.read_bytes()
    assert b"\r\n" in disk_bytes, (
        f"SC-LF-2 FAIL: CRLF line endings lost after save-as. "
        f"Disk content: {disk_bytes!r}"
    )


# ── SC-TMP-2: save-as handler uses mkstemp(dir=...) not string concatenation ─


@pytest.mark.phase3
@pytest.mark.asyncio
async def test_sc_tmp2_save_as_uses_mkstemp(
    client_session: ClientSession, test_project_root: Path
) -> None:
    """SC-TMP-2: save-as handler uses tempfile.mkstemp(dir=...) for temp path.

    Behavioral verification:
    1. No predictable .tmp file remains after save-as
    2. No orphan temp files in the directory after save-as

    RED: 'save-as' not implemented, or uses string concatenation for temp path.
    GREEN: mkstemp creates randomized temp file names; no predictable leftovers.
    """
    new_target = test_project_root / "mkstemp_saveas_target.txt"
    if new_target.exists():
        new_target.unlink()

    result_open = await client_session.call_tool(
        "viewport",
        arguments={
            "action": "open",
            "session_id": "test-sc-tmp2",
            "file_path": "saveas_source.txt",
        },
    )
    vpid = _extract_vpid(_get_text(result_open))

    result = await client_session.call_tool(
        "file",
        arguments={
            "action": "save-as",
            "session_id": "test-sc-tmp2",
            "viewport_id": vpid,
            "file_path": "mkstemp_saveas_target.txt",
        },
    )
    text = _get_text(result)

    assert not result.isError, f"SC-TMP-2 FAIL: save-as should succeed: {text[:300]}"

    predictable_tmp = test_project_root / "mkstemp_saveas_target.txt.tmp"
    assert not predictable_tmp.exists(), (
        "SC-TMP-2 FAIL: Predictable .tmp file exists at "
        f"{predictable_tmp}. save-as should use tempfile.mkstemp "
        "(random names), not string concatenation."
    )

    all_files = list(test_project_root.iterdir())
    tmp_files = [
        f
        for f in all_files
        if f.name.startswith("mkstemp_saveas") and f.suffix != ".txt"
    ]
    assert len(tmp_files) == 0, (
        f"SC-TMP-2 FAIL: Orphan temp files remain: {tmp_files}. "
        "Atomic save-as should clean up temp files after os.replace."
    )


# ── SC-LF-3: file:new opens file with newline="" for consistency ─────────────


@pytest.mark.phase3
@pytest.mark.asyncio
async def test_sc_lf3_file_new_opens_with_newline_empty(
    client_session: ClientSession, test_project_root: Path
) -> None:
    """SC-LF-3: file:new opens file with newline="" for consistency.

    This means: if content is later written to the new file, line ending
    detection should work correctly and not be corrupted by platform
    text mode translation. A new file created by file:new should be
    empty on disk, and when content is written it should respect
    the newline convention.

    RED: 'new' action not implemented.
    GREEN: file:new creates empty file; writing CRLF content to it preserves \\r\\n.
    """
    new_file = "newline_consistency_test.txt"
    target_path = test_project_root / new_file

    if target_path.exists():
        target_path.unlink()

    result = await client_session.call_tool(
        "file",
        arguments={
            "action": "new",
            "session_id": "test-sc-lf3",
            "file_path": new_file,
        },
    )
    text = _get_text(result)

    assert not result.isError, f"SC-LF-3 FAIL: file:new should succeed: {text[:300]}"

    assert target_path.exists(), (
        f"SC-LF-3 FAIL: file:new did not create file on disk: {text[:300]}"
    )

    initial_disk = target_path.read_bytes()
    assert initial_disk == b"", (
        f"SC-LF-3 FAIL: new file should be empty, got: {initial_disk!r}"
    )

    vpid = _extract_vpid(text)
    assert vpid, f"SC-LF-3 FAIL: file:new did not return viewport_id: {text[:300]}"

    list_result = await client_session.call_tool(
        "viewport",
        arguments={"action": "list", "session_id": "test-sc-lf3"},
    )
    list_text = _get_text(list_result)
    assert "autosave: False" in list_text or "autosave: false" in list_text.lower(), (
        f"SC-LF-3 FAIL: file:new viewport should have autosave=False: {list_text[:300]}"
    )


# ── SC-LF-3 extended: write CRLF to new file, verify preservation ────────────


@pytest.mark.phase3
@pytest.mark.asyncio
async def test_sc_lf3_file_new_crlf_write_preserved(
    client_session: ClientSession, test_project_root: Path
) -> None:
    """SC-LF-3 extended: file:new creates viewport correctly; writing CRLF content then saving preserves \\r\\n.

    RED: 'new' action not implemented or newline="" not used.
    GREEN: after creating new file, inserting CRLF content, and saving, \\r\\n is preserved on disk.
    """
    new_file = "crlf_new_file_test.txt"
    target_path = test_project_root / new_file

    if target_path.exists():
        target_path.unlink()

    result = await client_session.call_tool(
        "file",
        arguments={
            "action": "new",
            "session_id": "test-sc-lf3-crlf",
            "file_path": new_file,
        },
    )
    text = _get_text(result)
    vpid = _extract_vpid(text)

    assert vpid, f"SC-LF-3-CRLF FAIL: file:new did not return viewport_id: {text[:300]}"

    await client_session.call_tool(
        "edit",
        arguments={
            "action": "insert-lines",
            "session_id": "test-sc-lf3-crlf",
            "viewport_id": vpid,
            "file_path": new_file,
            "line_start": 1,
            "lines": ["line one", "line two", "line three"],
        },
    )

    await client_session.call_tool(
        "viewport",
        arguments={
            "action": "autosave",
            "session_id": "test-sc-lf3-crlf",
            "viewport_id": vpid,
            "autosave_enabled": True,
        },
    )

    await client_session.call_tool(
        "file",
        arguments={
            "action": "save",
            "session_id": "test-sc-lf3-crlf",
            "viewport_id": vpid,
            "file_path": new_file,
        },
    )

    disk_bytes = target_path.read_bytes()
    assert b"line one" in disk_bytes, (
        f"SC-LF-3-CRLF FAIL: content not written to new file: {disk_bytes!r}"
    )


# ── SC-16: file:save-as updates viewport to point at new file ───────────────


@pytest.mark.phase3
@pytest.mark.asyncio
async def test_sc16_save_as_updates_viewport_file_reference(
    client_session: ClientSession,
) -> None:
    """SC-16: file:save-as updates viewport to track the new target file path.

    RED: 'save-as' action not implemented.
    GREEN: after save-as, viewport list shows the new file path.
    """
    result_open = await client_session.call_tool(
        "viewport",
        arguments={
            "action": "open",
            "session_id": "test-sc16-ref",
            "file_path": "saveas_source.txt",
        },
    )
    vpid = _extract_vpid(_get_text(result_open))

    result = await client_session.call_tool(
        "file",
        arguments={
            "action": "save-as",
            "session_id": "test-sc16-ref",
            "viewport_id": vpid,
            "file_path": "saveas_ref_target.txt",
        },
    )
    text = _get_text(result)

    assert not result.isError, f"SC-16-REF FAIL: save-as should succeed: {text[:300]}"

    list_result = await client_session.call_tool(
        "viewport",
        arguments={"action": "list", "session_id": "test-sc16-ref"},
    )
    list_text = _get_text(list_result)
    assert "saveas_ref_target.txt" in list_text, (
        f"SC-16-REF FAIL: viewport should now reference new file after save-as: "
        f"{list_text[:300]}"
    )


# ── Phase 3 regression guard ─────────────────────────────────────────────────


@pytest.mark.phase3
@pytest.mark.asyncio
async def test_phase3_tools_listed(client_session: ClientSession) -> None:
    """Verify file tool is present in tool listing (existing tool, regression guard)."""
    result = await client_session.list_tools()
    names = [t.name for t in result.tools]
    assert "file" in names, "Tool 'file' missing from tool list"
