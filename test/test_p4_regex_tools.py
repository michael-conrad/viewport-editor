# SPDX-FileCopyrightText: 2026 Michael Conrad
# SPDX-License-Identifier: MIT
# Provenance: AI-generated
"""Phase 4 RED behavioral tests for regex:test and regex:escape (SC-28, SC-29).

These tests assert GREEN-phase behavior and MUST FAIL against current code
because the regex tool only returns "regex tool: not yet implemented".

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
def regex_project_root() -> Path:
    tmpdir = Path(tempfile.mkdtemp(prefix="ve-regex-test-"))
    (tmpdir / "sample.txt").write_text(
        "hello world\nfoo bar baz\n123-456-7890\nemail@test.com\n"
        "special [chars] here\ndollar $ign\n"
    )
    return tmpdir


@pytest.fixture(scope="module")
def regex_server_params(regex_project_root: Path) -> StdioServerParameters:
    return StdioServerParameters(
        command="uv",
        args=[
            "run",
            "python",
            "-m",
            "viewport_editor",
            "--project-root",
            str(regex_project_root),
        ],
    )


@pytest.fixture
async def regex_client(
    regex_server_params: StdioServerParameters,
) -> AsyncIterator[ClientSession]:
    try:
        async with stdio_client(regex_server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                yield session
    except RuntimeError as exc:
        msg = str(exc)
        if "Attempted to exit cancel scope in a different task" not in msg:
            raise


def _get_text(result: CallToolResult) -> str:
    parts: list[str] = []
    if result.content:
        for item in result.content:
            if hasattr(item, "text") and item.text:
                parts.append(item.text)
    return "\n".join(parts)


# --- SC-28: regex:test action ---


@pytest.mark.phase4
@pytest.mark.asyncio
async def test_regex_test_valid_pattern_returns_match_positions(
    regex_client: ClientSession,
) -> None:
    """SC-28: regex:test with valid pattern returns match positions (start/end offsets)."""
    result = await regex_client.call_tool(
        "regex",
        arguments={
            "action": "test",
            "pattern": r"\d{3}-\d{3}-\d{4}",
            "text": "123-456-7890",
        },
    )
    text = _get_text(result)
    assert not result.isError, f"regex:test valid pattern returned error: {text[:200]}"
    assert "123-456-7890" in text, (
        f"regex:test must include matched text in output, got: {text[:300]}"
    )
    assert "0:" in text or "start" in text.lower() or "match" in text.lower(), (
        f"regex:test must include match position/offset, got: {text[:300]}"
    )


@pytest.mark.phase4
@pytest.mark.asyncio
async def test_regex_test_invalid_pattern_returns_error(
    regex_client: ClientSession,
) -> None:
    """SC-28: regex:test with invalid pattern returns isError=true."""
    result = await regex_client.call_tool(
        "regex",
        arguments={
            "action": "test",
            "pattern": r"[invalid(",
            "text": "some text",
        },
    )
    assert result.isError, (
        f"regex:test with invalid pattern must return isError=true, got: {_get_text(result)[:200]}"
    )


@pytest.mark.phase4
@pytest.mark.asyncio
async def test_regex_test_no_match_returns_empty(
    regex_client: ClientSession,
) -> None:
    """SC-28: regex:test with no-match pattern returns empty results."""
    result = await regex_client.call_tool(
        "regex",
        arguments={
            "action": "test",
            "pattern": r"ZZZnonexistent",
            "text": "hello world",
        },
    )
    text = _get_text(result)
    assert not result.isError, f"regex:test no-match returned error: {text[:200]}"
    assert "0" in text and ("match" in text.lower() or "result" in text.lower()), (
        f"regex:test no-match must report 0 matches, got: {text[:300]}"
    )


@pytest.mark.phase4
@pytest.mark.asyncio
async def test_regex_test_capture_groups_returned(
    regex_client: ClientSession,
) -> None:
    """SC-28: regex:test returns capture groups from pattern."""
    result = await regex_client.call_tool(
        "regex",
        arguments={
            "action": "test",
            "pattern": r"(\w+)@(\w+)\.(\w+)",
            "text": "email@test.com",
        },
    )
    text = _get_text(result)
    assert not result.isError, f"regex:test capture groups returned error: {text[:200]}"
    assert "email" in text, (
        f"regex:test must include group match 'email', got: {text[:300]}"
    )
    assert "test" in text, (
        f"regex:test must include group match 'test', got: {text[:300]}"
    )
    assert "com" in text, (
        f"regex:test must include group match 'com', got: {text[:300]}"
    )


# --- SC-29: regex:escape action ---


@pytest.mark.phase4
@pytest.mark.asyncio
async def test_regex_escape_all_metacharacters(
    regex_client: ClientSession,
) -> None:
    """SC-29: regex:escape escapes all 12 regex metacharacters: . ^ $ * + ? { } [ ] \\ |."""
    result = await regex_client.call_tool(
        "regex",
        arguments={
            "action": "escape",
            "text": r".^$*+?{}[]\|",
        },
    )
    text = _get_text(result)
    assert not result.isError, (
        f"regex:escape metacharacters returned error: {text[:200]}"
    )
    assert r"\." in text, f"regex:escape must escape '.', got: {text[:300]}"
    assert r"\^" in text, f"regex:escape must escape '^', got: {text[:300]}"
    assert r"\$" in text, f"regex:escape must escape '$', got: {text[:300]}"
    assert r"\*" in text, f"regex:escape must escape '*', got: {text[:300]}"
    assert r"\+" in text, f"regex:escape must escape '+', got: {text[:300]}"
    assert r"\?" in text, f"regex:escape must escape '?', got: {text[:300]}"
    assert r"\{" in text, f"regex:escape must escape '{{', got: {text[:300]}"
    assert r"\}" in text, f"regex:escape must escape '}}', got: {text[:300]}"
    assert r"\[" in text, f"regex:escape must escape '[', got: {text[:300]}"
    assert r"\]" in text, f"regex:escape must escape ']', got: {text[:300]}"
    assert "\\\\" in text, f"regex:escape must escape backslash, got: {text[:300]}"
    assert r"\|" in text, f"regex:escape must escape '|', got: {text[:300]}"


@pytest.mark.phase4
@pytest.mark.asyncio
async def test_regex_escape_plain_text_unchanged(
    regex_client: ClientSession,
) -> None:
    """SC-29: regex:escape leaves plain text unchanged."""
    result = await regex_client.call_tool(
        "regex",
        arguments={
            "action": "escape",
            "text": "hello world 123",
        },
    )
    text = _get_text(result)
    assert not result.isError, f"regex:escape plain text returned error: {text[:200]}"
    assert "hello world 123" in text, (
        f"regex:escape must return plain text unchanged, got: {text[:300]}"
    )
