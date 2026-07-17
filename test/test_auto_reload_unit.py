# SPDX-FileCopyrightText: 2026 Michael Conrad
# SPDX-License-Identifier: MIT
# Provenance: AI-generated
"""RED test: format_external_modification_warning() does not exist yet.

SC-14: format_external_modification_warning() produces a YAML warning with
severity: external_modification and a prose note about overwriting external
changes.

This test MUST FAIL because the function does not exist yet (RED phase).

Co-authored with AI: OpenCode (deepseek-v4-flash)
"""

from __future__ import annotations


def test_sc14_external_modification_warning_format() -> None:
    """SC-14: format_external_modification_warning() produces severity and prose.

    RED: function does not exist yet — test will fail with AttributeError.
    """
    from viewport_editor.file_ops import format_external_modification_warning

    conflict: dict[str, object] = {
        "file": "/tmp/test.txt",
        "conflicts": {
            "mtime": {"stored": 1000, "current": 2000},
            "size": {"stored": 50, "current": 75},
        },
    }

    result = format_external_modification_warning(conflict)

    assert "severity: external_modification" in result, (
        f"SC-14 FAIL: output missing 'severity: external_modification'. "
        f"Got:\n{result}"
    )

    assert "overwriting" in result.lower() or "external change" in result.lower(), (
        f"SC-14 FAIL: output missing prose note about overwriting external changes. "
        f"Got:\n{result}"
    )


def test_sc16_auto_reload_conflict_refreshes_and_returns_notice() -> None:
    """SC-16: auto_reload_if_clean() refreshes buffer and returns notice on conflict.

    RED: conflict path returns None instead of calling refresh_if_changed()
    and returning a notice string.
    """
    from unittest.mock import patch
    from viewport_editor.viewport import ViewportManager, ViewportEntry

    mgr = ViewportManager(project_root="/tmp")
    session_id = "test-session"
    mgr._entries[session_id] = {}
    entry = ViewportEntry(
        file="/dev/null", line_start=1, line_end=1,
        mtime=1000.0, size=50, dirty=False,
    )
    mgr._entries[session_id][entry.viewport_id] = entry

    conflict_dict: dict[str, object] = {
        "file": "/dev/null",
        "conflicts": {
            "mtime": {"stored": 1000.0, "current": 2000.0},
            "size": {"stored": 50, "current": 75},
        },
    }

    with patch.object(mgr, "check_conflict", return_value=conflict_dict):
        with patch.object(mgr._buffer_mgr, "refresh_if_changed") as mock_refresh:
            result = mgr.auto_reload_if_clean(session_id, entry.viewport_id)

            # Assert refresh_if_changed IS called
            mock_refresh.assert_called_once()

            # Assert a notice string is returned
            assert result is not None, (
                "SC-16 FAIL: expected notice string when conflict detected, "
                "got None. Conflict path is a stub."
            )
            assert isinstance(result, str), (
                f"SC-16 FAIL: expected str return, got {type(result).__name__}"
            )
            assert len(result) > 0, (
                "SC-16 FAIL: expected non-empty notice string"
            )

            # Assert entry metadata is updated
            assert entry.mtime is not None and entry.mtime != 1000.0, (
                f"SC-16 FAIL: entry.mtime was not updated. "
                f"Still at {entry.mtime}"
            )
            assert entry.size is not None and entry.size != 50, (
                f"SC-16 FAIL: entry.size was not updated. "
                f"Still at {entry.size}"
            )


def test_sc17_auto_reload_dirty_with_conflict_returns_warning() -> None:
    """SC-17: auto_reload_if_clean() returns warning when dirty + conflict.

    RED: dirty+conflict path returns None instead of a warning string
    with severity: external_modification. refresh_if_changed() should
    NOT be called when the buffer is dirty.
    """
    from unittest.mock import patch
    from viewport_editor.viewport import ViewportManager, ViewportEntry

    mgr = ViewportManager(project_root="/tmp")
    session_id = "test-session"
    mgr._entries[session_id] = {}
    entry = ViewportEntry(
        file="/dev/null", line_start=1, line_end=1,
        mtime=1000.0, size=50, dirty=True,
    )
    mgr._entries[session_id][entry.viewport_id] = entry

    conflict_dict: dict[str, object] = {
        "file": "/dev/null",
        "conflicts": {
            "mtime": {"stored": 1000.0, "current": 2000.0},
            "size": {"stored": 50, "current": 75},
        },
    }

    with patch.object(mgr, "check_conflict", return_value=conflict_dict):
        with patch.object(mgr._buffer_mgr, "refresh_if_changed") as mock_refresh:
            result = mgr.auto_reload_if_clean(session_id, entry.viewport_id)

            # Assert refresh_if_changed is NOT called (dirty buffer)
            mock_refresh.assert_not_called()

            # Assert a warning string is returned
            assert result is not None, (
                "SC-17 FAIL: expected warning string when dirty + conflict, "
                "got None. Dirty+conflict path is a stub."
            )
            assert isinstance(result, str), (
                f"SC-17 FAIL: expected str return, got {type(result).__name__}"
            )

            # Assert warning contains severity: external_modification
            assert "severity: external_modification" in result, (
                f"SC-17 FAIL: output missing 'severity: external_modification'. "
                f"Got:\n{result}"
            )


def test_sc15_auto_reload_no_conflict_returns_none() -> None:
    """SC-15: auto_reload_if_clean() returns None when no conflict.

    RED: method does not exist yet — test will fail with AttributeError.
    """
    from unittest.mock import patch
    from viewport_editor.viewport import ViewportManager, ViewportEntry

    mgr = ViewportManager(project_root="/tmp")
    session_id = "test-session"
    mgr._entries[session_id] = {}
    entry = ViewportEntry(
        file="/dev/null", line_start=1, line_end=1,
        mtime=1000.0, size=50, dirty=False,
    )
    mgr._entries[session_id][entry.viewport_id] = entry

    with patch.object(mgr, "check_conflict", return_value=None):
        with patch.object(mgr._buffer_mgr, "refresh_if_changed") as mock_refresh:
            result = mgr.auto_reload_if_clean(session_id, entry.viewport_id)
            assert result is None, (
                f"SC-15 FAIL: expected None when no conflict, got {result!r}"
            )
            mock_refresh.assert_not_called()


def test_sc1_check_and_maybe_reload_delegates_to_auto_reload() -> None:
    """SC-1: _check_and_maybe_reload() delegates to auto_reload_if_clean().

    RED: function does not exist yet — test will fail with ImportError.
    """
    from unittest.mock import MagicMock, patch
    from viewport_editor.server import _check_and_maybe_reload
    from viewport_editor.viewport import ViewportEntry

    entry = ViewportEntry(
        file="/dev/null", line_start=1, line_end=1,
        mtime=1000.0, size=50, dirty=False,
    )
    file_path = "/dev/null"
    notice = "reloaded /dev/null (external change detected)"

    mock_mgr = MagicMock()
    mock_mgr.auto_reload_if_clean.return_value = notice

    session_id = "test-session"

    with patch("viewport_editor.server._manager", mock_mgr):
        result = _check_and_maybe_reload(session_id, file_path, entry)

        mock_mgr.auto_reload_if_clean.assert_called_once_with(
            session_id, entry.viewport_id
        )
        assert result == notice, (
            f"SC-1 FAIL: expected notice string, got {result!r}"
        )
