# SPDX-FileCopyrightText: 2026 Michael Conrad
# SPDX-License-Identifier: MIT
# Provenance: AI-generated
"""Minimal MCP server that provides a viewport-based editing interface.

The project root is set at construction time from the current working directory.
No command-line path argument is accepted — the server is self-contained.

Co-authored with AI: OpenCode (ollama-cloud/deepseek-v4-flash)
"""

import logging

logger = logging.getLogger(__name__)


class ViewportEditorServer:
    """MCP server providing viewport-based file editing for AI agents."""

    def __init__(self, project_root: str) -> None:
        self.project_root = project_root

    def run(self) -> int:
        """Start the MCP server and block until shutdown."""
        logger.info("viewport-editor starting, project root: %s", self.project_root)
        return 0
