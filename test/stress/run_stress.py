# SPDX-FileCopyrightText: 2026 Michael Conrad
# SPDX-License-Identifier: MIT
# Provenance: AI-generated
"""Stress test runner — executes sequences against in-memory MCP server.

Usage:
    uv run python -m test.stress.run_stress [--density {sparse|dense}] [--run-id STR] [--preserve]

No assertions. Runner only executes and logs to tmp/stress/<run_id>/.
After running, use audit_stress.py for mechanical checks, then dispatch
clean-room sub-agents ONE PER FINDING, SEQUENTIALLY per the protocol in
semantic-dispatch-procedure.md.
"""

from __future__ import annotations

import argparse
import json
import shutil
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastmcp import Client
from fastmcp.exceptions import ToolError

from viewport_editor.server import create_server

from .generator_clipboard import generate_clipboard_sequences
from .generator_crosstalk import generate_crosstalk_sequences
from .generator_diff import generate_diff_sequences
from .generator_edit_pairs import generate_edit_pair_sequences
from .generator_mtime import generate_mtime_sequences
from .models import Sequence, ToolCall


class _CompatResult:
    """Minimal backward-compatible result with .isError and .content."""

    def __init__(self, text: str, is_error: bool = False) -> None:
        self.isError = is_error
        self.content = [
            type(
                "TextContent", (), {"type": "text", "text": text, "annotations": None}
            )()
        ]


class _CompatClient:
    """Minimal wrapper around fastmcp.Client catching ToolError as isError."""

    def __init__(self, client: Client) -> None:
        self._client = client

    async def call_tool(
        self, name: str, arguments: dict[str, Any] | None = None, **kwargs: Any
    ) -> _CompatResult | Any:
        try:
            result = await self._client.call_tool(name, arguments=arguments, **kwargs)
            result.isError = result.is_error
            return result
        except ToolError as exc:
            msg = str(exc)
            if ": " in msg:
                msg = msg.split(": ", 1)[-1].strip()
            return _CompatResult(text=f"error: {msg}", is_error=True)


def _get_text(result: Any) -> str:
    parts: list[str] = []
    if hasattr(result, "content") and result.content:
        for item in result.content:
            if hasattr(item, "text") and item.text:
                parts.append(item.text)
    return "\n".join(parts)


def _extract_vpid(text: str) -> str | None:
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("viewport_id:"):
            return line.split("viewport_id:")[1].strip()
    return None


def _extract_vpids(text: str) -> list[str]:
    ids: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("viewport_id:"):
            ids.append(stripped.split("viewport_id:")[1].strip())
    return ids


def _collect_generators(density: str) -> list[Sequence]:
    sequences: list[Sequence] = []
    sequences.extend(generate_edit_pair_sequences(density=density))
    sequences.extend(generate_clipboard_sequences())
    sequences.extend(generate_diff_sequences())
    sequences.extend(generate_crosstalk_sequences())
    sequences.extend(generate_mtime_sequences())
    return sequences


def _is_external_modify_step(step: ToolCall) -> bool:
    return step.tool == "__external__" and step.params.get("action") == "modify_file"


async def _run_sequence(
    client: _CompatClient,
    seq: Sequence,
    seq_dir: Path,
    project_root: Path,
) -> dict[str, Any]:
    seq_dir.mkdir(parents=True, exist_ok=True)

    seed_path = seq_dir / "seed_content.txt"
    seed_path.write_text(seq.seed_content)

    params_path = seq_dir / "params.json"
    params_path.write_text(
        json.dumps(
            {
                "id": seq.id,
                "category": seq.category,
                "description": seq.description,
                "expected_save_success": seq.expected_save_success,
                "expected_content_checks": [
                    {"type": c.type, "target": c.target}
                    for c in seq.expected_content_checks
                ],
            },
            indent=2,
        )
    )

    seed_file = seq.id + ".txt"
    (project_root / seed_file).write_text(seq.seed_content)

    steps_log: list[dict[str, Any]] = []
    viewport_id: str | None = None

    # Check if this sequence manages its own viewport lifecycle
    seq_manages_viewport = any(
        s.tool == "viewport" and s.params.get("action") in ("open", "close")
        for s in seq.steps
    )

    if not seq_manages_viewport:
        # Auto-open a viewport on the seed file
        open_result = await client.call_tool(
            "viewport",
            arguments={"action": "open", "file_path": seed_file, "autosave": False},
        )
        open_text = _get_text(open_result)
        open_is_error = (
            open_result.isError if hasattr(open_result, "isError") else False
        )
        if not open_is_error:
            viewport_id = _extract_vpid(open_text)

        steps_log.append(
            {
                "tool": "viewport",
                "params": {"action": "open", "file_path": seed_file, "autosave": False},
                "isError": open_is_error,
                "response": open_text,
                "duration_ms": 0,
            }
        )

    for step in seq.steps:
        step_log: dict[str, Any] = {
            "tool": step.tool,
            "params": dict(step.params),
            "isError": False,
            "response": "",
            "duration_ms": 0,
        }

        if _is_external_modify_step(step):
            ext_params = step.params
            target_file = ext_params.get("file_path", seed_file)
            target_path = project_root / target_file
            new_content = ext_params.get("content", "")
            old_mtime = target_path.stat().st_mtime if target_path.exists() else 0
            target_path.write_text(new_content)
            if target_path.stat().st_mtime <= old_mtime:
                time.sleep(0.02)
                target_path.write_text(new_content)
            step_log["isError"] = False
            step_log["response"] = f"external modify: {target_file}"
            steps_log.append(step_log)
            continue

        params = dict(step.params)

        # Normalize file_path to point at our seed file
        if "file_path" in params:
            params["file_path"] = seed_file

        # Fill in viewport_id for steps that need it
        if viewport_id is not None:
            if params.get("viewport_id") == "" or params.get("viewport_id") is None:
                if step.tool in ("edit", "clipboard", "file"):
                    params["viewport_id"] = viewport_id
                elif step.tool == "viewport" and params.get("action") in (
                    "close",
                    "scroll",
                    "page-up",
                    "page-down",
                    "jump",
                    "autosave",
                    "set-display-mode",
                ):
                    params["viewport_id"] = viewport_id
                elif step.tool == "diff":
                    params.pop("viewport_id", None)
                    params["file_path"] = (
                        seed_file  # diff:apply uses file_path for auto-load
                    )

        t0 = time.time()
        result = await client.call_tool(step.tool, arguments=params)
        duration = int((time.time() - t0) * 1000)

        response_text = _get_text(result)
        step_log["isError"] = result.isError if hasattr(result, "isError") else False
        step_log["response"] = response_text
        step_log["duration_ms"] = duration
        # Track viewport lifecycle: close/reset invalidates current vpid
        if step.tool == "viewport" and params.get("action") == "close":
            viewport_id = None
        elif step.tool == "viewport" and params.get("action") == "open":
            vpid = _extract_vpid(response_text)
            if vpid and not step_log["isError"]:
                viewport_id = vpid

        steps_log.append(step_log)

    # Save (before close — viewport must exist for file:save)
    if seq.expected_save_success and viewport_id is not None:
        t0 = time.time()
        save_result = await client.call_tool(
            "file",
            arguments={
                "action": "save",
                "viewport_id": viewport_id,
                "file_path": seed_file,
            },
        )
        save_duration = int((time.time() - t0) * 1000)
        save_response = _get_text(save_result)
        save_is_error = (
            save_result.isError if hasattr(save_result, "isError") else False
        )
        steps_log.append(
            {
                "tool": "file",
                "params": {
                    "action": "save",
                    "viewport_id": viewport_id,
                    "file_path": seed_file,
                },
                "isError": save_is_error,
                "response": save_response,
                "duration_ms": save_duration,
            }
        )

    # Auto-close viewport (after save)
    if viewport_id is not None:
        t0 = time.time()
        close_result = await client.call_tool(
            "viewport",
            arguments={"action": "close", "viewport_id": viewport_id},
        )
        close_duration = int((time.time() - t0) * 1000)
        steps_log.append(
            {
                "tool": "viewport",
                "params": {"action": "close", "viewport_id": viewport_id},
                "isError": close_result.isError
                if hasattr(close_result, "isError")
                else False,
                "response": _get_text(close_result),
                "duration_ms": close_duration,
            }
        )

    final_path = project_root / seed_file
    final_content = final_path.read_text() if final_path.exists() else ""
    (seq_dir / "final_content.txt").write_text(final_content)

    (seq_dir / "steps.json").write_text(json.dumps(steps_log, indent=2))

    return {
        "id": seq.id,
        "category": seq.category,
        "steps_executed": len(seq.steps),
        "duration_ms": sum(s.get("duration_ms", 0) for s in steps_log),
    }


async def run_stress_test(
    density: str = "sparse",
    run_id: str | None = None,
    preserve: bool = False,
) -> Path:
    if run_id is None:
        run_id = datetime.now(timezone.utc).strftime("stress-%Y%m%dT%H%M%S")

    run_dir = Path("tmp") / "stress" / run_id
    if run_dir.exists() and not preserve:
        shutil.rmtree(run_dir)

    sequences = _collect_generators(density)
    total = len(sequences)

    print(f"Stress test run: {run_id}")
    print(f"Density: {density}")
    print(f"Sequences: {total}")
    print(f"Output: {run_dir}")
    print()

    temp_root = Path(tempfile.mkdtemp(prefix=f"ve-stress-{run_id}-"))
    server = create_server(str(temp_root))

    t_start = time.time()
    errors = 0
    summary_entries: list[dict[str, Any]] = []

    async with Client(transport=server) as raw_client:
        client = _CompatClient(raw_client)

        for i, seq in enumerate(sequences):
            seq_dir = run_dir / "sequences" / seq.id
            try:
                entry = await _run_sequence(client, seq, seq_dir, temp_root)
                summary_entries.append(entry)
                errors_text = ""
                if any(
                    s.get("isError", False)
                    for s in json.loads((seq_dir / "steps.json").read_text())
                ):
                    errors_text = " ⚠ (errors in log)"
                print(f"  [{i + 1}/{total}] {seq.id}: {seq.description}{errors_text}")
            except Exception as exc:
                errors += 1
                summary_entries.append(
                    {
                        "id": seq.id,
                        "category": seq.category,
                        "error": str(exc),
                    }
                )
                print(f"  [{i + 1}/{total}] {seq.id}: CRASHED — {exc}")

    duration = time.time() - t_start

    manifest = {
        "run_id": run_id,
        "density": density,
        "total_sequences": total,
        "errors": errors,
        "duration_seconds": round(duration, 2),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "sequences": summary_entries,
    }
    (run_dir / "manifest.json").write_text(json.dumps(manifest, indent=2))

    if not preserve:
        shutil.rmtree(temp_root, ignore_errors=True)

    print()
    print(f"Run complete in {duration:.1f}s")
    print(f"Errors: {errors}/{total}")
    print(f"Log: {run_dir}/")

    return run_dir


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Stress test runner for viewport-editor"
    )
    parser.add_argument("--density", choices=["sparse", "dense"], default="sparse")
    parser.add_argument("--run-id", type=str, default=None)
    parser.add_argument("--preserve", action="store_true", help="keep temp seed files")
    args = parser.parse_args()

    import asyncio

    asyncio.run(
        run_stress_test(
            density=args.density,
            run_id=args.run_id,
            preserve=args.preserve,
        )
    )


if __name__ == "__main__":
    main()
