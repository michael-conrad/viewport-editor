# Phase 01a — file-ops-format-warning

## Phase Metadata

- **Concern:** Add `format_external_modification_warning()` to `file_ops.py`
- **Files:** `src/viewport_editor/file_ops.py`
- **SCs:** SC-9, SC-10, SC-14
- **Dependencies:** Phase 00 (branch + baseline)
- **Entry:** Feature branch exists, baseline verified
- **Exit:** `format_external_modification_warning()` defined and produces correct output
- **Cost frame:** Cost is measured in defect-discovery-latency, not model roundtrips. Running verification costs minutes of execution time — a bounded delay that surfaces defects before they reach CI. Skipping a verification step to save a tool call costs the full pipeline of rework when the defect surfaces downstream: diagnosis, fix, re-review, re-CI, re-deploy — each of which costs more roundtrips than the skipped verification would have consumed. Correctness is the only success metric — there is no score for tool-call economy.

## Code Path Coverage

- `file_ops.py`: New function `format_external_modification_warning()` co-located with existing `format_conflict_warning()` at module level

## Cross-Cutting SCs

- SC-9: Auto-reload notice format (string check)
- SC-10: Stronger dirty conflict format includes `severity: external_modification`

## Interface Boundaries

- New function `file_ops.format_external_modification_warning(warning: dict) -> str`
- Consumed by `ViewportManager.auto_reload_if_clean()` (Phase 1b)

## State Transitions

- From: No `format_external_modification_warning` function exists
- To: Function defined with correct YAML output format

- [ ] 4. **Pre-RED baseline (**inline**).** Verify `format_external_modification_warning` does not exist yet: `grep -rn "format_external_modification_warning" src/`.
- [ ] 5. **RED (**sub-agent**).** Write unit test for SC-14 in `test/test_auto_reload_unit.py`: pass a conflict dict, verify output YAML contains `severity: external_modification` and the prose note about overwriting external changes. Test must fail because function doesn't exist yet.
- [ ] 6. **GREEN (**sub-agent**).** Implement `format_external_modification_warning(warning: dict) -> str` in `src/viewport_editor/file_ops.py` co-located with `format_conflict_warning()`. The function must produce a YAML string with `severity: external_modification` key and a prose note about overwriting external changes. The exact output format is defined in the spec — implement per that specification. **SC gate: this step FAILS if the output format does not match the spec.**
- [ ] 7. **GREEN doublecheck (**inline**).** Run the unit test from step 5 — confirm PASS.
- [ ] 7a. **REFACTOR (**inline**).** Clean up cross-references: verify `format_external_modification_warning` is importable from `file_ops`, check no stale imports or dead code remain. Verify consistency with existing `format_conflict_warning` naming and signature patterns.
- [ ] 8. **Checkpoint commit (**inline**).** `git add -A && git commit -m "feat: add format_external_modification_warning to file_ops"`

#### Phase 01a VbC

- [ ] 8a. **VbC (**clean-room**).** Verify: function exists, output format matches spec, unit test passes. **→ SC-9, SC-10, SC-14** `evidence_type: string` (SC-9, SC-10), `evidence_type: behavioral` (SC-14)
- [ ] 8b. **Behavioral test evaluation (**clean-room**).** Run `uv run pytest test/test_auto_reload_unit.py -v` — confirm PASS. **→ SC-14** `evidence_type: behavioral`

**Concern transition:** Leaving file-ops warning format → entering viewport auto-reload method. Phase 1b depends on Phase 1a's `format_external_modification_warning()`.
