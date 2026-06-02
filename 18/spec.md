---
id: 18
title: '[SPEC-FIX] flush_entry temp file not safely created; CRLF corruption on save; shallow tests'
state: open
author: michael-conrad
labels:
  - '[SPEC-FIX]'
  - needs-approval
created: '2026-06-01T03:47:45Z'
updated: '2026-06-02T02:44:32Z'
remote_url: https://github.com/michael-conrad/viewport-editor/issues/18
---

# [SPEC-FIX] flush_entry temp file not safely created; CRLF corruption on save; shallow tests

## Problem

Defects in the atomic write implementation discovered during adversarial audit of Plan #13, confirmed by dual cross-family drift audit (Gemma4:31b + Qwen3.5:35b, consensus FAIL).

### Defect 1: CRLF line ending corruption on save

**Spec requirement (Issue #1 §Key Design Properties #2):** "Preserved line endings — `splitlines(keepends=True)` stores lines with their original terminators. Phase 2 writes must use `"".join(lines)` with `open(path, "w", newline="")` to preserve original line endings on save."

**Current behavior:** `flush_entry()` in `file_ops.py:64` uses `open(tmp, "w")` without `newline=""`. Python's text mode rewrites `\r\n` to the platform default line separator, corrupting files that use CRLF (`\r\n`) line endings.

**Impact:** Any file with `\r\n` or `\r` line endings will have those endings silently converted to `\n` on save, regardless of the `line_ending` field reported to the agent at open time.

### Defect 2: Unsafe temp file creation (TOCTOU race)

**Current behavior:** `flush_entry()` in `file_ops.py:62` uses `resolved_path + ".tmp"` for the temp file path. This creates a predictable temp file name.

**Impact:** A predictable temp path creates a TOCTOU race condition — an attacker with local access could create a symlink at the `.tmp` path before the write, causing data to be written to an unintended location.

**Risk analysis in the original spec (#12 §Risk Analysis)** explicitly recommended: "Use `tempfile.mkstemp(dir=os.path.dirname(resolved_path))` to keep temp on same filesystem."

### Defect 3: Shallow behavioral test for atomic write

**Current behavior:** `test_sc13_atomic_write_integrity` in `test/test_phase2_edit_diff.py` only verifies that file content changed and no `.tmp` file remains. It does NOT verify CRLF line ending preservation or `mkstemp` usage — the two critical risk mitigations from spec #12.

**Impact:** The behavioral test gives false confidence. A PASS on the current test does not prove the atomic write meets spec #12 risk requirements.

### Defect 4: No behavioral test for SC-38 unicode decode

**Current behavior:** `_decode_unicode_escapes()` is wired into `_handle_edit_action()` (server.py:609-610), but zero behavioral tests verify that `\uNNNN` input in edit operations actually decodes to real Unicode characters.

**Impact:** SC-38 cannot be verified. A regression in the decode wiring would not be caught by any test.

### Defect 5: Inverted close auto-save logic

**Current behavior:** `viewport.py:140` close() auto-save logic is inverted — it saves when the viewport has no dirty changes, and does not save when there are dirty changes.

**Impact:** Calling `viewport:close` on a viewport with dirty changes and `autosave=on` results in data loss — the dirty changes are silently discarded.

### Out of Scope (moved to Phase 3 — #5)

The following SCs reference code that does not yet exist (`save-as` handler, `file:new` handler) and are UNSAT in Z3 dependency modeling. They move to Issue #5:

- **SC-LF-2** (`save-as` opens temp file with `newline=""`) → #5 Task 6 (save-as implementation)
- **SC-TMP-2** (`save-as` uses `mkstemp`) → #5 Task 6 (save-as implementation)
- **SC-LF-3** (`file:new` opens file with `newline=""`) → #5 Task 4 (file:new implementation)

## Affected Files

| File | Defect | Change |
|------|--------|--------|
| `src/viewport_editor/file_ops.py:62` | Unsafe temp path | `resolved_path + ".tmp"` → `tempfile.mkstemp(dir=os.path.dirname(resolved_path))` |
| `src/viewport_editor/file_ops.py:64` | CRLF corruption | `open(tmp, "w")` → `open(tmp, "w", newline="")` |
| `src/viewport_editor/viewport.py:140` | Inverted auto-save logic | Fix close() auto-save condition |
| `test/test_phase2_edit_diff.py` | Shallow atomic write test | Enhance with CRLF fixture + mkstemp verification |
| `test/test_phase2_edit_diff.py` | Missing unicode decode test | Add SC-38 behavioral test |

## Success Criteria

| ID | Criterion | Evidence Type |
|----|-----------|---------------|
| SC-LF-1 | `flush_entry` opens temp file with `newline=""` — CRLF files preserve `\r\n` after save | behavioral |
| SC-TMP-1 | `flush_entry` uses `tempfile.mkstemp(dir=...)` instead of string concatenation for temp path | behavioral |
| SC-24 | `viewport:close` with dirty buffer and autosave=on flushes changes to disk (not silently discards) | behavioral |
| SC-36 | Full CRLF round-trip: open CRLF file → edit → save → verify disk still contains `\r\n` | behavioral |
| SC-38 | Behavioral test verifies `\uNNNN` input decodes to real Unicode character in buffer | behavioral |
| SC-TEST-ATOMIC | Behavioral test for atomic write verifies CRLF preservation and mkstemp usage (not just content change) | behavioral |
| SC-REG | All 51 existing tests pass after fixes (not 63 — corrected count) | behavioral |

## TDD Items

### Item 1: CRLF preservation in flush_entry

- **RED**: Write behavioral test that creates a file with `\r\n` endings, opens a viewport, edits it, saves, and verifies the on-disk file still contains `\r\n` (read in binary mode, assert `b"\r\n"` present)
- **GREEN**: Add `newline=""` to `open(tmp, "w")` in `file_ops.py:64`
- **REFACTOR**: Run full test suite (51 tests)

### Item 2: mkstemp in flush_entry

- **RED**: Write behavioral test verifying `flush_entry` uses `tempfile.mkstemp` (mock/patch `tempfile.mkstemp` and verify it is called with correct `dir` argument)
- **GREEN**: Replace `resolved_path + ".tmp"` with `tempfile.mkstemp(dir=os.path.dirname(resolved_path))` in `file_ops.py:62`. Close the fd from mkstemp, open via `os.fdopen(fd, "w", newline="")` to combine mkstemp + newline preservation.
- **REFACTOR**: Run full test suite

### Item 3: Fix inverted close auto-save logic

- **RED**: Write behavioral test for SC-24: open viewport with autosave=on, edit buffer (dirty), close viewport, verify dirty changes flushed to disk
- **GREEN**: Fix the auto-save condition in `viewport.py:140` — save when dirty, not when clean
- **REFACTOR**: Also test: close clean viewport → no unnecessary write; close already-closed viewport → no-op

### Item 4: CRLF round-trip integration test

- **RED**: Write behavioral test for SC-36: create CRLF file → open viewport → edit (replace a line) → save → read file in binary mode → verify `\r\n` terminators preserved throughout
- **GREEN**: Already fixed by Item 1 — this test validates the round-trip end-to-end
- **REFACTOR**: Run full test suite

### Item 5: Enhance atomic write behavioral test

- **RED**: Write test creating a CRLF fixture file, saving via flush_entry, then reading on-disk result in binary mode to assert `\r\n` preserved. Write test mocking `tempfile.mkstemp` to verify it is called.
- **GREEN**: These tests overlap with Items 1-2 RED tests — they replace the shallow `test_sc13_atomic_write_integrity` assertions
- **REFACTOR**: Remove or update shallow assertions in `test_sc13_atomic_write_integrity`

### Item 6: Add SC-38 unicode decode behavioral test

- **RED**: Write test that opens a viewport in show mode, sends edit with `\uNNNN` escape (e.g., `\u0009` for tab), and verifies the buffer contains the real character after edit
- **GREEN**: No code change — `_decode_unicode_escapes` is already wired. Test validates existing behavior.
- **REFACTOR**: Run full test suite

## Dependencies

- **Requires:** #13 (completed — atomic write + unicode decode)
- **Blocks:** #17 (clipboard), #5 (file ops), #8 (diff/search/regex), #6 (integration)
- **SAT ordering:** #18 must complete first (proven via Z3 constraint model)

## Verification (behavioral — all SCs are behavioral)

Per-SC behavioral evidence artifacts must be generated as defined in the SC table above.

**Cumulative regression guard:**
`uv run pytest test/ -k "phase1 or phase2" > ./tmp/behavioral-evidence-regression-18.log 2>&1` — all P1+P2 tests must still pass after #18 changes.

**Full #18 suite:**
`uv run pytest test/ > ./tmp/behavioral-evidence-18.log 2>&1` — all 51 tests pass.

**Evidence artifacts are exempt from ./tmp/ cleanup per the spec §Behavioral Evidence Capture Protocol and survive until PR merge cleanup.**

## Risk Analysis

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| mkstemp fd leak on exception | Low | Low (fd leak) | Use `os.fdopen()` which auto-closes on context exit |
| mkstemp file permission differs from original | Low | Low | Set `umask` or `os.chmod` to match original; acceptable for MVP |
| `newline=""` changes behavior for files with mixed line endings | Low | Low | `newline=""` tells Python to write exactly what's in the string — no translation. This is the correct behavior. |
| Close auto-save fix may break existing close tests | Medium | Medium | Add explicit close tests with dirty + autosave=on before fixing |

## Audit Provenance

| Audit | Auditors | Verdict | Date |
|-------|----------|---------|------|
| Adversarial audit #13 | Gemma4:31b + Mistral3 | FAIL (2+7 findings) | 2026-06-01 |
| Drift audit #13 | Gemma4:31b + Qwen3.5:35b | FAIL (3+6 findings, consensus) | 2026-06-01 |
| Artifacts | `./tmp/adversarial-audit-drift/auditor1-drift.yaml`, `auditor2-drift.yaml`, `consensus.yaml` | | |

---

🤖 Co-authored with AI: OpenCode (ollama-cloud/glm-5.1)