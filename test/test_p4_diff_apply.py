# SPDX-FileCopyrightText: 2026 Michael Conrad
# SPDX-License-Identifier: MIT
# Provenance: AI-generated
"""Phase 4 RED behavioral tests for diff:apply of viewport-editor MCP server.

SC-23: diff:apply stages diff into buffer; auto-loads file if not open.

These tests assert GREEN-phase behavior and MUST FAIL against current code
because diff:apply action does not exist in the diff tool handler.

Co-authored with AI: OpenCode (ollama-cloud/glm-5.1)
"""

from __future__ import annotations

import tempfile
import uuid
from pathlib import Path
from typing import Any

import pytest


@pytest.fixture(scope="module")
def test_project_root() -> Path:
    tmpdir = Path(tempfile.mkdtemp(prefix="ve-p4-diff-apply-test-"))
    (tmpdir / "diff_target.txt").write_text("alpha\nbeta\ngamma\ndelta\nepsilon\n")
    (tmpdir / "fuzzy_target.txt").write_text(
        "  indented line\nplain line\n  another indented\n"
    )
    (tmpdir / "autolaod_target.txt").write_text("auto line one\nauto line two\n")
    return tmpdir


def _get_text(result: Any) -> str:
    parts: list[str] = []
    if result.content:
        for item in result.content:
            if hasattr(item, "text") and item.text:
                parts.append(item.text)
    return "\n".join(parts)


def _extract_vpid(text: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("viewport_id:"):
            return stripped.split(":", 1)[1].strip()
    return ""


@pytest.mark.phase4
async def test_diff_apply_stages_into_buffer(client_session: Any) -> None:
    """SC-23: diff:apply stages diff into buffer and returns diff summary."""
    sid = f"test-apply-stage-{uuid.uuid4().hex[:8]}"
    result = await client_session.call_tool(
        "viewport",
        {
            "action": "open",
            "session_id": sid,
            "file_path": "diff_target.txt",
        },
    )
    vpid = _extract_vpid(_get_text(result))

    patch = "--- a/diff_target.txt\n+++ b/diff_target.txt\n@@ -1,5 +1,5 @@\n alpha\n-beta\n+bravo\n gamma\n delta\n epsilon\n"

    result = await client_session.call_tool(
        "diff",
        {
            "action": "apply",
            "session_id": sid,
            "viewport_id": vpid,
            "patch": patch,
        },
    )
    text = _get_text(result)
    assert "error" not in text.lower() or "applied" in text.lower(), (
        f"diff:apply should succeed, got: {text}"
    )

    result = await client_session.call_tool(
        "diff",
        {
            "action": "show",
            "session_id": sid,
            "viewport_id": vpid,
        },
    )
    diff_text = _get_text(result)
    assert "-beta" in diff_text, (
        f"diff:show must show removed line -beta, got: {diff_text}"
    )
    assert "+bravo" in diff_text, (
        f"diff:show must show added line +bravo, got: {diff_text}"
    )


@pytest.mark.phase4
async def test_diff_apply_auto_loads_unopened(client_session: Any) -> None:
    """SC-23: diff:apply auto-loads file if not in any viewport."""
    sid = f"test-apply-autoload-{uuid.uuid4().hex[:8]}"

    patch = "--- a/autolaod_target.txt\n+++ b/autolaod_target.txt\n@@ -1,2 +1,2 @@\n-auto line one\n+auto line ONE\n auto line two\n"

    result = await client_session.call_tool(
        "diff",
        {
            "action": "apply",
            "session_id": sid,
            "file_path": "autolaod_target.txt",
            "patch": patch,
        },
    )
    text = _get_text(result)
    assert "error" not in text.lower() or "applied" in text.lower(), (
        f"diff:apply should auto-load and succeed, got: {text}"
    )

    diff_text = _get_text(
        await client_session.call_tool(
            "viewport",
            {
                "action": "list",
                "session_id": sid,
            },
        )
    )
    assert "autolaod_target.txt" in diff_text, (
        f"file should be open after auto-load, viewports: {diff_text}"
    )


@pytest.mark.phase4
async def test_diff_apply_fuzzy_context_matching(client_session: Any) -> None:
    """SC-23: diff:apply applies with modified context lines (fuzzy matching)."""
    sid = f"test-apply-fuzzy-{uuid.uuid4().hex[:8]}"
    result = await client_session.call_tool(
        "viewport",
        {
            "action": "open",
            "session_id": sid,
            "file_path": "fuzzy_target.txt",
        },
    )
    vpid = _extract_vpid(_get_text(result))

    # Diff context lines have extra leading whitespace stripped vs file content
    # File has "  indented line" but diff context says "indented line"
    patch = (
        "--- a/fuzzy_target.txt\n"
        "+++ b/fuzzy_target.txt\n"
        "@@ -1,4 +1,4 @@\n"
        " indented line\n"
        "-plain line\n"
        "+modified line\n"
        " another indented\n"
    )

    result = await client_session.call_tool(
        "diff",
        {
            "action": "apply",
            "session_id": sid,
            "viewport_id": vpid,
            "patch": patch,
        },
    )
    text = _get_text(result)
    assert "error" not in text.lower() or "applied" in text.lower(), (
        f"diff:apply with fuzzy context should succeed, got: {text}"
    )

    diff_text = _get_text(
        await client_session.call_tool(
            "diff",
            {
                "action": "show",
                "session_id": sid,
                "viewport_id": vpid,
            },
        )
    )
    assert "-plain line" in diff_text, (
        f"diff:show must show removed 'plain line', got: {diff_text}"
    )
    assert "+modified line" in diff_text, (
        f"diff:show must show added 'modified line', got: {diff_text}"
    )


@pytest.mark.phase4
async def test_diff_apply_no_match_rejects(client_session: Any) -> None:
    """SC-23: diff:apply returns isError when context doesn't match anywhere."""
    sid = f"test-apply-nomatch-{uuid.uuid4().hex[:8]}"
    result = await client_session.call_tool(
        "viewport",
        {
            "action": "open",
            "session_id": sid,
            "file_path": "diff_target.txt",
        },
    )
    vpid = _extract_vpid(_get_text(result))

    # Context line "THIS_LINE_DOES_NOT_EXIST" won't match any line in file
    patch = (
        "--- a/diff_target.txt\n"
        "+++ b/diff_target.txt\n"
        "@@ -1,5 +1,5 @@\n"
        " THIS_LINE_DOES_NOT_EXIST\n"
        "-beta\n"
        "+bravo\n"
    )

    result = await client_session.call_tool(
        "diff",
        {
            "action": "apply",
            "session_id": sid,
            "viewport_id": vpid,
            "patch": patch,
        },
    )
    text = _get_text(result)
    assert result.isError, (
        f"diff:apply with unmatchable context must return isError=true, got: {text}"
    )
    assert "context" in text.lower() or "match" in text.lower(), (
        f"diff:apply error should mention context match failure, got: {text}"
    )


@pytest.mark.phase4
async def test_diff_apply_autosave_gate(client_session: Any) -> None:
    """SC-23: diff:apply triggers autosave gate — switches to buffered mode."""
    sid = f"test-apply-autosavegate-{uuid.uuid4().hex[:8]}"
    result = await client_session.call_tool(
        "viewport",
        {
            "action": "open",
            "session_id": sid,
            "file_path": "diff_target.txt",
            "autosave": True,
        },
    )
    vpid = _extract_vpid(_get_text(result))

    patch = "--- a/diff_target.txt\n+++ b/diff_target.txt\n@@ -1,5 +1,5 @@\n alpha\n-beta\n+bravo\n gamma\n delta\n epsilon\n"

    result = await client_session.call_tool(
        "diff",
        {
            "action": "apply",
            "session_id": sid,
            "viewport_id": vpid,
            "patch": patch,
        },
    )
    text = _get_text(result)
    assert (
        "autosave gate" in text.lower()
        or "buffered mode" in text.lower()
        or "applied" in text.lower()
    ), f"diff:apply on autosave=on viewport should trigger autosave gate, got: {text}"
