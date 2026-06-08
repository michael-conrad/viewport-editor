# Phase 5 Integration Test — Overview Analysis Report

**Issue #6** | **Branch:** `feature/viewport-buffered-workflow-test` | **Model:** deepseek-v4-flash:cloud

---

## 1. Infrastructure Delivered

| Component | Count | Location |
|-----------|-------|----------|
| Behavioral cards (specs) | 9 | `tests/behaviors/viewport-*.card.md` |
| Harness scripts (thin wrappers) | 9 | `tests/behaviors/viewport-*.sh` |
| Shared runner | 1 | `tests/behaviors/run-viewport-scenario.sh` |
| Gutenberg fixture files (gzipped) | 6 | `tests/fixtures/ebooks/` |
| Tool description updates (dark prose) | 7 tools | `src/viewport_editor/server.py` |
| Card catalogue with metrics | 1 | `.issues/6/spec-artifacts/cards.md` |
| Timeout documentation | 1 | `tests/behaviors/TIMEOUT.md` |
| Observational doc update | 1 | `docs/mcp-plugin-behavior.md` |

---

## 2. Behavioral Results Summary

| SC | Scenario | Exit | Verdict |
|----|----------|------|---------|
| 1 | Buffered workflow | 0 | ✅ Full pipeline: open→edit→diff→save→close |
| 2 | Autosave=on | 0 | ✅ Edit→close→autosave flush to disk |
| 3 | Autosave toggle | 0 | ✅ Buffer isolation confirmed pre/post toggle |
| 4 | Session isolation | 0 | 🔍 Observational: shared buffer per (session,file) |
| 5 | Conflict detection | 0 | ✅ Hard conflict blocks save, soft warning on edit |
| 6 | Clipboard cross-viewport | 0 | ✅ Copy from A → paste into B with provenance |
| 7 | Stash-pop-swap | 0 | ✅ Full clipboard round-trip |
| 8 | Search and navigate | 0 | ✅ search→jump→edit→regex→diff→save |
| 9 | Code navigation | 0 | ✅ Class jump→function jump→search→edit→diff→save |

---

## 3. Bugs Found and Corrected

### False Positives (Harness Path Bug)

Three reports filed and closed after root cause identified:

| Issue | Title | Root Cause | Resolution |
|-------|-------|------------|------------|
| #58 | Autosave flush not persisting | `VIEWPORT_PROJECT_ROOT` pointed server to `$TEST_HOME/workdir/` while agent's `bash grep` checked project root — different file copies | Removed `VIEWPORT_PROJECT_ROOT`. Server defaults to project root CWD |
| #59 | Conflict detection silent overwrite | Same path mismatch — `bash echo >>` modified wrong file copy | Same fix as #58 |

Both were closed as harness bugs, not server defects.

### Observational Correction

| Issue | Title | Correction |
|-------|-------|------------|
| #57 | SC-4 session isolation card | Rewrote as observational-only card. Updated `docs/mcp-plugin-behavior.md` Section 5 to correct "sub-agent transport continuity" → "full-session isolation (separate CLI invocations)" and added Section 6 documenting same-connection buffer sharing |

### Bug Found During Analysis

- **Case-sensitivity bug in `viewport:jump`** (`viewport.py:230`): `target_str` is lowered for text matching but `line` is not. Agent discovered this during SC-9 but was not authorized to fix.

---

## 4. Context Window Impact Analysis

### Stderr Volume by Scenario

| Scenario | Stderr | LLM Calls | Skill Evals | Dominant Cost Driver |
|----------|--------|-----------|-------------|---------------------|
| SC-2 (autosave-on) | 2.9MB | 6 | 390 | Baseline — simplest path |
| SC-1 (buffered) | 5.8MB | 11 | 782 | Baseline |
| SC-3 (toggle) | 6.4MB | 14 | ~800 | Verify-do-verify loop |
| SC-6 (clipboard) | 6.9MB | ~12 | ~900 | Multi-viewport tracking |
| SC-9 (nav) | 7.5MB | 14 | 1014 | Bug discovery distraction |
| SC-8 (search) | 7.6MB | 14 | ~1000 | Regex deliberation |
| SC-7 (stash) | 9.2MB | 17 | 1248 | Stash state verification |
| SC-4 (isolation) | 10.4MB | 19 | 1406 | Pipeline suppression failure |
| SC-5 (conflict) | 7.0MB | 15 | ~900 | Conflict response parsing |

### Five Systemic Overhead Drivers

1. **Pipeline suppression insufficient.** Even with pair-mode framing, the agent enters plan/exit cycles. SC-4 had 1548 plan enter/exit evaluations — pure overhead for an observational card.

2. **Tool description re-reads.** The dark prose tool descriptions contrast viewport-editor tools against built-in alternatives. Each invocation re-evaluates this tradeoff, compounding overhead on every tool call.

3. **Bug discovery derailment.** SC-9 spent substantial context investigating a `viewport.py:230` case-sensitivity bug that was unrelated to the card instructions.

4. **State verification loops.** SC-3 and SC-7 pattern: perform MCP operation → `bash grep` to verify → re-read tool description → next step. Each `bash grep` crosses the tool sandbox boundary, requiring an LLM round-trip to interpret output.

5. **Permission evaluation bloat.** 50-70% of stderr volume is permission evaluation data. Each skill evaluation emits ~2KB of ruleset JSON. 800-1400 evaluations per session produces 1.5-3MB of overhead per run.

---

## 5. Harness Architecture

### Prompt Pattern

```
Enter pair mode. We need to apply the instructions from the spec <path>
so that I can review them. You are authorized to perform the instructions
in the spec. This is not a 14 point pipeline implementation. This is only
so I can review if the card has the correct instructions by looking at
the results of the instructions being applied.
```

The spec is placed at `.issues/<scenario>/spec.md` — the agent's approval-gate searches this location. No authorization language appears in the spec itself. The spec is a work instruction only.

### Timeout Model

Two independent layers documented in `TIMEOUT.md`:
- **Bash tool timeout** (outer bound): 900000ms for complex scenarios
- **Model run timeout** (inner): None — `opencode-cli run` waits indefinitely

---

## 6. Artifacts Produced

```
tmp/behavioral-evidence-viewport-*-GREEN-ollama-deepseek-v4-flash-cloud/
  ├── card.md          — The spec as delivered to the agent
  ├── exit_code        — 0 (all runs)
  ├── manifest.yaml    — Scenario metadata
  ├── stdout.log       — Agent prose response
  └── stderr.log       — Full tool dispatch trace
```

All 9 artifact directories preserved. Total stderr across all runs: ~63MB.

---

## 7. Unresolved Items

- **SC-4 card is observational-only.** The `docs/mcp-plugin-behavior.md` update is applied but the card is currently marked as a behavioral SC in the spec table. Needs to be relabeled as observational in `.issues/6/spec.md`.
- **Case-sensitivity bug in `viewport:jump`** (`viewport.py:230`) — discovered but unfixed.
- **Pipeline suppression for observational cards** needs a stronger mechanism than pair-mode framing alone.

---

🤖 Co-authored with AI: OpenCode (deepseek-v4-flash)