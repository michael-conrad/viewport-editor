# SPDX-FileCopyrightText: 2026 Michael Conrad
# SPDX-License-Identifier: MIT
# Provenance: AI-generated
"""Shared test fixtures for viewport-editor.

Co-authored with AI: OpenCode (deepseek-v4-flash)
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, AsyncIterator

import pytest
from fastmcp import Client
from fastmcp.exceptions import ToolError


from viewport_editor.server import create_server


class _CompatResult:
    """Backward-compatible call_tool result with .isError and .content.

    Mimics the old mcp.types.CallToolResult for tests that check error states.
    """

    def __init__(self, text: str, is_error: bool = False) -> None:
        self.isError = is_error
        self.content = [
            type(
                "TextContent", (), {"type": "text", "text": text, "annotations": None}
            )()
        ]

    def __repr__(self) -> str:
        return f"CompatResult(isError={self.isError}, text={self.content[0].text[:60]})"


class _CompatClient:
    """Wraps a fastmcp.Client to provide backward-compatible call_tool results
    with .isError (camelCase), matching mcp.types.CallToolResult.

    Fastmcp raises ToolError on tool exceptions — we catch and convert
    to the old result-with-isError pattern.
    """

    def __init__(self, client: Client) -> None:
        self._client = client

    def __getattr__(self, name: str) -> Any:
        return getattr(self._client, name)

    async def call_tool(
        self, name: str, arguments: dict[str, Any] | None = None, **kwargs: Any
    ) -> Any:
        try:
            result = await self._client.call_tool(name, arguments=arguments, **kwargs)
            result.isError = result.is_error
            return result
        except ToolError as exc:
            msg = str(exc)
            # Strip "Error calling tool 'X':" prefix if present
            if ": " in msg:
                msg = msg.split(": ", 1)[-1].strip()
            # Prepend "error:" to match old SDK error response format
            return _CompatResult(text=f"error: {msg}", is_error=True)

    async def list_tools(self) -> Any:
        tools = await self._client.list_tools()
        return _ListToolsResult(tools=tools)


class _ListToolsResult:
    """Wraps a list of Tool into an object with .tools attribute,
    matching the old MCP SDK's ListToolsResult protocol."""

    def __init__(self, tools: list[Any]) -> None:
        self.tools = tools


@pytest.fixture(scope="module")
def _server(test_project_root: Path) -> Any:
    """Module-scoped server so session state persists across test functions."""
    return create_server(str(test_project_root))


@pytest.fixture
async def client_session(
    _server: Any,
) -> AsyncIterator[_CompatClient]:
    """Create an in-memory MCP client connected to a module-scoped server.

    The _server is module-scoped so session state persists across test
    functions (matching the old stdio-subprocess behavior where one server
    process ran for the whole module).
    """
    async with Client(transport=_server) as client:
        yield _CompatClient(client)


@pytest.fixture
async def search_client(
    _server: Any,
) -> AsyncIterator[_CompatClient]:
    """Alias for client_session used by test_p4_search_find.py."""
    async with Client(transport=_server) as client:
        yield _CompatClient(client)


@pytest.fixture
async def regex_client(
    _server: Any,
) -> AsyncIterator[_CompatClient]:
    """Alias for client_session used by test_p4_regex_tools.py."""
    async with Client(transport=_server) as client:
        yield _CompatClient(client)
