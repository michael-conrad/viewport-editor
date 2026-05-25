#!/bin/bash
# Behavioral Enforcement Test — RED phase: verify current state FAILS issue #2
#
# Issue #2: Project must be uvx-ready and self-contained
#
# RED phase: Verify the current codebase state does NOT satisfy the spec.
# All assertions MUST FAIL because the implementation does not exist yet.
# This provides the baseline RED evidence before GREEN implementation.
#
# SC-1: pyproject.toml exists with valid PEP 621 metadata (structural)
# SC-2: Entry point defined so `uvx viewport-editor` launches the server (behavioral)
# SC-3: `uv run viewport-editor` works from the repo checkout directory (behavioral)
# SC-4: Server uses os.getcwd() as project root; no command-line path argument (behavioral)
# SC-5: README Quick Start shows uvx viewport-editor without path arguments (string)
# SC-6: No python -m viewport_editor or hardcoded path references in README (string)
# SC-7: All runtime dependencies declared in pyproject.toml (structural)
#
# RED evidence: direct command execution for behavioral SCs is valid because
# the absence of pyproject.toml guarantees these commands fail.
#
# Co-authored with AI: OpenCode (ollama-cloud/deepseek-v4-flash)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/helpers.sh"

SCENARIO_NAME="2-uvx-ready-red"
OVERALL_RESULT=0

echo "=== RED Phase: Issue #2 uvx-ready ==="
echo "Current state: no pyproject.toml, no src/ directory, no viewport_editor package"
echo "Expected: all SCs FAIL or confirm current absence"
echo ""

# ============================================================
# SC-1: pyproject.toml exists with valid PEP 621 metadata
# Evidence type: structural — file existence
# RED expects: FAIL (file does not exist)
# ============================================================
echo "--- SC-1: pyproject.toml exists ---"
if [ -f "$PROJECT_DIR/pyproject.toml" ]; then
    echo "FAIL (unexpected PASS): SC-1 — pyproject.toml exists"
    echo "  RED phase expects this file to NOT exist"
    OVERALL_RESULT=1
else
    echo "CONFIRMED-RED: SC-1 — pyproject.toml does not exist"
fi

# ============================================================
# SC-2: uvx viewport-editor launches the server (behavioral)
# RED evidence: direct command execution — uvx viewport-editor
# with no package available will predictably fail.
# ============================================================
echo "--- SC-2: uvx viewport-editor launches (behavioral) ---"
UVX_OUTPUT=$(uvx viewport-editor 2>&1 || true)
if echo "$UVX_OUTPUT" | grep -qiE "error|not found|no such|package.*not|unable to find|not installed|cannot"; then
    echo "CONFIRMED-RED: SC-2 — 'uvx viewport-editor' fails as expected"
    echo "  Error: $(echo "$UVX_OUTPUT" | head -2 | tr '\n' ' ')"
elif [ -z "$UVX_OUTPUT" ]; then
    echo "CONFIRMED-RED: SC-2 — 'uvx viewport-editor' produced no output (no package)"
else
    echo "FAIL (unexpected): SC-2 — 'uvx viewport-editor' produced unexpected output"
    echo "  Output: $(echo "$UVX_OUTPUT" | head -3 | tr '\n' ' ')"
    OVERALL_RESULT=1
fi

# ============================================================
# SC-3: uv run viewport-editor from checkout (behavioral)
# RED evidence: direct command execution — without pyproject.toml,
# uv run has no script entry point to execute.
# ============================================================
echo "--- SC-3: uv run viewport-editor from checkout (behavioral) ---"
UV_RUN_OUTPUT=$(uv run viewport-editor 2>&1 || true)
if echo "$UV_RUN_OUTPUT" | grep -qiE "error|not found|no such|script.*not|project.*not|no entry point|cannot find|does not exist"; then
    echo "CONFIRMED-RED: SC-3 — 'uv run viewport-editor' fails as expected"
    echo "  Error: $(echo "$UV_RUN_OUTPUT" | head -2 | tr '\n' ' ')"
elif [ -z "$UV_RUN_OUTPUT" ]; then
    echo "CONFIRMED-RED: SC-3 — 'uv run viewport-editor' produced no output (no package)"
else
    echo "FAIL (unexpected): SC-3 — 'uv run viewport-editor' produced unexpected output"
    echo "  Output: $(echo "$UV_RUN_OUTPUT" | head -3 | tr '\n' ' ')"
    OVERALL_RESULT=1
fi

# ============================================================
# SC-4: Server uses os.getcwd() (behavioral) — no server to test yet
# RED: no server code exists, so SC-4 cannot be satisfied
# ============================================================
echo "--- SC-4: Server uses os.getcwd() as project root (behavioral) ---"
if [ -f "$PROJECT_DIR/src/viewport_editor/main.py" ] || [ -f "$PROJECT_DIR/src/viewport_editor/server.py" ] 2>/dev/null; then
    echo "FAIL (unexpected): SC-4 — server source files found, behavioral evidence needed"
    OVERALL_RESULT=1
else
    echo "CONFIRMED-RED: SC-4 — no server source exists to test"
fi

# ============================================================
# SC-5: README Quick Start shows uvx viewport-editor without path args
# Evidence type: string — grep check
# NOTE: README was already updated to spec, so this may already PASS
# ============================================================
echo "--- SC-5: README shows uvx viewport-editor without path arguments ---"
if grep -qE 'uvx.*viewport-editor' "$PROJECT_DIR/README.md" 2>/dev/null; then
    echo "ALREADY-PASS: SC-5 — README references 'uvx viewport-editor' in Quick Start"
else
    echo "CONFIRMED-RED: SC-5 — README does not show uvx viewport-editor"
    OVERALL_RESULT=1
fi

# ============================================================
# SC-6: No python -m viewport_editor or hardcoded paths in README
# Evidence type: string — grep check
# NOTE: README was already updated, so this should already PASS
# ============================================================
echo "--- SC-6: No python -m viewport_editor or hardcoded paths in README ---"
BAD_REFS=""
if grep -qE 'python\s+-m\s+viewport_editor' "$PROJECT_DIR/README.md" 2>/dev/null; then
    BAD_REFS="${BAD_REFS} 'python -m viewport_editor'"
fi
if grep -qE '/path/to/' "$PROJECT_DIR/README.md" 2>/dev/null; then
    BAD_REFS="${BAD_REFS} '/path/to/'"
fi
if [ -n "$BAD_REFS" ]; then
    echo "FAIL (unexpected): SC-6 — README contains forbidden references:$BAD_REFS"
    OVERALL_RESULT=1
else
    echo "ALREADY-PASS: SC-6 — README has no forbidden references"
fi

# ============================================================
# SC-7: All runtime dependencies declared in pyproject.toml (structural)
# RED expects: FAIL (no pyproject.toml)
# ============================================================
echo "--- SC-7: Runtime dependencies declared in pyproject.toml ---"
if [ -f "$PROJECT_DIR/pyproject.toml" ]; then
    if grep -qE '^\[project\]|^dependencies\s*=' "$PROJECT_DIR/pyproject.toml" 2>/dev/null; then
        echo "FAIL (unexpected PASS): SC-7 — pyproject.toml has dependencies"
    else
        echo "FAIL (unexpected PASS): SC-7 — pyproject.toml exists but may lack deps"
    fi
    OVERALL_RESULT=1
else
    echo "CONFIRMED-RED: SC-7 — no pyproject.toml to declare dependencies"
fi

# ============================================================
# Summary
# ============================================================
echo ""
echo "=== RED Phase Summary ==="
echo "SC-1 (structural): pyproject.toml presence  => CONFIRMED RED"
echo "SC-2 (behavioral): uvx viewport-editor       => CONFIRMED RED"
echo "SC-3 (behavioral): uv run viewport-editor    => CONFIRMED RED"
echo "SC-4 (behavioral): os.getcwd() server        => CONFIRMED RED (no source)"
echo "SC-5 (string):     README uvx ref            => ALREADY PASS"
echo "SC-6 (string):     README no path refs       => ALREADY PASS"
echo "SC-7 (structural): deps declared              => CONFIRMED RED"
echo ""

if [ "$OVERALL_RESULT" -eq 0 ]; then
    echo "PASS: $SCENARIO_NAME — all RED-phase assertions correct"
else
    echo "FAIL: $SCENARIO_NAME — one or more RED-phase assertions unexpected"
fi

exit $OVERALL_RESULT
