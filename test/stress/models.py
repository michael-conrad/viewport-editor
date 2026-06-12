# SPDX-FileCopyrightText: 2026 Michael Conrad
# SPDX-License-Identifier: MIT
# Provenance: AI-generated
"""Data models for stress test sequences.

Co-authored with AI: OpenCode (deepseek-v4-flash)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


@dataclass
class ToolCall:
    """A single tool invocation in a stress test sequence."""

    tool: str
    params: dict


ContentCheckType = Literal[
    "line_count", "contains", "not_contains", "exact_match", "positional"
]


@dataclass
class ContentCheck:
    """A post-hoc correctness check against final file content."""

    type: ContentCheckType
    target: str | int


@dataclass
class Sequence:
    """A complete stress test sequence: seed file, steps, expected outcome."""

    id: str
    category: str
    seed_content: str
    steps: list[ToolCall]
    expected_save_success: bool = True
    expected_content_checks: list[ContentCheck] = field(default_factory=list)
    description: str = ""


@dataclass
class FindingsManifestEntry:
    """An entry in the findings manifest, describing a sequence that needs
    AI semantic analysis after mechanical checks flagged an anomaly."""

    sequence_id: str
    category: str
    seed_content: str
    steps_summary: str
    final_content: str
    mechanical_flags: list[str]
    semantic_question: str
