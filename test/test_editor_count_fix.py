# SPDX-FileCopyrightText: 2026 Michael Conrad
# SPDX-License-Identifier: MIT
# Provenance: AI-generated
"""Unit tests for editor apply_edit and apply_replace_all count fields.

The `replace` action (apply_edit) returns count derived from actual content
change, not a hardcoded constant or the pre-replacement total.
When old_text is not found, returns found=False, count=0 — no exception.

The `replace-all` action (apply_replace_all) likewise returns found=False,
count=0 for not-found — no exception.

Co-authored with AI: OpenCode (ollama-cloud/glm-5.1)
"""

from __future__ import annotations

import pytest

from viewport_editor.editor import apply_edit, apply_replace_all


class TestApplyEditCountField:
    """Verify apply_edit returns count derived from reality (replacements made)."""

    def test_replace_single_occurrence_returns_count_1(self) -> None:
        """When old_text appears once, count=1 and total_matches=1."""
        content = "hello world"
        new_content, result = apply_edit(content, "hello", "HELLO")
        assert result["found"] is True
        assert result["count"] == 1
        assert result["total_matches"] == 1
        assert new_content == "HELLO world"

    def test_replace_first_of_many_returns_count_1(self) -> None:
        """When old_text appears multiple times, count=1 (first only) but total_matches=N."""
        content = "aaa bbb aaa ccc aaa"
        new_content, result = apply_edit(content, "aaa", "XXX")
        assert result["found"] is True
        assert result["count"] == 1
        assert result["total_matches"] == 3
        assert new_content == "XXX bbb aaa ccc aaa"

    def test_replace_first_of_two_returns_count_1(self) -> None:
        """Two occurrences: replace changes first one only."""
        content = "foo and foo"
        new_content, result = apply_edit(content, "foo", "FOO")
        assert result["found"] is True
        assert result["count"] == 1
        assert result["total_matches"] == 2
        assert new_content == "FOO and foo"

    def test_count_derived_not_hardcoded(self) -> None:
        """Count is derived from content comparison, not a hardcoded constant.

        If new_text contains old_text as a substring, count should still
        reflect actual replacements (1 for replace, not the residual count).
        """
        content = "abc"
        new_content, result = apply_edit(content, "abc", "abc-XYZ")
        assert result["found"] is True
        assert result["count"] == 1
        assert "abc" in new_content  # new_text contains old_text as prefix
        assert new_content == "abc-XYZ"

    def test_not_found_returns_found_false_count_0(self) -> None:
        """When old_text not found, returns found=False, count=0, no exception."""
        content = "hello world"
        new_content, result = apply_edit(content, "notfound", "XXX")
        assert result["found"] is False
        assert result["count"] == 0
        assert result["total_matches"] == 0
        assert new_content == content  # unchanged


class TestApplyReplaceAllCountField:
    """Verify apply_replace_all returns count=N (all replacements made)."""

    def test_replace_all_returns_total_count(self) -> None:
        """replace-all returns count=N where N is total replacements made."""
        content = "aaa bbb aaa ccc aaa"
        new_content, result = apply_replace_all(content, "aaa", "XXX")
        assert result["found"] is True
        assert result["count"] == 3
        assert "total_matches" not in result
        assert new_content == "XXX bbb XXX ccc XXX"

    def test_replace_all_single_occurrence(self) -> None:
        """replace-all with one occurrence returns count=1."""
        content = "hello world"
        new_content, result = apply_replace_all(content, "hello", "HELLO")
        assert result["found"] is True
        assert result["count"] == 1
        assert new_content == "HELLO world"

    def test_replace_all_not_found_returns_found_false_count_0(self) -> None:
        """When old_text not found, returns found=False, count=0, no exception."""
        content = "hello world"
        new_content, result = apply_replace_all(content, "notfound", "XXX")
        assert result["found"] is False
        assert result["count"] == 0
        assert new_content == content  # unchanged