# Synced from GitHub Issue #6

## Parent Plan

#4 — MVP: Viewport-Editor MCP Server

## Concern

End-to-end integration testing across all subsystems — viewport, buffer, edit, file ops, clipboard, search, regex, diff.

## SCs Covered

Integration coverage for all prior SCs from all phases.

## SC-to-Task Traceability

| # | Task | Validates | Test Function | Behavioral Evidence Artifact |
|---|------|-----------|---------------|------------------------------|
| 1 | RED: Full buffered workflow integration | All edit+file+diff SCs | `test_integration_buffered_workflow` — open file, edit:replace, diff:show shows changes, file:save writes to disk, viewport:close, verify disk content | `./tmp/behavioral-evidence-P5-workflow-buffered.log` |
| 2 | RED: Full autosave=on workflow | SC-14, SC-24 | `test_integration_autosave_on_workflow` — open with autosave=on, edit:replace, verify disk reflects edit immediately | `./tmp/behavioral-evidence-P5-autosave-on.log` |
| 3 | RED: Autosave toggle workflow | SC-14, SC-32 | `test_integration_autosave_toggle` — open autosave=off, edit, diff:show shows pending, toggle autosave=on, verify flush to disk | `./tmp/behavioral-evidence-P5-autosave-toggle.log` |
| 4 | RED: N-session isolation | SC-26 | `test_integration_session_isolation` — N=2 sessions open same file, each edits independently, verify no cross-session contamination | `./tmp/behavioral-evidence-P5-session-isolation.log` |
| 5 | RED: Conflict detection save rejection | SC-11, SC-25 | `test_integration_conflict_detection` — external file modification between edit and save triggers hard conflict; external modification before edit triggers soft warning | `./tmp/behavioral-evidence-P5-conflict-detection.log` |
| 6 | RED: Clipboard cross-viewport workflow | SC-39, SC-40, SC-41, SC-42 | `test_integration_clipboard_cross_viewport` — copy from viewport A, paste into viewport B, verify content and provenance | `./tmp/behavioral-evidence-P5-clipboard-cross.log` |
| 7 | RED: Clipboard stash-pop workflow | SC-43, SC-44, SC-45 | `test_integration_stash_pop_swap` — copy, stash, edit, pop, verify clipboard restored from stash | `./tmp/behavioral-evidence-P5-stash-pop.log` |

## Dependencies

- **Requires:** #18, #17 (Clipboard Core), #22 (Clipboard Stash), #23 (File New + Save-As), #24 (File Delete), #25 (Autosave Integration), #26 (Diff Apply), #27 (Search Find), #28 (Regex Tools)
- **Blocks:** Nothing (final phase)
- **SAT ordering:** After ALL other issues (proven via Z3 constraint model)

## Verification (behavioral)

**Full suite (implicit cumulative regression guard):**
`uv run pytest test/ > ./tmp/behavioral-evidence-P5-full-suite.log 2>&1` — complete test suite passes. This is the ultimate regression check — all P1+P2+P3+P4+P5 tests must pass together.

**Evidence artifacts are exempt from ./tmp/ cleanup per the spec §Behavioral Evidence Capture Protocol and survive until PR merge cleanup.**

Feature branch: `feature/p5-integration`

---

🤖 Co-authored with AI: OpenCode (glm-5.1)