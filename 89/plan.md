# Implementation Plan — [#89](https://github.com/michael-conrad/viewport-editor/issues/89) — Rename MCP plugin key from "viewport-editor" to "editor"

- **Spec:** [#89](https://github.com/michael-conrad/viewport-editor/issues/89)
- **Goal:** Rename the MCP plugin key from `"viewport-editor"` to `"editor"` in all user-facing JSON config blocks and section headers in `README.md`, without modifying the `command` array values or any source code.
- **Architecture:** Single file, 4 exact string replacements. No structural changes, no code changes, no dependency changes.
- **Files:** `README.md`

> **Compliance Requirement:** All steps and sub-steps in this document MUST be followed in order. Failure to comply with any step — including but not limited to verification gates, test phases, audit checkpoints, and review steps — will result in the feature branch being rejected and discarded, requiring a full rework from scratch and loss of all prior work. There is no valid reason to skip, compress, reorder, or omit any step. If a step appears redundant or unnecessary, follow it anyway — the cost of following an extra step is negligible compared to the cost of rework from a skipped step.

> **One-step-at-a-time protocol:** Each numbered step is exactly one sub-agent dispatch. The orchestrator completes step N, reports completion to chat, then proceeds to step N+1. Steps MUST NOT be combined, batched, or executed in parallel. The RED→GREEN transition is a zero-tolerance gate: the RED test's artifact output MUST be read and confirmed as FAILING before any GREEN implementation begins. If the RED test artifact is not read, or if it shows PASS when FAIL was expected, the phase is poisoned — all work in it MUST be discarded and the phase restarted from RED.

## Phase 1 — Rename plugin key in README.md

- **Concern:** Replace 4 occurrences of `"viewport-editor"` (as plugin key) and `viewport-editor MCP Plugin` (as section header) with `"editor"` and `editor MCP Plugin` respectively, in `README.md` only.
- **Files:** `README.md`
- **SCs:** SC-1, SC-2, SC-3, SC-4, SC-5
- **Dependencies:** None
- **Entry:** Spec approved, solve SAT
- **Exit:** All 4 replacements verified, grep confirms no stale plugin keys, `git diff --stat` shows only `README.md` changed
- **Cost-frame:** This is a single-file documentation change. The orchestrator holds routing metadata only (issue number, file path, SC list). All file reads, edits, and verification are dispatched to clean-room sub-agents. The orchestrator does NOT preload file paths, expected outcomes, or step sequences into sub-agent prompts.

- [ ] 1. **Pre-RED baseline (**clean-room**).** Read `README.md` and record the current count of `"viewport-editor":` (plugin key occurrences) and `viewport-editor MCP Plugin` (section header). **→ SC-1, SC-2, SC-3**
- [ ] 2. **RED phase (**clean-room**).** Write a grep-based RED test script to `./tmp/issue-89/red-test.sh` that asserts `"viewport-editor":` appears 3+ times and `viewport-editor MCP Plugin` appears 1+ times in `README.md`. Run it — it MUST PASS (confirming the old keys exist before change). **→ SC-1, SC-2, SC-3**
- [ ] 3. **Z3 check RED (**inline**).** `solve check` — verify RED test artifact exists and shows PASS. **→ SC-1, SC-2, SC-3**
- [ ] 4. **RED doublecheck (**inline**).** Read RED test output, confirm it shows the expected old-key counts. **→ SC-1, SC-2, SC-3**
- [ ] 5. **GREEN phase (**clean-room**).** Apply 4 exact string replacements to `README.md`:
      1. In the first JSON config block (Installation-Free section): replace `"viewport-editor"` (plugin key) with `"editor"`
      2. In the second JSON config block (Installation-Free section): replace `"viewport-editor"` (plugin key) with `"editor"`
      3. In the third JSON config block (Consuming Repo Instructions section): replace `"viewport-editor"` (plugin key) with `"editor"`
      4. In the AGENTS stanza section header: replace `viewport-editor MCP Plugin` with `editor MCP Plugin`
      Do NOT change any `"viewport-editor"` values inside `command` arrays. **→ SC-1, SC-2, SC-3, SC-4**
- [ ] 6. **Z3 check GREEN (**inline**).** `solve check` — verify GREEN phase completed. **→ SC-1, SC-2, SC-3, SC-4**
- [ ] 7. **Post-GREEN enforcement (**clean-room**).** Run `grep '"viewport-editor":' README.md` — assert 0 matches (SC-1). Run `grep '"editor":' README.md` — assert 3+ matches (SC-2). Run `grep 'editor MCP Plugin' README.md` — assert 1 match (SC-3). Run `grep '"viewport-editor"' README.md` — assert matches are ONLY inside `command` arrays, not plugin keys (SC-4). **→ SC-1, SC-2, SC-3, SC-4**
- [ ] 8. **Z3 check post-GREEN (**inline**).** `solve check` — verify post-GREEN enforcement output has PASS. **→ SC-1, SC-2, SC-3, SC-4**
- [ ] 9. **Structural checks (**clean-room**).** Run `git diff --stat` — assert only `README.md` changed (SC-5). **→ SC-5**
- [ ] 10. **GREEN doublecheck (**inline**).** Read the post-GREEN enforcement output and structural check output. Confirm all 4 replacements are correct and no unintended changes exist. **→ SC-1, SC-2, SC-3, SC-4, SC-5**
- [ ] 11. **Checkpoint tag (**inline**).** Create checkpoint tag for Phase 1 completion. **→ SC-1, SC-2, SC-3, SC-4, SC-5**
- [ ] 12. **Checkpoint commit (**inline**).** Commit the changes to `README.md` with message: `rename MCP plugin key from "viewport-editor" to "editor" in README.md`. **→ SC-1, SC-2, SC-3, SC-4, SC-5**

#### Phase 1 VbC

- [ ] 13. **VbC (**clean-room**).** Verify all 5 SCs: SC-1 (0 stale plugin keys), SC-2 (3+ new keys), SC-3 (section header renamed), SC-4 (command values unchanged), SC-5 (only README.md changed). **→ SC-1, SC-2, SC-3, SC-4, SC-5**

- [ ] 14. **Adversarial audit (**clean-room**).** Dispatch adversarial-audit for plan-fidelity and concern-separation. **→ SC-1, SC-2, SC-3, SC-4, SC-5**
- [ ] 15. **Cross-validate (**clean-room**).** Cross-validate VbC and audit results. **→ SC-1, SC-2, SC-3, SC-4, SC-5**
- [ ] 16. **Regression check (**clean-room**).** Run `uvx ruff check README.md` (advisory) and verify no regressions. **→ SC-5**
- [ ] 17. **Review prep (**clean-room**).** Prepare PR body and review context. **→ SC-1, SC-2, SC-3, SC-4, SC-5**
- [ ] 18. **Executive summary (**inline**).** Report completion with summary, URL, and byline. **→ SC-1, SC-2, SC-3, SC-4, SC-5**

> **Compliance Requirement:** All steps and sub-steps in this document MUST be followed in order. Failure to comply with any step — including but not limited to verification gates, test phases, audit checkpoints, and review steps — will result in the feature branch being rejected and discarded, requiring a full rework from scratch and loss of all prior work. There is no valid reason to skip, compress, reorder, or omit any step. If a step appears redundant or unnecessary, follow it anyway — the cost of following an extra step is negligible compared to the cost of rework from a skipped step.

> **One step at a time protocol:** Each numbered step is a single unit of work. The orchestrator completes exactly one step, reports the result, and proceeds to the next step without asking for permission. "Combining steps" means performing work that spans multiple plan step numbers in a single operation — regardless of how many tool calls, dispatches, or response turns it takes. The self-check is: "does the work I just completed correspond to exactly one plan step number?" If the work touches files or concerns from step N and step N+1, it is combined. The RED→GREEN transition is a zero-tolerance gate: the RED test MUST be verified as FAILING (by reading its artifact output) before any GREEN implementation begins. Skipping this verification invalidates the entire phase and all work in it.
>
> **Self-remediation protocol:** If the orchestrator combines steps or skips a gate, it MUST self-remediate by reverting only the work belonging to the incorrectly-combined step and re-dispatching from the failed step. Do NOT revert work from correctly-executed prior steps. No halting, no asking for permission, no "should I?" — the answer is always revert the offending step and re-dispatch.

## Self-Review Evidence

| Check | Result | Detail |
|-------|--------|--------|
| Spec coverage | ✅ PASS | All 5 SCs (SC-1 through SC-5) referenced in plan steps |
| Placeholder check | ✅ PASS | No TBD, TODO, or placeholder markers |
| Type consistency | ✅ PASS | All evidence types match spec: SC-1/2/3/4 = string, SC-5 = structural |
| Step-actionability | ✅ PASS | Every step has a concrete action (grep, edit, commit, verify) |
| Pipeline completeness | ✅ PASS | RED → Z3 → GREEN → Z3 → VbC → audit → cross-validate → review-prep |

## Exit Criteria

- **C1.** All 4 string replacements applied correctly: 3 plugin key renames + 1 section header rename
- **C2.** SC-1: `grep '"viewport-editor":' README.md` returns 0 matches
- **C3.** SC-2: `grep '"editor":' README.md` returns 3+ matches
- **C4.** SC-3: `grep 'editor MCP Plugin' README.md` returns 1 match
- **C5.** SC-4: All `"viewport-editor"` occurrences in `command` arrays are unchanged
- **C6.** SC-5: `git diff --stat` shows only `README.md` changed
- **C7.** Plan followed in order with no skipped or combined steps
- **C8.** All verification gates passed (VbC, adversarial audit, cross-validate, regression check)
