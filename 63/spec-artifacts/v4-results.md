# V4 Position Bias Results

## Result
Position bias exists but is small (~15 points) and only matters when intent signal is weak. Strong directive language in descriptions eliminates position bias entirely.

## Data (DeepSeek V4 Flash, 20 trials)

| Tool | First | Last | Delta |
|------|:-----:|:----:|:-----:|
| `write_file` | 100% PASS | 100% PASS | 0 |
| `read_file` | 70% FAIL | 55% FAIL | -15 |

## Analysis
- **write_file** at 100% regardless of position: the prompt includes "using the recommended writing tool," providing strong intent signal
- **read_file** at 70%/55%: the prompt "Read src/main.py and find the BUILD_VERSION value" has weaker tool selection signal
- The 15-point position bias for read_file confirms the mcp-naming-bias research but the effect is small relative to semantic matching (which adds +30-40 points)

## Action
No architectural change needed. The V2 elaborated descriptions with directive language are the primary defense against position bias. Keeping viewport-editor MCP registered first (natural order in opencode.jsonc) is sufficient — no special ordering required.
