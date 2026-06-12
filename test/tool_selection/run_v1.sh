#!/bin/bash
# V1 Verb-Class Runner
# Runs opencode-cli from the isolated test project (/tmp/octest) so session-init
# loads the test project's minimal .opencode/ context, NOT the main project's
# heavy approval-gate + pre-implementation pipeline configuration.
#
# Usage:
#   bash run_v1.sh                          # Full 20-trial DeepSeek gating
#   bash run_v1.sh --quick                  # 5-trial debug mode
#   bash run_v1.sh --tool read              # Single tool
#   bash run_v1.sh --variant verb           # Single variant
#   bash run_v1.sh --model deepseek         # Single model
#
# SPDX-FileCopyrightText: 2026 Michael Conrad
# SPDX-License-Identifier: MIT
# Provenance: AI-generated

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
TEST_HOME_WRAPPER="$PROJECT_DIR/.opencode/tests/with-test-home"
TEST_PROJECT="/tmp/octest"

# Timeout per model (seconds) — minimums, double on timeout
declare -A MODEL_TIMEOUTS
MODEL_TIMEOUTS["ollama/deepseek-v4-flash:cloud"]=120
MODEL_TIMEOUTS["ollama/gpt-oss:20b-128k"]=1800
MODEL_TIMEOUTS["ollama/nemotron3:33b-128k"]=1800
MODEL_TIMEOUTS["ollama/qwen3.6:35b-256k"]=1800
MODEL_TIMEOUTS["ollama/devstral-small-2:24b-384k"]=3600
MODEL_TIMEOUTS["ollama/gemma4:31b"]=3600

# Config
TRIALS=20
QUICK=0
FILTER_TOOL=""
FILTER_VARIANT=""
MODEL="ollama/deepseek-v4-flash:cloud"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --quick) QUICK=1; TRIALS=5; shift ;;
        --tool) FILTER_TOOL="$2"; shift 2 ;;
        --variant) FILTER_VARIANT="$2"; shift 2 ;;
        --model) MODEL="$2"; shift 2 ;;
        *) echo "Unknown: $1"; exit 1 ;;
    esac
done

declare -A TOOL_PROMPTS
TOOL_PROMPTS["read"]="Read src/main.py and find the BUILD_VERSION value."
TOOL_PROMPTS["write"]="Write BUILD_VERSION = 42 to tmp/output.txt using the recommended writing tool."
TOOL_PROMPTS["edit"]="Change BUILD_VERSION from 1 to 2 in src/main.py using the recommended editing tool."
TOOL_PROMPTS["find"]="Search for BUILD_VERSION across the project using the recommended search tool."
TOOL_PROMPTS["diff"]="Review pending changes by showing the diff for src/main.py."

declare -A TOOL_TOOLNAMES
TOOL_TOOLNAMES["read_verb"]="read"
TOOL_TOOLNAMES["read_verb_noun"]="read_file"
TOOL_TOOLNAMES["write_verb"]="write"
TOOL_TOOLNAMES["write_verb_noun"]="write_file"
TOOL_TOOLNAMES["edit_verb"]="edit"
TOOL_TOOLNAMES["edit_verb_noun"]="edit_text"
TOOL_TOOLNAMES["find_verb"]="find"
TOOL_TOOLNAMES["find_verb_noun"]="find_text"
TOOL_TOOLNAMES["diff_verb"]="diff"
TOOL_TOOLNAMES["diff_verb_noun"]="diff"

VARIANTS=("verb" "verb_noun")
TOOLS=("read" "write" "edit" "find" "diff")

[ -n "$FILTER_TOOL" ] && TOOLS=("$FILTER_TOOL")
[ -n "$FILTER_VARIANT" ] && VARIANTS=("$FILTER_VARIANT")

OUTPUT_DIR="${TOOL_SELECTION_OUTPUT:-$PROJECT_DIR/tmp/v1-results-$(date +%Y%m%d-%H%M%S)}"
mkdir -p "$OUTPUT_DIR"

# Per-trial timeout in ms = model timeout + 30s buffer
TIMEOUT_MS=$(( (${MODEL_TIMEOUTS[$MODEL]:-120} + 30) * 1000 ))

echo "=== V1 Verb-Class Testing ==="
echo "Model: $MODEL"
echo "Trials per variant: $TRIALS"
echo "Per-trial timeout: $((TIMEOUT_MS / 1000))s"
echo "Output: $OUTPUT_DIR"
echo ""

OVERALL_RESULT=0

run_trial() {
    local variant_id="$1"
    local tool_type="$2"
    local trial_num="$3"
    local workdir="$4"

    local run_id
    run_id=$(date +%s)$RANDOM
    local fixture_value="v3.${run_id}"

    # Ensure fixtures exist in test project
    cat > "$TEST_PROJECT/src/main.py" << FIXEOF
BUILD_VERSION = 1
CONFIG_ID = "${run_id}"
FIXEOF
    chmod -R +r "$TEST_PROJECT/src" "$TEST_PROJECT/tmp"

    local tool_name="${TOOL_TOOLNAMES[${tool_type}_${variant_id}]}"
    local prompt="${TOOL_PROMPTS[$tool_type]}"

    # Build inline config content
    config_content=$(cat << 'JSONEOF'
{
  "$schema": "https://opencode.ai/config.json",
  "provider": {
    "ollama": {
      "options": { "baseURL": "http://localhost:11434/v1", "chunkTimeout": 300000 },
      "models": { "$MODEL_PLACEHOLDER": {} }
    }
  },
  "mcp": {
    "viewport-editor": {
      "type": "local",
      "command": ["uv", "run", "--directory", "$PROJECT_DIR_PLACEHOLDER", "python3", "-m", "test.tool_selection.test_server", "$VARIANT_PLACEHOLDER", "$TEST_PROJECT_PLACEHOLDER"],
      "enabled": true
    },
    "srclight": { "enabled": false },
    "the-notebook-mcp": { "enabled": false }
  }
}
JSONEOF
)
    config_content="${config_content/\$MODEL_PLACEHOLDER/$MODEL}"
    config_content="${config_content/\$PROJECT_DIR_PLACEHOLDER/$PROJECT_DIR}"
    config_content="${config_content/\$VARIANT_PLACEHOLDER/$variant_id}"
    config_content="${config_content/\$TEST_PROJECT_PLACEHOLDER/$TEST_PROJECT}"

    # Setup isolated test home
    local test_home
    test_home=$("$TEST_HOME_WRAPPER" --setup "$PROJECT_DIR" 2>/dev/null | grep '^TEST_HOME=' | cut -d= -f2-)
    if [ -z "$test_home" ]; then
        echo "FATAL: --setup failed"
        return
    fi

    # Run opencode-cli FROM the test project directory so project detection
    # finds /tmp/octest/.opencode/ (minimal context, no pipeline gates, AGENTS.md
    # with tool selection mandates) instead of the main project's heavy config.
    cd "$TEST_PROJECT"
    HOME="$test_home" \
    XDG_CONFIG_HOME="$test_home/.config" \
    XDG_CACHE_HOME="$test_home/.cache" \
    XDG_RUNTIME_DIR="$test_home/.runtime" \
    XDG_DATA_HOME="$test_home/.local/share" \
    XDG_STATE_HOME="$test_home/.local/state" \
    OPENCODE_CONFIG_CONTENT="$config_content" \
        opencode-cli run "$prompt" --model "$MODEL" --log-level INFO --print-logs \
            --thinking --variant minimal --pure \
            2>"$workdir/stderr.log" >"$workdir/stdout.log" || true
    cd "$PROJECT_DIR"

    # Detect which tool was dispatched from stderr.
    # Check ALL dispatches — the agent may read first, then perform the intended action.
    local stderr_file="$workdir/stderr.log"
    if [ ! -f "$stderr_file" ]; then
        echo "UNKNOWN"
        return
    fi

    local all_tool_calls
    all_tool_calls=$(grep '⚙.*viewport-editor_' "$stderr_file" 2>/dev/null || true)

    if [ -z "$all_tool_calls" ]; then
        echo "UNKNOWN"
        return
    fi

    # Check if the CORRECT tool was dispatched in any call.
    # Use word boundary (\b) to avoid "read" matching "read_file".
    if echo "$all_tool_calls" | grep -q "viewport-editor_${tool_name}\b"; then
        echo "CUSTOM_CORRECT"
    elif echo "$all_tool_calls" | grep -qE 'viewport-editor_(read|write|edit|find|diff|read_file|write_file|edit_text|find_text)'; then
        local first_wrong
        first_wrong=$(echo "$all_tool_calls" | grep -o 'viewport-editor_[a-z_]*' | head -1)
        echo "CUSTOM_WRONG:${first_wrong#viewport-editor_}"
    else
        local other_name
        other_name=$(echo "$all_tool_calls" | grep -o 'viewport-editor_[a-z_]*' | head -1)
        echo "CUSTOM_OTHER:${other_name#viewport-editor_}"
    fi
}

echo "variant_id,tool_type,trial_num,result,expected_tool" > "$OUTPUT_DIR/results.csv"

for variant_id in "${VARIANTS[@]}"; do
    for tool_type in "${TOOLS[@]}"; do
        local_tool_name="${TOOL_TOOLNAMES[${tool_type}_${variant_id}]}"
        echo "=== Variant: $variant_id | Tool: $tool_type (name: $local_tool_name) ==="

        variant_dir="$OUTPUT_DIR/${variant_id}/${tool_type}"
        mkdir -p "$variant_dir"

        for trial_num in $(seq 1 "$TRIALS"); do
            trial_dir=$(mktemp -d "$variant_dir/trial-${trial_num}-XXXXXX")
            result=$(run_trial "$variant_id" "$tool_type" "$trial_num" "$trial_dir")
            echo "$variant_id,$tool_type,$trial_num,$result,$local_tool_name" >> "$OUTPUT_DIR/results.csv"
            printf "  Trial %2d/%d: %s\n" "$trial_num" "$TRIALS" "$result"
        done
        echo ""
    done
done

echo ""
echo "=== Summary ==="
python3 -c "
import csv, sys, os
from collections import defaultdict

filepath = '$OUTPUT_DIR/results.csv'
if not os.path.exists(filepath):
    print('No results found')
    sys.exit(0)

data = defaultdict(dict)
ordered = []
with open(filepath) as f:
    reader = csv.DictReader(f)
    for row in reader:
        key = (row['variant_id'], row['tool_type'])
        if key not in data:
            data[key] = defaultdict(int)
            ordered.append(key)
        data[key][row['result']] += 1

for vid, tt in ordered:
    counts = data[(vid, tt)]
    total = sum(counts.values())
    cc = counts.get('CUSTOM_CORRECT', 0)
    cw = sum(v for k, v in counts.items() if k.startswith('CUSTOM_WRONG'))
    co = sum(v for k, v in counts.items() if k.startswith('CUSTOM_OTHER'))
    bi = counts.get('BUILTIN', 0)
    unk = counts.get('UNKNOWN', 0)
    sc = counts.get('SRCLIGHT', 0)
    pct = round(100 * cc / total, 1) if total > 0 else 0
    marker = 'PASS' if pct >= 80 else 'FAIL'
    print(f'{vid:15s} {tt:10s} correct={cc}/{total} ({pct}%) wrong={cw} other={co} builtin={bi} unk={unk} srclight={sc} [{marker}]')
" 2>/dev/null || echo "Summary error"

echo ""
echo "Results: $OUTPUT_DIR/results.csv"