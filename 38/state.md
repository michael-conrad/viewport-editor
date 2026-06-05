---
issue_number: 38
title: "[SPEC-FIX] Remove agent-provided session_id, derive from MCP connection context"
state: open
labels:
  - "SPEC-FIX"
created: 2026-06-03T14:26:34Z
updated: 2026-06-04T13:45:12Z
prerequisites:
  - issue: 39
    title: "Parameter name normalization"
    status: completed
    pr: 45
  - issue: 46
    title: "Switch from official mcp SDK to standalone fastmcp"
    status: open
dependents: []
workflow_phase: blocked
branch: TBD
blockers:
  - issue: 46
    reason: "Standalone fastmcp must be in place for ctx.session_id to exist"
phase_plan:
  phase_a:
    title: "Core Session Derivation"
    depends_on: 46
    description: "Change ctx: Any → ctx: Context, extract session_id from ctx.session_id, remove session_id tool parameter"
  phase_b:
    title: "Manager-Level Cleanup"
    depends_on: phase_a
    description: "Remove session_id from ViewportManager, BufferManager, test fixtures"
---