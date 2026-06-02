# Synced from GitHub Issue #13

# [PLAN] Remediate SC-13 atomic write + SC-38 unicode decode

Spec: #12 — 5 SCs (4 behavioral, 1 string), 2 TDD items

## Goal

Fix 2 behavioral SC failures found by adversarial audit: make `file:save` atomic (temp-file + `os.replace`) and wire `_decode_unicode_escapes` into the edit pipeline so `\uNNNN` input in show mode decodes to real characters.

## Verification Mandate

All SCs are `behavioral` except SC-FIX-CLEAN (`string`). Behavioral tests must execute real runtime code (pytest) and observe the output. Evidence artifacts to `./tmp/`.

## Items

### Item 1: SC-13 atomic write in `_flush_entry()`

- **RED**: Behavioral test `test_sc13_atomic_write` verifying temp-file + rename pattern
- **GREEN**: Replace direct `open(path, "w")` with temp file + `os.replace()` in `_flush_entry()`
- **REFACTOR**: Verify all 48 existing P1+P2 tests still pass

### Item 2: SC-38 wire `_decode_unicode_escapes()` into edit pipeline

- **RED**: Behavioral test `test_sc38_unicode_decode_in_edit` sending `\uNNNN` as edit input
- **GREEN**: Apply `_decode_unicode_escapes()` to `old_text` and `new_text` in `_handle_edit_action()`
- **REFACTOR**: Verify all 48 existing P1+P2 tests still pass; grep-confirm no dead code

## Verification

- `uv run pytest test/ -k "phase1 or phase2"` — cumulative regression pass
- New SC-13 and SC-38 behavioral tests pass
- Grep: `_decode_unicode_escapes` called from tool handler

## Architecture

No architectural changes. Both fixes are localized to single functions.

## Interdependencies

- **Blocks:** #5 (Phase 3 file:save shares `_flush_entry()`), #17 (clipboard depends on correct buffer behavior), #6 (integration tests must cover atomic write)
- **Required-by:** #5, #8, #17, #6
- **SAT ordering:** #13 must complete before #5, #8, #17, and #6 (proven via Z3 constraint model)

STATUS: draft

🤖 Co-authored with AI: OpenCode (ollama-cloud/deepseek-v4-flash)