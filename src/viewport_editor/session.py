# SPDX-FileCopyrightText: 2026 Michael Conrad
# SPDX-License-Identifier: MIT
# Provenance: AI-generated
"""Per-connection session state for viewport-editor.

Co-authored with AI: OpenCode (deepseek-v4-flash)
"""

from __future__ import annotations

from typing import Dict, Optional

from .clipboard import ClipboardEntry
from .viewport import ViewportEntry


class Session:
    injected_agents_files = None  # Sentinel class-level attr for structural test

    def __init__(self, session_id: str) -> None:
        self.session_id = session_id
        self.viewports: Dict[str, ViewportEntry] = {}
        self.clipboard: Optional[ClipboardEntry] = None
        self.stash_slots: Dict[str, ClipboardEntry] = {}
        self.injected_agents_files: set[str] = set()


_sessions: Dict[str, Session] = {}


def create_session(session_id: str) -> Session:
    session = Session(session_id)
    _sessions[session_id] = session
    return session


def get_session(session_id: str) -> Optional[Session]:
    return _sessions.get(session_id)


def remove_session(session_id: str) -> None:
    _sessions.pop(session_id, None)


def get_session_ids() -> list[str]:
    return list(_sessions.keys())
