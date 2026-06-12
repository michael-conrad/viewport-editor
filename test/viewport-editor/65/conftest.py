# SPDX-FileCopyrightText: 2026 Michael Conrad
# SPDX-License-Identifier: MIT
# Provenance: AI-generated
"""Conftest for Phase 2 AGENTS.md injection tests.

Provides test_project_root fixture so tests in this directory can create
temporary directory structures with AGENTS.md files.

Co-authored with AI: OpenCode (deepseek-v4-flash)
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any

import pytest


@pytest.fixture(scope="module")
def test_project_root() -> Any:
    """Create a temporary project root with a basic file for MCP server fixture."""
    tmpdir = Path(tempfile.mkdtemp(prefix="ve-phase2-"))
    (tmpdir / "root_file.txt").write_text("line 1\nline 2\nline 3\n")
    return tmpdir
