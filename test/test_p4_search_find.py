# SPDX-FileCopyrightText: 2026 Michael Conrad
# SPDX-License-Identifier: MIT
# Provenance: AI-generated
"""Phase 4 RED tests for search:find (SC-17).

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
def search_project_root() -> Path:
    tmpdir = Path(tempfile.mkdtemp(prefix="ve-search-"))
    (tmpdir / "alpha.py").write_text(
        "def hello():\n    print('hello world')\n    return True\n\ndef goodbye():\n    print('goodbye')\n    return False\n"
    )
    (tmpdir / "beta.py").write_text(
        "import os\n\ndef hello():\n    print('hello from beta')\n\nx = 42\n"
    )
    (tmpdir / "gamma.txt").write_text(
        "line one\nline two with hello\nline three\nLINE FOUR UPPER\nline five\n"
    )
    return tmpdir


@pytest.fixture(scope="module")
def search_server_params(search_project_root: Path) -> StdioServerParameters:
    return StdioServerParameters(
        command="uv",
        args=[
            "run",
            "python",
            "-m",
            "viewport_editor",
            "--project-root",
            str(search_project_root),
        ],
    )


@pytest.fixture
async def search_client(
    search_server_params: StdioServerParameters,
) -> AsyncIterator[ClientSession]:
    try:
        async with stdio_client(search_server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                yield session
    except RuntimeError as exc:
        msg = str(exc)
        if "Attempted to exit cancel scope in a different task" not in msg:
            raise


@pytest.mark.phase4
@pytest.mark.asyncio
async def test_search_find_substring_default(
    search_client: ClientSession,
) -> None:
    """SC-17: search:find with substring (default) returns structured results with line numbers."""
    result = await search_client.call_tool(
        "search",
        arguments={
            "action": "find",
            "session_id": "sc17-sub",
            "pattern": "hello",
        },
    )
    text = _get_text(result)
    assert not result.isError, f"search:find returned error: {text[:200]}"
    assert "results:" in text or "matches:" in text or "find" in text.lower()
    assert "line" in text.lower(), "results must include line numbers"
    assert "hello" in text, "results must contain the matched pattern"


@pytest.mark.phase4
@pytest.mark.asyncio
async def test_search_find_regex_flag(
    search_client: ClientSession,
) -> None:
    """SC-17: search:find with regex=True uses regex pattern matching."""
    result = await search_client.call_tool(
        "search",
        arguments={
            "action": "find",
            "session_id": "sc17-regex",
            "pattern": r"def \w+",
            "regex": True,
        },
    )
    text = _get_text(result)
    assert not result.isError, f"search:find regex returned error: {text[:200]}"
    assert "line" in text.lower(), "regex results must include line numbers"
    assert "def " in text, "regex results must contain matched function definitions"


@pytest.mark.phase4
@pytest.mark.asyncio
async def test_search_find_scope_file(
    search_client: ClientSession,
) -> None:
    """SC-17: search:find scoped to a single file returns results only from that file."""
    result = await search_client.call_tool(
        "search",
        arguments={
            "action": "find",
            "session_id": "sc17-sf",
            "pattern": "hello",
            "scope": "file",
            "file_path": "alpha.py",
        },
    )
    text = _get_text(result)
    assert not result.isError, f"search:find scope=file returned error: {text[:200]}"
    assert "alpha.py" in text, "scoped file results must reference the file"
    assert "line" in text.lower(), "scoped results must include line numbers"


@pytest.mark.phase4
@pytest.mark.asyncio
async def test_search_find_scope_viewport(
    search_client: ClientSession,
) -> None:
    """SC-17: search:find scoped to viewport searches only within the open viewport."""
    open_result = await search_client.call_tool(
        "viewport",
        arguments={
            "action": "open",
            "session_id": "sc17-sv",
            "file_path": "alpha.py",
        },
    )
    open_text = _get_text(open_result)
    vpid = _extract_vpid(open_text)

    result = await search_client.call_tool(
        "search",
        arguments={
            "action": "find",
            "session_id": "sc17-sv",
            "pattern": "hello",
            "scope": "viewport",
            "viewport_id": vpid,
        },
    )
    text = _get_text(result)
    assert not result.isError, (
        f"search:find scope=viewport returned error: {text[:200]}"
    )
    assert "line" in text.lower(), "viewport-scoped results must include line numbers"


@pytest.mark.phase4
@pytest.mark.asyncio
async def test_search_find_scope_all_open(
    search_client: ClientSession,
) -> None:
    """SC-17: search:find scoped to all_open searches across all open viewports."""
    await search_client.call_tool(
        "viewport",
        arguments={
            "action": "open",
            "session_id": "sc17-ao",
            "file_path": "alpha.py",
        },
    )
    await search_client.call_tool(
        "viewport",
        arguments={
            "action": "open",
            "session_id": "sc17-ao",
            "file_path": "beta.py",
        },
    )

    result = await search_client.call_tool(
        "search",
        arguments={
            "action": "find",
            "session_id": "sc17-ao",
            "pattern": "hello",
            "scope": "all_open",
        },
    )
    text = _get_text(result)
    assert not result.isError, (
        f"search:find scope=all_open returned error: {text[:200]}"
    )
    assert "line" in text.lower(), "all_open results must include line numbers"
    assert "alpha.py" in text or "beta.py" in text, (
        "all_open results must reference at least one open viewport file"
    )


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
