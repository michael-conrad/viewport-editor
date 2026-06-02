# Synced from GitHub Issue #28 at 2026-06-02T02:48:04Z

## Parent Plan

#4 — MVP: Viewport-Editor MCP Server

## Concern

Regex utility tools — testing patterns against text and escaping metacharacters for safe use in search patterns.

## SCs Covered

| SC | Description |
|----|-------------|
| SC-28 | regex:test returns match positions for valid patterns; isError on invalid patterns |
| SC-29 | regex:escape escapes all 12 regex metacharacters; plain text unchanged |

## SC-to-Task Traceability

| # | Task | SCs | Test Function | Behavioral Evidence Artifact |
|---|------|-----|---------------|------------------------------|
| 1 | RED: regex:test returns match positions for valid patterns | SC-28 | `test_regex_test_returns_match_positions` — start/end positions for each match; `test_regex_test_no_match` — returns empty results | `./tmp/behavioral-evidence-SC-28.log` |
| 2 | Implement regex:test | SC-28 | `test_regex_test_capture_groups` — capture groups returned; `test_regex_test_invalid_pattern` — isError on invalid regex | `./tmp/behavioral-evidence-SC-28-invalid.log` |
| 3 | RED: regex:escape escapes metacharacters correctly | SC-29 | `test_regex_escape_dot` — `.` becomes `\.`; `test_regex_escape_asterisk` — `*` becomes `\*` | `./tmp/behavioral-evidence-SC-29.log` |
| 4 | Implement regex:escape | SC-29 | `test_regex_escape_all_metacharacters` — all 12 regex metacharacters escaped; `test_regex_escape_noop_on_safe_string` — plain text unchanged | `./tmp/behavioral-evidence-SC-29-comprehensive.log` |

## Dependencies

- **Requires:** #18 (bug fixes)
- **Blocks:** Integration Tests
- **SAT ordering:** After #18, before Integration Tests

## Verification (behavioral)

Per-SC behavioral evidence artifacts as defined above.

**Regression guard:**
`uv run pytest test/ -k "phase1 or phase2 or p4_regex" > ./tmp/behavioral-evidence-regression-regex.log 2>&1`

**Feature suite:**
`uv run pytest test/ -k "p4_regex" > ./tmp/behavioral-evidence-regex.log 2>&1`

**Evidence artifacts are exempt from ./tmp/ cleanup.**

## Workflow Pipeline

Standard pipeline. Feature branch: `feature/p4-regex-tools`

---

🤖 Co-authored with AI: OpenCode (glm-5.1)