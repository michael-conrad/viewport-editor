# SPDX-FileCopyrightText: 2026 Michael Conrad
# SPDX-License-Identifier: MIT
# Provenance: AI-generated
"""SC-3 Behavioral test: ctx.session_id returns non-empty string within handler.

Verifies that fastmcp's auto-injected ctx: Context provides a valid
session_id to tool handlers.

Co-authored with AI: OpenCode (deepseek-v4-flash)
"""

from __future__ import annotations

import uuid

import pytest
from fastmcp import FastMCP, Context, Client


@pytest.mark.asyncio
async def test_sc3_session_id_is_non_empty_string() -> None:
    """ctx.session_id returns a non-empty string within a tool handler."""
    captured: list[str] = []

    server = FastMCP("test-session")

    @server.tool()
    def probe(ctx: Context) -> str:
        sid = ctx.session_id
        captured.append(sid)
        return f"sid={sid}"

    async with Client(transport=server) as client:
        await client.call_tool("probe", arguments={})

    assert len(captured) == 1
    sid = captured[0]
    assert isinstance(sid, str), f"session_id should be str, got {type(sid)}"
    assert len(sid) > 0, "session_id should be non-empty"
    assert uuid.UUID(sid), f"session_id should be a valid UUID, got {sid}"


@pytest.mark.asyncio
async def test_sc3_two_clients_different_session_ids() -> None:
    """Two separate Client instances get different session_id values."""
    ids: list[str] = []

    def make_server(label: str) -> FastMCP:
        srv = FastMCP(label)

        @srv.tool()
        def probe(ctx: Context) -> str:
            ids.append(ctx.session_id)
            return f"sid={ctx.session_id}"

        return srv

    async with Client(transport=make_server("a")) as c1:
        await c1.call_tool("probe", arguments={})
    async with Client(transport=make_server("b")) as c2:
        await c2.call_tool("probe", arguments={})

    assert len(ids) == 2, f"Expected 2 session IDs, got {len(ids)}"
    assert ids[0] != ids[1], (
        f"Two clients should have different session IDs: {ids}"
    )