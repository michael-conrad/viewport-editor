#!/bin/bash
# V3 Comparison Framing Runner
# Tests bare vs positive differentiation vs negative comparison descriptions.
# Uses verb_noun naming + elaborated descriptions (locked from V1/V2).
# 
# Usage:
#   bash run_v3.sh                          # Full run
#   bash run_v3.sh --quick                  # 5-trial debug mode
#   bash run_v3.sh --tool read_file         # Single tool
#   bash run_v3.sh --variant bare           # Single variant
#   bash run_v3.sh --model deepseek         # Single model
#
# SPDX-FileCopyrightText: 2026 Michael Conrad
# SPDX-License-Identifier: MIT
# Provenance: AI-generated

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
TEST_HOME_WRAPPER="$PROJECT_DIR/.opencode/tests/with-test-home"
TEST_PROJECT="/tmp/octest"

declare -A MODEL_TIMEOUTS
MODEL_TIMEOUTS["ollama/deepseek-v4-flash:cloud"]=120

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
TOOL_PROMPTS["read_file"]="Read src/main.py and find the BUILD_VERSION value."
TOOL_PROMPTS["write_file"]="Write BUILD_VERSION = 42 to tmp/output.txt using the recommended writing tool."
TOOL_PROMPTS["edit_text"]="Change BUILD_VERSION from 1 to 2 in src/main.py using the recommended editing tool."
TOOL_PROMPTS["find_text"]="Search for BUILD_VERSION across the project using the recommended search tool."
TOOL_PROMPTS["diff"]="Review pending changes by showing the diff for src/main.py."

declare -A TOOL_NAMES
TOOL_NAMES["read_file"]="read_file"
TOOL_NAMES["write_file"]="write_file"
TOOL_NAMES["edit_text"]="edit_text"
TOOL_NAMES["find_text"]="find_text"
TOOL_NAMES["diff"]="diff"

ALL_TOOLS=("read_file" "write_file" "edit_text" "find_text" "diff")
[ -n "$FILTER_TOOL" ] && ALL_TOOLS=("$FILTER_TOOL")

VARIANTS=("bare" "positive" "negative")
[ -n "$FILTER_VARIANT" ] && VARIANTS=("$FILTER_VARIANT")

OUTPUT_DIR="${TOOL_SELECTION_OUTPUT:-$PROJECT_DIR/tmp/v3-results-$(date +%Y%m%d-%H%M%S)}"
mkdir -p "$OUTPUT_DIR"
TIMEOUT_MS=$(( (${MODEL_TIMEOUTS[$MODEL]:-120} + 30) * 1000 ))

echo "=== V3 Comparison Framing Testing ==="
echo "Model: $MODEL"
echo "Trials per variant: $TRIALS"
echo "Output: $OUTPUT_DIR"
echo ""

run_trial() {
    local variant_id="$1"
    local tool_type="$2"
    local trial_num="$3"
    local workdir="$4"
    local run_id=$(date +%s)$RANDOM

    cat > "$TEST_PROJECT/src/main.py" << FIXEOF
BUILD_VERSION = 1
CONFIG_ID = "${run_id}"
FIXEOF
    chmod -R +r "$TEST_PROJECT/src" "$TEST_PROJECT/tmp"

    local tool_name="${TOOL_NAMES[$tool_type]}"
    local prompt="${TOOL_PROMPTS[$tool_type]}"

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

    local test_home
    test_home=$("$TEST_HOME_WRAPPER" --setup "$PROJECT_DIR" 2>/dev/null | grep '^TEST_HOME=' | cut -d= -f2-)
    [ -z "$test_home" ] && { echo "FATAL"; return; }

    cd "$TEST_PROJECT"
    HOME="$test_home" XDG_CONFIG_HOME="$test_home/.config" XDG_CACHE_HOME="$test_home/.cache" \
    XDG_RUNTIME_DIR="$test_home/.runtime" XDG_DATA_HOME="$test_home/.local/share" XDG_STATE_HOME="$test_home/.local/state" \
    OPENCODE_CONFIG_CONTENT="$config_content" \
        opencode-cli run "$prompt" --model "$MODEL" --log-level INFO --print-logs \
            --thinking --variant minimal --pure \
            2>"$workdir/stderr.log" >"$workdir/stdout.log" || true
    cd "$PROJECT_DIR"

    local tool_calls
    tool_calls=$(grep '⚙.*viewport-editor_' "$workdir/stderr.log" 2>/dev/null || true)
    [ -z "$tool_calls" ] && { echo "UNKNOWN"; return; }

    if echo "$tool_calls" | grep -q "viewport-editor_${tool_name}\b"; then
        echo "CUSTOM_CORRECT"
    elif echo "$tool_calls" | grep -qE 'viewport-editor_(read|write|edit|find|diff|read_file|write_file|edit_text|find_text)'; then
        echo "CUSTOM_WRONG:$(echo "$tool_calls" | grep -o 'viewport-editor_[a-z_]*' | head -1 | cut -d_ -f2-)"
    else
        echo "CUSTOM_OTHER"
    fi
}

echo "variant_id,tool_type,trial_num,result,expected_tool" > "$OUTPUT_DIR/results.csv"

for variant_id in "${VARIANTS[@]}"; do
    for tool_type in "${ALL_TOOLS[@]}"; do
        echo "=== Variant: $variant_id | Tool: $tool_type ==="
        mkdir -p "$OUTPUT_DIR/${variant_id}/${tool_type}"
        for trial_num in $(seq 1 "$TRIALS"); do
            trial_dir=$(mktemp -d "$OUTPUT_DIR/${variant_id}/${tool_type}/trial-${trial_num}-XXXXXX")
            result=$(run_trial "$variant_id" "$tool_type" "$trial_num" "$trial_dir")
            echo "$variant_id,$tool_type,$trial_num,$result,${TOOL_NAMES[$tool_type]}" >> "$OUTPUT_DIR/results.csv"
            printf "  Trial %2d/%d: %s\n" "$trial_num" "$TRIALS" "$result"
        done
        echo ""
    done
done

echo "=== Summary ==="
python3 -c "
import csv
from collections import defaultdict
d={}
o=[]
with open('$OUTPUT_DIR/results.csv') as f:
    for row in csv.DictReader(f):
        k=(row['variant_id'],row['tool_type'])
        if k not in d: d[k]=defaultdict(int); o.append(k)
        d[k][row['result']]+=1
for vid,tt in o:
    c=d[(vid,tt)]; t=sum(c.values()); cc=c.get('CUSTOM_CORRECT',0); p=round(100*cc/t,1) if t>0 else 0
    m='PASS' if p>=80 else 'FAIL'
    print(f'{vid:10s} {tt:10s} correct={cc}/{t} ({p}%) [{m}]')
"
echo "Results: $OUTPUT_DIR/results.csv"