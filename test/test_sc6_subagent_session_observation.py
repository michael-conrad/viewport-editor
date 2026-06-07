# SPDX-FileCopyrightText: 2026 Michael Conrad
# SPDX-License-Identifier: MIT
# Provenance: AI-generated
"""SC-6 Observational: document session behavior of two Client connections.

ZERO assertions — prints session IDs and viewport list for manual inspection.

Co-authored with AI: OpenCode (deepseek-v4-flash)
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastmcp import Client, Context

from viewport_editor.server import create_server


@pytest.mark.asyncio
async def test_sc6_observe_two_sessions(tmp_path: Path) -> None:
    """Two sequential Client connections: observe session IDs and viewport state.

    Observational only — zero assertions. See docs/mcp-plugin-behavior.md for
    the human-interpreted summary of these observations.

    Observation purpose: determine whether session forwarding (sharing
    ctx.session_id between sub-agent and orchestrator) is needed.
    Two Client connections correspond to orchestrator + sub-agent.
    If C2 sees C1's viewports, forwarding is NOT needed (same session
    backend). If C2 sees NO open viewports, forwarding IS needed.
    """

    (tmp_path / "test.txt").write_text("hello world\nline 2\nline 3\n")

    server = create_server(str(tmp_path))

    @server.tool()
    def probe_sid(ctx: Context, label: str) -> str:
        return f"{label}: {ctx.session_id}"

    # C1: open test.txt and probe session id
    async with Client(transport=server) as c1:
        r_open = await c1.call_tool(
            "viewport",
            arguments={"action": "open", "file_path": "test.txt"},
        )
        r_probe1 = await c1.call_tool("probe_sid", arguments={"label": "C1"})

    # C2: list viewports and probe session id
    async with Client(transport=server) as c2:
        r_list = await c2.call_tool(
            "viewport",
            arguments={"action": "list"},
        )
        r_probe2 = await c2.call_tool("probe_sid", arguments={"label": "C2"})

    c1_sid = r_probe1.content[0].text
    c2_sid = r_probe2.content[0].text
    same_diff = "SAME" if c1_sid == c2_sid else "DIFFERENT"
    forwarding_needed = "YES" if same_diff == "DIFFERENT" else "NO"
    c1_open_text = r_open.content[0].text if r_open.content else "(no output)"

    print()
    print("=== SC-6 Observational: Two Session Behavior ===")
    print(f"  C1 open result: {c1_open_text}")
    print(f"  C1 session ID:  {c1_sid}")
    print(f"  C2 session ID:  {c2_sid}")
    print(f"  Sessions are:   {same_diff}")
    print(f"  Forwarding needed: {forwarding_needed}")
    print("  C2 viewport list output:")
    for item in r_list.content:
        print(f"    {item.text}")
    print("=== End SC-6 Observation ===")
