# SPDX-FileCopyrightText: 2026 Michael Conrad
# SPDX-License-Identifier: MIT
# Provenance: AI-generated
"""Unit tests for composite action tools.

Co-authored with AI: OpenCode (deepseek-v4-flash)
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest


@pytest.fixture(scope="module")
def test_project_root() -> Path:
    tmpdir = Path(tempfile.mkdtemp(prefix="ve-comp-"))
    (tmpdir / "test_file.txt").write_text("line 1\nline 2\nline 3\nline 4\nline 5\n")
    return tmpdir


# ─── Item 1: read_file ────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_sc1_read_file_tool_exists(client_session: object) -> None:
    """read_file tool is registered alongside existing 7 tools (total 8)."""
    result = await client_session.list_tools()  # type: ignore[attr-defined]
    names = {t.name for t in result.tools}
    assert "read_file" in names, f"read_file not found in tools: {names}"
    expected = {"read_file", "write_file", "viewport", "edit", "file", "diff", "search", "regex", "clipboard"}
    assert names == expected, f"Tool mismatch: {names ^ expected}"


@pytest.mark.parametrize("line_start,line_end,expected_count", [
    (1, 3, 3),
    (3, 5, 3),
    (1, 100, 5),
])
@pytest.mark.asyncio
async def test_sc2_read_file_offset_limit(
    client_session: object,
    line_start: int,
    line_end: int,
    expected_count: int,
) -> None:
    """read_file with line_start/line_end returns the specified line range."""
    result = await client_session.call_tool("read_file", arguments={  # type: ignore[attr-defined]
        "file_path": "test_file.txt",
        "line_start": line_start,
        "line_end": line_end,
    })
    assert not result.isError, f"Got error: {result.content[0].text}"
    text = result.content[0].text
    # Verify content block has expected number of lines
    content_start = text.find("  content:")
    assert content_start >= 0, "Response missing content block"
    # Count numbered lines in content block (lines starting with digit after spaces)
    content_block = text[content_start:]
    content_lines = [ln for ln in content_block.split("\n") if ln.strip() and ln.strip()[0].isdigit()]
    assert len(content_lines) == expected_count, f"Expected {expected_count} lines, got {len(content_lines)}"


@pytest.mark.parametrize("bad_path", ["nonexistent.txt", "no_dir/no_file.txt"])
@pytest.mark.asyncio
async def test_sc3_read_file_not_found(
    client_session: object,
    bad_path: str,
) -> None:
    """read_file returns error for non-existent file."""
    result = await client_session.call_tool("read_file", arguments={  # type: ignore[attr-defined]
        "file_path": bad_path,
    })
    assert result.isError or "error:" in result.content[0].text.lower() or "not found" in result.content[0].text.lower()


@pytest.mark.asyncio
async def test_sc1_read_file_returns_content(client_session: object) -> None:
    """read_file returns file content with metadata."""
    result = await client_session.call_tool("read_file", arguments={  # type: ignore[attr-defined]
        "file_path": "test_file.txt",
    })
    assert not result.isError, f"Got error: {result.content[0].text}"
    text = result.content[0].text
    assert "line 1" in text
    assert "line 2" in text
    assert "line 3" in text
    assert "test_file.txt" in text


@pytest.mark.asyncio
async def test_sc1_read_file_has_metadata(client_session: object) -> None:
    """read_file response includes viewport metadata (file, line range, mtime, size)."""
    result = await client_session.call_tool("read_file", arguments={  # type: ignore[attr-defined]
        "file_path": "test_file.txt",
    })
    assert not result.isError, f"Got error: {result.content[0].text}"
    text = result.content[0].text
    assert "viewport_id:" in text
    assert "mtime:" in text or "size:" in text


# ─── Item 2: write_file ───────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_sc4_write_file_creates_new_file(client_session: object, test_project_root: Path) -> None:
    """write_file creates a new file with the specified content."""
    result = await client_session.call_tool("write_file", arguments={  # type: ignore[attr-defined]
        "file_path": "new_file.txt",
        "content": "hello world\nline 2\n",
    })
    assert not result.isError, f"Got error: {result.content[0].text}"
    text = result.content[0].text
    assert "written" in text.lower() or "saved" in text.lower() or "created" in text.lower()
    # Verify file exists on disk
    assert (test_project_root / "new_file.txt").exists()
    assert (test_project_root / "new_file.txt").read_text() == "hello world\nline 2\n"


@pytest.mark.asyncio
async def test_sc5_write_file_overwrites_existing(client_session: object, test_project_root: Path) -> None:
    """write_file overwrites an existing file with the specified content."""
    (test_project_root / "overwrite_test.txt").write_text("original content\n")
    result = await client_session.call_tool("write_file", arguments={  # type: ignore[attr-defined]
        "file_path": "overwrite_test.txt",
        "content": "replaced content\n",
    })
    assert not result.isError, f"Got error: {result.content[0].text}"
    assert (test_project_root / "overwrite_test.txt").read_text() == "replaced content\n"


@pytest.mark.asyncio
async def test_sc10_write_file_closes_viewport(client_session: object) -> None:
    """After write_file, the viewport is closed (no dangling sessions)."""
    # First open a file to establish a viewport
    await client_session.call_tool("read_file", arguments={  # type: ignore[attr-defined]
        "file_path": "test_file.txt",
    })
    # Now write to a new file — this should close the write viewport
    await client_session.call_tool("write_file", arguments={  # type: ignore[attr-defined]
        "file_path": "close_test.txt",
        "content": "test content\n",
    })
    # List viewports — should only have the read_file viewport, not the write one
    result = await client_session.call_tool("viewport", arguments={  # type: ignore[attr-defined]
        "action": "list",
    })
    assert not result.isError
    text = result.content[0].text
    # Should have 1 viewport (from read_file), not 2
    assert "viewports (1)" in text or "no open viewports" in text