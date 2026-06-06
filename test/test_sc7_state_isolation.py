# SPDX-FileCopyrightText: 2026 Michael Conrad
# SPDX-License-Identifier: MIT
# Provenance: AI-generated
"""SC-7 Behavioral test: ctx.set_state/get_state session isolation.

Verifies that per-session state set via one Client connection is
not visible to a different Client connection on the same server.

Co-authored with AI: OpenCode (deepseek-v4-flash)
"""

from __future__ import annotations

import pytest
from fastmcp import FastMCP, Context, Client


@pytest.mark.asyncio
async def test_sc7_session_isolation() -> None:
    """Session A sets state, session B reads None (isolated)."""
    server = FastMCP("sc7-isolation")

    @server.tool()
    async def set_val(ctx: Context, key: str, val: str) -> str:
        await ctx.set_state(key, val)
        return f"set {key}={val}"

    @server.tool()
    async def get_val(ctx: Context, key: str) -> str:
        val = await ctx.get_state(key)
        return f"{key}={val!r}"

    # Session A: set state
    async with Client(transport=server) as a:
        r = await a.call_tool("set_val", arguments={"key": "color", "val": "blue"})
        assert not r.is_error

        # Session A: read back — should see "blue"
        r = await a.call_tool("get_val", arguments={"key": "color"})
        assert "blue" in r.content[0].text

    # Session B: different connection — should not see A's state
    async with Client(transport=server) as b:
        r = await b.call_tool("get_val", arguments={"key": "color"})
        assert "blue" not in r.content[0].text
        # fastmcp returns None as Python None, converted to str
        assert "None" in r.content[0].text or "val=None" in r.content[0].text


@pytest.mark.asyncio
async def test_sc7_counter_isolated_per_session() -> None:
    """Counter state stays isolated per session (spec requirement)."""
    server = FastMCP("sc7-counter")

    @server.tool()
    async def increment(ctx: Context) -> str:
        count = await ctx.get_state("count") or 0
        count += 1
        await ctx.set_state("count", count)
        return f"count={count}"

    async with Client(transport=server) as a:
        r = await a.call_tool("increment", arguments={})
        assert r.content[0].text == "count=1"
        r = await a.call_tool("increment", arguments={})
        assert r.content[0].text == "count=2"

    # Session B starts fresh
    async with Client(transport=server) as b:
        r = await b.call_tool("increment", arguments={})
        assert r.content[0].text == "count=1", (
            f"Expected count=1 for fresh session, got {r.content[0].text}"
        )