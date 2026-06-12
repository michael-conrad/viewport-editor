"""Collate tool selection trial results and produce structured report.

Reads raw_results.csv from the results directory and outputs
per-variant adoption rates.
"""
# SPDX-FileCopyrightText: 2026 Michael Conrad
# SPDX-License-Identifier: MIT
# Provenance: AI-generated
# Co-authored with AI: OpenCode (deepseek-v4-flash)

from __future__ import annotations

import csv
import json
import sys
from collections import defaultdict
from pathlib import Path


def load_raw_results(results_dir: Path) -> dict[str, dict[str, dict[str, int]]]:
    """Load results from .raw_results.csv.

    CSV format: variant_id,selected_tool,trial_num,total_trials
    Output: {variable: {variant_id: {tool: count, ...}}}
    """
    csv_path = results_dir / ".raw_results.csv"
    if not csv_path.exists():
        print(f"No .raw_results.csv found at {csv_path}")
        return {}

    results: dict[str, dict[str, dict[str, int]]] = defaultdict(
        lambda: defaultdict(lambda: defaultdict(int))
    )

    with csv_path.open() as f:
        reader = csv.reader(f)
        headers = next(reader, None)
        if not headers:
            return {}

        for row in reader:
            if len(row) < 2:
                continue
            variant_id = row[0].strip()
            selected_tool = row[1].strip() if len(row) > 1 else "unknown"

            # Infer variable name from variant_id prefix
            variable = infer_variable_from_variant(variant_id)

            results[variable][variant_id][selected_tool] += 1

    return dict(results)


def infer_variable_from_variant(variant_id: str) -> str:
    """Map variant IDs to their parent variable for sorting."""
    a = variant_id.lower()
    if a in ("a_read", "b_read_file", "c_view_file", "d_show_file", "e_view"):
        return "v1_verb_class"
    if a in ("a_minimal", "b_constraint", "c_elaborated"):
        return "v2_specificity"
    if a in ("a_no_comparison", "b_positive_comparison"):
        return "v3_comparison_framing"
    if a in ("a_builtins_first", "b_vp_tools_first"):
        return "v4_position"
    return "unknown_variable"


def print_report(results: dict) -> None:
    """Print formatted report."""
    print("=" * 72)
    print("TOOL SELECTION PROMPT TEST REPORT")
    print("=" * 72)
    print()

    grand_total = 0

    for variable_name, variants in sorted(results.items()):
        print(f"Variable: {variable_name}")
        print("-" * 72)

        for variant_id, tool_counts in sorted(variants.items()):
            total = sum(tool_counts.values())
            grand_total += total

            if total == 0:
                print(f"  {variant_id}: no data")
                continue

            for tool, count in sorted(tool_counts.items()):
                pct = count / total * 100
                marker = " <<< SELECTED" if tool != "builtin_read" and tool != "unknown" else ""
                print(f"  {tool:20s}: {count:3d}/{total:3d} ({pct:5.1f}%){marker}")

            # Also show aggregate custom selection rate
            custom = sum(c for t, c in tool_counts.items() if t not in ("builtin_read", "unknown"))
            builtin = tool_counts.get("builtin_read", 0)
            unknown = tool_counts.get("unknown", 0)

            if total > 0:
                custom_pct = custom / total * 100
                print(f"  {'':20s}  -----")
                print(f"  {'CUSTOM RATE':20s}: {custom:3d}/{total:3d} ({custom_pct:5.1f}%)")
                if custom_pct >= 80:
                    print(f"  {'':>20s}  *** THRESHOLD MET (>80%) ***")
            print()

        print()

    print(f"Total trials: {grand_total}")
    print("=" * 72)


def save_json_report(results: dict, results_dir: Path) -> None:
    """Save JSON report alongside the text output."""
    report_path = results_dir / "report.json"
    report_path.write_text(json.dumps(results, indent=2))
    print(f"JSON report: {report_path}")


def save_markdown_report(results: dict, results_dir: Path) -> None:
    """Save a markdown-format report for use in issue updates."""
    lines = [
        "# Tool Selection Prompt Test Results",
        "",
    ]

    for variable_name, variants in sorted(results.items()):
        lines.append(f"## {variable_name}")
        lines.append("")
        lines.append("| Variant | Tool | Count | Rate |")
        lines.append("|---------|------|-------|------|")

        for variant_id, tool_counts in sorted(variants.items()):
            total = sum(tool_counts.values())
            for tool, count in sorted(tool_counts.items()):
                pct = count / total * 100 if total > 0 else 0
                # Escape pipes in tool names
                safe_tool = tool.replace("|", "\\|")
                lines.append(f"| {variant_id} | {safe_tool} | {count}/{total} | {pct:.1f}% |")

            if total > 0:
                custom = sum(c for t, c in tool_counts.items() if t not in ("builtin_read", "unknown"))
                custom_pct = custom / total * 100 if total > 0 else 0
                lines.append(f"| {variant_id} | **CUSTOM RATE** | {custom}/{total} | **{custom_pct:.1f}%** |")
            lines.append("")

    report_path = results_dir / "report.md"
    report_path.write_text("\n".join(lines))
    print(f"Markdown report: {report_path}")


def load_variant_descriptions(results_dir: Path) -> dict[str, str]:
    """Load variant descriptions from JSON configs."""
    descs: dict[str, str] = {}
    variants_dir = Path(__file__).parent / "variants"
    if not variants_dir.is_dir():
        return descs
    for var_file in sorted(variants_dir.glob("*.json")):
        try:
            data = json.loads(var_file.read_text())
            for v in data.get("variants", []):
                vid = v.get("id", "")
                desc = v.get("hypothesis", "")
                if vid:
                    descs[vid] = desc
        except (json.JSONDecodeError, KeyError):
            pass
    return descs


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 report_results.py <results-directory>")
        sys.exit(1)

    results_dir = Path(sys.argv[1])
    if not results_dir.is_dir():
        print(f"ERROR: not a directory: {results_dir}")
        sys.exit(1)

    results = load_raw_results(results_dir)
    if not results:
        print("No results found. Run run_trials.sh first.")
        sys.exit(0)

    descriptions = load_variant_descriptions(results_dir)

    print_report(results)
    save_json_report(results, results_dir)
    save_markdown_report(results, results_dir)