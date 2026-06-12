# Semantic Check Dispatch Procedure

## Purpose

After `audit_stress.py` produces `findings_manifest.json`, an AI orchestrator reads the manifest and dispatches clean-room sub-agents **one per finding, sequentially** to perform semantic analysis. The audit script does NOT dispatch AI itself.

## Mandate: One Agent Per Finding, Sequential Analysis

**This is a hard requirement.** The orchestrator MUST dispatch exactly one clean-room sub-agent per finding entry, in sequence. Each sub-agent receives ONLY its single entry's data — no other entries, no run statistics, no orchestrator reasoning.

### Why Sequential, Not Batched

| Approach | Problem |
|----------|---------|
| **Batched** (multiple findings in one dispatch) | Sub-agent context is contaminated by other entries; verdicts bleed across findings; evidence is conflated |
| **Parallel** (concurrent dispatches) | Sub-agents cannot reference each other's findings; orchestrator cannot aggregate incrementally |
| **Sequential (MANDATED)** | Each sub-agent is clean-room for its single entry; orchestrator aggregates results one at a time; evidence is per-finding and traceable |

### Why One Per Finding, Not One Per Category

Findings with the same mechanical flag (e.g., `edit_target_not_found_step_2`) may have different root causes. A replace-all → replace failure and a delete-lines → delete-lines failure both produce `edit_target_not_found_step_2`, but the semantic correctness depends on the specific seed content, step parameters, and final content. Grouping them assumes equivalence that may not hold.

## Manifest Format

`findings_manifest.json` is a JSON list. Each entry contains:

```json
{
  "sequence_id": "edit-pair-0043",
  "category": "edit_pairs",
  "seed_content": "line 1\\nline 2\\n...",
  "steps_summary": "edit:replace -> edit:delete-lines(4,5)",
  "final_content": "line 1\\nline 2\\n...",
  "mechanical_flags": ["line_range_step_2"],
  "semantic_question": "The seed content was modified by the sequence... Does the final content correctly reflect all operations?"
}
```

## Dispatch Protocol

For each entry in `findings_manifest.json`, in order:

1. **Read entry data** — sequence_id, seed_content, final_content, semantic_question
2. **Read steps log** — load `tmp/stress/<run_id>/sequences/<sequence_id>/steps.json` to get error/success info for each step
3. **Build annotated steps_summary** — for each step in the steps log, append `[SUCCESS]` or `[ERROR: <error message>]` to the operation summary
4. **Dispatch ONE clean-room sub-agent** with ONLY:
   - The seed content
   - The annotated steps summary (with SUCCESS/ERROR per step)
   - The final content
   - The semantic question
   - The tool semantics reference (from this document)
5. **Sub-agent returns**: PASS or ANOMALY with specific evidence
6. **Record result** — append to the running aggregate
7. **Proceed to next entry** — repeat from step 1

**Do NOT skip entries.** Every finding in the manifest must receive a semantic verdict. If a finding is trivially expected behavior (e.g., expected error path), the sub-agent will return PASS with evidence explaining why.

## Clean-Room Sub-Agent Input Contract

Each sub-agent receives ONLY:
- The seed file content
- The ordered steps executed (as text summary)
- The final content on disk
- The semantic question

## Clean-Room Sub-Agent Exclusion Contract — ZERO TOLERANCE

The sub-agent MUST NOT receive any of the following. Violation is a process-integrity failure — the sub-agent's verdict is contaminated and must be discarded.

| Prohibited | Why |
|------------|-----|
| **Other agent results** | Prior PASS/FAIL verdicts bias the sub-agent toward agreement or disagreement |
| **Orchestrator's own analysis** | The orchestrator's reasoning about what the answer "should be" contaminates the clean-room |
| **Any expectations** | Phrases like "this is expected behavior" or "this is likely a bug" pre-judge the outcome |
| **Other entries in the manifest** | Cross-entry context conflates independent findings |
| **Overall run statistics** | "37 out of 272 failed" creates anchoring bias |
| **Prior sub-agent verdicts or evidence** | Sequential dependency — each sub-agent must be independent |
| **Mechanical flag interpretations** | The sub-agent should evaluate content correctness, not audit flag correctness |

The sub-agent receives ONLY:
- The seed file content
- The ordered steps executed (as text summary)
- The final content on disk
- The semantic question

That is the complete input contract. Nothing else.

## Sub-Agent Expected Output

The sub-agent's only job: "Is the final content correct for the given edit sequence?" This is a **semantic** question — not structural, not mechanical. The mechanical audit has already checked ordering, offsets, truncation, and line presence. The AI auditor evaluates whether the content makes semantic sense given the operations applied.

### Mandatory Prompt Template — Invariant Per Finding (ZERO TOLERANCE)

**The prompt template is FROZEN.** It MUST be used identically for every finding. Only three fields vary:
- `seed_content`
- `steps_summary`
- `final_content`

No other part of the prompt may change between findings. No commentary, no expectations, no pattern labels, no operator reasoning, no references to other findings. Any orchestrator that deviates from this template has produced contaminated results.

Violation is a process-integrity failure. To maintain test integrity:
- Do NOT add introductory text (e.g., "this is a replace-all poisoning case")
- Do NOT vary the tool semantics reference between findings
- Do NOT include mechanical flags in the prompt
- Do NOT include orchestrator commentary or analysis
- Do NOT reference prior or subsequent findings
- Do NOT explain what the "expected" answer should be

The template below is the ONLY acceptable prompt structure:

```
You are a clean-room semantic auditor. You have NO context beyond what is provided below.
You have NOT seen any other findings, any prior results, or any analysis from any other agent.

## Tool Semantics Reference

The following tools were used in the sequence. Each applies to the current buffer state (not a snapshot):

- viewport:open — loads a file into a buffer; displays its content
- viewport:close — closes the viewport (does NOT save or modify content)
- edit:replace(old_text, new_text) — replaces the FIRST occurrence of old_text with new_text in the buffer. Fails with EditTargetNotFoundError if old_text does not exist.
- edit:replace-all(old_text, new_text) — replaces ALL occurrences of old_text with new_text in the buffer.
- edit:insert-lines(line_start, lines) — inserts lines BEFORE the specified line number. Shifts subsequent content down.
- edit:delete-lines(line_start, line_end) — removes the specified line range. Shifts subsequent content up. Fails if range exceeds file length.
- edit:swap-lines(a_start, a_end, b_start, b_end) — exchanges two line ranges. Fails if ranges are invalid.
- edit:move-lines(start, end, target_line) — moves a line range to before target_line. Shifts content.
- clipboard:copy(line_start, line_end) — copies lines from buffer to clipboard. Does NOT modify buffer content.
- clipboard:cut(line_start, line_end) — removes lines from buffer AND places them in clipboard.
- clipboard:paste(target_line) — inserts clipboard content BEFORE target_line. Does NOT clear clipboard.
- clipboard:stash(name) — saves a copy of current clipboard to a named slot. Clipboard unchanged.
- clipboard:pop(name) — replaces current clipboard content from a named slot. Fails with ViewportError if the named slot does not exist. Slot content preserved.
- clipboard:swap(name) — exchanges clipboard content with a named slot. Fails if clipboard empty or slot not found.
- diff:apply(patch) — applies a unified diff patch to the current buffer. Multi-hunk patches apply sequentially with offset tracking.
- file:save — flushes buffer to disk (atomic write). Fails if external file modification detected (mtime conflict).

## Entry Data

**seed_content:** [the initial file content before any operations]

**steps_summary:** [ordered sequence of operations, each annotated with result: SUCCESS or ERROR + error message if failed]

**final_content:** [the file content on disk after all operations completed]

The sub-agent MUST receive error information for each step. Without knowing which steps failed, the sub-agent cannot evaluate whether failures were correct behavior or bugs. Error information is extracted from the steps log before dispatch — the mechanical flags themselves are NOT sent.

## Critical Behavioral Invariant

When an operation returns ERROR, the buffer content is left in its prior valid state. The error does NOT corrupt the buffer. The error only means the operation was not performed. Subsequent operations (including file:save) operate on the unchanged valid state.

Therefore: A SUCCESS on file:save immediately after an ERROR on a prior operation is NOT anomalous. The save is persisting valid content. Do NOT flag this as an anomaly.

## Task

Evaluate whether the final content and tool behavior are semantically correct for the given sequence. This is a two-part evaluation.

**Part 1 — Tool Response Correctness:** For each step in steps_summary, check whether the tool's response ([SUCCESS] or [ERROR]) matches what you would expect given the buffer state at that point. This is the primary concern — wrong tool responses are the strongest signal of a real bug. Check for:
- An operation that succeeded when it SHOULD have failed (e.g., tool should have rejected invalid input but silently accepted it, potentially corrupting content)
- An operation that failed when it SHOULD have succeeded (e.g., valid operation rejected, blocking legitimate edits)
- An operation where the wrong error message was produced (e.g., wrong error type for the failure mode)

**Part 2 — Content Correctness:** Check whether the final content is explainable by the sequence of operations applied to the seed content. Content that cannot be explained by the stated operations may indicate a corruption bug. Remember that ERROR steps leave the buffer unchanged from its prior state.

This is NOT a mechanical check. Ordering, offset accuracy, line counts, and truncation have already been verified by separate checks.

Return PASS or ANOMALY. There are no exceptions — ANOMALY always means the sub-agent found a real semantic defect or real tool misbehavior. If you are uncertain, state clearly what you are uncertain about and why. Ambiguous or self-contradictory verdicts are not acceptable.
```

## Final Report Format

After all entries processed, produce `.issues/stress-report-<run-id>.md`:

```markdown
# Stress Test Report: <run-id>

## Mechanical Summary
- Total sequences: N
- Passed mechanical: N
- Failed mechanical (AI dispatched): N

## AI Semantic Analysis
| Sequence | Mechanical Flags | Semantic Verdict | Evidence |
|----------|-----------------|------------------|----------|
| edit-pair-0043 | line_range_step_2 | PASS | Content correctly reflects delete-lines operation; offset shift is expected |
| edit-pair-0074 | edit_target_not_found_step_2, edit_target_not_found_step_3 | FAIL | After replace-all, subsequent replace ops should fail — correct error handling |
```

## When to Skip AI Dispatch

If `findings_manifest.json` is empty (all sequences passed mechanical checks), no AI dispatch is needed. The mechanical_report.md alone constitutes the final report.
