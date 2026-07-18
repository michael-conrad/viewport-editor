# SPDX-FileCopyrightText: 2026 Michael Conrad
# SPDX-License-Identifier: MIT
# Provenance: AI-generated
"""Entry point for viewport-editor MCP server.

Co-authored with AI: OpenCode (deepseek-v4-flash)
"""

import argparse
import os

from .server import create_server


def main() -> None:
    parser = argparse.ArgumentParser(description="viewport-editor MCP server")
    parser.add_argument(
        "--project-root",
        default=os.getcwd(),
        help="Root directory for file operations (default: cwd)",
    )
    args = parser.parse_args()

    server = create_server(project_root=args.project_root)
    server.run()


if __name__ == "__main__":
    main()
