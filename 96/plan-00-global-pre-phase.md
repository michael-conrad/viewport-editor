# Phase 00 — global-pre-phase

## Phase Metadata

- **Concern:** Branch setup, baseline verification, environment readiness
- **Files:** None (no source changes)
- **SCs:** None
- **Dependencies:** None
- **Entry:** Authorization received, plan approved
- **Exit:** Feature branch created, baseline tests pass, environment ready
- **Cost frame:** Cost is measured in defect-discovery-latency, not model roundtrips. Running verification costs minutes of execution time — a bounded delay that surfaces defects before they reach CI. Skipping a verification step to save a tool call costs the full pipeline of rework when the defect surfaces downstream: diagnosis, fix, re-review, re-CI, re-deploy — each of which costs more roundtrips than the skipped verification would have consumed. Correctness is the only success metric — there is no score for tool-call economy.

## Code Path Coverage

No code paths covered — this phase is purely operational.

## Cross-Cutting SCs

None.

## Interface Boundaries

None.

## State Transitions

- From: Pre-implementation (no branch)
- To: Feature branch created, baseline verified

- [ ] 1. **Coherence gate (**clean-room**).** Verify plan coherence against spec: check all SCs are mapped to phases, all file paths exist, all function signatures match source. **→ SC-all**
- [ ] 2. **Pre-work (**sub-agent**).** Create feature branch `feature/96-auto-reload-viewport-buffer`, sync submodules, verify provenance. Dispatch via `skill({name: "git-workflow"})` → `task(prompt: "execute pre-work task from git-workflow-branch skill")`.
- [ ] 3. **Baseline verification (**inline**).** Run `uv run pytest test/` to confirm all tests pass before any changes. Record baseline test count and pass rate.

#### Phase 00 VbC

- [ ] 3a. **VbC (**clean-room**).** Verify: branch exists, baseline tests pass, no uncommitted changes. **→ SC-all** `evidence_type: structural`
