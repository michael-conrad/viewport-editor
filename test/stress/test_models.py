# SPDX-FileCopyrightText: 2026 Michael Conrad
# SPDX-License-Identifier: MIT
# Provenance: AI-generated
"""Unit tests for stress test data models.

Co-authored with AI: OpenCode (deepseek-v4-flash)
"""

from __future__ import annotations

from test.stress.models import (
    ContentCheck,
    FindingsManifestEntry,
    Sequence,
    ToolCall,
)


def test_tool_call_dataclass() -> None:
    tc = ToolCall(
        tool="edit", params={"action": "replace", "old_text": "a", "new_text": "b"}
    )
    assert tc.tool == "edit"
    assert tc.params["old_text"] == "a"
    assert tc.params["new_text"] == "b"


def test_content_check_dataclass() -> None:
    cc = ContentCheck(type="line_count", target=5)
    assert cc.type == "line_count"
    assert cc.target == 5

    cc2 = ContentCheck(type="contains", target="hello")
    assert cc2.type == "contains"
    assert cc2.target == "hello"


def test_sequence_dataclass() -> None:
    seq = Sequence(
        id="test-001",
        category="edit_pairs",
        seed_content="line 1\nline 2\nline 3\n",
        steps=[
            ToolCall(
                tool="edit",
                params={"action": "replace", "old_text": "line 2", "new_text": "X"},
            ),
        ],
        expected_save_success=True,
        expected_content_checks=[ContentCheck(type="contains", target="X")],
        description="Replace line 2 with X",
    )
    assert seq.id == "test-001"
    assert seq.category == "edit_pairs"
    assert len(seq.steps) == 1
    assert len(seq.expected_content_checks) == 1
    assert seq.expected_save_success is True


def test_sequence_defaults() -> None:
    seq = Sequence(id="minimal", category="clipboard", seed_content="a\nb\n", steps=[])
    assert seq.expected_save_success is True
    assert seq.expected_content_checks == []
    assert seq.description == ""


def test_findings_manifest_entry() -> None:
    entry = FindingsManifestEntry(
        sequence_id="edit-pair-042",
        category="edit_pairs",
        seed_content="a\nb\nc\n",
        steps_summary="replace('b', 'X')",
        final_content="a\nX\nc\n",
        mechanical_flags=["line_count_mismatch"],
        semantic_question="Does the final content match the expected edit result?",
    )
    assert entry.sequence_id == "edit-pair-042"
    assert len(entry.mechanical_flags) == 1
    assert "line_count_mismatch" in entry.mechanical_flags
