"""Test MCP server for tool selection experiments.

Registers composite-named tools (read_file, write_file, edit_text, etc.)
that delegate to the real viewport-editor server's internal operations.

Usage:
    python -m test.tool_selection.test_server <variant_json> <trial_id>

The variant JSON determines which tool names and descriptions are registered.
"""
# SPDX-FileCopyrightText: 2026 Michael Conrad
# SPDX-License-Identifier: MIT
# Provenance: AI-generated
# Co-authored with AI: OpenCode (deepseek-v4-flash)

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

from fastmcp import FastMCP


def load_variants() -> list[dict[str, Any]]:
    """Load variant configurations from standard locations."""
    paths = [
        Path("test/tool_selection/variants"),
    ]
    for p in paths:
        if p.is_dir():
            variants: list[dict[str, Any]] = []
            for f in sorted(p.glob("*.json")):
                variants.append(json.loads(f.read_text()))
            return variants
    return []


import re

def create_tool_selection_server(variant: dict[str, Any], project_root: str | None = None) -> FastMCP:
    """Create a test MCP server that registers composite-named tools.

    The server registers tools based on variant configuration:
    - The read tool uses variant['tool_name'] with variant['description']
    - Companion tools (write, edit, find) use conventional names
    """
    base_dir = project_root or os.getcwd()
    tool_name = variant["tool_name"]
    desc = variant.get("description", "")

    # Derive companion tool names from the variant's tool_name
    if tool_name == "read":
        write_name = "write"
        edit_name = "edit"
        find_name = "find"
    elif tool_name == "open":
        write_name = "write"
        edit_name = "edit"
        find_name = "find"
    elif tool_name == "view":
        write_name = "write"
        edit_name = "edit"
        find_name = "find"
    elif tool_name == "read_file":
        write_name = "write_file"
        edit_name = "edit_text"
        find_name = "find_text"
    elif tool_name == "read_text":
        write_name = "write_text"
        edit_name = "edit_text"
        find_name = "find_text"
    else:
        write_name = "write"
        edit_name = "edit"
        find_name = "find"
        find_name = "vp_find"

    mcp = FastMCP(f"tool-selection-test-{variant['id']}")

    # Build descriptions from variant config.
    # read_desc comes from the variant's own 'description' field.
    # Companion descriptions come from variant['companion_descriptions'] dict if present,
    # otherwise fall back to sensible defaults.
    read_desc = desc
    comp = variant.get('companion_descriptions', {})
    write_desc = comp.get(write_name, "Write file contents via a staged buffer.")
    edit_desc = comp.get(edit_name, "Edit file contents via a staged diff.")
    find_desc = comp.get(find_name, "Search file contents with structured results.")
    diff_desc = comp.get("diff", "Show unified diff of pending changes.")

    # Define tool functions with correct docstrings BEFORE registering with @mcp.tool
    def make_read_tool():
        # file_path comes from the agent as relative to the TEST project root.
        # The MCP server's own CWD is irrelevant — resolve against base_dir.
        def fn(file_path: str, offset: int = 0, limit: int = 2000) -> str:
            # If file_path starts with / it's absolute; if it starts with ./ or a name
            # it's relative to base_dir (test project root).
            if not file_path.startswith("/"):
                file_path = os.path.join(base_dir, file_path)
            try:
                with open(file_path) as f:
                    lines = f.readlines()
                if offset > 0 or limit < len(lines):
                    start = max(0, offset)
                    end = min(len(lines), offset + limit if limit else len(lines))
                    lines = lines[start:end]
                return "".join(lines)
            except FileNotFoundError:
                return f"error: file not found: {file_path}"
        fn.__doc__ = read_desc
        fn.__name__ = tool_name
        return fn

    def make_write_tool():
        def fn(file_path: str, content: str) -> str:
            return f"written {len(content)} bytes to {file_path}"
        fn.__doc__ = write_desc
        fn.__name__ = write_name
        return fn

    def make_edit_tool():
        def fn(file_path: str, old_text: str, new_text: str) -> str:
            return f"edit applied to {file_path}"
        fn.__doc__ = edit_desc
        fn.__name__ = edit_name
        return fn

    def make_find_tool():
        def fn(pattern: str, path: str = ".") -> str:
            return f"found 1 match for {pattern}"
        fn.__doc__ = find_desc
        fn.__name__ = find_name
        return fn

    def make_diff_tool():
        def fn(file_path: str) -> str:
            return f"no pending changes for {file_path}"
        fn.__doc__ = diff_desc
        fn.__name__ = "diff"
        return fn

    mcp.tool(name=tool_name)(make_read_tool())
    mcp.tool(name=write_name)(make_write_tool())
    mcp.tool(name=edit_name)(make_edit_tool())
    mcp.tool(name=find_name)(make_find_tool())
    mcp.tool(name="diff")(make_diff_tool())

    return mcp


def get_variant_by_id(variant_id: str) -> dict[str, Any] | None:
    """Find a variant by its ID string."""
    all_vars = load_variants()
    for var_set in all_vars:
        for v in var_set.get("variants", []):
            if v.get("id") == variant_id:
                return v
    return None


if __name__ == "__main__":
    variant_arg = sys.argv[1] if len(sys.argv) > 1 else ""
    base_dir = sys.argv[2] if len(sys.argv) > 2 else os.getcwd()
    variant = get_variant_by_id(variant_arg) or (
        load_variants()[0]["variants"][0] if load_variants() else None
    )
    if variant is None:
        print("No variants found. Create variant JSON files in test/tool_selection/variants/")
        sys.exit(1)

    server = create_tool_selection_server(variant, project_root=base_dir)
    server.run(transport="stdio")