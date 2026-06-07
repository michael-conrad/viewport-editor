# SPDX-FileCopyrightText: 2026 Michael Conrad
# SPDX-License-Identifier: MIT
# Provenance: AI-generated
"""SC-6 Observational: sub-agent viewport isolation from orchestrator.

C1 (orchestrator) opens a viewport. C2 (sub-agent) connects concurrently
while C1 is still active. This models the real MCP dispatch scenario:
orchestrator dispatches a clean-room sub-agent via task() — the sub-agent
gets its own Client connection with its own ctx.session_id.

Key question: can the sub-agent (C2) see the orchestrator's (C1) viewports?

If C2's `viewport:list` shows C1's viewports, then session forwarding
(cross-Client session sharing) is NOT needed — same backend sees all.
If C2 sees "no open viewports", then session forwarding IS needed.

Zero assertions — observational only.

Co-authored with AI: OpenCode (deepseek-v4-flash)
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastmcp import Client, Context

from viewport_editor.server import create_server


@pytest.mark.asyncio
async def test_sc6_subagent_viewport_isolation(tmp_path: Path) -> None:
    """Orchestrator (C1) + sub-agent (C2) — concurrent connections. Observes
    whether C2 sees C1's open viewports.

    Models real MCP flow: C1 = orchestrator, C2 = clean-room sub-agent.
    """

    (tmp_path / "test.txt").write_text("hello world\nline 2\nline 3\n")

    server = create_server(str(tmp_path))

    @server.tool()
    def probe_sid(ctx: Context, label: str) -> str:
        return f"{label}: {ctx.session_id}"

    async with Client(transport=server) as c1, Client(transport=server) as c2:
        # C1: open a viewport
        r_open = await c1.call_tool(
            "viewport",
            arguments={"action": "open", "file_path": "test.txt"},
        )
        r_probe1 = await c1.call_tool("probe_sid", arguments={"label": "C1"})

        # C2: while C1 is STILL ACTIVE, check if C2 sees C1's viewport
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
    c2_list_texts = [item.text for item in r_list.content]

    print()
    print("=== SC-6: Sub-agent Viewport Isolation ===")
    print(f"  C1 open result: {c1_open_text}")
    print(f"  C1 session ID:  {c1_sid}")
    print(f"  C2 session ID:  {c2_sid}")
    print(f"  Sessions are:   {same_diff}")
    print(f"  Forwarding needed: {forwarding_needed}")
    print("  C2 viewport list output:")
    for t in c2_list_texts:
        print(f"    {t}")
    print("=== End SC-6 ===")
