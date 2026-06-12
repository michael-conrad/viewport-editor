# SPDX-FileCopyrightText: 2026 Michael Conrad
# SPDX-License-Identifier: MIT
# Provenance: AI-generated
"""Tests for stress test runner.

Co-authored with AI: OpenCode (deepseek-v4-flash)
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest


from .run_stress import run_stress_test


@pytest.mark.asyncio
async def test_runner_sparse_creates_log_directory(tmp_path: Path) -> None:
    """SC-1: sparse run creates log dir with all sequences."""
    run_dir = await run_stress_test(density="sparse", run_id="test-sparse")
    assert run_dir.exists(), f"log directory {run_dir} not created"
    assert (run_dir / "manifest.json").exists(), "manifest.json missing"

    # Verify manifest
    manifest = json.loads((run_dir / "manifest.json").read_text())
    assert manifest["density"] == "sparse"
    assert manifest["total_sequences"] > 0
    assert "duration_seconds" in manifest
    assert "errors" in manifest


@pytest.mark.asyncio
async def test_runner_sequences_self_contained(tmp_path: Path) -> None:
    """SC-3: each sequence dir has params, seed, steps, final_content."""
    run_dir = await run_stress_test(density="sparse", run_id="test-self-contained")
    seqs_dir = run_dir / "sequences"
    assert seqs_dir.exists()
    seq_dirs = list(seqs_dir.iterdir())
    assert len(seq_dirs) > 0, "no sequence directories"

    for seq_dir in seq_dirs:
        assert (seq_dir / "params.json").exists(), (
            f"{seq_dir.name}: params.json missing"
        )
        assert (seq_dir / "seed_content.txt").exists(), (
            f"{seq_dir.name}: seed_content.txt missing"
        )
        assert (seq_dir / "steps.json").exists(), f"{seq_dir.name}: steps.json missing"
        assert (seq_dir / "final_content.txt").exists(), (
            f"{seq_dir.name}: final_content.txt missing"
        )

        # Verify steps.json is valid JSON
        steps = json.loads((seq_dir / "steps.json").read_text())
        assert isinstance(steps, list), f"{seq_dir.name}: steps should be a list"
