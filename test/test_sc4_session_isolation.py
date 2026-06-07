# SPDX-FileCopyrightText: 2026 Michael Conrad
# SPDX-License-Identifier: MIT
# Provenance: AI-generated
"""SC-4 Behavioral test: two in-memory clients have different session IDs.

Verifies that two Client(server) instances produce distinct
ctx.session_id values from the same FastMCP server.

Co-authored with AI: OpenCode (deepseek-v4-flash)
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest
from fastmcp import Client, Context, FastMCP


@pytest.mark.asyncio
async def test_sc4_unique_session_ids() -> None:
    """Two clients on the same server get different session IDs.

    Verifies ctx.session_id from fastmcp's auto-injected Context
    differs between two concurrent Client connections.
    """
    tmpdir = Path(tempfile.mkdtemp(prefix="ve-sc4-"))
    (tmpdir / "test.txt").write_text("line 1\n")

    captured: dict[str, str] = {}

    # Build a test server with a probe tool that captures ctx.session_id
    server = FastMCP("sc4-test")

    @server.tool()
    def probe(ctx: Context, label: str) -> str:
        captured[label] = ctx.session_id
        return f"{label}: {ctx.session_id}"

    # Connect two clients to the same server
    async with Client(transport=server) as c1:
        await c1.call_tool("probe", arguments={"label": "client-a"})
    async with Client(transport=server) as c2:
        await c2.call_tool("probe", arguments={"label": "client-b"})

    assert "client-a" in captured
    assert "client-b" in captured
    assert captured["client-a"] != captured["client-b"], (
        f"Expected different session IDs, got both = {captured['client-a']}"
    )


@pytest.mark.asyncio
async def test_sc4_concurrent_clients() -> None:
    """Two concurrent clients connecting to the same server have different IDs."""
    ids: list[str] = []
    import asyncio

    server = FastMCP("sc4-concurrent")

    @server.tool()
    def probe(ctx: Context) -> str:
        ids.append(ctx.session_id)
        return f"sid={ctx.session_id}"

    async with Client(transport=server) as c1, Client(transport=server) as c2:
        r1, r2 = await asyncio.gather(
            c1.call_tool("probe", arguments={}),
            c2.call_tool("probe", arguments={}),
        )

    assert len(ids) == 2
    assert ids[0] != ids[1], (
        f"Concurrent clients should have different session IDs: {ids}"
    )
