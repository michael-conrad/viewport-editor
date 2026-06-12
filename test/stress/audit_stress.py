# SPDX-FileCopyrightText: 2026 Michael Conrad
# SPDX-License-Identifier: MIT
# Provenance: AI-generated
"""Mechanical audit for stress test logs — runs post-hoc, no server needed.

Produces:
  - mechanical_report.md — human-readable summary
  - findings_manifest.json — entries needing AI semantic analysis

The audit script does NOT dispatch AI sub-agents. It produces a structured
findings manifest. An AI orchestrator then dispatches clean-room sub-agents
ONE PER FINDING, SEQUENTIALLY — never batched, never parallel, never
categorized. See semantic-dispatch-procedure.md for the mandated protocol.

INVARIANT PROMPT MANDATE: The semantic dispatch prompt template is FROZEN
in semantic-dispatch-procedure.md. It MUST be used identically for every
finding with only three fields varying: seed_content, steps_summary,
final_content. No commentary, expectations, pattern labels, or operator
reasoning may be added. Violation produces contaminated results.

Usage:
    uv run python -m test.stress.audit_stress [--run-dir DIR] [--output PATH]
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .models import ContentCheck, FindingsManifestEntry


def _find_run_dirs() -> list[Path]:
    """Find all stress run directories."""
    stress_dir = Path("tmp/stress")
    if not stress_dir.exists():
        return []
    return sorted(stress_dir.iterdir())


def _load_steps(seq_dir: Path) -> list[dict[str, Any]]:
    steps_file = seq_dir / "steps.json"
    if not steps_file.exists():
        return []
    try:
        return json.loads(steps_file.read_text())
    except (json.JSONDecodeError, OSError):
        return []


def _load_params(seq_dir: Path) -> dict[str, Any]:
    params_file = seq_dir / "params.json"
    if not params_file.exists():
        return {}
    try:
        return json.loads(params_file.read_text())
    except (json.JSONDecodeError, OSError):
        return {}


def _load_final_content(seq_dir: Path) -> str:
    final_file = seq_dir / "final_content.txt"
    if not final_file.exists():
        return ""
    try:
        return final_file.read_text()
    except OSError:
        return ""


def _load_seed_content(seq_dir: Path) -> str:
    seed_file = seq_dir / "seed_content.txt"
    if not seed_file.exists():
        return ""
    try:
        return seed_file.read_text()
    except OSError:
        return ""


def _check_hard_errors(
    steps: list[dict[str, Any]],
    expected_save_success: bool,
) -> list[str]:
    """Check for unexpected isError=true in steps."""
    flags: list[str] = []
    for i, step in enumerate(steps):
        if step.get("isError", False):
            # Expected error paths by tool/response pattern
            response = step.get("response", "")
            if "Edit target not found" in response:
                # Expected: replace after replace-all or delete shifts content
                flags.append(f"edit_target_not_found_step_{i}")
            elif (
                "invalid line range" in response
                or "invalid range" in response
                or "invalid target_line" in response
            ):
                # Expected: post-delete ranges are invalid
                flags.append(f"line_range_step_{i}")
            elif "stash slot" in response and "not found" in response:
                if not expected_save_success:
                    flags.append(f"expected_error_step_{i}")
                else:
                    flags.append(f"unexpected_error_step_{i}")
            elif "clipboard is empty" in response:
                if not expected_save_success:
                    flags.append(f"expected_error_step_{i}")
                else:
                    flags.append(f"unexpected_error_step_{i}")
            elif "external modify" in response.lower() and expected_save_success:
                flags.append(f"expected_error_step_{i}")
            else:
                flags.append(f"unexpected_error_step_{i}")
    return flags


def _check_content_checks(
    final_content: str,
    checks: list[ContentCheck],
    expected_save_success: bool,
) -> list[str]:
    """Run expected content checks against final content.

    Only applies checks when save was expected (disk reflects buffer).
    """
    flags: list[str] = []

    if not expected_save_success:
        return flags

    lines = final_content.splitlines(keepends=True)
    line_count = len(lines)

    for check in checks:
        if check.type == "line_count":
            if isinstance(check.target, int) and line_count != check.target:
                flags.append(
                    f"line_count_mismatch: expected {check.target}, got {line_count}"
                )
        elif check.type == "contains":
            if isinstance(check.target, str) and check.target not in final_content:
                flags.append(f"missing_expected_content: '{check.target}'")
        elif check.type == "not_contains":
            if isinstance(check.target, str) and check.target in final_content:
                flags.append(f"unexpected_content: '{check.target}'")
        elif check.type == "exact_match":
            if isinstance(check.target, str) and final_content != check.target:
                flags.append("content_mismatch")
    return flags


def _check_truncation(
    seed_content: str,
    final_content: str,
    steps: list[dict[str, Any]],
) -> list[str]:
    """Check if final content looks truncated."""
    flags: list[str] = []

    # Count deletes and inserts in steps
    deletes = sum(
        1
        for s in steps
        if s.get("tool") == "edit" and s["params"].get("action") == "delete-lines"
    )
    cuts = sum(
        1
        for s in steps
        if s.get("tool") == "clipboard" and s["params"].get("action") == "cut"
    )

    # If no deletes/cuts but final is much shorter than seed, flag truncation
    if deletes == 0 and cuts == 0:
        if final_content and len(final_content) < len(seed_content) * 0.5:
            flags.append("possible_truncation_no_deletes")

    # If file is empty and we didn't delete everything, flag
    if not final_content.strip() and deletes == 0:
        flags.append("empty_final_no_deletes")

    return flags


def _check_seed_lines_missing(
    seed_content: str,
    final_content: str,
    steps: list[dict[str, Any]],
    expected_save_success: bool,
) -> list[str]:
    """Check for seed lines that are missing from final content.

    Only flags lines that were NOT intentionally modified by an edit step.
    """
    flags: list[str] = []

    # Skip check entirely if save was not expected (disk state doesn't reflect buffer)
    if not expected_save_success:
        return flags

    # Skip check for sequences with replace-all — it fundamentally changes all content
    has_replace_all = any(
        s.get("tool") == "edit" and s["params"].get("action") == "replace-all"
        for s in steps
    )
    if has_replace_all:
        return flags

    # Collect all text that was intentionally replaced or removed
    intentionally_removed: set[str] = set()

    # Add old_text from replace operations
    for s in steps:
        params = s.get("params", {})
        if s.get("tool") == "edit":
            if params.get("action") in ("replace",):
                old = params.get("old_text", "").strip()
                if old:
                    intentionally_removed.add(old)

    # If any delete-lines, move-lines, or swap-lines operations occurred,
    # the content structure is intentionally altered — skip seed-line checks
    # because we can't know exactly which lines were kept
    has_structural_change = any(
        s.get("tool") == "edit"
        and s["params"].get("action")
        in (
            "delete-lines",
            "move-lines",
            "swap-lines",
            "replace-all",
        )
        for s in steps
    )
    if has_structural_change:
        return flags

    # Also skip if any clipboard cut or diff apply occurred
    has_cut = any(
        s.get("tool") == "clipboard" and s["params"].get("action") == "cut"
        for s in steps
    )
    if has_cut:
        return flags

    has_diff_apply = any(
        s.get("tool") == "diff" and s["params"].get("action") == "apply" for s in steps
    )
    if has_diff_apply:
        return flags

    seed_lines = [ln.strip() for ln in seed_content.splitlines() if ln.strip()]
    for line in seed_lines:
        if line in intentionally_removed:
            continue  # Intentionally replaced by edit operation
        if line not in final_content and "line" in line:
            flags.append(f"seed_line_missing: '{line}'")
    return flags


def _make_semantic_question(
    sequence_id: str,
    seed_content: str,
    steps: list[dict[str, Any]],
    final_content: str,
    mechanical_flags: list[str],
) -> str:
    """Build a targeted semantic question for AI analysis."""
    step_summaries: list[str] = []
    for s in steps:
        tool = s.get("tool", "?")
        params = s.get("params", {})
        if tool == "viewport":
            action = params.get("action", "")
            step_summaries.append(f"viewport:{action}")
        elif tool == "edit":
            action = params.get("action", "")
            if action in ("replace", "replace-all"):
                old = params.get("old_text", "")[:20]
                new = params.get("new_text", "")[:20]
                step_summaries.append(f"edit:{action}('{old}'->'{new}')")
            else:
                ls = params.get("line_start", 0)
                le = params.get("line_end", 0)
                step_summaries.append(f"edit:{action}({ls}-{le})")
        elif tool == "clipboard":
            action = params.get("action", "")
            step_summaries.append(f"clipboard:{action}")
        elif tool == "diff":
            action = params.get("action", "")
            step_summaries.append(f"diff:{action}")
        elif tool == "file":
            action = params.get("action", "")
            step_summaries.append(f"file:{action}")
        else:
            step_summaries.append(f"{tool}:{params}")

    flags_str = ", ".join(mechanical_flags)

    return (
        f"The seed content was modified by the sequence of operations above. "
        f"Does the final file content correctly reflect all operations applied in order? "
        f"Mechanical checks flagged: {flags_str}. "
        f"Focus on: line ordering correctness, offset accuracy after deletions/insertions, "
        f"proper application of all edit operations, and absence of corruption or drift. "
        f"Respond with PASS or FAIL and specific evidence."
    )


async def audit_run(run_dir: Path, output_dir: Path | None = None) -> Path:
    """Audit a stress test run directory.

    Returns path to the output directory.
    """
    if output_dir is None:
        output_dir = run_dir

    manifest_path = run_dir / "manifest.json"
    if not manifest_path.exists():
        print(f"error: no manifest.json in {run_dir}")
        sys.exit(1)

    manifest = json.loads(manifest_path.read_text())
    run_id = manifest.get("run_id", "unknown")
    total = manifest.get("total_sequences", 0)
    seq_dir = run_dir / "sequences"

    if not seq_dir.exists():
        print(f"error: no sequences/ in {run_dir}")
        sys.exit(1)

    all_flags: dict[str, list[str]] = {}
    findings: list[FindingsManifestEntry] = []
    passed = 0
    failed = 0

    for seq_path in sorted(seq_dir.iterdir()):
        if not seq_path.is_dir():
            continue

        seq_id = seq_path.name
        steps = _load_steps(seq_path)
        params = _load_params(seq_path)
        seed_content = _load_seed_content(seq_path)
        final_content = _load_final_content(seq_path)

        expected_save = params.get("expected_save_success", True)
        checks_raw = params.get("expected_content_checks", [])
        checks = [ContentCheck(type=c["type"], target=c["target"]) for c in checks_raw]

        flags: list[str] = []

        # Mechanical checks
        flags.extend(_check_hard_errors(steps, expected_save))
        flags.extend(_check_content_checks(final_content, checks, expected_save))
        flags.extend(_check_truncation(seed_content, final_content, steps))
        flags.extend(
            _check_seed_lines_missing(seed_content, final_content, steps, expected_save)
        )

        all_flags[seq_id] = flags

        if flags:
            failed += 1
            # Create findings manifest entry
            findings.append(
                FindingsManifestEntry(
                    sequence_id=seq_id,
                    category=params.get("category", "unknown"),
                    seed_content=seed_content,
                    steps_summary="",  # Filled below
                    final_content=final_content,
                    mechanical_flags=flags,
                    semantic_question="",
                )
            )
        else:
            passed += 1

    # Write mechanical report
    report_lines = [
        "# Stress Test Mechanical Report",
        "",
        f"**Run:** {run_id}",
        f"**Total sequences:** {total}",
        f"**Passed:** {passed}",
        f"**Failed (flag raised):** {failed}",
        f"**Timestamp:** {datetime.now(timezone.utc).isoformat()}",
        "",
    ]

    if findings:
        report_lines.append(f"## Failed Sequences ({len(findings)})")
        report_lines.append("")
        report_lines.append("| Sequence | Category | Flags |")
        report_lines.append("|----------|----------|-------|")
        for entry in findings:
            flags_str = "; ".join(entry.mechanical_flags)
            report_lines.append(
                f"| {entry.sequence_id} | {entry.category} | {flags_str} |"
            )
        report_lines.append("")

    report_lines.append("## All Sequences")
    report_lines.append("")
    report_lines.append("| Sequence | Result | Flags |")
    report_lines.append("|----------|--------|-------|")
    for seq_id in sorted(all_flags.keys()):
        flags = all_flags[seq_id]
        result = "⚠ FAIL" if flags else "✅ PASS"
        flags_str = "; ".join(flags) if flags else ""
        report_lines.append(f"| {seq_id} | {result} | {flags_str} |")

    report_text = "\n".join(report_lines)
    report_path = output_dir / "mechanical_report.md"
    report_path.write_text(report_text)

    # Write findings manifest
    # First, fill in steps_summary and semantic_question for each finding
    findings_data: list[dict[str, Any]] = []
    for entry in findings:
        seq_path = seq_dir / entry.sequence_id
        steps = _load_steps(seq_path)

        findings_data.append(
            {
                "sequence_id": entry.sequence_id,
                "category": entry.category,
                "seed_content": entry.seed_content,
                "steps_summary": " → ".join(
                    f"{s.get('tool', '?')}:{s.get('params', {}).get('action', '?')}"
                    for s in steps
                ),
                "final_content": entry.final_content,
                "mechanical_flags": entry.mechanical_flags,
                "semantic_question": _make_semantic_question(
                    entry.sequence_id,
                    entry.seed_content,
                    steps,
                    entry.final_content,
                    entry.mechanical_flags,
                ),
            }
        )

    manifest_path_out = output_dir / "findings_manifest.json"
    manifest_path_out.write_text(json.dumps(findings_data, indent=2))

    # Copy output files to .issues/ if not already there
    if output_dir == run_dir:
        issues_dir = Path(".issues")
        if issues_dir.exists():
            for fname in ("mechanical_report.md", "findings_manifest.json"):
                src = output_dir / fname
                if src.exists():
                    dst = issues_dir / f"stress-{run_id}-{fname}"
                    shutil.copy2(src, dst)
                    report_lines.append(f"\nCopied {fname} to .issues/")

    print(f"Mechanical report: {report_path}")
    print(f"Findings manifest: {manifest_path_out}")
    print(f"Passed: {passed}, Failed: {failed}")

    return output_dir


def main() -> None:
    parser = argparse.ArgumentParser(description="Stress test audit")
    parser.add_argument(
        "--run-dir",
        type=str,
        default=None,
        help="Path to run directory (default: latest)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output directory (default: same as run-dir)",
    )
    args = parser.parse_args()

    if args.run_dir:
        run_dir = Path(args.run_dir)
        if not run_dir.exists():
            print(f"error: run directory not found: {run_dir}")
            sys.exit(1)
    else:
        dirs = _find_run_dirs()
        if not dirs:
            print("error: no stress test runs found in tmp/stress/")
            sys.exit(1)
        run_dir = dirs[-1]  # latest

    output_dir = Path(args.output) if args.output else run_dir

    import asyncio

    asyncio.run(audit_run(run_dir, output_dir))


if __name__ == "__main__":
    main()
