#!/bin/bash
# Tool selection prompt test runner — artifact-only generator
# Runs N trials per tool-naming variant, collects dispatch evidence from stderr.
# See .opencode/tests/AGENTS.md for the test harness specification and paradigm.
#
# SPDX-FileCopyrightText: 2026 Michael Conrad
# SPDX-License-Identifier: MIT
# Provenance: AI-generated
#
# TIMEOUT MANDATE (MANDATORY — Tier 1):
# Always increase bash tool timeouts as needed, especially for local models.
# See test/tool_selection/AGENTS.md for per-model minimum timeout values.
# A timeout is NOT a model failure — it is a harness configuration error.
# If a model timeout occurs, double the timeout and retry. Do not skip.

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
TEST_HOME_WRAPPER="$PROJECT_DIR/.opencode/tests/with-test-home"

TRIALS="${TOOL_SELECTION_TRIALS:-20}"
MODEL="${TOOL_SELECTION_MODEL:-ollama/deepseek-v4-flash:cloud}"
# Model set: the 6 validation models for this testing phase.
# Set TOOL_SELECTION_MODEL to one of these to run against a specific model.
# Full set: deepseek-v4-flash:cloud (primary), devstral-small-2:24b-384k, gemma4:31b-256k,
#           gpt-oss:20b-128k, nemotron3:33b-128k, qwen3.6:35b-256k
OUTPUT_DIR="${TOOL_SELECTION_OUTPUT:-$PROJECT_DIR/tmp/tool-selection-results-$(date +%Y%m%d-%H%M%S)}"

RUN_VARIANT="${1:-}"
PROMPT_FILE="${2:-$SCRIPT_DIR/prompts/read_file_prompt.txt}"

mkdir -p "$OUTPUT_DIR"

if [ ! -f "$PROMPT_FILE" ]; then
    mkdir -p "$(dirname "$PROMPT_FILE")"
    cat > "$PROMPT_FILE" << 'PROMPTEOF'
Read src/main.py and find the create_server function definition.
PROMPTEOF
fi
PROMPT="$(cat "$PROMPT_FILE")"

echo "=== Tool Selection Prompt Testing ==="
echo "Model: $MODEL"
echo "Trials per variant: $TRIALS"
echo "Output: $OUTPUT_DIR"
echo "Prompt: $PROMPT"
echo ""

# Collect list of all (variable_name, variant_id) pairs
PAIRS=()
for var_file in "$SCRIPT_DIR/variants"/*.json; do
    var_name="$(basename "$var_file" .json)"
    python3 -c "
import json, sys
with open('$var_file') as f:
    data = json.load(f)
for v in data['variants']:
    print(f'{data[\"variable\"]}|{v[\"id\"]}|{v[\"tool_name\"]}')
" 2>/dev/null | while IFS='|' read -r variable vid tname; do
        echo "$variable|$vid|$tname"
    done
done > "$OUTPUT_DIR/.pairlist"

# Register the pairlist outside the subshell
PAIRFILE="$OUTPUT_DIR/.pairlist"

run_trial() {
    local variant_id="$1"
    local trial_num="$2"
    local workdir="$3"

    # Create fixture at a predictable path under PROJECT_DIR so opencode can find it.
    # Use unique random value so model cannot answer from training data.
    local run_id
    run_id=$(date +%s)$RANDOM
    local fixture_value="v3.${run_id}"
    local fixture_relpath="tmp/test-fixture-${variant_id}-trial-${trial_num}.py"
    local fixture_abspath="$PROJECT_DIR/$fixture_relpath"
    mkdir -p "$(dirname "$fixture_abspath")"
    cat > "$fixture_abspath" << FIXTUREEOF
BUILD_VERSION = "${fixture_value}"
BUILD_DATE = "2026-06-09"
CONFIG_ID = "${run_id}"
FIXTUREEOF

    # Per-trial prompt referencing the fixture
    local trial_prompt="Read ${fixture_relpath} and find the BUILD_VERSION value. Use a file reading tool."

    # Build inline config via OPENCODE_CONFIG_CONTENT (position 6)
    local config_content
    config_content=$(cat << 'JSONEOF'
{
  "$schema": "https://opencode.ai/config.json",
  "provider": {
    "ollama": {
      "options": { "baseURL": "http://localhost:11434/v1" },
      "models": { "$MODEL_PLACEHOLDER": {} }
    }
  },
  "mcp": {
    "viewport-editor": {
      "type": "local",
      "command": ["uv", "run", "--directory", "$PROJECT_DIR_PLACEHOLDER", "python3", "-m", "test.tool_selection.test_server", "$VARIANT_PLACEHOLDER"],
      "enabled": true
    },
    "srclight": { "enabled": false },
    "the-notebook-mcp": { "enabled": false }
  },
  "tools": {
    "read": true,
    "write": true,
    "edit": true,
    "grep": true,
    "glob": true
  }
}
JSONEOF
)
    config_content="${config_content/\$MODEL_PLACEHOLDER/$MODEL}"
    config_content="${config_content/\$PROJECT_DIR_PLACEHOLDER/$PROJECT_DIR}"
    config_content="${config_content/\$VARIANT_PLACEHOLDER/$variant_id}"

    # Create test home and run opencode-cli directly so OPENCODE_CONFIG_CONTENT survives
    local test_home
    test_home=$("$TEST_HOME_WRAPPER" --setup "$PROJECT_DIR" 2>/dev/null | grep '^TEST_HOME=' | cut -d= -f2-)
    if [ -z "$test_home" ]; then
        echo "FATAL: --setup failed"
        rm -f "$fixture_abspath"
        echo "unknown"
        return
    fi

    cd "$PROJECT_DIR"
    HOME="$test_home" \
    XDG_CONFIG_HOME="$test_home/.config" \
    XDG_CACHE_HOME="$test_home/.cache" \
    XDG_RUNTIME_DIR="$test_home/.runtime" \
    XDG_DATA_HOME="$test_home/.local/share" \
    XDG_STATE_HOME="$test_home/.local/state" \
    OPENCODE_CONFIG_CONTENT="$config_content" \
    opencode-cli run "$trial_prompt" --model "$MODEL" --log-level INFO --print-logs \
        --thinking --variant minimal \
        2>"$workdir/stderr.log" >"$workdir/stdout.log" || true

    # Export session DB reasoning trace to artifact directory
    local session_db="$test_home/.local/share/opencode/opencode.db"
    if [ -f "$session_db" ]; then
        python3 -c "
import json, os, sqlite3
from pathlib import Path
db_path = '$session_db'
artifact_dir = '$workdir'
try:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    # Get the latest session's message IDs to scope the export
    cursor.execute('SELECT id FROM session ORDER BY time_created DESC LIMIT 1')
    session_row = cursor.fetchone()
    if session_row:
        sid = session_row['id']
        # Export parts for this session
        cursor.execute('SELECT * FROM part WHERE session_id = ?', (sid,))
        rows = [dict(row) for row in cursor.fetchall()]
        if rows:
            with open(os.path.join(artifact_dir, 'session.json'), 'w') as f:
                json.dump({'parts': rows}, f, indent=2, default=str)
            # Extract reasoning text from data JSON field
            reasoning_texts = []
            for r in rows:
                d = r.get('data', {})
                if isinstance(d, str):
                    try: d = json.loads(d)
                    except: pass
                if isinstance(d, dict) and d.get('type') == 'reasoning':
                    reasoning_texts.append(d.get('text', ''))
            if reasoning_texts:
                with open(os.path.join(artifact_dir, 'reasoning.txt'), 'w') as f:
                    f.write('\n\n---\n\n'.join(reasoning_texts))
        conn.close()
except Exception as e:
    pass
" 2>/dev/null || true
    fi

    # Detect which tool was selected from stderr.
    # Only count as "selected custom tool" if the model actually dispatched
    # a call to the viewport-editor tool (⚙ viewport-editor_<tool_name> {...}).
    # MCP server registration log lines ("type=local found") do NOT count.
    local stderr_file="$workdir/stderr.log"
    if [ ! -f "$stderr_file" ]; then
        echo "unknown"
        return
    fi

    # Extract actual tool dispatch lines (⚙ prefix = tool call executed)
    local tool_call
    tool_call=$(grep '⚙.*viewport-editor_' "$stderr_file" 2>/dev/null | grep -o 'viewport-editor_[a-z_]*' | head -1 || true)

    if [ -n "$tool_call" ]; then
        # Strip viewport-editor_ prefix
        local tool_name="${tool_call#viewport-editor_}"
        echo "$tool_name"
    elif grep -q 'srclight_codebase_map\|srclight_.*CallTool' "$stderr_file" 2>/dev/null; then
        echo "srclight"
    else
        echo "unknown"
    fi
}

# Main loop — read from pairfile without pipe (avoid subshell termination)
exec 3<"$PAIRFILE"
echo "variant_id tool_selected trial trial_of" > "$OUTPUT_DIR/.raw_results.csv"

while IFS='|' read -r variable_name variant_id tool_name <&3; do
    if [ -n "$RUN_VARIANT" ] && [ "$variant_id" != "$RUN_VARIANT" ]; then
        continue
    fi

    echo "=== Variable: $variable_name | Variant: $variant_id (tool: $tool_name) ==="

    variant_dir="$OUTPUT_DIR/${variable_name}/${variant_id}"
    mkdir -p "$variant_dir"

    for trial_num in $(seq 1 "$TRIALS"); do
        trial_dir=$(mktemp -d "$variant_dir/trial-${trial_num}-XXXXXX")
        selected=$(run_trial "$variant_id" "$trial_num" "$trial_dir")

        # Log trial result
        is_custom=0
        [ "$selected" != "builtin_read" ] && [ "$selected" != "unknown" ] && is_custom=1

        echo "$variant_id,$selected,$trial_num,$TRIALS" >> "$OUTPUT_DIR/.raw_results.csv"
        printf "  Trial %2d/%d: selected=%-15s (custom=%d)\n" "$trial_num" "$TRIALS" "$selected" "$is_custom"
    done

    echo ""
done

# Generate report
echo "=== Summary ==="
echo ""
python3 "$SCRIPT_DIR/report_results.py" "$OUTPUT_DIR" 2>/dev/null || {
    echo "=== Quick summary from raw data ==="
    echo ""
    sort -t',' -k1,1 "$OUTPUT_DIR/.raw_results.csv" 2>/dev/null | \
        awk -F',' '{counts[$1","$2]++; total[$1]++} END {for (k in counts) print k","counts[k]","total[k]}'
}

echo ""
echo "Report saved to: $OUTPUT_DIR"