# Synced from GitHub Issue #9

## Parent Plan

#4 — MVP: Viewport-Editor MCP Server

## Concern

The core editing subsystem — edits always stage into buffer, inspected via diff, flushed on explicit save or autosave.

## SCs Covered

SC-9, SC-10, SC-11, SC-12, SC-13, SC-18, SC-19, SC-20, SC-21, SC-22, SC-25

SC-25 (soft conflict warning on edit operations) via shared conflict layer from Phase 1.

Note: SC-23 (diff:apply) is a Phase 4 concern — it belongs to the diff tool, not the edit tool. Removed from Phase 2's SCs list per audit finding.

## SC-to-Task Traceability

Each key task maps to specific SCs and a behavioral test that must produce a passing artifact.

| # | Task | SCs | Test Function | Behavioral Evidence Artifact |
|---|------|-----|---------------|------------------------------|
| 1 | RED: Buffer model — apply edits, track original vs pending | SC-9, SC-10, SC-13, SC-18, SC-19, SC-20, SC-21, SC-22 | `test_buffer_model_apply_and_track` — verify buffer tracks pending state diverging from disk original | `./tmp/behavioral-evidence-SC-9-10-13-18-22-buffer.log` |
| 2 | Implement buffer with line tracking | (same SCs, GREEN phase) | `test_buffer_line_tracking_preserves_endings` — verify \n, \r\n, \r endings preserved | `./tmp/behavioral-evidence-SC-line-endings.log` |
| 3 | RED: edit:replace stages into buffer, file unchanged on disk (autosave=off) | SC-9 | `test_edit_replace_stages_autosave_off` — file content on disk unchanged, buffer diverges | `./tmp/behavioral-evidence-SC-9.log` |
| 4 | Implement edit:replace with buffer integration | SC-9 | `test_edit_replace_integration` — multiple replaces, boundary cases | `./tmp/behavioral-evidence-SC-9-integration.log` |
| 5 | RED: edit:replace with autosave=on writes to disk atomically | SC-13 | `test_edit_replace_autosave_on_flushes` — file content on disk changes immediately after edit | `./tmp/behavioral-evidence-SC-13.log` |
| 6 | Implement autosave flush after edit | SC-13 | `test_autosave_flush_atomicity` — verify atomic write (temp + rename) | `./tmp/behavioral-evidence-SC-13-atomic.log` |
| 7 | RED: diff:show returns correct unified diff of pending changes | SC-10 | `test_diff_show_returns_unified_diff` — verify unified diff format against known before/after | `./tmp/behavioral-evidence-SC-10.log` |
| 8 | Implement diff:show | SC-10 | `test_diff_show_empty_no_pending` — verify no diff shown when buffer clean | `./tmp/behavioral-evidence-SC-10-clean.log` |
| 9 | RED: file:save rejects on mtime/size mismatch OR missing file (unless force) | SC-11 | `test_file_save_rejects_stale_mtime` — isError=true on mismatch + force=false; `test_file_save_force_overrides` — passes on force=true | `./tmp/behavioral-evidence-SC-11.log` |
| 10 | Implement hard conflict check on save | SC-11 | `test_file_save_missing_file_rejects` — file deleted on disk before save | `./tmp/behavioral-evidence-SC-11-missing.log` |
| 11 | RED: file:discard reverts buffer to disk state | SC-12 | `test_file_discard_reverts` — buffer matches disk after discard, dirty flag cleared | `./tmp/behavioral-evidence-SC-12.log` |
| 12 | Implement file:discard | SC-12 | `test_file_discard_clean_noop` — discarding a clean buffer is no-op | `./tmp/behavioral-evidence-SC-12-noop.log` |
| 13 | RED: replace-all, insert-lines, delete-lines, swap-lines, move-lines each stage correctly | SC-18, SC-19, SC-20, SC-21, SC-22 | `test_edit_replace_all_stages`, `test_edit_insert_lines_stages`, `test_edit_delete_lines_stages`, `test_edit_swap_lines_stages`, `test_edit_move_lines_stages` | `./tmp/behavioral-evidence-SC-18.log` through `./tmp/behavioral-evidence-SC-22.log` |
| 14 | Implement remaining edit actions | SC-18, SC-19, SC-20, SC-21, SC-22 | `test_edit_replace_all_autosave_on`, `test_edit_insert_at_boundary`, etc. | `./tmp/behavioral-evidence-SC-18-22-integration.log` |
| 15 | RED: Soft conflict warning on edit operations via shared conflict layer | SC-25 | `test_edit_conflict_warning_on_external_change` — edit after external file modification returns YAML warning | `./tmp/behavioral-evidence-SC-25-edit.log` |
| 16 | Verify SC-25 edit-side conflict warnings | SC-25 | `test_edit_conflict_warning_viewport_still_works` — verify viewport conflict checks unbroken after edit conflict layer changes | `./tmp/behavioral-evidence-SC-25-cross-phase.log` |

## Dependency

Phase 1 complete (viewport + session infrastructure)

## Verification (behavioral — all SCs are behavioral)

Per-SC behavioral evidence artifacts must be generated as defined in the SC-to-Task Traceability table above.

**Cumulative regression guard (Phase 1 backward compatibility):**
`uv run pytest test/ -k "phase1 or phase2" > ./tmp/behavioral-evidence-regression-phase2.log 2>&1` — all P1 tests must still pass after P2 changes. This catches cross-phase breakage on shared modules (conflict.py, server.py, viewport.py).

**Full Phase 2 suite:**
`uv run pytest test/ -k "phase2" > ./tmp/behavioral-evidence-phase2.log 2>&1` — all phase 2 tests pass.

**Evidence artifacts are exempt from ./tmp/ cleanup per the spec §Behavioral Evidence Capture Protocol and survive until PR merge cleanup.**

---

🤖 Co-authored with AI: OpenCode (ollama-cloud/deepseek-v4-flash)