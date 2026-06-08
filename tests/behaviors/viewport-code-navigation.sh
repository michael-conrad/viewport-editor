#!/bin/bash
# Behavioral test: viewport-code-navigation
# See .opencode/tests/AGENTS.md for the test harness specification and paradigm.
# This script is an artifact-only generator — it does NOT evaluate model output.
#
# SC-9: Code navigation workflow — jump to class, function, symbol, edit, save.
#
# Co-authored with AI: OpenCode (deepseek-v4-flash)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec bash "$SCRIPT_DIR/run-viewport-scenario.sh" "viewport-code-navigation" "$@"