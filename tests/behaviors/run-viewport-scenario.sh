#!/bin/bash
# run-viewport-scenario.sh — Shared harness runner for viewport-editor behavioral tests.
#
# Creates an isolated test project with fixtures, runs opencode-cli from that
# project's root directory. The main repo is NEVER the agent's CWD.
# The MCP server is started via `uv run --project <main-repo>` so the agent
# can use viewport-editor tools, but all file operations are scoped to the
# test project directory.
#
# Usage:
#   bash tests/behaviors/run-viewport-scenario.sh <scenario-name> [model]
#
# Environment:
#   BEHAVIOR_MODEL  — model to use (default: ollama/deepseek-v4-flash:cloud)
#   BEHAVIOR_PHASE  — RED or GREEN (default: GREEN)
#
# Artifacts:
#   ./tmp/behavioral-evidence-<name>-<phase>-<model-slug>/
#
# Co-authored with AI: OpenCode (deepseek-v4-flash)

set -euo pipefail

if [ $# -lt 1 ]; then
    echo "Usage: $0 <scenario-name> [model]" >&2
    exit 1
fi

SCENARIO_NAME="$1"
MODEL="${2:-${BEHAVIOR_MODEL:-ollama/deepseek-v4-flash:cloud}}"
PHASE="${BEHAVIOR_PHASE:-GREEN}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MAIN_REPO="$(cd "$SCRIPT_DIR/../.." && pwd)"

CARD_FILE="$SCRIPT_DIR/$SCENARIO_NAME.card.md"
if [ ! -f "$CARD_FILE" ]; then
    echo "Error: card file not found: $CARD_FILE" >&2
    exit 1
fi

FIXTURES_SRC="$MAIN_REPO/tests/fixtures/ebooks"
TMP_DIR="$MAIN_REPO/tmp"

# Step 1: Create isolated test project directory
TEST_PROJECT="$TMP_DIR/test-project-$(date +%Y%m%d-%H%M%S)-$$"
mkdir -p "$TEST_PROJECT"

# Initialize minimal git repo (needed by approval-gate and session init)
git init -q "$TEST_PROJECT"
git -C "$TEST_PROJECT" config user.email "test@test.dev"
git -C "$TEST_PROJECT" config user.name "Test Agent"
git -C "$TEST_PROJECT" commit -q --allow-empty -m "init"

# Step 2: Create XDG home (inside test project tmp to keep everything isolated)
TEST_HOME="$TEST_PROJECT/.xdg-home"
mkdir -p "$TEST_HOME/.config/opencode" "$TEST_HOME/.cache" "$TEST_HOME/.local/share" "$TEST_HOME/.local/state"

# Step 3: Decompress fixtures into test project root
for gz in "$FIXTURES_SRC"/*.txt.gz "$FIXTURES_SRC"/*.yaml.gz "$FIXTURES_SRC"/*.py.gz "$FIXTURES_SRC"/*.md.gz; do
    [ -f "$gz" ] || continue
    base="$(basename "$gz" .gz)"
    gunzip -c "$gz" > "$TEST_PROJECT/$base"
done

# Step 4: Create .issues/ with spec inside the test project
mkdir -p "$TEST_PROJECT/.issues/$SCENARIO_NAME"
cp "$CARD_FILE" "$TEST_PROJECT/.issues/$SCENARIO_NAME/spec.md"

# .issues/ needs its own git commit for the approval-gate to find it
git -C "$TEST_PROJECT" add -A
git -C "$TEST_PROJECT" commit -q --allow-empty -m "add fixtures and spec"

# Step 5: Build config with models + MCP server
# Provider config needed so opencode-cli can resolve the model.
# MCP server points at main repo via --project.
MODEL_JSON=$(python3 << PYEOF
import json, subprocess
models = {}
try:
    result = subprocess.run(['ollama', 'list'], capture_output=True, text=True, timeout=15)
    for line in result.stdout.strip().split('\n')[1:]:
        parts = line.split()
        if parts:
            name = parts[0]
            if 'embed' not in name.lower() and 'nomic' not in name.lower() and 'mxbai' not in name.lower() and 'e5' not in name.lower():
                models[name] = {}
except Exception:
    pass
if not models:
    models = {"deepseek-v4-flash:cloud": {}}
print(json.dumps(models))
PYEOF
)

OPENCODE_CONFIG_CONTENT=$(python3 << PYEOF
import json
cfg = {
    "\$schema": "https://opencode.ai/config.json",
    "provider": {
        "ollama": {
            "options": {"baseURL": "http://localhost:11434/v1"},
            "models": json.loads('''$MODEL_JSON''')
        }
    },
    "mcp": {
        "viewport-editor": {
            "type": "local",
            "command": ["uv", "run", "--project", "$MAIN_REPO", "viewport-editor"]
        }
    }
}
print(json.dumps(cfg))
PYEOF
)

# Step 6: Create artifact directory inside test project
MODEL_SLUG=$(echo "$MODEL" | tr '/:@' '-')
ARTIFACT_DIR="$TEST_PROJECT/behavioral-evidence-$SCENARIO_NAME-$PHASE-$MODEL_SLUG"
mkdir -p "$ARTIFACT_DIR"

# Copy card to artifact directory for evaluation reference
cp "$CARD_FILE" "$ARTIFACT_DIR/card.md"

# Step 7: Run opencode-cli from within the isolated test project
SPEC_PATH=".issues/$SCENARIO_NAME/spec.md"
PROMPT="Enter pair mode. We need to apply the instructions from the spec $SPEC_PATH so that I can review them. You are authorized to perform the instructions in the spec. This is not a 14 point pipeline implementation. This is only so I can review if the card has the correct instructions by looking at the results of the instructions being applied."

cd "$TEST_PROJECT"

env -i \
    HOME="$TEST_HOME" \
    XDG_CONFIG_HOME="$TEST_HOME/.config" \
    XDG_CACHE_HOME="$TEST_HOME/.cache" \
    XDG_DATA_HOME="$TEST_HOME/.local/share" \
    XDG_STATE_HOME="$TEST_HOME/.local/state" \
    OPENCODE_CONFIG_CONTENT="$OPENCODE_CONFIG_CONTENT" \
    PATH="$PATH" \
    SHELL="${SHELL:-/bin/bash}" \
    USER="${USER:-$(id -un)}" \
    LANG="${LANG:-en_US.UTF-8}" \
    TERM="${TERM:-xterm-256color}" \
    opencode-cli run "$PROMPT" --model "$MODEL" --log-level INFO --print-logs \
    > "$ARTIFACT_DIR/stdout.log" \
    2> "$ARTIFACT_DIR/stderr.log"

EXIT_CODE=$?

# Step 8: Write metadata
echo "$EXIT_CODE" > "$ARTIFACT_DIR/exit_code"

cat > "$ARTIFACT_DIR/manifest.yaml" << EOF
scenario_name: $SCENARIO_NAME
phase: $PHASE
model: $MODEL
timestamp: $(date -u +%Y-%m-%dT%H:%M:%SZ)
exit_code: $EXIT_CODE
harness_version: 1
EOF

# Step 9: Preserve artifacts by copying to main repo tmp/ (only external reference after test completes)
PERSISTENT_DIR="$MAIN_REPO/tmp/behavioral-evidence-$SCENARIO_NAME-$PHASE-$MODEL_SLUG"
mkdir -p "$PERSISTENT_DIR"
cp -r "$ARTIFACT_DIR"/* "$PERSISTENT_DIR/"

# Cleanup — remove test project
rm -rf "$TEST_PROJECT"

echo "Artifacts: $PERSISTENT_DIR"
exit 0