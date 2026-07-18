# Phase 03a — trunk-migration-merge

## Phase Metadata

- **Concern:** Merge `dev` into `main`, delete `dev` branch
- **Files:** None (git operations only)
- **SCs:** SC-18, SC-19
- **Dependencies:** Phase 2b (all implementation complete)
- **Entry:** All Phase 1/2 changes committed and pushed
- **Exit:** `dev` merged into `main`, `dev` deleted locally and on remote
- **Cost frame:** Cost is measured in defect-discovery-latency, not model roundtrips. Running verification costs minutes of execution time — a bounded delay that surfaces defects before they reach CI. Skipping a verification step to save a tool call costs the full pipeline of rework when the defect surfaces downstream: diagnosis, fix, re-review, re-CI, re-deploy — each of which costs more roundtrips than the skipped verification would have consumed. Correctness is the only success metric — there is no score for tool-call economy.

## Code Path Coverage

No code paths — pure git operations.

## Cross-Cutting SCs

None.

## Interface Boundaries

None.

## State Transitions

- From: `dev` branch exists with feature commits
- To: `dev` merged into `main`, `dev` deleted

### Item 1: Merge dev into main (SC-18)

- [ ] 34. **Pre-RED baseline (**inline**).** Verify `dev` branch exists and has commits not in `main`: `git log --oneline main..dev`.
- [ ] 35. **GREEN (**inline**).** Merge `dev` into `main` preserving all commits: `git checkout main && git merge dev --no-ff`. **SC gate: this step FAILS if merge does not preserve all commits.**
- [ ] 35a. **GREEN doublecheck (**inline**).** Verify `git log main` contains all commits from `dev`: `git log --oneline dev..main` should be empty.
- [ ] 35b. **REFACTOR (**inline**).** Verify no conflicts during merge, check `git status` is clean.
- [ ] 35c. **Checkpoint commit (**inline**).** `git push origin main`

### Item 2: Delete dev branch (SC-19)

- [ ] 36. **GREEN (**inline**).** Delete `dev` branch locally: `git branch -d dev`. **SC gate: this step FAILS if dev cannot be deleted.**
- [ ] 36a. **GREEN doublecheck (**inline**).** Delete `dev` branch on remote: `git push origin --delete dev`.
- [ ] 36b. **REFACTOR (**inline**).** Verify `git branch -a` shows no `dev` branch.
- [ ] 37. **Checkpoint commit (**inline**).** No commit needed — git operations are self-contained.

#### Phase 03a VbC

- [ ] 37a. **VbC (**clean-room**).** Verify: `dev` merged into `main`, all commits preserved, `dev` deleted locally and on remote. **→ SC-18, SC-19** `evidence_type: string`

**Concern transition:** Leaving merge/delete → entering docs update. Phase 3b depends on Phase 3a's merge being complete.
