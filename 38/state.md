---
issue_number: 38
title: "[SPEC-FIX] Remove agent-provided session_id, derive from MCP connection context"
state: open
labels:
  - "SPEC-FIX"
created: 2026-06-03T14:26:34Z
updated: 2026-06-07T04:15:00Z
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
  phase_a:
    title: "Core Session Derivation"
    depends_on: 46
    description: "Remove session_id from 6 tool stubs + 19 handlers in server.py. Extract ctx.session_id at entry point."
  phase_b:
    title: "Manager-Level Cleanup"
    depends_on: phase_a
    description: "Remove session_id from ViewportManager (29 methods), BufferManager (9 methods), and 16 test files"
  phase_c:
    title: "MCP Plugin Behavioral Documentation"
    depends_on: phase_a + phase_b
    description: "Produce docs/mcp-plugin-behavior.md documenting observed session behavior"
---