# SPDX-FileCopyrightText: 2026 Michael Conrad
# SPDX-License-Identifier: MIT
# Provenance: AI-generated
"""viewport-editor MCP server — a focused, windowed editing experience for AI agents.

Co-authored with AI: OpenCode (ollama-cloud/deepseek-v4-flash)
"""

import os
import sys

from .server import ViewportEditorServer


def main() -> None:
    """Launch the viewport-editor MCP server.

    The project root is determined from the current working directory.
    No command-line arguments are accepted.
    """
    project_root = os.getcwd()
    server = ViewportEditorServer(project_root)
    sys.exit(server.run())
