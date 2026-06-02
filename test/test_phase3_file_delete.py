# SPDX-FileCopyrightText: 2026 Michael Conrad
# SPDX-License-Identifier: MIT
# Provenance: AI-generated
"""Phase 3 RED behavioral tests for file:delete tool of viewport-editor MCP server.

These tests assert GREEN-phase behavior and MUST FAIL against current code
(which does not handle the "delete" file action). When Phase 3 is implemented,
these tests must PASS.

SCs covered:
- SC-30: file:delete removes file on disk; rejects when buffer has uncommitted changes

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
    tmpdir = Path(tempfile.mkdtemp(prefix="ve-p3-delete-test-"))
    (tmpdir / "delete_target.txt").write_text("line one\nline two\nline three\n")
    (tmpdir / "dirty_delete_target.txt").write_text("original content\n")
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


# ── SC-30: file:delete removes file on disk ─────────────────────────────────


@pytest.mark.phase3
@pytest.mark.asyncio
async def test_file_delete_removes_file(
    client_session: ClientSession, test_project_root: Path
) -> None:
    """SC-30: file:delete removes file on disk.

    Opens a file, deletes it via file:delete, verifies the file
    no longer exists on disk and the viewport is closed.
    """
    target_path = test_project_root / "delete_target.txt"
    assert target_path.exists(), (
        f"Test setup failed: {target_path} should exist before deletion"
    )

    result_open = await client_session.call_tool(
        "viewport",
        arguments={
            "action": "open",
            "session_id": "test-sc30-delete",
            "file_path": "delete_target.txt",
        },
    )
    text_open = _get_text(result_open)
    vpid = _extract_vpid(text_open)
    assert vpid, f"Failed to open viewport: {text_open[:300]}"

    result = await client_session.call_tool(
        "file",
        arguments={
            "action": "delete",
            "session_id": "test-sc30-delete",
            "viewport_id": vpid,
        },
    )
    text = _get_text(result)

    assert not result.isError, (
        f"SC-30 FAIL: file:delete should succeed, got error: {text[:300]}"
    )

    assert not target_path.exists(), (
        f"SC-30 FAIL: file should not exist on disk after delete: {text[:300]}"
    )

    assert "deleted" in text.lower() or "removed" in text.lower(), (
        f"SC-30 FAIL: response should confirm deletion: {text[:300]}"
    )


# ── SC-30: file:delete rejects when buffer has uncommitted changes ────────────


@pytest.mark.phase3
@pytest.mark.asyncio
async def test_file_delete_dirty_buffer_rejects(
    client_session: ClientSession,
) -> None:
    """SC-30: file:delete rejects when buffer has uncommitted changes.

    Opens a file, edits it (making buffer dirty), then attempts delete.
    Should return isError indicating dirty buffer.
    """
    result_open = await client_session.call_tool(
        "viewport",
        arguments={
            "action": "open",
            "session_id": "test-sc30-dirty",
            "file_path": "dirty_delete_target.txt",
        },
    )
    text_open = _get_text(result_open)
    vpid = _extract_vpid(text_open)
    assert vpid, f"Failed to open viewport: {text_open[:300]}"

    await client_session.call_tool(
        "edit",
        arguments={
            "action": "replace",
            "session_id": "test-sc30-dirty",
            "viewport_id": vpid,
            "old_text": "original content",
            "new_text": "modified content",
        },
    )

    result = await client_session.call_tool(
        "file",
        arguments={
            "action": "delete",
            "session_id": "test-sc30-dirty",
            "viewport_id": vpid,
        },
    )
    text = _get_text(result)

    assert result.isError, (
        f"SC-30 FAIL: file:delete should reject dirty buffer, got: {text[:300]}"
    )
    assert (
        "dirty" in text.lower()
        or "uncommitted" in text.lower()
        or "unsaved" in text.lower()
    ), f"SC-30 FAIL: error should mention dirty/uncommitted buffer: {text[:300]}"


# ── Phase 3 regression guard for file:delete ──────────────────────────────────


@pytest.mark.phase3
@pytest.mark.asyncio
async def test_phase3_delete_tools_listed(client_session: ClientSession) -> None:
    """Verify file tool is present in tool listing (regression guard)."""
    result = await client_session.list_tools()
    names = [t.name for t in result.tools]
    assert "file" in names, "Tool 'file' missing from tool list"
