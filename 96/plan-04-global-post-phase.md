# Phase 04 — global-post-phase

## Phase Metadata

- **Concern:** Full regression, audit, finishing checklist, review-prep, cleanup
- **Files:** All
- **SCs:** SC-12, SC-13
- **Dependencies:** Phase 3b (trunk migration docs complete)
- **Entry:** All phases complete and committed
- **Exit:** Regression passes, audit passes, finishing checklist complete, review-prep complete, cleanup complete
- **Cost frame:** Cost is measured in defect-discovery-latency, not model roundtrips. Running verification costs minutes of execution time — a bounded delay that surfaces defects before they reach CI. Skipping a verification step to save a tool call costs the full pipeline of rework when the defect surfaces downstream: diagnosis, fix, re-review, re-CI, re-deploy — each of which costs more roundtrips than the skipped verification would have consumed. Correctness is the only success metric — there is no score for tool-call economy.

## Code Path Coverage

All modified files.

## Cross-Cutting SCs

- SC-12: Full regression suite
- SC-13: Anti-lobotomization audit

## Interface Boundaries

All modified interfaces.

## State Transitions

- From: All implementation complete
- To: Branch ready for PR, cleanup complete

- [ ] 42. **Collect behavioral evidence (**inline**).** Copy behavioral test artifacts from `{project_root}/tmp/behavioral-evidence-*/` into `{project_root}/tmp/96/artifacts/`.
- [ ] 43. **Audit (**clean-room**).** Dispatch adversarial audit of all deliverables: verify spec fidelity, plan coherence, code quality, test coverage. Dispatch via `skill({name: "audit"})` → `task(prompt: "execute audit task from audit skill")`.
- [ ] 44. **Cross-validate (**clean-room**).** Cross-validate verification results: ensure all SCs have PASS verdicts with correct evidence types. **→ SC-13**
- [ ] 45. **Regression check (**inline**).** Run `uv run pytest test/` — confirm zero regressions. **→ SC-12**
- [ ] 46. **Finishing checklist (**sub-agent**).** Run finishing-a-development-branch checklist: verify uncommitted changes, run linters, verify branch readiness. Dispatch via `skill({name: "finishing-a-development-branch"})` → `task(prompt: "execute checklist task from finishing-a-development-branch skill")`.
- [ ] 47. **Review-prep (**sub-agent**).** Prepare PR body, generate compare URL, verify base branch. Dispatch via `skill({name: "git-workflow"})` → `task(prompt: "execute review-prep task from git-workflow-pr skill")`.

#### Phase 04 VbC

- [ ] 47a. **VbC (**clean-room**).** Verify: audit PASS, cross-validate PASS, regression PASS, finishing checklist complete, review-prep complete. **→ SC-12, SC-13** `evidence_type: behavioral`
