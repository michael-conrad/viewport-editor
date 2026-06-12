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
    """SC-5: injected_agents_files field exists on Session."""
    assert hasattr(Session, "injected_agents_files"), (
        "Session dataclass missing required field 'injected_agents_files'"
    )


def test_injected_agents_files_default_is_set() -> None:
    """SC-5b: injected_agents_files defaults to empty set or isinstance check."""
    import dataclasses

    # If Session is a dataclass, verify type via fields()
    if dataclasses.is_dataclass(Session):
        for f in dataclasses.fields(Session):
            if f.name == "injected_agents_files":
                assert f.type == set[str], f"Expected set[str], got {f.type}"
                return
    else:
        # Plain class: create instance and check type
        session = Session(session_id="test")
        assert isinstance(getattr(session, "injected_agents_files", None), set), (
            "injected_agents_files should be a set"
        )
