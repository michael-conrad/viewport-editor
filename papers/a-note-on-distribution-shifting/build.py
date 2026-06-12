#!/usr/bin/env -S uv run --script
# fmt: off
"exec" "uv" "run" "--script" "$0" "$@" # MUST GO BEFORE PEP 723 HEADER

# PEP 723 HEADER MUST BE AFTER BASH GUARD
# /// script
# requires-python = "~=3.12"
# dependencies = []
# ///

# fmt: on
# SPDX-FileCopyrightText: 2026 Michael Conrad
# SPDX-License-Identifier: MIT
# Provenance: AI-generated
"""
Build LaTeX paper: xelatex + biber/bibtex + makeindex.

Usage: ./papers/<slug>/build.py

Requires: xelatex, biber (or bibtex), makeindex on $PATH.

Co-authored with AI: OpenCode (ollama-cloud/deepseek-v4-flash)
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path


def find_tool(name: str) -> str | None:
    return shutil.which(name)


def run(cmd: list[str], cwd: Path, label: str, env: dict[str, str] | None = None) -> None:
    print(f"[{label}] Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, env=env)
    if result.returncode != 0:
        # bibtex exit 2 = warnings (e.g., no citations found) — not fatal
        if label == "bibtex" and result.returncode == 2:
            print(f"[{label}] Warnings (exit {result.returncode}) — continuing")
        else:
            print(f"[{label}] FAILED (exit {result.returncode})", file=sys.stderr)
            print(result.stderr, file=sys.stderr)
            sys.exit(result.returncode)
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)


def main() -> None:
    script_dir = Path(__file__).resolve().parent
    src_dir = script_dir / "src"
    build_dir = script_dir / "build"
    paper_root = script_dir / "paper.pdf"

    # Guard: check required tools
    xelatex_path = find_tool("xelatex")
    if not xelatex_path:
        print("ERROR: xelatex not found on $PATH. Install TeX Live.", file=sys.stderr)
        sys.exit(1)

    biber_path = find_tool("biber")
    bibtex_path = find_tool("bibtex")
    if not biber_path and not bibtex_path:
        print("ERROR: neither biber nor bibtex found on $PATH.", file=sys.stderr)
        sys.exit(1)

    makeindex_path = find_tool("makeindex")
    if not makeindex_path:
        print("ERROR: makeindex not found on $PATH.", file=sys.stderr)
        sys.exit(1)

    use_biber = biber_path is not None
    bib_tool = "biber" if use_biber else "bibtex"
    print(f"Using bibliography tool: {bib_tool}")

    # Ensure build directory exists
    build_dir.mkdir(parents=True, exist_ok=True)

    # Step 1: xelatex (first pass — generates .aux, .idx)
    run(
        [xelatex_path, "-output-directory", str(build_dir), str(src_dir / "paper.tex")],
        cwd=script_dir,
        label="xelatex (1)",
    )

    # Step 2: bibliography (run from build/ so bibtex/biber find .aux)
    bib_env = os.environ.copy()
    bib_env["BIBINPUTS"] = str(src_dir) + ":"
    if use_biber:
        run(
            [biber_path, "paper"],
            cwd=build_dir,
            label="biber",
        )
    else:
        run(
            [bibtex_path, "paper"],
            cwd=build_dir,
            label="bibtex",
            env=bib_env,
        )

    # Step 3: makeindex (only if .idx exists, run from build/)
    idx_file = build_dir / "paper.idx"
    if idx_file.exists():
        run(
            [makeindex_path, "paper.idx"],
            cwd=build_dir,
            label="makeindex",
        )

    # Step 4: xelatex (second pass — incorporates bibliography)
    run(
        [xelatex_path, "-output-directory", str(build_dir), str(src_dir / "paper.tex")],
        cwd=script_dir,
        label="xelatex (2)",
    )

    # Step 5: xelatex (third pass — resolves cross-references)
    run(
        [xelatex_path, "-output-directory", str(build_dir), str(src_dir / "paper.tex")],
        cwd=script_dir,
        label="xelatex (3)",
    )

    # Step 6: copy final PDF to paper root
    built_pdf = build_dir / "paper.pdf"
    if not built_pdf.exists():
        print("ERROR: paper.pdf was not produced in build/", file=sys.stderr)
        sys.exit(1)

    shutil.copy2(built_pdf, paper_root)
    print(f"Copied paper.pdf to {paper_root}")


if __name__ == "__main__":
    main()
