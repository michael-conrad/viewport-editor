# V2 Description Specificity Results

## Winner
**Elaborated** — most consistent across all 5 tools.

## Data (DeepSeek V4 Flash, 20 trials per variant)

| Tool | Minimal | Constraint | Elaborated | Winner |
|------|:-------:|:----------:|:----------:|:------:|
| `read_file` | 80% PASS | 65% FAIL | 80% PASS | Tie (elaborated wins via consistency) |
| `write_file` | 85% PASS | 95% PASS | 95% PASS | Elaborated/Constraint tie |
| `edit_text` | 100% PASS | 100% PASS | 100% PASS | Three-way tie |
| `find_text` | 75% FAIL | 70% FAIL | 100% PASS | **Elaborated** |
| `diff` | 90% PASS | 100% PASS | 90% PASS | Constraint (marginal) |

## Analysis

- **Minimal** (`"Search file contents."`) has highest UNKNOWN rate — not enough information for the model to understand what the tool does vs alternatives
- **Constraint** (Anthropic-recommended pattern) underperforms on read_file (65%) and find_text (70%) — the shortest descriptions hurt the most for these tools
- **Elaborated** provides enough context for the model to correctly route all tool types. The Over-Specification Paradox (S* ~0.509) does not appear to trigger within the elaborated level for these 5 tools
- Contradicts Anthropic's recommendation but confirms the spec's caveat: "the optimal specificity level varies by model"

## Winning Descriptions (Locked)

```
read_file:
  Read file contents from the local filesystem into a staged buffer viewport.
  If the file path does not exist, an error is returned. Supports offset/limit
  for partial reads. The viewport remains open for follow-up edits. No content
  touches disk until explicitly confirmed via file:save. Use this for all file
  reading tasks including config files, source code, and logs.

write_file:
  Write file contents to the local filesystem through a staged buffer with
  automated viewport lifecycle management. Opens a viewport, replaces the
  entire buffer content, saves to disk, and closes the viewport. Conflict
  detection catches external file modifications before overwrite. New files
  are created automatically. Use this for creating new files or full-file
  overwrites.

edit_text:
  Perform exact string replacements in files through a staged buffer with
  automated viewport lifecycle management. Opens a viewport, applies the
  replacement, saves to disk, and closes the viewport. Conflict detection
  prevents overwriting externally modified files. For write/edit overlap,
  use edit_text for targeted changes under 100 characters — use write_file
  for full-file replacement.

find_text:
  Fast content search tool that works with any project size. Searches file
  contents using substring (default) or regex matching. Returns structured
  results with line numbers, file paths, and matching text for navigation
  via viewport:jump. Supports scoping to a single file or project-wide
  search.

diff:
  Show unified diff of staged edits in a viewport buffer before they are
  committed to disk. Returns the diff as standard unified format with
  context lines, additions, and deletions. If no changes are pending,
  returns an empty result. Use this before file:save to verify edits are
  correct.
```

## Raw Results
- `tmp/v2-results-20260611-101312/` — read_file
- `tmp/v2-results-20260611-101951/` — write_file
- `tmp/v2-results-20260611-102751/` — edit_text
- `tmp/v2-results-20260611-103810/` — find_text
- `tmp/v2-results-20260611-104708/` — diff
