"""Test MCP server for tool selection experiments.

Registers composite-named tools (read_file, write_file, edit_text, etc.)
that delegate to the real viewport-editor server's internal operations.

Usage:
    python -m test.tool_selection.test_server <variant_json> <trial_id>

The variant JSON determines which tool names and descriptions are registered.
V1 verb_class variants register all 5 tools simultaneously.
ACE variants register a single tool + companions for head-to-head A/B testing.
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


def create_tool_selection_server(
    variant: dict[str, Any], project_root: str | None = None
) -> FastMCP:
    """Create a test MCP server that registers composite tools.

    Supports two variant formats:
    1. V1 verb_class: variant['tools'] dict with all 5 tool name -> description pairs
    2. ACE/legacy: variant['tool_name'] + companion tool derivation
    """
    base_dir = project_root or os.getcwd()
    mcp = FastMCP(f"tool-selection-test-{variant['id']}")

    # V1 format: tools dict with all 5 tools
    if "tools" in variant:
        tool_defs = variant["tools"]
        for name, desc in tool_defs.items():
            mcp.tool(name=name)(_make_mcp_tool_fn(name, desc, base_dir))
        return mcp

    # Legacy format: single tool_name + companion derivation
    tool_name = variant["tool_name"]
    desc = variant.get("description", "")

    # Derive companion tool names from the variant's tool_name
    if tool_name in ("read", "open", "view"):
        write_name, edit_name, find_name = "write", "edit", "find"
    elif tool_name in ("read_file", "read_text"):
        write_name = "write_file" if tool_name == "read_file" else "write_text"
        edit_name = "edit_text"
        find_name = "find_text"
    else:
        write_name, edit_name, find_name = "write", "edit", "find"

    comp = variant.get("companion_descriptions", {})
    write_desc = comp.get(write_name, "Write file contents via a staged buffer.")
    edit_desc = comp.get(edit_name, "Edit file contents via a staged diff.")
    find_desc = comp.get(find_name, "Search file contents with structured results.")
    diff_desc = comp.get("diff", "Show unified diff of pending changes.")

    mcp.tool(name=tool_name)(_make_mcp_tool_fn(tool_name, desc, base_dir))
    mcp.tool(name=write_name)(_make_mcp_tool_fn(write_name, write_desc, base_dir))
    mcp.tool(name=edit_name)(_make_mcp_tool_fn(edit_name, edit_desc, base_dir))
    mcp.tool(name=find_name)(_make_mcp_tool_fn(find_name, find_desc, base_dir))
    mcp.tool(name="diff")(_make_mcp_tool_fn("diff", diff_desc, base_dir))

    return mcp


def _make_mcp_tool_fn(name: str, description: str, base_dir: str):
    """Create an MCP tool function with the given name and description.

    Each tool simulates its action (read/write/edit/find/diff) against
    the test project's filesystem for realistic responses.
    """
    if name in ("read", "read_file", "read_text", "open", "view"):
        def read_fn(file_path: str = "", offset: int = 0, limit: int = 2000) -> str:
            if not file_path:
                file_path = base_dir
            if not file_path.startswith("/"):
                file_path = os.path.join(base_dir, file_path)
            try:
                with open(file_path) as f:
                    lines = f.readlines()
                if offset > 0 or limit < len(lines):
                    start = max(0, offset)
                    end = min(len(lines), offset + limit) if limit else len(lines)
                    lines = lines[start:end]
                return "".join(lines)
            except FileNotFoundError:
                return f"error: file not found: {file_path}"
        read_fn.__doc__ = description
        read_fn.__name__ = name
        return read_fn

    elif name in ("write", "write_file", "write_text"):
        def write_fn(file_path: str = "", content: str = "") -> str:
            full_path = file_path if file_path.startswith("/") else os.path.join(base_dir, file_path)
            try:
                with open(full_path, "w") as f:
                    f.write(content)
                return f"written {len(content)} bytes to {file_path}"
            except OSError as e:
                return f"error: {e}"
        write_fn.__doc__ = description
        write_fn.__name__ = name
        return write_fn

    elif name in ("edit", "edit_text"):
        def edit_fn(file_path: str = "", old_text: str = "", new_text: str = "") -> str:
            full_path = file_path if file_path.startswith("/") else os.path.join(base_dir, file_path)
            try:
                with open(full_path) as f:
                    content = f.read()
                count = content.count(old_text)
                if count == 0:
                    return f"error: old text not found in {file_path}"
                content = content.replace(old_text, new_text)
                with open(full_path, "w") as f:
                    f.write(content)
                return f"edit applied to {file_path}: {count} replacement(s)"
            except FileNotFoundError:
                return f"error: file not found: {file_path}"
        edit_fn.__doc__ = description
        edit_fn.__name__ = name
        return edit_fn

    elif name in ("find", "find_text"):
        def find_fn(pattern: str = "", file_path: str = "", regex: bool = False) -> str:
            search_root = file_path if file_path else "."
            search_path = search_root if search_root.startswith("/") else os.path.join(base_dir, search_root)
            if os.path.isfile(search_path):
                target_files = [search_path]
            else:
                target_files = []
                for root, dirs, files in os.walk(search_path):
                    for f in files:
                        target_files.append(os.path.join(root, f))
            total = 0
            lines_out = []
            for fp in target_files:
                try:
                    with open(fp) as f:
                        for i, line in enumerate(f, 1):
                            if (regex and re.search(pattern, line)) or (not regex and pattern in line):
                                total += 1
                                rel = os.path.relpath(fp, base_dir)
                                lines_out.append(f"  - line: {i}  file: {rel}  text: {line.strip()[:80]}")
                except (OSError, UnicodeError):
                    pass
            header = f"find results for '{pattern}': {total} match(es)"
            if lines_out:
                return header + "\n" + "\n".join(lines_out)
            return header + "\n  matches: 0"
        find_fn.__doc__ = description
        find_fn.__name__ = name
        return find_fn

    elif name == "diff":
        def diff_fn(file_path: str = "") -> str:
            return f"no pending changes for {file_path}"
        diff_fn.__doc__ = description
        diff_fn.__name__ = name
        return diff_fn

    else:
        def fallback_fn(**kwargs: Any) -> str:
            return f"called {name} with {kwargs}"
        fallback_fn.__doc__ = description
        fallback_fn.__name__ = name
        return fallback_fn


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