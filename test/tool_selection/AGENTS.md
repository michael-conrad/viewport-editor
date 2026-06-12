# AGENTS.md — Tool Selection Test Framework

## Timeout Mandate (MANDATORY — Tier 1)

**Always increase bash tool timeouts as needed, especially for local models.**

The default 120s timeout is NEVER sufficient for model runs — it is a harness configuration error. Failing to extend timeouts for local model inference is a process-integrity failure. A timeout is NOT a model failure — it is a harness configuration error.

Timeouts must be extended per-model. These are MINIMUMS — increase further if the model is cold-loading:

| Model | Min Timeout | Reason |
|-------|-------------|--------|
| `ollama/deepseek-v4-flash:cloud` | 120s | Cloud inference, fast |
| `ollama/devstral-small-2:24b-384k` | 300s | 24B local model |
| `ollama/gemma4:31b-256k` | **3600s** | 19GB model — very slow load |
| `ollama/gpt-oss:20b-128k` | 1800s | 20B local model |
| `ollama/nemotron3:33b-128k` | 1800s | 33B local model |
| `ollama/qwen3.6:35b-256k` | 1800s | 35B local model |

If a model timeout occurs, double the timeout and retry. Do not skip the model.

**Provider config also requires `chunkTimeout`** set to at least 300000ms for slow local models. OpenCode's streaming timeout kills connections if no chunk arrives within `chunkTimeout`.

## Session Resume

Multi-turn sessions are supported via `opencode-cli run --continue` (resume last session) or `opencode-cli run --session <id>`. On SSE Read Errors or other transient failures, resume with `--continue` to retry from where the session left off rather than restarting from scratch.

## File Path Resolution

MCP tool handlers resolve file paths relative to the test project root (`VIEWPORT_PROJECT_ROOT` or `os.getcwd()`). Fixtures must be created inside the test project directory, never in the main project root.

## Model Set (6 models)

| Priority | Model | Type | Notes |
|----------|-------|------|-------|
| 1 | `ollama/deepseek-v4-flash:cloud` | Cloud | Primary development model |
| 2 | `ollama/devstral-small-2:24b-384k` | Local | Lightweight — lower capability |
| 3 | `ollama/gemma4:31b-256k` | Local | Mid-range, extended context |
| 4 | `ollama/gpt-oss:20b-128k` | Local | Weaker — edge of comprehension |
| 5 | `ollama/nemotron3:33b-128k` | Local | Mid-range, extended context |
| 6 | `ollama/qwen3.6:35b-256k` | Local | Long-context variant |