---
issue_number: 38
title: "[SPEC-FIX] Remove agent-provided session_id, derive from MCP connection context"
state: open
labels:
  - "SPEC-FIX"
created: 2026-06-03T14:26:34Z
updated: 2026-06-07T18:00:00Z
prerequisites:
  - issue: 39
    title: "Parameter name normalization"
    status: completed
    pr: 45
  - issue: 46
    title: "Switch from official mcp SDK to standalone fastmcp"
    status: completed
dependents: []
workflow_phase: spec_ready
branch: TBD
blockers: []
phase_plan:
  card_1:
    title: "Core Session Derivation"
    depends_on: 46
    description: "Remove session_id from 6 tool stubs + 19 handlers in server.py. Extract ctx.session_id at entry point."
    status: completed
    pr: 49
  card_2:
    title: "SC-6 Observational Test"
    depends_on: card_1
    description: "Empirical test documenting two-client session behavior. No assertions, observational only."
    status: pending
  card_3:
    title: "Observational Documentation + Rollback"
    depends_on: card_2
    description: "docs/mcp-plugin-behavior.md citing test output from SC-1 through SC-6. Tag fix/pre-session-id-refactor, close issue #38."
    status: pending
---