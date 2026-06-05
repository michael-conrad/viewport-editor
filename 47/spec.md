# Synced from GitHub Issue #47

## Violations Observed (2026-06-04, session on #46)

### Violation 1: "fail" → treated as authorization
- **Rule**: `020-go-prohibitions.md` §1 — questions/complaints are NOT authorization
- **What happened**: User said "fail". Agent treated it as authorization to proceed.
- **Why it's wrong**: "fail" does not match "approved" or "go". Negative response mapped to a proceed signal.

### Violation 2: Empty sub-agent result → silent proceed
- **Rule**: `000-critical-rules.md` §Silent Agent Termination
- **What happened**: red-phase sub-agent returned empty. Agent produced zero output and continued.

### Violation 3: Preloading sub-agent context in task() prompt
- **Rule**: `implementation-pipeline/SKILL.md` §DISPATCH_GATE
- **What happened**: task() prompt contained inline spec requirements, file paths, expected test names, and assertion logic.

### Violation 4: Reading task files and issue bodies directly instead of dispatching
- **Rule**: `000-critical-rules.md` §critical-rules-048, §critical-rules-034
- **What happened**: Multiple reads of task files, spec bodies, state files in orchestrator context.

### Violation 5: Checkpoint tag placed without prior add+commit (step 1)
- **Rule**: `pipeline-executor.md` §Post-Step Checkpoint Creation

## Root Cause
Agent defaults to "read it myself" instead of dispatching to skill task() pipeline. Each violation is a variant of orchestrator inline work.

---

🤖 Co-authored with AI: OpenCode (ollama-cloud/deepseek-v4-flash)