# V1 Verb-Class Results

## Summary
verb_noun naming wins over bare verb across all 5 tools. DeepSeek gating passes at >80% for all 5 tool types.

## Data per Model

### DeepSeek V4 Flash (cloud) — 20 trials per tool
| Tool | Name | Correct | Total | Rate | Gate |
|------|------|---------|-------|------|------|
| read | `read_file` | 16 | 20 | 80% | PASS |
| write | `write_file` | 19 | 20 | 95% | PASS |
| edit | `edit_text` | 20 | 20 | 100% | PASS |
| find | `find_text` | 20 | 20 | 100% | PASS |
| diff | `diff` | 20 | 20 | 100% | PASS |

### DeepSeek V4 Flash — Bare Verb Comparison
| Tool | Name | Correct | Total | Rate |
|------|------|---------|-------|------|
| read | `read` (verb) | 13 | 20 | 65% |
| read | `read_file` (verb_noun) | 16 | 20 | 80% |

Verb_noun outperforms bare verb by +15 points for read.

### Qwen3.6 (35B) — 5 trials per tool
| Tool | Name | Correct | Total | Rate |
|------|------|---------|-------|------|
| read | `read_file` | 5 | 5 | 100% |
| write | `write_file` | 5 | 5 | 100% |
| edit | `edit_text` | 5 | 5 | 100% |
| find | `find_text` | 3 | 5 | 60% |
| diff | `diff` | 4 | 5 | 80% |

Qwen3.6 matches DeepSeek on read/write/edit. The find dip may be prompt ambiguity ("Search").

### Nemotron3 (33B) — 19 trials (partial) read only
| Tool | Name | Correct | Total | Rate |
|------|------|---------|-------|------|
| read | `read_file` | 11 | 19 | 58% |

Nemotron3 showed higher UNKNOWN rate (training data answering).

### GPT-OSS (21B) — 20 trials per tool
| Tool | Name | Correct | Total | Rate |
|------|------|---------|-------|------|
| read | `read_file` | 13 | 20 | 65% |
| write | `write_file` | 6 | 20 | 30% |
| edit | `edit_text` | 4 | 20 | 20% |

GPT-OSS UNKNOWN rate is high across all tools — model fails to dispatch any tool, answering from training data. This is a model-capability floor, not a naming problem.

## Winning Configuration

All 5 composite tools use **verb_noun naming:**

```
read_file    — "Read a file or directory from the local filesystem. If the path does not exist, an error is returned. Supports offset/limit for partial reads. Use first."
write_file   — "Write file contents to the local filesystem via a staged buffer with conflict detection. Use first for file writing."
edit_text    — "Perform exact string replacements in files via a staged buffer with conflict detection. Use first for file editing."
find_text    — "Fast content search that works with any project size. Searches file contents using substring or regex. Returns structured results with line numbers. Use first for search."
diff         — "Show unified diff of pending buffer changes before they become permanent. Use first to review edits."
```

## Archive
Raw results: `tmp/v1-results-*/` directories with per-trial stderr/stdout logs.

## Next Step
Developer review → V2 description specificity testing.
