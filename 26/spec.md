# Synced from GitHub Issue #26 at 2026-06-02T02:47:48Z

## Parent Plan

#4 — MVP: Viewport-Editor MCP Server

## Concern

Staging diff patches into the viewport buffer — importing unified diff format and applying changes with fuzzy context matching. Includes auto-loading file if not already open.

## SCs Covered

| SC | Description |
|----|-------------|
| SC-23 | diff:apply stages diff into buffer; auto-loads file if not open |

## Out of Scope

- SC-17 (search:find) — separate issue
- SC-28 (regex:test) — separate issue
- SC-29 (regex:escape) — separate issue

## SC-to-Task Traceability

| # | Task | SCs | Test Function | Behavioral Evidence Artifact |
|---|------|-----|---------------|------------------------------|
| 1 | RED: diff:apply stages diff into buffer; auto-loads file | SC-23 | `test_diff_apply_stages_into_buffer` — buffer shows pending changes after diff:apply; `test_diff_apply_auto_loads_unopened` — file automatically opened if not in any viewport | `./tmp/behavioral-evidence-SC-23-apply.log` |
| 2 | Implement diff parser and buffer staging | SC-23 | `test_diff_apply_fuzzy_context_matching` — patch applies with modified context lines; `test_diff_apply_no_match_rejects` — isError when context doesn't match any location | `./tmp/behavioral-evidence-SC-23-fuzzy.log` |

## Dependencies

- **Requires:** #18 (bug fixes), Autosave Integration (diff:apply triggers autosave gate)
- **Blocks:** Integration Tests
- **SAT ordering:** After Autosave Integration, before Integration Tests

## Verification (behavioral)

Per-SC behavioral evidence artifacts as defined above.

**Regression guard:**
`uv run pytest test/ -k "phase1 or phase2 or p3_autosave or p4_diff" > ./tmp/behavioral-evidence-regression-diff.log 2>&1`

**Feature suite:**
`uv run pytest test/ -k "p4_diff" > ./tmp/behavioral-evidence-diff.log 2>&1`

**Evidence artifacts are exempt from ./tmp/ cleanup.**

## Workflow Pipeline

Standard pipeline. Feature branch: `feature/p4-diff-apply`

---

🤖 Co-authored with AI: OpenCode (ollama-cloud/glm-5.1)