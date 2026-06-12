# SPDX-FileCopyrightText: 2026 Michael Conrad
# SPDX-License-Identifier: MIT
# Provenance: AI-generated
"""Structural test: _find_sibling_agents_md uses os.path.realpath().

SC-12: os.path.realpath() is used for symlink-safe path comparison.

Co-authored with AI: OpenCode (deepseek-v4-flash)
"""

from __future__ import annotations

import ast
import os


def test_find_sibling_agents_md_uses_realpath() -> None:
    """SC-12: _find_sibling_agents_md function contains os.path.realpath()."""
    # Resolve file_ops.py relative to this project root
    here = os.path.dirname(os.path.abspath(__file__))
    # navigate up to project root: test/viewport-editor/65 -> go up 3 levels
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(here)))
    source_path = os.path.join(project_root, "src", "viewport_editor", "file_ops.py")

    with open(source_path) as f:
        source = f.read()

    assert "_find_sibling_agents_md" in source, (
        "Function _find_sibling_agents_md not found in file_ops.py"
    )

    tree = ast.parse(source)
    found_func = False
    has_realpath = False
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "_find_sibling_agents_md":
            found_func = True
            for sub in ast.walk(node):
                if isinstance(sub, ast.Call):
                    func = sub.func
                    if (
                        isinstance(func, ast.Attribute)
                        and func.attr == "realpath"
                        and isinstance(func.value, ast.Attribute)
                        and func.value.attr == "path"
                    ):
                        has_realpath = True
            break

    assert found_func, "_find_sibling_agents_md function not found in AST"
    assert has_realpath, "_find_sibling_agents_md must call os.path.realpath()"
