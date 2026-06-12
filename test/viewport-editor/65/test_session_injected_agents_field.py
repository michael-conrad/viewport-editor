# SPDX-FileCopyrightText: 2026 Michael Conrad
# SPDX-License-Identifier: MIT
# Provenance: AI-generated
"""Structural test: Session class has injected_agents_files field.

SC-5: injected_agents_files field exists on Session.
SC-5b: field type is set[str].

Co-authored with AI: OpenCode (deepseek-v4-flash)
"""

from __future__ import annotations

from viewport_editor.session import Session


def test_injected_agents_files_field_exists() -> None:
    """SC-5: injected_agents_files field exists on Session instance."""
    session = Session(session_id="test-sc5")
    assert hasattr(session, "injected_agents_files"), (
        "Session instance missing required field 'injected_agents_files'"
    )


def test_injected_agents_files_default_is_set() -> None:
    """SC-5b: injected_agents_files defaults to empty set."""
    session = Session(session_id="test-sc5b")
    assert isinstance(session.injected_agents_files, set), (
        "injected_agents_files should be a set"
    )
