#!/bin/bash
# Verification test for #41: pyright resolves mcp.server.fastmcp after adding venv config
# SC-1: uvx pyright src/ exits with 0 errors (no pre-existing noise)

set -euo pipefail

OUTPUT=$(uvx pyright src/ 2>&1 || true)
ERROR_COUNT=$(echo "$OUTPUT" | grep -c " - error:" || true)

echo "pyright error count: $ERROR_COUNT"
echo "$OUTPUT"

if [ "$ERROR_COUNT" -eq 0 ]; then
    echo "PASS: pyright reports 0 errors — fix verified"
else
    echo "FAIL: expected 0 errors, got $ERROR_COUNT"
    exit 1
fi
