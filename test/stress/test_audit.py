# SPDX-FileCopyrightText: 2026 Michael Conrad
# SPDX-License-Identifier: MIT
# Provenance: AI-generated
"""Tests for the stress test audit module.

Co-authored with AI: OpenCode (deepseek-v4-flash)
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from test.stress.audit_stress import audit_run


@pytest.mark.asyncio
async def test_audit_runs_on_valid_log_dir() -> None:
    """Verify audit runs on an existing stress test log directory."""
    from test.stress.run_stress import run_stress_test

    run_dir = await run_stress_test(density="sparse", run_id="test-audit-valid")
    output_dir = Path(tempfile.mkdtemp(prefix="ve-audit-test-"))
    await audit_run(run_dir, output_dir)
    assert (output_dir / "mechanical_report.md").exists(), (
        "mechanical_report.md missing"
    )
    assert (output_dir / "findings_manifest.json").exists(), (
        "findings_manifest.json missing"
    )


@pytest.mark.asyncio
async def test_audit_manifest_is_valid_json() -> None:
    """SC-5: findings manifest is valid JSON with semantic_question field per entry."""
    from test.stress.run_stress import run_stress_test

    run_dir = await run_stress_test(density="sparse", run_id="test-audit-json")
    output_dir = Path(tempfile.mkdtemp(prefix="ve-audit-json-"))
    await audit_run(run_dir, output_dir)

    manifest = json.loads((output_dir / "findings_manifest.json").read_text())
    if manifest:
        for entry in manifest:
            assert "semantic_question" in entry, (
                f"missing semantic_question in {entry.get('sequence_id', '?')}"
            )
            assert isinstance(entry["semantic_question"], str)
            assert len(entry["semantic_question"]) > 20
