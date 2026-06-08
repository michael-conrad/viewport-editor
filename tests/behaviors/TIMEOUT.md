# Test Harness — Timeout Model

## Two-Layer Timeout Architecture

The test harness has two independent timeout boundaries. Confusing them causes silent hangs.

### Layer 1: Tool Call Timeout (Bash Tool)

Set via the `timeout` parameter on the `bash` tool (in milliseconds). This is the **outer shell** — it bounds how long the harness script itself can run. If this fires, the script is killed mid-execution, producing no artifact at all (or partial files).

**Default:** 600000ms (10 minutes)
**Increase when:** The model run needs more time for complex multi-step scenarios

### Layer 2: Model Run Timeout (opencode-cli run)

`opencode-cli run` has no built-in timeout. The model runs until it produces a complete response. The script waits for it.

**No timeout = no kill.** The script waits indefinitely for the model to finish. The only timeout is Layer 1 (the bash tool call). If Layer 1 fires, `opencode-cli run` is killed mid-response — stdout.log and stderr.log will be truncated.

### Key Rule

**Increase the bash tool timeout, NOT the script.** Adding `timeout N` inside the script creates nested timeouts that race against the bash tool timeout. The script's `wait` on `opencode-cli run` is naturally bounded only by the bash tool layer.

### Recommended Values

| Scenario | Bash Tool Timeout |
|----------|-------------------|
| Simple prompt (hello world) | 60000 (1 min) |
| Multi-step workflow (open → edit → diff → save) | 600000 (10 min) |
| Complex navigation (SC-9: code nav with jumps + search + edit + diff) | 900000 (15 min) |

### When to Increase

- Agent output appears truncated (check wc -l on stdout.log)
- Stderr.log ends abruptly without session cleanup lines
- The scenario has 5+ sequential MCP tool calls
- The model displays extended thinking/reasoning blocks