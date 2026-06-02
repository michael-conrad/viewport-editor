# Synced from GitHub Issue #24 at 2026-06-02T02:47:27Z

## Parent Plan

#4 — MVP: Viewport-Editor MCP Server

## Concern

Removing files from disk with safety checks (rejection when buffer is dirty).

## SCs Covered

| SC | Description |
|----|-------------|
| SC-30 | file:delete removes file on disk; rejects when buffer has uncommitted changes |

## SC-to-Task Traceability

| # | Task | SCs | Test Function | Behavioral Evidence Artifact |
|---|------|-----|---------------|------------------------------|
| 1 | RED: file:delete removes file on disk | SC-30 | `test_file_delete_removes_file` — file no longer exists on disk after file:delete | `./tmp/behavioral-evidence-SC-30.log` |
| 2 | Implement file:delete | SC-30 | `test_file_delete_dirty_buffer_rejects` — deleting file with dirty buffer returns isError | `./tmp/behavioral-evidence-SC-30-dirty.log` |

## Dependencies

- **Requires:** #18 (bug fixes)
- **Blocks:** Integration Tests
- **SAT ordering:** After #18, before Integration Tests

## Verification (behavioral)

Per-SC behavioral evidence artifacts as defined above.

**Regression guard:**
`uv run pytest test/ -k "phase1 or phase2 or p3_delete" > ./tmp/behavioral-evidence-regression-delete.log 2>&1`

**Feature suite:**
`uv run pytest test/ -k "p3_delete" > ./tmp/behavioral-evidence-delete.log 2>&1`

**Evidence artifacts are exempt from ./tmp/ cleanup.**

## Workflow Pipeline

Standard pipeline. Feature branch: `feature/p3-file-delete`

---

🤖 Co-authored with AI: OpenCode (ollama-cloud/glm-5.1)