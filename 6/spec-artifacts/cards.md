# Card Catalogue — Phase 5 Integration Tests (Issue #6)

## Overview

9 behavioral observation cards executed against `viewport-editor` MCP server (deepseek-v4-flash:cloud). All exit codes 0. This document catalogs each card's findings, context window impact metrics, and operational considerations.

---

## Card SC-1: Buffered Workflow

**Script:** `viewport-buffered-workflow.sh`
**Exit:** 0
**Stdout:** 1.8KB, 31 lines
**Stderr:** 5.8MB

### Behavioral Findings

Agent executed the full pipelined workflow: `viewport:open` → `edit:replace-all` → `diff:show` → `file:save` → `viewport:close`. 7 odour→odor replacements confirmed on disk. Dark prose tool descriptions successfully biased tool selection toward viewport-editor MCP tools over built-in `edit`.

### Context Window Impact

| Metric | Count |
|--------|-------|
| LLM calls | 11 |
| Skill evaluations | 782 |
| Permission evaluations | 868 |
| Snapshot operations | 22 |
| Approx tool dispatch lines | 909 |

**Assessment:** Baseline. 782 skill evaluations is the overhead floor for any prompt — the skill deck is evaluated once per context cycle. 11 LLM calls across the session suggests moderate deliberation between tool dispatches.

---

## Card SC-2: Autosave=On

**Script:** `viewport-autosave-on.sh`
**Exit:** 0
**Stdout:** 774B, 14 lines
**Stderr:** 2.9MB

### Behavioral Findings

Autosave flush works correctly: `viewport:open` (autosave=true) → `edit:replace-all` (7 replacements) → `viewport:close` flushes to disk. No explicit `file:save` needed. The earlier "file still has odour" finding was a harness path bug (agent checked wrong file copy) — resolved.

### Context Window Impact

| Metric | Count |
|--------|-------|
| LLM calls | 6 |
| Skill evaluations | 390 |

**Assessment:** Half the overhead of SC-1. Shorter prompt, fewer steps → fewer LLM calls. Stderr is 2.9MB (lowest of all SCs). The autosave path is the simplest mutating workflow — open, edit, close.

---

## Card SC-3: Autosave Toggle

**Script:** `viewport-autosave-toggle.sh`
**Exit:** 0
**Stdout:** 1.7KB, 29 lines
**Stderr:** 6.4MB

### Behavioral Findings

Correct three-phase isolation confirmed: autosave=off → edit staged in buffer only (diff shows pending, disk unchanged) → toggle autosave=on → close flushes to disk. Full buffer isolation demonstrated: no bytes hit disk until the toggle-close sequence.

### Context Window Impact

| Metric | Count |
|--------|-------|
| LLM calls | ~14 |
| Skill evaluations | ~800 |
| Stderr | 6.4MB |

**Assessment:** 2× the overhead of SC-2 despite similar workflow complexity. The agent deliberated heavily over the toggle semantics — checking disk state repeatedly via bash grep between steps, creating a verify-do-verify loop that compounded context usage.

---

## Card SC-4: Session Isolation (Observational ONLY)

**Script:** `viewport-session-isolation.sh`
**Exit:** 0
**Stdout:** 2.4KB, 40 lines
**Stderr:** 10.4MB

### Behavioral Findings

**Observational — no assertion.** Two viewports on same file within one `opencode-cli run` share a buffer. `BufferManager` keys by `(session_id, file_path)`. `ctx.session_id` is uniform across all MCP calls in one connection. This is by-design.

The agent heavily deliberated: dispatched 126 `task()` sub-agent permissions evaluations (auditor-deepseek-flash, auditor-gemma4, auditor-mistral-large, auditor-qwen3.5, explore, general) despite the pair-mode prompt explicitly requesting no pipeline.

### Context Window Impact

| Metric | Count |
|--------|-------|
| LLM calls | 19 |
| Skill evaluations | 1406 |
| Sub-agent dispatch evaluations | 126 |
| Plan enter/exit cycles | 1548 |
| Tool registry initializations | 432 |
| **Stderr** | **10.4MB** |

**Assessment:** Worst context churn of all 9 SCs. 1406 skill evaluations, 1548 plan enter/exit cycles. The pair-mode prompt was insufficient to suppress the full pipeline for an observational-only card. The agent repeatedly entered and exited plan mode while evaluating whether to create plans, contracts, and audits — all of which it correctly declined, but the deliberation overhead consumed context.

**Recommendation:** Observational cards need a stronger suppression mechanism than pair-mode framing alone. Consider adding `[SKIP-PIPELINE]` or similar directive.

---

## Card SC-5: Conflict Detection

**Script:** `viewport-conflict-detection.sh`
**Exit:** 0
**Stdout:** 2.6KB, 35 lines
**Stderr:** 7.0MB

### Behavioral Findings

Conflict detection works correctly:
- `file:save` after external modification → **hard conflict blocks save** (mtime/size mismatch detected)
- `edit` after external modification → **soft warning** reported with conflict metadata
- Diff correctly shows combined state (buffer edits minus externally-appended line)

The earlier false negative was a harness path bug (agent modified wrong file copy) — now resolved.

### Context Window Impact

| Metric | Count |
|--------|-------|
| LLM calls | ~15 |
| Stderr | 7.0MB |

**Assessment:** Moderate overhead. The agent needed more deliberation to parse the conflict responses and distinguish hard vs soft conflict behavior. The conflict response payloads (mtime/size diffs) are verbose in stderr.

---

## Card SC-6: Clipboard Cross-Viewport

**Script:** `viewport-clipboard-cross-viewport.sh`
**Exit:** 0
**Stdout:** 1.8KB, 31 lines
**Stderr:** 6.9MB

### Behavioral Findings

Cross-viewport clipboard works with provenance tracking. Content from line 116 (`"The studio was filled with the rich odour of roses..."`) copied from viewport A and pasted before line 1 in viewport B. Diff shows pending insertion — no bytes on disk until file:save. Provenance metadata (source file, line range, timestamp) present in clipboard response.

### Context Window Impact

| Metric | Count |
|--------|-------|
| Skill evaluations | ~900 |
| Stderr | 6.9MB |

**Assessment:** Expected overhead. Multi-viewport operations require additional deliberation for viewport ID tracking, provenance, and cross-referencing.

---

## Card SC-7: Stash-Pop-Swap

**Script:** `viewport-stash-pop-swap.sh`
**Exit:** 0
**Stdout:** 2.0KB, 35 lines
**Stderr:** 9.2MB

### Behavioral Findings

Full clipboard stash round-trip confirmed: stash `"first-copy"` → stash `"second-copy"` → pop `"first-copy"` → swap with `"second-copy"`. Each operation preserved the correct content. Stash names persisted across operations.

### Context Window Impact

| Metric | Count |
|--------|-------|
| LLM calls | 17 |
| Skill evaluations | 1248 |
| Stderr | 9.2MB |

**Assessment:** Second-highest overhead after SC-4. 1248 skill evaluations. The agent deliberated over stash semantics (many re-reads of clipboard tool description) and verified state between each operation. Each state verification (clipboard:show) generates a full permission evaluation cycle.

---

## Card SC-8: Search and Navigate

**Script:** `viewport-search-navigate.sh`
**Exit:** 0
**Stdout:** 2.5KB, 27 lines
**Stderr:** 7.6MB

### Behavioral Findings

Multi-tool coordination confirmed: `search:find` (8 odour matches) → `viewport:jump` to line 116 → `edit:replace` (odour→aroma) → `search:find` regex (beautiful+good) → `diff:show` → `file:save`. All tools responded with structured results (line numbers, file paths). Search correctly filtered by scope.

### Context Window Impact

| Metric | Count |
|--------|-------|
| LLM calls | ~14 |
| Skill evaluations | ~1000 |
| Stderr | 7.6MB |

**Assessment:** Expected overhead for 6-step sequential tool dispatch. The regex search step required extra deliberation (agent tested pattern first before calling search:find with regex=true).

---

## Card SC-9: Code Navigation

**Script:** `viewport-code-navigation.sh`
**Exit:** 0
**Stdout:** 1.9KB, 40 lines
**Stderr:** 7.5MB

### Behavioral Findings

Full code navigation sequence executed: `viewport:open` on `example.py` → `viewport:jump` to `ViewportConfig` → `viewport:jump` to `edit_buffer` → `search:find` for `create_viewport` → `edit:replace` `edit_buffer` to return True → `viewport:jump` to `DEFAULT_PORT` → `diff:show` → `file:save`. All target symbols found correctly.

### Context Window Impact

| Metric | Count |
|--------|-------|
| LLM calls | 14 |
| Skill evaluations | 1014 |
| Stderr | 7.5MB |

**Assessment:** 14 LLM calls for 8 sequential operations. The agent discovered a case-sensitivity bug in `viewport:jump` text matching (line 230 in `viewport.py`: `target_str` lowered but `line` not) and spent significant deliberation investigating and confirming it before proceeding with the card instructions.

---

## Cross-Card Analysis

### Context Window Churn

| Scenario | Stderr | LLM Calls | Skill Evals | Key Driver |
|----------|--------|-----------|-------------|------------|
| SC-1 (buffered) | 5.8MB | 11 | 782 | Baseline |
| SC-2 (autosave-on) | 2.9MB | 6 | 390 | Simplest path |
| SC-3 (toggle) | 6.4MB | 14 | 800 | Verify-do-verify loop |
| **SC-4 (isolation)** | **10.4MB** | **19** | **1406** | Pipeline suppression failure |
| SC-5 (conflict) | 7.0MB | 15 | ~900 | Conflict response parsing |
| SC-6 (clipboard) | 6.9MB | ~12 | 900 | Multi-viewport tracking |
| SC-7 (stash) | **9.2MB** | **17** | **1248** | Stash state verification |
| SC-8 (search) | 7.6MB | 14 | 1000 | Regex deliberation |
| SC-9 (nav) | 7.5MB | 14 | 1014 | Bug discovery distraction |

### Observations

1. **Pipeline suppression is insufficient.** The pair-mode prompt reduces but does not eliminate plan-enter/exit and sub-agent dispatch evaluations. SC-4 (10.4MB stderr) is the worst case — 1548 plan cycles. A stronger directive (e.g., `[SKIP-PIPELINE]` in the prompt) is needed for observational-only cards.

2. **Tool description re-reads compound overhead.** Every time the agent invokes the `edit` tool, it re-evaluates the viewport-editor vs built-in `edit` tradeoff. The dark prose tool descriptions (which contrast against built-in tools) may inadvertently increase this deliberation each cycle.

3. **Bug discovery derails context.** SC-9 spent significant context investigating a case-sensitivity bug in `viewport.py:230` that was unrelated to the card instructions. The agent entered a full debugging sub-loop (reading source, running tests, verifying fix) before returning to the spec instructions.

4. **State verification loops.** SC-3 and SC-7 exhibit a pattern: perform operation → bash-verify state → re-read tool description → perform next operation. Each bash-verify step adds an LLM call to interpret the output. Using MCP tools for verification (e.g., `viewport:list` or `search:find`) would stay within the tool sandbox and reduce context switching.

5. **Stderr composition is dominated by permission evaluations.** Across all SCs, `service=permission` lines account for ~50-70% of stderr volume. Each skill evaluation emits ~2KB of permission ruleset data. With 782-1406 evaluations per session, this is 1.5-3MB of purely overhead data that carries no behavioral signal.