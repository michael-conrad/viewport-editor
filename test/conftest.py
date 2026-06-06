# SPDX-FileCopyrightText: 2026 Michael Conrad
# SPDX-License-Identifier: MIT
# Provenance: AI-generated
"""Shared test fixtures for viewport-editor.

Co-authored with AI: OpenCode (deepseek-v4-flash)
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import AsyncIterator

import pytest
from fastmcp import Client

from viewport_editor.server import create_server


@pytest.fixture(scope="module")
def test_project_root() -> Path:
    """Create a temporary project root with seed files for testing."""
    tmpdir = Path(tempfile.mkdtemp(prefix="ve-test-"))
    (tmpdir / "test_file.txt").write_text("line 1\nline 2\nline 3\nline 4\nline 5\n")
    (tmpdir / "long_file.txt").write_text("\n".join(f"line {i}" for i in range(1, 101)))
    (tmpdir / "non_printing.txt").write_bytes(b"null\x00byte\ncontrol\x01\x02end\n")
    (tmpdir / "unicode_test.txt").write_text("line A\nline B\nline C\nline D\nline E\n")
    return tmpdir


@pytest.fixture
async def fastmcp_client(
    test_project_root: Path,
) -> AsyncIterator[Client]:
    """Create an in-memory MCP client connected to a viewport-editor server.

    The server uses the temporary project root from test_project_root.
    No stdio subprocess is spawned — the client connects directly in-process.
    """
    server = create_server(str(test_project_root))
    async with Client(transport=server) as client:
        yield client
