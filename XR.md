# Issue Cross-Reference Ledger

Tracks dependency and enablement relationships between all open issues.
Maintained at: `.issues/XR.md`

## Dependency Graph

```mermaid
flowchart LR
    S1["#1: MVP SPEC"] --> P4["#4: MVP PLAN"]
    P4 --> I18["#18: Bug Fixes"]
    I18 --> I17["#17: Clipboard Core"]
    I17 --> I22["#22: Clipboard Stash"]
    I18 --> I23["#23: File New + Save-As"]
    I18 --> I24["#24: File Delete"]
    I18 --> I25["#25: Autosave"]
    I25 --> I26["#26: Diff Apply"]
    I18 --> I27["#27: Search Find"]
    I18 --> I28["#28: Regex Tools"]
    I22 --> I6["#6: Integration Tests"]
    I23 --> I6
    I24 --> I6
    I25 --> I6
    I26 --> I6
    I27 --> I6
    I28 --> I6

    P39["#39/#45: Param Names PR"] -- prereq --> I46["#46: fastmcp switch"]
    I46 -- enables --> I38["#38: Remove session_id"]

    subgraph P46["#46 Plan Phases"]
        P1["P1: Dep Switch"]
        P2["P2: ctx:Context Annotation"]
        P3["P3: In-Memory Client"]
        P4["P4: Server Infra"]
        P5["P5: Session Isolation"]
        P6["P6: Decision Gate"]
        P1 --> P2
        P1 --> P3
        P1 --> P4
        P2 --> P5
        P3 --> P5
        P5 --> P6
    end
```

## Entry Index

| # | Title | Type | Status | Prerequisites | Dependents |
|---|-------|------|--------|--------------|------------|
| 1 | MVP: Viewport-Editor MCP Server | SPEC | open | none | #4 |
| 4 | MVP: Viewport-Editor MCP Server | PLAN | open | #1 | #18, #17, #22, #23, #24, #25, #26, #27, #28, #6 |
| 6 | Phase 5: Integration Tests | plan-sub | open | #18, #17, #22, #23, #24, #25, #26, #27, #28 | none |
| 17 | Clipboard Core (copy/cut/paste) | spec | open | #18 | #22 |
| 18 | Bug Fixes (CRLF, mkstemp, close, tests) | spec | open | #4, #13 | #17, #22, #23, #24, #25, #27, #28, #6 |
| 22 | Clipboard Stash | spec | open | #17 | #6 |
| 23 | File New + Save-As | spec | open | #18 | #6 |
| 24 | File Delete | spec | open | #18 | #6 |
| 25 | Autosave Integration | spec | open | #18, #17 | #26, #6 |
| 26 | Diff Apply | spec | open | #25 | #6 |
| 27 | Search Find | spec | open | #18 | #6 |
| 28 | Regex Tools | spec | open | #18 | #6 |
| 38 | Remove session_id, derive from MCP connection | SPEC-FIX | open | #39, #46 | none |
| 39 | Normalize tool parameter naming | SPEC-FIX | closed (PR #45 merged) | none | #46 |
| 46 | Switch from official mcp to standalone fastmcp | SPEC+PLAN | open | #39 | #38 |

## Enablement Map

| Issue | What it enables | For whom |
|-------|----------------|----------|
| #46 (fastmcp switch) | `ctx.session_id` for connection-derived session identity | #38 |
| #18 (bug fixes) | Stable buffer/file operations | #17, #22, #23, #24, #25, #27, #28 |

## Important Notes (do not track progress here)

- #46 is a prerequisite for #38 — without standalone fastmcp, there is no `ctx.session_id`
- #39/#45 is a prerequisite for #46 — `ctx` is now first parameter, making `ctx: Context` annotation clean
- #38 Phase A depends on #46 Cards 2+3 completing (Context annotations + session_id working)