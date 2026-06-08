#!/bin/bash
# Behavioral test: viewport-session-isolation
# See .opencode/tests/AGENTS.md for the test harness specification and paradigm.
# This script is an artifact-only generator — it does NOT evaluate model output.
#
# SC-4: N-session isolation — two viewports on same file, independent edits.
#
# Co-authored with AI: OpenCode (deepseek-v4-flash)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec bash "$SCRIPT_DIR/run-viewport-scenario.sh" "viewport-session-isolation" "$@"