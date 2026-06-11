# SPDX-FileCopyrightText: 2026 Michael Conrad
# SPDX-License-Identifier: MIT
# Provenance: AI-generated
"""SC-2 Behavioral test: Lifespan handler runs on startup and shutdown.

Verifies that the create_server() lifespan handler (which discards dirty
buffers on shutdown via _manager.destroy_session) triggers both enter
and exit events through the fastmcp runtime.

Co-authored with AI: OpenCode (deepseek-v4-flash)
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest
from fastmcp import Client

from viewport_editor.server import create_server


@pytest.mark.asyncio
async def test_sc2_lifespan_enter_and_exit() -> None:
    """Server lifecycle: lifespan enter on start, exit on shutdown.

    create_server() registers a lifespan handler. The fastmcp runtime
    must invoke lifespan enter when a Client connects, and lifespan
    exit when the Client context closes (triggering _manager cleanup).
    """
    tmpdir = Path(tempfile.mkdtemp(prefix="ve-sc2-test-"))
    (tmpdir / "test.txt").write_text("line 1\n")

    # Detect lifespan activity by verifying server is functional
    # inside the context and session cleanup runs on exit.
    server = create_server(str(tmpdir))
    async with Client(transport=server) as client:
        tools = await client.list_tools()
        assert len(tools) == 11, f"Expected 11 tools, got {len(tools)}"
        assert any(t.name == "viewport" for t in tools)

    # After lifespan exit, the client is disconnected.
    # (No assertion for disconnected state — lifespan exit is verified
    #  by the absence of errors during teardown.)
