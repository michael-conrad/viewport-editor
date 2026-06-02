# Synced from GitHub Issue #25 at 2026-06-02T02:47:41Z

## Parent Plan

#4 — MVP: Viewport-Editor MCP Server

## Concern

The autosave=on behavior across all operations — file:save/diff:show/file:discard return empty state when autosave is on, and viewport:close with dirty buffer auto-saves to disk.

## SCs Covered

| SC | Description |
|----|-------------|
| SC-14 | With autosave=on, file:save/diff:show/file:discard return empty/no-op state |
| SC-24 | viewport:close with dirty buffer and autosave=on flushes changes to disk (not silently discards) |

Note: SC-24's bug fix (inverted close logic) is in #18. This issue adds the full behavioral tests and the autosave=on integration across all operations.

## Out of Scope

- SC-LF-2, SC-TMP-2, SC-LF-3 (file:new/save-as CRLF/mkstemp) — handled in File New + Save-As issue
- SC-30 (file:delete) — handled in File Delete issue
- SC-42 (cut/paste autosave gate) — handled in Clipboard Core (#17)

## SC-to-Task Traceability

| # | Task | SCs | Test Function | Behavioral Evidence Artifact |
|---|------|-----|---------------|------------------------------|
| 1 | RED: With autosave=on, file:save/diff:show/discard return empty state | SC-14 | `test_autosave_on_file_save_noop` — save returns "no pending changes"; `test_autosave_on_diff_show_empty` — diff:show returns empty diff; `test_autosave_on_discard_empty` — file:discard returns empty state | `./tmp/behavioral-evidence-SC-14.log` |
| 2 | Implement autosave=on gate in file:save, diff:show, file:discard | SC-14 | Verify all three operations return no-op/empty when autosave=on | `./tmp/behavioral-evidence-SC-14-gate.log` |
| 3 | RED: viewport:close with dirty buffer auto-saves | SC-24 | `test_viewport_close_dirty_auto_saves` — dirty buffer flushed to disk on close | `./tmp/behavioral-evidence-SC-24.log` |
| 4 | Implement auto-save on close (behavioral verification) | SC-24 | `test_viewport_close_already_closed_noop` — closing already-closed viewport is no-op; `test_viewport_close_clean_noop` — clean close doesn't write unnecessarily | `./tmp/behavioral-evidence-SC-24-noop.log` |

## Dependencies

- **Requires:** #18 (bug fixes — SC-24 bug fix for inverted close logic), #17 (Clipboard Core — cut/paste autosave gate patterns)
- **Blocks:** Diff Apply (diff:apply uses autosave gate), Integration Tests
- **SAT ordering:** After #18 and #17, before Diff Apply

## Verification (behavioral)

Per-SC behavioral evidence artifacts as defined above.

**Regression guard:**
`uv run pytest test/ -k "phase1 or phase2 or p3_autosave" > ./tmp/behavioral-evidence-regression-autosave.log 2>&1`

**Feature suite:**
`uv run pytest test/ -k "p3_autosave" > ./tmp/behavioral-evidence-autosave.log 2>&1`

**Evidence artifacts are exempt from ./tmp/ cleanup.**

## Workflow Pipeline

Standard pipeline. Feature branch: `feature/p3-autosave`

---

🤖 Co-authored with AI: OpenCode (ollama-cloud/glm-5.1)