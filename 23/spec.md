# Synced from GitHub Issue #23 at 2026-06-02T05:44:52Z

## Parent Plan

#4 — MVP: Viewport-Editor MCP Server

## Concern

Creating new files (`file:new`) and saving to a different path (`file:save-as`), including CRLF preservation and safe temp file creation for save-as (SC-LF-2 and SC-TMP-2, moved from #18 because they reference unimplemented code).

## SCs Covered

| SC | Origin | Description |
|----|--------|-------------|
| SC-15 | #5 | file:new creates file and opens viewport with autosave=off |
| SC-16 | #5 | file:save-as with force=false rejects existing target; force=true overwrites |
| SC-LF-2 | #18 (moved) | save-as handler opens temp file with newline="" — CRLF files preserved after save-as |
| SC-TMP-2 | #18 (moved) | save-as handler uses tempfile.mkstemp(dir=...) instead of string concatenation for temp path |
| SC-LF-3 | #18 (moved) | file:new opens file with newline="" for consistency |

## Out of Scope

- SC-14, SC-24 (autosave integration) — handled in separate Autosave Integration issue
- SC-30 (file:delete) — handled in separate File Delete issue

## SC-to-Task Traceability

| # | Task | SCs | Test Function | Behavioral Evidence Artifact |
|---|------|-----|---------------|------------------------------|
| 1 | RED: file:new creates file and opens viewport with autosave=off | SC-15, SC-LF-3 | `test_file_new_creates_file` — file exists on disk after file:new; `test_file_new_autosave_off` — viewport opens with autosave=off; `test_file_new_newline_empty` — created file has newline="" (CRLF-safe) | `./tmp/behavioral-evidence-SC-15.log` |
| 2 | Implement file:new with newline="" | SC-15, SC-LF-3 | `test_file_new_existing_rejects` — file:new on existing path returns isError | `./tmp/behavioral-evidence-SC-15-existing.log` |
| 3 | RED: file:save-as rejects existing target when force=false | SC-16 | `test_file_save_as_rejects_existing` — isError when target exists and force=false | `./tmp/behavioral-evidence-SC-16-reject.log` |
| 4 | Implement file:save-as | SC-16, SC-LF-2, SC-TMP-2 | `test_file_save_as_force_overwrites` — target overwritten when force=true; `test_file_save_as_crlf_preserved` — CRLF file preserved after save-as; `test_file_save_as_mkstemp` — save-as uses mkstemp for temp path | `./tmp/behavioral-evidence-SC-16-force.log` |

## Dependencies

- **Requires:** #18 (bug fixes — CRLF/mkstemp in flush_entry must be fixed first)
- **Blocks:** Autosave Integration, Integration Tests
- **SAT ordering:** After #18, before Autosave Integration

## Verification (behavioral)

Per-SC behavioral evidence artifacts as defined above.

**Regression guard:**
`uv run pytest test/ -k "phase1 or phase2 or p3_filenew" > ./tmp/behavioral-evidence-regression-filenew.log 2>&1`

**Feature suite:**
`uv run pytest test/ -k "p3_filenew" > ./tmp/behavioral-evidence-filenew.log 2>&1`

**Evidence artifacts are exempt from ./tmp/ cleanup.**

## Workflow Pipeline

Standard pre-work through post-PR cleanup pipeline (see #18 for template).

Feature branch: `feature/p3-filenew-saveas`

---

🤖 Co-authored with AI: OpenCode (ollama-cloud/glm-5.1)