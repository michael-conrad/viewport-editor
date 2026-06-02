# Synced from GitHub Issue #27 at 2026-06-02T02:47:57Z

## Parent Plan

#4 — MVP: Viewport-Editor MCP Server

## Concern

Locating text in viewport buffers — substring search (default), regex search (with flag), scoped to viewport/file/all_open.

## SCs Covered

| SC | Description |
|----|-------------|
| SC-17 | search:find returns structured results with line numbers, supporting substring (default), regex (with flag), and scope (viewport/file/all_open) |

## SC-to-Task Traceability

| # | Task | SCs | Test Function | Behavioral Evidence Artifact |
|---|------|-----|---------------|------------------------------|
| 1 | RED: search:find returns structured results with line numbers | SC-17 | `test_search_find_substring_default` — line numbers and content returned for substring match | `./tmp/behavioral-evidence-SC-17-substring.log` |
| 2 | Implement search:find (substring default, regex with flag) | SC-17 | `test_search_find_regex_flag` — regex pattern search; `test_search_find_scope_file` — scoped to single file; `test_search_find_scope_viewport` — scoped to viewport | `./tmp/behavioral-evidence-SC-17-regex-scope.log` |
| 3 | Implement search:find scope=all_open | SC-17 | `test_search_find_scope_all_open` — searches across all open viewports | `./tmp/behavioral-evidence-SC-17-all-open.log` |

## Dependencies

- **Requires:** #18 (bug fixes — unicode decode affects search)
- **Blocks:** Integration Tests
- **SAT ordering:** After #18, before Integration Tests

## Verification (behavioral)

Per-SC behavioral evidence artifacts as defined above.

**Regression guard:**
`uv run pytest test/ -k "phase1 or phase2 or p4_search" > ./tmp/behavioral-evidence-regression-search.log 2>&1`

**Feature suite:**
`uv run pytest test/ -k "p4_search" > ./tmp/behavioral-evidence-search.log 2>&1`

**Evidence artifacts are exempt from ./tmp/ cleanup.**

## Workflow Pipeline

Standard pipeline. Feature branch: `feature/p4-search-find`

---

🤖 Co-authored with AI: OpenCode (ollama-cloud/glm-5.1)