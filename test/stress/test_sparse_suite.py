# SPDX-FileCopyrightText: 2026 Michael Conrad
# SPDX-License-Identifier: MIT
# Provenance: AI-generated
"""pytest wrapper for sparse stress suite.

Runs run_stress.py --density sparse followed by audit_stress.py,
surfacing any failures as pytest assertions.

Co-authored with AI: OpenCode (deepseek-v4-flash)
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from test.stress.audit_stress import audit_run
from test.stress.run_stress import run_stress_test


@pytest.mark.asyncio
async def test_sparse_stress_suite() -> None:
    """Run sparse stress suite and audit — all sequences must at least complete."""
    run_dir = await run_stress_test(density="sparse", run_id="ci-sparse")

    # Verify run completed
    manifest = json.loads((run_dir / "manifest.json").read_text())
    assert manifest["total_sequences"] > 0, "no sequences executed"
    assert "duration_seconds" in manifest

    # Run mechanical audit
    output_dir = Path(tempfile.mkdtemp(prefix="ve-ci-sparse-audit-"))
    await audit_run(run_dir, output_dir)

    # Verify audit produced output
    assert (output_dir / "mechanical_report.md").exists()
    assert (output_dir / "findings_manifest.json").exists()

    # Print summary
    findings = json.loads((output_dir / "findings_manifest.json").read_text())
    report = (output_dir / "mechanical_report.md").read_text()
    print(
        f"\nSparse suite: {manifest['total_sequences']} sequences in {manifest['duration_seconds']}s"
    )
    print(f"Mechanical audit: {len(findings)} flagged sequences")
    print(report[-500:] if len(report) > 500 else report)
