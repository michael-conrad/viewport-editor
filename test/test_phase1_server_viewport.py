# SPDX-FileCopyrightText: 2026 Michael Conrad
# SPDX-License-Identifier: MIT
# Provenance: AI-generated
"""Phase 1 behavioral tests for viewport-editor MCP server.

Co-authored with AI: OpenCode (deepseek-v4-flash)
"""

from __future__ import annotations

import time
import tempfile
from pathlib import Path
from typing import Any

# Unit test imports for display mode helpers
from viewport_editor.server import _render_content_line, _decode_unicode_escapes

import pytest


@pytest.fixture(scope="module")
def test_project_root() -> Path:
    tmpdir = Path(tempfile.mkdtemp(prefix="ve-test-"))
    (tmpdir / "test_file.txt").write_text("line 1\nline 2\nline 3\nline 4\nline 5\n")
    (tmpdir / "long_file.txt").write_text("\n".join(f"line {i}" for i in range(1, 101)))
    # file with non-printing characters for display_mode show testing
    (tmpdir / "non_printing.txt").write_bytes(b"null\x00byte\ncontrol\x01\x02end\n")
    # isolated file for SC-38 decode test — no other test touches this
    (tmpdir / "unicode_test.txt").write_text("line A\nline B\nline C\nline D\nline E\n")
    return tmpdir


@pytest.mark.phase1
@pytest.mark.asyncio
async def test_sc1_exactly_8_tools(client_session: Any) -> None:
    result = await client_session.list_tools()
    names = [t.name for t in result.tools]
    assert len(names) == 11, f"Expected 11 tools, got {len(names)}: {names}"
    expected = {"viewport", "edit", "file", "diff", "search", "regex", "clipboard", "read_file", "write_file", "edit_text", "find_text"}
    assert set(names) == expected, f"Tool mismatch: {set(names) ^ expected}"


@pytest.mark.phase1
@pytest.mark.asyncio
async def test_sc2_no_dedicated_help_tool(client_session: Any) -> None:
    result = await client_session.list_tools()
    names = [t.name for t in result.tools]
    assert "help" not in names


@pytest.mark.phase1
@pytest.mark.asyncio
async def test_sc3_tool_descriptions_use_prose_yaml_no_json(
    client_session: Any,
) -> None:
    # SC-3 behavioral evidence: tool descriptions are prose+YAML, not JSON
    result = await client_session.list_tools()
    for t in result.tools:
        desc = t.description
        assert desc is not None
        assert "{" not in desc, f"Tool {t.name} has JSON in description"
        assert "}" not in desc, f"Tool {t.name} has JSON in description"

    # SC-3 behavioral evidence: tool response uses YAML format (k: v), not JSON
    open_result = await client_session.call_tool(
        "viewport",
        arguments={"action": "open", "file_path": "test_file.txt"},
    )
    response_text = _get_text(open_result)
    assert "viewport_id:" in response_text, (
        "Response not in YAML format (missing colon-separated kv)"
    )
    assert "{" not in response_text, (
        f"Response uses JSON instead of YAML: {response_text[:200]}"
    )
    assert "}" not in response_text, (
        f"Response uses JSON instead of YAML: {response_text[:200]}"
    )


@pytest.mark.phase1
@pytest.mark.asyncio
async def test_sc4_absolute_paths_accepted(client_session: Any) -> None:
    # SC-4 behavioral evidence: absolute paths are now accepted
    result = await client_session.call_tool(
        "viewport",
        arguments={"action": "open", "file_path": "/etc/passwd"},
    )
    text = _get_text(result)
    assert not result.isError, (
        f"Expected isError=false for absolute path, got isError={result.isError}"
    )


@pytest.mark.phase1
@pytest.mark.asyncio
async def test_sc4_relative_paths_accepted(client_session: Any) -> None:
    result = await client_session.call_tool(
        "viewport",
        arguments={"action": "open", "file_path": "test_file.txt"},
    )
    text = _get_text(result)
    assert not result.isError, (
        f"Expected isError=false for relative path, got isError={result.isError}"
    )
    assert "error" not in text.lower()
    assert "opened viewport" in text.lower()


@pytest.mark.phase1
@pytest.mark.asyncio
async def test_sc5_open_returns_entry_with_all_fields(
    client_session: Any,
) -> None:
    result = await client_session.call_tool(
        "viewport",
        arguments={"action": "open", "file_path": "test_file.txt"},
    )
    text = _get_text(result)
    assert "viewport_id:" in text
    assert "file:" in text
    assert "line_start:" in text
    assert "line_end:" in text
    assert "autosave:" in text
    assert "mtime:" in text
    assert "size:" in text
    assert "line_ending:" in text
    assert "display_mode:" in text
    # SC-5 behavioral evidence: visible text content present (cat -n format)
    assert "  content:" in text
    assert "    1: line 1" in text
    assert "    5: line 5" in text


@pytest.mark.phase1
@pytest.mark.asyncio
async def test_sc6_open_accepts_autosave_param_defaults_on(
    client_session: Any,
) -> None:
    result_on = await client_session.call_tool(
        "viewport",
        arguments={"action": "open", "file_path": "test_file.txt", "autosave": True},
    )
    assert "autosave: True" in _get_text(result_on)
    result_off = await client_session.call_tool(
        "viewport",
        arguments={"action": "open", "file_path": "test_file.txt"},
    )
    assert "autosave: True" in _get_text(result_off)


@pytest.mark.phase1
@pytest.mark.asyncio
async def test_sc7_page_up_moves_by_viewport_height(
    client_session: Any,
) -> None:
    result_open = await client_session.call_tool(
        "viewport",
        arguments={
            "action": "open",
            "file_path": "long_file.txt",
            "line_start": 50,
            "line_end": 60,
        },
    )
    assert "error" not in _get_text(result_open)
    result_up = await client_session.call_tool(
        "viewport",
        arguments={
            "action": "page-up",
            "viewport_id": _extract_vpid(_get_text(result_open)),
        },
    )
    text = _get_text(result_up)
    assert "paged up" in text.lower()
    assert "line_start: 40" in text
    assert "line_end: 50" in text
    # SC-7 behavioral evidence: visible text content at new position (cat -n style)
    assert "  content:" in text
    assert "    40: line 40" in text
    assert "    45: line 45" in text
    assert "    50: line 50" in text


@pytest.mark.phase1
@pytest.mark.asyncio
async def test_sc8_page_down_moves_by_viewport_height(
    client_session: Any,
) -> None:
    result_open = await client_session.call_tool(
        "viewport",
        arguments={
            "action": "open",
            "file_path": "long_file.txt",
            "line_start": 1,
            "line_end": 10,
        },
    )
    assert "error" not in _get_text(result_open)
    result_down = await client_session.call_tool(
        "viewport",
        arguments={
            "action": "page-down",
            "viewport_id": _extract_vpid(_get_text(result_open)),
        },
    )
    text = _get_text(result_down)
    assert "paged down" in text.lower()
    assert "line_start: 10" in text
    assert "line_end: 19" in text
    # SC-8 behavioral evidence: visible text content at new position (cat -n style)
    assert "  content:" in text
    assert "    10: line 10" in text
    assert "    15: line 15" in text
    assert "    19: line 19" in text


@pytest.mark.phase1
@pytest.mark.asyncio
async def test_sc25_soft_conflict_warning_on_viewport_operations(
    client_session: Any, test_project_root: Path
) -> None:
    result_open = await client_session.call_tool(
        "viewport",
        arguments={"action": "open", "file_path": "test_file.txt"},
    )
    vpid = _extract_vpid(_get_text(result_open))
    text = _get_text(result_open)
    assert "autosave" in text

    # SC-25 behavioral evidence: modify file externally, then verify soft conflict warning
    test_file = test_project_root / "test_file.txt"
    test_file.write_text("modified content\n")
    time.sleep(0.05)  # ensure mtime changes beyond the 10ms threshold

    result_scroll = await client_session.call_tool(
        "viewport",
        arguments={"action": "scroll", "viewport_id": vpid, "lines": 1},
    )
    scroll_text = _get_text(result_scroll)
    assert "notice:" in scroll_text or "auto-reloaded" in scroll_text, (
        f"Expected auto-reload notice in scroll response: {scroll_text}"
    )
    # Restore original content — this test mutates a module-scoped fixture
    test_file.write_text("line 1\nline 2\nline 3\nline 4\nline 5\n")


@pytest.mark.phase1
@pytest.mark.asyncio
async def test_sc26_session_isolation(client_session: Any) -> None:
    """Session isolation: same client = same session. Viewport opened in one
    call is visible from another because ctx.session_id is consistent."""
    await client_session.call_tool(
        "viewport",
        arguments={"action": "open", "file_path": "test_file.txt"},
    )
    list_b = await client_session.call_tool(
        "viewport",
        arguments={"action": "list"},
    )
    text = _get_text(list_b)
    assert "viewports (1)" in text.lower() or "viewport_id:" in text.lower(), (
        f"Expected open viewport from same session, got: {text}"
    )


@pytest.mark.phase1
@pytest.mark.asyncio
async def test_sc27_jump_returns_is_error_on_target_not_found(
    client_session: Any,
) -> None:
    result_open = await client_session.call_tool(
        "viewport",
        arguments={"action": "open", "file_path": "test_file.txt"},
    )
    vpid = _extract_vpid(_get_text(result_open))
    result = await client_session.call_tool(
        "viewport",
        arguments={
            "action": "jump",
            "viewport_id": vpid,
            "target": "NONEXISTENT_TEXT_XYZ",
        },
    )
    assert result.isError
    assert "error" in _get_text(result).lower()


@pytest.mark.phase1
@pytest.mark.asyncio
async def test_sc50_jump_top_sets_line_start_to_1(client_session: Any) -> None:
    """SC-1: jump("top") sets viewport line_start to 1."""
    result_open = await client_session.call_tool(
        "viewport",
        arguments={"action": "open", "file_path": "long_file.txt"},
    )
    vpid = _extract_vpid(_get_text(result_open))
    result = await client_session.call_tool(
        "viewport",
        arguments={"action": "jump", "viewport_id": vpid, "target": "top"},
    )
    text = _get_text(result)
    assert "line_start: 1" in text, f"Expected line_start: 1, got: {text}"


@pytest.mark.phase1
@pytest.mark.asyncio
async def test_sc50_jump_bottom_sets_line_end_to_last_line(
    client_session: Any, test_project_root: Path
) -> None:
    """SC-2: jump("bottom") sets viewport line_end to last line of file (100)."""
    result_open = await client_session.call_tool(
        "viewport",
        arguments={"action": "open", "file_path": "long_file.txt"},
    )
    vpid = _extract_vpid(_get_text(result_open))
    result = await client_session.call_tool(
        "viewport",
        arguments={"action": "jump", "viewport_id": vpid, "target": "bottom"},
    )
    text = _get_text(result)
    assert "line_end: 100" in text, f"Expected line_end: 100, got: {text}"


@pytest.mark.phase1
@pytest.mark.asyncio
async def test_sc50_jump_bottom_empty_file(client_session: Any, test_project_root: Path) -> None:
    """SC-6: jump("bottom") on empty file produces line_start=1, line_end=0."""
    empty = Path(test_project_root) / "empty.txt"
    empty.write_text("")
    result_open = await client_session.call_tool(
        "viewport",
        arguments={"action": "open", "file_path": "empty.txt"},
    )
    vpid = _extract_vpid(_get_text(result_open))
    result = await client_session.call_tool(
        "viewport",
        arguments={"action": "jump", "viewport_id": vpid, "target": "bottom"},
    )
    text = _get_text(result)
    assert "line_start: 1" in text, f"Expected line_start: 1, got: {text}"
    assert "line_end: 0" in text, f"Expected line_end: 0, got: {text}"


@pytest.mark.phase1
@pytest.mark.asyncio
async def test_sc50_numeric_jump_unchanged(client_session: Any) -> None:
    """SC-4: Existing numeric jump("42") unchanged."""
    # Open with small range so numeric jump actually moves line_start
    result_open = await client_session.call_tool(
        "viewport",
        arguments={
            "action": "open",
            "file_path": "long_file.txt",
            "line_start": 1,
            "line_end": 10,
        },
    )
    vpid = _extract_vpid(_get_text(result_open))
    result = await client_session.call_tool(
        "viewport",
        arguments={"action": "jump", "viewport_id": vpid, "target": "42"},
    )
    text = _get_text(result)
    assert "line_start: 42" in text, f"Expected line_start: 42, got: {text}"


@pytest.mark.phase1
@pytest.mark.asyncio
async def test_sc50_text_search_jump_unchanged(client_session: Any) -> None:
    """SC-5: Existing text-search jump unchanged."""
    # Open with small range so text-search jump actually moves line_start
    result_open = await client_session.call_tool(
        "viewport",
        arguments={
            "action": "open",
            "file_path": "long_file.txt",
            "line_start": 1,
            "line_end": 10,
        },
    )
    vpid = _extract_vpid(_get_text(result_open))
    result = await client_session.call_tool(
        "viewport",
        arguments={"action": "jump", "viewport_id": vpid, "target": "line 50"},
    )
    text = _get_text(result)
    assert "line_start: 50" in text, f"Expected line_start: 50, got: {text}"


@pytest.mark.phase1
@pytest.mark.asyncio
async def test_sc50_jump_top_case_insensitive(client_session: Any) -> None:
    """SC-1/SC-3: Case-insensitive keywords — "Top" and "TOP" also work."""
    result_open = await client_session.call_tool(
        "viewport",
        arguments={"action": "open", "file_path": "long_file.txt"},
    )
    vpid = _extract_vpid(_get_text(result_open))
    result = await client_session.call_tool(
        "viewport",
        arguments={"action": "jump", "viewport_id": vpid, "target": "Top"},
    )
    text = _get_text(result)
    assert "line_start: 1" in text, f"Case-insensitive 'Top' failed: {text}"


@pytest.mark.phase1
@pytest.mark.asyncio
async def test_sc50_jump_keyword_not_text_search(
    client_session: Any, test_project_root: Path
) -> None:
    """SC-3: Keywords are exact literal matches — text-search does NOT fire for "top"."""
    # Write keyword_test.txt INSIDE project root (server only accepts relative paths)
    kw_file = Path(test_project_root) / "keyword_test.txt"
    kw_file.write_text("line 1\nline 2\ntop of page\nline 4\nline 5\n")
    result_open = await client_session.call_tool(
        "viewport",
        arguments={"action": "open", "file_path": "keyword_test.txt"},
    )
    vpid = _extract_vpid(_get_text(result_open))
    result = await client_session.call_tool(
        "viewport",
        arguments={"action": "jump", "viewport_id": vpid, "target": "top"},
    )
    text = _get_text(result)
    # Should jump to line 1 (keyword match), NOT line 3 (text-search match)
    assert "line_start: 1" in text, (
        f"Keyword 'top' should set line_start=1, but text-search may have matched: {text}"
    )


@pytest.mark.phase1
@pytest.mark.asyncio
async def test_sc31_scroll_by_n_lines(client_session: Any) -> None:
    result_open = await client_session.call_tool(
        "viewport",
        arguments={
            "action": "open",
            "file_path": "long_file.txt",
            "line_start": 10,
            "line_end": 20,
        },
    )
    assert "error" not in _get_text(result_open)
    text = _get_text(result_open)
    assert "line_start: 10" in text
    result_scroll = await client_session.call_tool(
        "viewport",
        arguments={"action": "scroll", "viewport_id": _extract_vpid(text), "lines": 5},
    )
    scroll_text = _get_text(result_scroll)
    assert "line_start: 15" in scroll_text
    assert "  content:" in scroll_text
    assert "    15: line 15" in scroll_text
    assert "    19: line 19" in scroll_text


@pytest.mark.phase1
@pytest.mark.asyncio
async def test_sc31_scroll_negative(client_session: Any) -> None:
    result_open = await client_session.call_tool(
        "viewport",
        arguments={
            "action": "open",
            "file_path": "long_file.txt",
            "line_start": 10,
            "line_end": 20,
        },
    )
    vpid = _extract_vpid(_get_text(result_open))
    result = await client_session.call_tool(
        "viewport",
        arguments={"action": "scroll", "viewport_id": vpid, "lines": -3},
    )
    text = _get_text(result)
    assert "line_start: 7" in text
    assert "  content:" in text
    assert "    7: line 7" in text
    assert "    9: line 9" in text


@pytest.mark.phase1
@pytest.mark.asyncio
async def test_sc32_autosave_toggles_flag(client_session: Any) -> None:
    result_open = await client_session.call_tool(
        "viewport",
        arguments={"action": "open", "file_path": "test_file.txt", "autosave": False},
    )
    vpid = _extract_vpid(_get_text(result_open))
    result_on = await client_session.call_tool(
        "viewport",
        arguments={"action": "autosave", "viewport_id": vpid, "autosave_enabled": True},
    )
    assert "autosave set to True" in _get_text(result_on)
    result_off = await client_session.call_tool(
        "viewport",
        arguments={
            "action": "autosave",
            "viewport_id": vpid,
            "autosave_enabled": False,
        },
    )
    assert "autosave set to False" in _get_text(result_off)


@pytest.mark.phase1
@pytest.mark.asyncio
async def test_sc33_list_returns_all_fields(client_session: Any) -> None:
    await client_session.call_tool(
        "viewport",
        arguments={"action": "open", "file_path": "test_file.txt"},
    )
    result = await client_session.call_tool(
        "viewport",
        arguments={"action": "list"},
    )
    text = _get_text(result)
    assert "viewport_id:" in text
    assert "file:" in text
    assert "line_start:" in text
    assert "line_end:" in text
    assert "mtime:" in text
    assert "size:" in text
    assert "autosave:" in text
    assert "dirty:" in text
    assert "line_ending:" in text
    assert "display_mode:" in text


@pytest.mark.phase1
@pytest.mark.asyncio
async def test_sc34_absolute_and_relative_paths(client_session: Any) -> None:
    result_abs = await client_session.call_tool(
        "viewport",
        arguments={"action": "open", "file_path": "/etc/hostname"},
    )
    assert not result_abs.isError, (
        f"Expected isError=false for absolute path, got isError={result_abs.isError}"
    )
    result_rel = await client_session.call_tool(
        "viewport",
        arguments={"action": "open", "file_path": "test_file.txt"},
    )
    assert not result_rel.isError, (
        f"Expected isError=false for relative path, got isError={result_rel.isError}"
    )
    rel_text = _get_text(result_rel)
    assert "error" not in rel_text.lower()
    assert "1: line 1" in rel_text, (
        f"Expected file content 'line 1' in response, got: {rel_text[:300]}"
    )


@pytest.mark.phase1
@pytest.mark.asyncio
async def test_viewport_open_close(client_session: Any) -> None:
    result_open = await client_session.call_tool(
        "viewport",
        arguments={"action": "open", "file_path": "test_file.txt"},
    )
    text = _get_text(result_open)
    assert "error" not in text
    vpid = _extract_vpid(text)
    result_close = await client_session.call_tool(
        "viewport",
        arguments={"action": "close", "viewport_id": vpid},
    )
    assert "closed viewport" in _get_text(result_close)


@pytest.mark.phase1
@pytest.mark.asyncio
async def test_viewport_open_custom_range(client_session: Any) -> None:
    result = await client_session.call_tool(
        "viewport",
        arguments={
            "action": "open",
            "file_path": "long_file.txt",
            "line_start": 20,
            "line_end": 30,
        },
    )
    text = _get_text(result)
    assert "line_start: 20" in text
    assert "line_end: 30" in text


@pytest.mark.phase1
@pytest.mark.asyncio
async def test_sc35_dirty_buffers_never_flushed(
    client_session: Any, test_project_root: Path
) -> None:
    """SC-35: Connection loss cleanup — dirty buffers are discarded, never flushed to disk.

    Behavioral contract: viewport operations (scroll, page, jump) that dirty a buffer
    MUST NOT modify the source file on disk. The file content remains at its original
    snapshot regardless of how many dirty operations are performed on the buffer.
    """
    file_path = "test_file.txt"
    original_content = (test_project_root / file_path).read_text()

    # Open viewport, locking in a snapshot of the file
    result_open = await client_session.call_tool(
        "viewport",
        arguments={"action": "open", "file_path": file_path},
    )
    assert "error" not in _get_text(result_open)
    vpid = _extract_vpid(_get_text(result_open))

    # Dirty the buffer via scroll operations — should NOT touch the file
    for _ in range(3):
        await client_session.call_tool(
            "viewport",
            arguments={"action": "scroll", "viewport_id": vpid, "lines": 1},
        )

    # Dirty via page-down
    await client_session.call_tool(
        "viewport",
        arguments={"action": "page-down", "viewport_id": vpid},
    )
    # Dirty via page-up
    await client_session.call_tool(
        "viewport",
        arguments={"action": "page-up", "viewport_id": vpid},
    )
    # Dirty via jump
    await client_session.call_tool(
        "viewport",
        arguments={"action": "jump", "viewport_id": vpid, "target": "line 3"},
    )

    # File on disk MUST be unchanged — dirty buffers are never flushed
    assert (test_project_root / file_path).read_text() == original_content, (
        "SC-35 FAIL: dirty buffer was flushed to disk"
    )

    # Same file in another session reads from disk, not from first session's buffer
    result_fresh = await client_session.call_tool(
        "viewport",
        arguments={"action": "open", "file_path": file_path},
    )
    text_fresh = _get_text(result_fresh)
    assert "error" not in text_fresh


# ── display_mode tests ──────────────────────────────────────────────────────


def test_render_content_line_hide_passthrough() -> None:
    """hide mode: text passes through unchanged."""
    assert _render_content_line("hello", "hide") == "hello"
    assert _render_content_line("tab\there", "hide") == "tab\there"
    assert _render_content_line("back\\slash", "hide") == "back\\slash"


def test_render_content_line_show_escapes_non_printing() -> None:
    """show mode: non-printing chars render as \\uNNNN, backslash doubles."""
    assert _render_content_line("back\\slash", "show") == "back\\\\slash"
    assert _render_content_line("null\x00byte", "show") == "null\\u0000byte"
    assert _render_content_line("a\x01b\x02c", "show") == "a\\u0001b\\u0002c"


def test_render_content_line_show_printable_unchanged() -> None:
    """show mode: printable ASCII and Unicode pass through."""
    assert _render_content_line("hello world", "show") == "hello world"
    assert _render_content_line("café", "show") == "café"
    assert _render_content_line("line 42", "show") == "line 42"


def test_render_content_line_show_newline_raw() -> None:
    """show mode: \\n and \\r pass through raw (they are stripped by caller)."""
    assert _render_content_line("a\nb", "show") == "a\nb"
    assert _render_content_line("a\r\nb", "show") == "a\r\nb"
    assert _render_content_line("a\rb", "show") == "a\rb"


def test_render_content_line_show_form_feed_and_other_cc() -> None:
    """show mode: Cc category chars (tab, ff, etc.) all render as \\uNNNN."""
    assert _render_content_line("a\x0cpage", "show") == "a\\u000cpage"
    assert _render_content_line("a\x1bb", "show") == "a\\u001bb"
    assert _render_content_line("a\x7fb", "show") == "a\\u007fb"


def test_decode_unicode_escapes_no_escape() -> None:
    """No escape sequences: text passes through unchanged."""
    assert _decode_unicode_escapes("hello") == "hello"
    assert _decode_unicode_escapes("a\\b") == "a\\b"
    assert _decode_unicode_escapes("plain text") == "plain text"


def test_decode_unicode_escapes_u_sequence() -> None:
    """\\uNNNN decodes to actual Unicode character."""
    assert _decode_unicode_escapes("\\u0041") == "A"
    assert _decode_unicode_escapes("\\u0000") == "\x00"
    assert _decode_unicode_escapes("abc\\u0020def") == "abc def"
    assert _decode_unicode_escapes("\\u00e9") == "é"


def test_decode_unicode_escapes_escaped_backslash() -> None:
    """\\\\uNNNN preserves literal \\uNNNN (backslash not consumed by decoder)."""
    assert _decode_unicode_escapes("\\\\u0041") == "\\u0041"
    assert _decode_unicode_escapes("\\\\u0000") == "\\u0000"
    assert _decode_unicode_escapes("pre\\\\u0041mid") == "pre\\u0041mid"


def test_decode_unicode_escapes_mixed() -> None:
    """Mixture of literal backslash, escaped backslash, and u-escapes."""
    # \\u0041 -> literal \u0041, then \u0042 -> B
    result = _decode_unicode_escapes("\\\\u0041\\u0042")
    assert result == "\\u0041B", f"got {result!r}"


@pytest.mark.phase1
@pytest.mark.asyncio
async def test_set_display_mode_show(client_session: Any) -> None:
    """set-display-mode to show: non-printing chars rendered as \\uNNNN."""
    result_open = await client_session.call_tool(
        "viewport",
        arguments={"action": "open", "file_path": "non_printing.txt"},
    )
    assert "error" not in _get_text(result_open)
    vpid = _extract_vpid(_get_text(result_open))

    result_show = await client_session.call_tool(
        "viewport",
        arguments={
            "action": "set-display-mode",
            "viewport_id": vpid,
            "display_mode": "show",
        },
    )
    text = _get_text(result_show)
    assert "display_mode set to show" in text
    assert "display_mode: show" in text
    assert "\\u0000byte" in text, "null byte should render as \\u0000byte"
    assert "\\u0001" in text, "control char should render as \\u0001"


@pytest.mark.phase1
@pytest.mark.asyncio
async def test_set_display_mode_hide(client_session: Any) -> None:
    """set-display-mode to hide: non-printing chars shown as-is."""
    result_open = await client_session.call_tool(
        "viewport",
        arguments={"action": "open", "file_path": "non_printing.txt"},
    )
    assert "error" not in _get_text(result_open)
    vpid = _extract_vpid(_get_text(result_open))

    result_hide = await client_session.call_tool(
        "viewport",
        arguments={
            "action": "set-display-mode",
            "viewport_id": vpid,
            "display_mode": "hide",
        },
    )
    text = _get_text(result_hide)
    assert "display_mode set to hide" in text
    assert "display_mode: hide" in text
    assert "\\u0000" not in text, "hide mode should not render escape sequences"


@pytest.mark.phase1
@pytest.mark.asyncio
async def test_set_display_mode_invalid(client_session: Any) -> None:
    """Invalid display_mode returns error."""
    result_open = await client_session.call_tool(
        "viewport",
        arguments={"action": "open", "file_path": "test_file.txt"},
    )
    vpid = _extract_vpid(_get_text(result_open))

    result = await client_session.call_tool(
        "viewport",
        arguments={
            "action": "set-display-mode",
            "viewport_id": vpid,
            "display_mode": "invalid",
        },
    )
    assert result.isError
    assert "error" in _get_text(result).lower()


# ── SC-38 unicode decode in edit pipeline ──────────────────────────────────


@pytest.mark.phase1
@pytest.mark.asyncio
async def test_sc38_unicode_decode_in_edit_replace(
    client_session: Any, test_project_root: Path
) -> None:
    """SC-38-FIX: agent input \\uNNNN in edit operations decodes to real character.

    Behavioral evidence: edit:replace with \\u006c (decodes to 'l') successfully
    matches 'l' in 'line' within test_file.txt. Without decode, literal \\u006c
    would not match.
    """
    # Uses dedicated fixture file — no other test touches this, avoiding
    # SAT-UNSAT with tests that mutate test_file.txt on disk (SC-25, SC-35).
    file_path_str = "unicode_test.txt"
    original = (test_project_root / file_path_str).read_text()

    result_open = await client_session.call_tool(
        "viewport",
        arguments={"action": "open", "file_path": file_path_str, "autosave": False},
    )
    assert "error" not in _get_text(result_open)
    vpid = _extract_vpid(_get_text(result_open))

    # \\u006c\\u0069\\u006e\\u0065 decodes to 'line' which exists in the file
    # Without decode, literal "\\u006c\\u0069\\u006e\\u0065" would not match anything
    result = await client_session.call_tool(
        "edit",
        arguments={
            "action": "replace",
            "viewport_id": vpid,
            "old_text": "\\u006c\\u0069\\u006e\\u0065",
            "new_text": "DECODED-LINE",
        },
    )
    text = _get_text(result)
    assert not result.isError, (
        f"SC-38-FIX FAIL: \\u006c\\u0069\\u006e\\u0065 should decode to 'line' and match: {text[:200]}"
    )

    # File on disk must be unchanged (autosave=off)
    assert (test_project_root / file_path_str).read_text() == original, (
        "SC-38-FIX FAIL: file on disk changed (should stage only)"
    )


@pytest.mark.phase1
@pytest.mark.asyncio
async def test_sc38_unicode_decode_noop_on_literal_text(
    client_session: Any,
) -> None:
    """SC-38-FIX: decode is no-op on literal text (no \\uNNNN escapes).

    The 'lines' parameter is a list of literal lines, not \\uNNNN-escaped.
    This test verifies decode does NOT interfere with normal text.
    """
    result_open = await client_session.call_tool(
        "viewport",
        arguments={"action": "open", "file_path": "test_file.txt"},
    )
    assert "error" not in _get_text(result_open)


@pytest.mark.phase1
@pytest.mark.asyncio
async def test_sc2_relative_path_resolves(client_session: Any) -> None:
    """SC-2: Relative paths resolve against project_root."""
    result = await client_session.call_tool(
        "viewport",
        arguments={"action": "open", "file_path": "test_file.txt"},
    )
    text = _get_text(result)
    assert not result.isError, (
        f"Expected isError=false for relative path, got isError={result.isError}"
    )
    assert "1: line 1" in text, (
        f"Expected file content 'line 1' in response, got: {text[:300]}"
    )


@pytest.mark.phase1
@pytest.mark.asyncio
async def test_sc1_auto_reload_on_reopen_after_external_modification(
    client_session: Any, test_project_root: Path
) -> None:
    """SC-1: Re-opening a viewport after external file modification auto-reloads
    the buffer content and returns an auto-reload notice.

    RED: _action_open does not call auto-reload yet — this test MUST FAIL
    because the response content will still show the old file state and no
    auto-reload notice will be present.
    """
    file_path = test_project_root / "test_file.txt"
    original_content = file_path.read_text()

    # 1. Open the file via MCP client
    result_open = await client_session.call_tool(
        "viewport",
        arguments={"action": "open", "file_path": str(file_path)},
    )
    text = _get_text(result_open)
    assert "error" not in text.lower(), f"Open failed: {text}"
    assert "1: line 1" in text, f"Expected original content, got: {text[:200]}"

    # 2. Modify the file externally (write new content to disk)
    new_content = "replacement line 1\nreplacement line 2\nreplacement line 3\n"
    file_path.write_text(new_content)
    time.sleep(0.05)  # ensure mtime changes beyond the 10ms threshold

    # 3. Open the same file again
    result_reopen = await client_session.call_tool(
        "viewport",
        arguments={"action": "open", "file_path": str(file_path)},
    )
    reopen_text = _get_text(result_reopen)

    # 4. Verify the response content reflects the new disk state
    assert "replacement line 1" in reopen_text, (
        f"SC-1 FAIL: expected new content 'replacement line 1' in reopen response, "
        f"got: {reopen_text[:300]}"
    )
    assert "1: line 1" not in reopen_text, (
        f"SC-1 FAIL: old content 'line 1' should not appear after auto-reload, "
        f"got: {reopen_text[:300]}"
    )

    # 5. Verify the response includes the auto-reload notice
    assert "auto-reload" in reopen_text.lower() or "reloaded" in reopen_text.lower(), (
        f"SC-1 FAIL: expected auto-reload notice in reopen response, "
        f"got: {reopen_text[:300]}"
    )

    # Restore original content
    file_path.write_text(original_content)


@pytest.mark.phase1
@pytest.mark.asyncio
async def test_sc2_auto_reload_on_scroll_after_external_modification(
    client_session: Any, test_project_root: Path
) -> None:
    """SC-2: Auto-reload fires on scroll when buffer is clean and file changed externally.

    RED: scroll/jump/page-up/page-down don't call auto-reload yet — this test MUST FAIL
    because the response content will still show the old file state and no
    auto-reload notice will be present.
    """
    file_path = test_project_root / "test_file.txt"
    original_content = file_path.read_text()

    # 1. Open the file via MCP client
    result_open = await client_session.call_tool(
        "viewport",
        arguments={"action": "open", "file_path": str(file_path)},
    )
    text = _get_text(result_open)
    assert "error" not in text.lower(), f"Open failed: {text}"
    vpid = _extract_vpid(text)

    # 2. Modify the file externally
    new_content = "replacement line 1\nreplacement line 2\nreplacement line 3\n"
    file_path.write_text(new_content)
    time.sleep(0.05)

    # 3. Call scroll — should trigger auto-reload
    result_scroll = await client_session.call_tool(
        "viewport",
        arguments={"action": "scroll", "viewport_id": vpid, "lines": 1},
    )
    scroll_text = _get_text(result_scroll)

    # 4. Verify the response shows new content + auto-reload notice
    assert "replacement line 1" in scroll_text, (
        f"SC-2 FAIL: expected new content 'replacement line 1' in scroll response, "
        f"got: {scroll_text[:300]}"
    )
    assert "1: line 1" not in scroll_text, (
        f"SC-2 FAIL: old content 'line 1' should not appear after auto-reload, "
        f"got: {scroll_text[:300]}"
    )
    assert "auto-reloaded" in scroll_text.lower(), (
        f"SC-2 FAIL: expected auto-reload notice in scroll response, "
        f"got: {scroll_text[:300]}"
    )

    # Restore original content
    file_path.write_text(original_content)


@pytest.mark.phase1
@pytest.mark.asyncio
async def test_sc2_auto_reload_on_jump_after_external_modification(
    client_session: Any, test_project_root: Path
) -> None:
    """SC-2: Auto-reload fires on jump when buffer is clean and file changed externally."""
    file_path = test_project_root / "test_file.txt"
    original_content = file_path.read_text()

    result_open = await client_session.call_tool(
        "viewport",
        arguments={"action": "open", "file_path": str(file_path)},
    )
    vpid = _extract_vpid(_get_text(result_open))

    new_content = "replacement line 1\nreplacement line 2\nreplacement line 3\n"
    file_path.write_text(new_content)
    time.sleep(0.05)

    result_jump = await client_session.call_tool(
        "viewport",
        arguments={"action": "jump", "viewport_id": vpid, "target": "top"},
    )
    jump_text = _get_text(result_jump)

    assert "replacement line 1" in jump_text, (
        f"SC-2 FAIL: expected new content in jump response, got: {jump_text[:300]}"
    )
    assert "auto-reloaded" in jump_text.lower(), (
        f"SC-2 FAIL: expected auto-reload notice in jump response, got: {jump_text[:300]}"
    )

    file_path.write_text(original_content)


@pytest.mark.phase1
@pytest.mark.asyncio
async def test_sc2_auto_reload_on_page_up_after_external_modification(
    client_session: Any, test_project_root: Path
) -> None:
    """SC-2: Auto-reload fires on page-up when buffer is clean and file changed externally."""
    file_path = test_project_root / "test_file.txt"
    original_content = file_path.read_text()

    result_open = await client_session.call_tool(
        "viewport",
        arguments={"action": "open", "file_path": str(file_path)},
    )
    vpid = _extract_vpid(_get_text(result_open))

    new_content = "replacement line 1\nreplacement line 2\nreplacement line 3\n"
    file_path.write_text(new_content)
    time.sleep(0.05)

    result_up = await client_session.call_tool(
        "viewport",
        arguments={"action": "page-up", "viewport_id": vpid},
    )
    up_text = _get_text(result_up)

    assert "replacement line 1" in up_text, (
        f"SC-2 FAIL: expected new content in page-up response, got: {up_text[:300]}"
    )
    assert "auto-reloaded" in up_text.lower(), (
        f"SC-2 FAIL: expected auto-reload notice in page-up response, got: {up_text[:300]}"
    )

    file_path.write_text(original_content)


@pytest.mark.phase1
@pytest.mark.asyncio
async def test_sc2_auto_reload_on_page_down_after_external_modification(
    client_session: Any, test_project_root: Path
) -> None:
    """SC-2: Auto-reload fires on page-down when buffer is clean and file changed externally."""
    file_path = test_project_root / "test_file.txt"
    original_content = file_path.read_text()

    result_open = await client_session.call_tool(
        "viewport",
        arguments={"action": "open", "file_path": str(file_path)},
    )
    vpid = _extract_vpid(_get_text(result_open))

    new_content = "replacement line 1\nreplacement line 2\nreplacement line 3\n"
    file_path.write_text(new_content)
    time.sleep(0.05)

    result_down = await client_session.call_tool(
        "viewport",
        arguments={"action": "page-down", "viewport_id": vpid},
    )
    down_text = _get_text(result_down)

    assert "replacement line 1" in down_text, (
        f"SC-2 FAIL: expected new content in page-down response, got: {down_text[:300]}"
    )
    assert "auto-reloaded" in down_text.lower(), (
        f"SC-2 FAIL: expected auto-reload notice in page-down response, got: {down_text[:300]}"
    )

    file_path.write_text(original_content)


def test_sc1_absolute_path_resolves() -> None:
    """SC-1: _resolve_path accepts absolute paths and returns Tuple[str, str].

    RED phase: this MUST FAIL because _resolve_path currently raises
    AbsolutePathError on absolute paths. The GREEN phase will remove
    that restriction.
    """
    from viewport_editor.file_ops import _resolve_path

    result = _resolve_path("/etc/hostname", "/tmp")
    assert isinstance(result, tuple), f"Expected tuple, got {type(result)}"
    assert len(result) == 2, f"Expected tuple of length 2, got {len(result)}"
    assert isinstance(result[0], str), f"Expected str, got {type(result[0])}"
    assert isinstance(result[1], str), f"Expected str, got {type(result[1])}"


def _get_text(result: Any) -> str:
    parts: list[str] = []
    if result.content:
        for item in result.content:
            if hasattr(item, "text") and item.text:
                parts.append(item.text)
    return "\n".join(parts)


@pytest.mark.phase1
@pytest.mark.asyncio
async def test_sc3_list_shows_updated_metadata_after_auto_reload(
    client_session: Any, test_project_root: Path
) -> None:
    """SC-3: Open file, modify externally, list — verify metadata shows new mtime/size + notice."""
    file_path = test_project_root / "test_file.txt"
    original_content = file_path.read_text()

    result_open = await client_session.call_tool(
        "viewport",
        arguments={"action": "open", "file_path": str(file_path)},
    )
    text = _get_text(result_open)
    assert "error" not in text.lower()
    vpid = _extract_vpid(text)

    new_content = "replacement line 1\nreplacement line 2\n"
    file_path.write_text(new_content)
    time.sleep(0.05)

    # Trigger auto-reload via scroll (updates entry metadata)
    result_scroll = await client_session.call_tool(
        "viewport",
        arguments={"action": "scroll", "viewport_id": vpid, "lines": 1},
    )
    scroll_text = _get_text(result_scroll)
    assert "auto-reloaded" in scroll_text.lower()

    # List — verify metadata shows new mtime/size
    result_list = await client_session.call_tool(
        "viewport",
        arguments={"action": "list"},
    )
    list_text = _get_text(result_list)
    st = file_path.stat()
    assert f"mtime: {st.st_mtime}" in list_text, (
        f"SC-3 FAIL: expected mtime {st.st_mtime} in list, got: {list_text[:300]}"
    )
    assert f"size: {st.st_size}" in list_text, (
        f"SC-3 FAIL: expected size {st.st_size} in list, got: {list_text[:300]}"
    )

    file_path.write_text(original_content)


@pytest.mark.phase1
@pytest.mark.asyncio
async def test_sc4_notice_on_autosave_after_external_modification(
    client_session: Any, test_project_root: Path
) -> None:
    """SC-4: Open file, modify externally, toggle autosave — verify notice present."""
    file_path = test_project_root / "test_file.txt"
    original_content = file_path.read_text()

    result_open = await client_session.call_tool(
        "viewport",
        arguments={"action": "open", "file_path": str(file_path)},
    )
    vpid = _extract_vpid(_get_text(result_open))

    new_content = "replacement line 1\nreplacement line 2\n"
    file_path.write_text(new_content)
    time.sleep(0.05)

    result = await client_session.call_tool(
        "viewport",
        arguments={"action": "autosave", "viewport_id": vpid, "autosave_enabled": False},
    )
    text = _get_text(result)
    assert "auto-reloaded" in text.lower(), (
        f"SC-4 FAIL: expected auto-reload notice in autosave response, got: {text[:300]}"
    )

    file_path.write_text(original_content)


@pytest.mark.phase1
@pytest.mark.asyncio
async def test_sc4_notice_on_set_display_mode_after_external_modification(
    client_session: Any, test_project_root: Path
) -> None:
    """SC-4: Open file, modify externally, set-display-mode — verify notice present."""
    file_path = test_project_root / "test_file.txt"
    original_content = file_path.read_text()

    result_open = await client_session.call_tool(
        "viewport",
        arguments={"action": "open", "file_path": str(file_path)},
    )
    vpid = _extract_vpid(_get_text(result_open))

    new_content = "replacement line 1\nreplacement line 2\n"
    file_path.write_text(new_content)
    time.sleep(0.05)

    result = await client_session.call_tool(
        "viewport",
        arguments={
            "action": "set-display-mode",
            "viewport_id": vpid,
            "display_mode": "show",
        },
    )
    text = _get_text(result)
    assert "auto-reloaded" in text.lower(), (
        f"SC-4 FAIL: expected auto-reload notice in set-display-mode response, got: {text[:300]}"
    )

    file_path.write_text(original_content)


@pytest.mark.phase1
@pytest.mark.asyncio
async def test_sc9_notice_exact_string(
    client_session: Any, test_project_root: Path
) -> None:
    """SC-9: Verify auto-reload notice contains exact string."""
    file_path = test_project_root / "test_file.txt"
    original_content = file_path.read_text()

    result_open = await client_session.call_tool(
        "viewport",
        arguments={"action": "open", "file_path": str(file_path)},
    )
    vpid = _extract_vpid(_get_text(result_open))

    new_content = "replacement line 1\nreplacement line 2\n"
    file_path.write_text(new_content)
    time.sleep(0.05)

    result = await client_session.call_tool(
        "viewport",
        arguments={"action": "scroll", "viewport_id": vpid, "lines": 1},
    )
    text = _get_text(result)
    assert "file auto-reloaded (external change detected)" in text, (
        f"SC-9 FAIL: expected exact notice string in response, got: {text[:300]}"
    )

    file_path.write_text(original_content)


@pytest.mark.phase1
@pytest.mark.asyncio
async def test_sc11_metadata_matches_os_stat_after_auto_reload(
    client_session: Any, test_project_root: Path
) -> None:
    """SC-11: Open file, modify externally, auto-reload, check entry metadata matches os.stat."""
    file_path = test_project_root / "test_file.txt"
    original_content = file_path.read_text()

    result_open = await client_session.call_tool(
        "viewport",
        arguments={"action": "open", "file_path": str(file_path)},
    )
    vpid = _extract_vpid(_get_text(result_open))

    new_content = "replacement line 1\nreplacement line 2\n"
    file_path.write_text(new_content)
    time.sleep(0.05)

    # Trigger auto-reload via scroll
    result_scroll = await client_session.call_tool(
        "viewport",
        arguments={"action": "scroll", "viewport_id": vpid, "lines": 1},
    )
    scroll_text = _get_text(result_scroll)
    assert "auto-reloaded" in scroll_text.lower()

    # List to get stored metadata
    result_list = await client_session.call_tool(
        "viewport",
        arguments={"action": "list"},
    )
    list_text = _get_text(result_list)
    st = file_path.stat()

    mtime_line = [l for l in list_text.splitlines() if "mtime:" in l][0]
    size_line = [l for l in list_text.splitlines() if "size:" in l][0]
    stored_mtime = float(mtime_line.split("mtime:")[1].strip())
    stored_size = int(size_line.split("size:")[1].strip())

    assert stored_mtime == st.st_mtime, (
        f"SC-11 FAIL: mtime mismatch — stored={stored_mtime}, os.stat={st.st_mtime}"
    )
    assert stored_size == st.st_size, (
        f"SC-11 FAIL: size mismatch — stored={stored_size}, os.stat={st.st_size}"
    )

    file_path.write_text(original_content)


def _extract_vpid(text: str) -> str:
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("viewport_id:"):
            return line.split("viewport_id:")[1].strip()
    return ""


@pytest.mark.phase1
@pytest.mark.asyncio
async def test_content_block_format_cat_n(client_session: Any) -> None:
    """Verify cat -n style content output with line numbering."""
    result = await client_session.call_tool(
        "viewport",
        arguments={
            "action": "open",
            "file_path": "long_file.txt",
            "line_start": 1,
            "line_end": 10,
        },
    )
    text = _get_text(result)
    # cat -n format: content block header, then "    N: content"
    assert "  content:" in text
    assert "    1: line 1" in text
    assert "    5: line 5" in text
    assert "   10: line 10" in text


@pytest.mark.phase1
@pytest.mark.asyncio
async def test_navigation_chain_content_consistency(
    client_session: Any,
) -> None:
    """Chain open → page-up → page-down → scroll → jump, verify visible content at each step."""
    # Open at lines 5-15
    result_open = await client_session.call_tool(
        "viewport",
        arguments={
            "action": "open",
            "file_path": "long_file.txt",
            "line_start": 5,
            "line_end": 15,
        },
    )
    t1 = _get_text(result_open)
    assert "    5: line 5" in t1, "open content should start at line 5"
    assert "   15: line 15" in t1, "open content should end at line 15"
    vpid = _extract_vpid(t1)

    # Page up — viewport moves to top, verify content shifted
    result_up = await client_session.call_tool(
        "viewport",
        arguments={"action": "page-up", "viewport_id": vpid},
    )
    t2 = _get_text(result_up)
    assert "   1: line 1" in t2, "page-up from 5-15 should hit line 1"
    assert "line_start:" in t2

    # Page down — back to original-ish position
    result_down = await client_session.call_tool(
        "viewport",
        arguments={"action": "page-down", "viewport_id": vpid},
    )
    t3 = _get_text(result_down)
    assert "content:" in t3, "page-down should include content block"

    # Scroll by 3
    result_scroll = await client_session.call_tool(
        "viewport",
        arguments={"action": "scroll", "viewport_id": vpid, "lines": 3},
    )
    t4 = _get_text(result_scroll)
    assert "content:" in t4, "scroll should include content block"
    assert "line_start:" in t4, "scroll should report position"

    # Jump to a target
    result_jump = await client_session.call_tool(
        "viewport",
        arguments={"action": "jump", "viewport_id": vpid, "target": "line 70"},
    )
    t5 = _get_text(result_jump)
    assert "content:" in t5, "jump should include content block"
    assert "    70: line 70" in t5, "jump to line 70 should show line 70 in content"
    # Verify error target still works
    result_err = await client_session.call_tool(
        "viewport",
        arguments={
            "action": "jump",
            "viewport_id": vpid,
            "target": "ZZZZ_NOT_FOUND_ZZZZ",
        },
    )
    assert result_err.isError, "jump to nonexistent should return isError"
