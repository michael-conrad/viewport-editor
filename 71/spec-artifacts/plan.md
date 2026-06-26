# Plan: Stress Test Framework for All Viewport-Editor Actions

**Issue:** #71
**Status:** DRAFT
**Created:** 2026-06-12

## Overview

Create a three-component stress test framework: Generators (produce `Sequence` data records), Runner (executes sequences against in-memory MCP server, writes self-contained logs), Audit (post-hoc mechanical checks + findings manifest for AI semantic analysis).

## Phase 1: Generators + Runner Infrastructure

### Task 1.1 — Create `test/stress/` package and data models

**Files:**
- `test/stress/__init__.py` — docstring-only package init
- `test/stress/models.py` — `Sequence`, `ToolCall`, `ContentCheck` dataclasses

**Data classes:**

```python
@dataclass
class ToolCall:
    tool: str
    params: dict

@dataclass
class ContentCheck:
    type: Literal["line_count", "contains", "not_contains", "exact_match", "positional"]
    target: str | int

@dataclass
class Sequence:
    id: str
    category: str
    seed_content: str
    steps: list[ToolCall]
    expected_save_success: bool
    expected_content_checks: list[ContentCheck]
    description: str
```

**TDD:**
- RED: Write unit test `test/stress/test_models.py` — instantiate each dataclass, verify field types
- GREEN: Create `__init__.py` and `models.py` with dataclasses
- REFACTOR: Verify `uv run pytest test/stress/test_models.py -x -q` passes

### Task 1.2 — Create `generator_edit_pairs.py`

**File:** `test/stress/generator_edit_pairs.py`

Exports `generate_edit_pair_sequences() -> list[Sequence]`.

Generates:
- 36 ordered pairs (6 operations × 6 operations) × 3 positions × 2 content sizes = 216 dense
- ~40 sparse (subset: non-overlapping + same-position only, single-line content)
- ~50 triple-chain high-risk sequences (replace→replace→replace, delete→insert→delete, move→replace→move, swap→replace-all, replace-all→delete, insert→insert→insert stacking)

Operations: `replace`, `replace-all`, `insert-lines`, `delete-lines`, `swap-lines`, `move-lines`

Positions: `non-overlapping`, `overlapping`, `same_position`

Content sizes: `single_line` (1-2 lines), `multi_line` (5-10 lines)

Seed content for single-line: `"line 1\nline 2\nline 3\nline 4\nline 5\n"`
Seed content for multi-line: `"line 1\nline 2\nline 3\nline 4\nline 5\nline 6\nline 7\nline 8\nline 9\nline 10\n"`

**TDD:**
- RED: Write test `test/stress/test_generator_edit_pairs.py` — assert `len(generate_edit_pair_sequences(density="sparse")) == ~40`, assert `len(generate_edit_pair_sequences(density="dense")) == ~266`
- GREEN: Implement generator with combinatorial logic
- REFACTOR: Verify counts match spec

### Task 1.3 — Create `generator_clipboard.py`

**File:** `test/stress/generator_clipboard.py`

Exports `generate_clipboard_sequences() -> list[Sequence]`.

Generates ~15 sequences:
- copy(A) → edit → paste(A') — clipboard retains original through edits
- cut(range) → paste(different position) — offset correctness after reinsertion
- cut → cut → paste-first → paste-second — multiple cut offset accounting
- copy(A) → stash("x") → cut(B) → pop("x") → paste — stash lifecycle
- copy(A) → stash("x") → swap("x") → paste — swap semantics
- paste with empty clipboard — error path
- stash with empty clipboard — error path
- pop nonexistent slot — error path

**TDD:**
- RED: Write test asserting correct count and structure
- GREEN: Implement generator
- REFACTOR: Verify

### Task 1.4 — Create `generator_diff.py`

**File:** `test/stress/generator_diff.py`

Exports `generate_diff_sequences() -> list[Sequence]`.

Generates ~15 sequences:
- Single hunk, middle of file
- Multi-hunk, non-overlapping
- Multi-hunk with fuzzy context matching
- Hunk at line 1 (beginning boundary)
- Hunk at last line (end boundary)
- Overlapping hunks (intentionally invalid — error path)
- apply on unsaved viewport (autosave gate)

**TDD:**
- RED: Write test asserting correct count and structure
- GREEN: Implement generator
- REFACTOR: Verify

### Task 1.5 — Create `generator_crosstalk.py`

**File:** `test/stress/generator_crosstalk.py`

Exports `generate_crosstalk_sequences() -> list[Sequence]`.

Generates ~10 sequences:
- Open same file in 2 viewports, edit both, save both
- Session A edits, Session B reads
- Open → close → reopen same file
- Sweep stale sessions (4-hour idle eviction)
- Session A open file, Session B open same, A saves, B tries save

**TDD:**
- RED: Write test asserting correct count and structure
- GREEN: Implement generator
- REFACTOR: Verify

### Task 1.6 — Create `generator_mtime.py`

**File:** `test/stress/generator_mtime.py`

Exports `generate_mtime_sequences() -> list[Sequence]`.

Generates ~10 sequences:
- Open → save → externally modify → open again (refresh_if_changed)
- Open → externally modify → save (no force) — mtime conflict blocks save
- Open → externally modify → save (force=true) — force override
- Open → save → externally modify → edit → save — combined stale+edit
- Open → edit → external modify → save — conflict warning on edit

**TDD:**
- RED: Write test asserting correct count and structure
- GREEN: Implement generator
- REFACTOR: Verify

### Task 1.7 — Create `run_stress.py`

**File:** `test/stress/run_stress.py`

Usage: `uv run python test/stress/run_stress.py [--density {sparse|dense}] [--run-id STR] [--preserve]`

Behavior:
1. Create temp directory for seed files (one per sequence)
2. Start module-scoped server via `create_server(str(temp_project_root))` with `fastmcp.Client` in-memory transport
3. For each sequence:
   a. Create seed file with `seed_content`
   b. Open viewport on seed file via `client.call_tool("viewport", {"action": "open", "file_path": seq_id})`
   c. Execute steps in order, recording each tool call + response
   d. After final step, attempt `file:save` (unless `expected_save_success=False`)
   e. Read final disk state
   f. Write sequence directory: `params.json`, `seed_content.txt`, `steps.json`, `final_content.txt`
4. Write `manifest.json` with run metadata
5. Print summary to stdout

**No assertions in runner.** Runner only executes and logs.

Server fixture pattern (from `test/conftest.py`):
```python
import tempfile
from pathlib import Path
from fastmcp import Client
from viewport_editor.server import create_server

temp_root = Path(tempfile.mkdtemp(prefix="ve-stress-"))
server = create_server(str(temp_root))
async with Client(transport=server) as client:
    # wrap in _CompatClient for backward-compatible isError
    from test.conftest import _CompatClient
    c = _CompatClient(client)
    # ... execute sequences
```

Log directory structure:
```
tmp/stress/<run_id>/
├── manifest.json
├── sequences/
│   ├── edit-pair-001/
│   │   ├── params.json
│   │   ├── seed_content.txt
│   │   ├── steps.json
│   │   └── final_content.txt
│   └── ...
```

**TDD:**
- RED: Write test `test/stress/test_runner.py` — create 3 known sequences, run against server, verify log directory structure
- GREEN: Implement runner
- REFACTOR: Verify `uv run python test/stress/run_stress.py --density sparse` produces log dir with all sequences

### Task 1.8 — Phase 1 integration test

**RED:** Write `test/stress/test_phase1_integration.py` — run sparse suite, verify:
- All sequence directories present
- Each has `params.json`, `seed_content.txt`, `steps.json`, `final_content.txt`
- `manifest.json` has correct run metadata
- No unhandled exceptions

**GREEN:** Fix runner issues until integration test passes.

## Phase 2: Audit Module + Findings Manifest

### Task 2.1 — Create `audit_stress.py`

**File:** `test/stress/audit_stress.py`

Usage: `uv run python test/stress/audit_stress.py [--run-dir STR] [--output PATH]`

Behavior:
1. Read `manifest.json` for run metadata
2. Iterate sequence directories
3. For each sequence, run mechanical checks:
   - Hard errors: any step with `isError=true` that wasn't expected
   - Content truncation: `final_content.txt` shorter than expected based on operations
   - Content corruption: expected content checks against `final_content.txt`
   - Missing lines: seed lines absent in final
   - Extra lines: content in final not attributable to any step
4. Write `mechanical_report.md` to run directory
5. For any sequence that failed mechanical checks, emit a findings manifest entry with targeted semantic question
6. Write `findings_manifest.json` — list of sequences needing AI semantic analysis
7. Copy `mechanical_report.md` + `findings_manifest.json` to `.issues/` with run id

**Findings manifest format (NDJSON):**
```json
{
  "sequence_id": "edit-pair-042",
  "category": "edit_pairs",
  "seed_content": "line 1\nline 2\n...",
  "steps_summary": "replace('line 2', 'X') → delete-lines(3,5) → insert-lines(3, ['Y'])",
  "final_content": "line 1\nX\nY\n...",
  "mechanical_flags": ["line_count_mismatch", "content_corruption"],
  "semantic_question": "The seed content was edited by the sequence above. Does the final content match what the edits should produce? Focus on line ordering, offset correctness after deletions, and any drift not explained by the edit sequence."
}
```

**TDD:**
- RED: Write test `test/stress/test_audit.py` — create known-good and known-bad log directories, verify audit reports correct PASS/FAIL
- GREEN: Implement audit
- REFACTOR: Verify

### Task 2.2 — Create `test/stress/semantic-dispatch-procedure.md`

**File:** `test/stress/semantic-dispatch-procedure.md`

Reference doc describing the orchestrator dispatch protocol:
- For each entry in `findings_manifest.json`:
  1. Read entry data
  2. Dispatch clean-room sub-agent with ONLY entry data
  3. Sub-agent returns PASS/FAIL with evidence
  4. Aggregate into final stress report at `.issues/stress-report-<run-id>.md`

**INVARIANT PROMPT TEMPLATE MANDATE:** The semantic dispatch prompt is a
FROZEN template. Only three fields vary per finding: seed_content,
steps_summary, final_content. No commentary, pattern labels, expectations,
or operator reasoning may be added. Any deviation produces contaminated
results and invalidates the audit. See semantic-dispatch-procedure.md for
the exact template.

### Task 2.3 — Phase 2 integration test

**RED:** Write test that:
1. Creates known-good log directory (all sequences correct)
2. Runs audit → verifies `mechanical_report.md` shows all PASS
3. Creates known-bad log directory (inject truncation, missing lines)
4. Runs audit → verifies `findings_manifest.json` has entries with `semantic_question` fields

**GREEN:** Fix audit until integration test passes.

## Phase 3: CI Integration + Re-gate

### Task 3.1 — Bundle sparse suite as pytest target

**File:** `test/stress/test_sparse_suite.py`

A pytest wrapper that calls `run_stress.py --density sparse` then `audit_stress.py` on the output:

```python
"""pytest wrapper for sparse stress suite."""
import subprocess
import json
from pathlib import Path

def test_sparse_stress_suite(tmp_path):
    run_id = "ci-sparse"
    result = subprocess.run(
        ["uv", "run", "python", "test/stress/run_stress.py",
         "--density", "sparse", "--run-id", run_id],
        capture_output=True, text=True, cwd=tmp_path
    )
    assert result.returncode == 0, f"Runner failed: {result.stderr}"
    
    audit_result = subprocess.run(
        ["uv", "run", "python", "test/stress/audit_stress.py",
         "--run-dir", f"tmp/stress/{run_id}"],
        capture_output=True, text=True, cwd=tmp_path
    )
    assert audit_result.returncode == 0, f"Audit failed: {audit_result.stderr}"
```

**TDD:**
- RED: Write test that runs sparse suite via subprocess, expects zero exit
- GREEN: Wire up wrapper
- REFACTOR: Verify `uv run pytest test/stress/test_sparse_suite.py -x -q` passes

### Task 3.2 — Wire into cumulative regression guard

Add `test/stress/` to the test discovery path. The sparse suite runs as part of the normal test suite:

```bash
VIEWPORT_STRESS_DENSITY=sparse uv run pytest test/stress/ -x -q
```

**TDD:**
- RED: Run `uv run pytest test/stress/ -x -q` — should discover and run all stress tests
- GREEN: Fix any discovery issues
- REFACTOR: Verify

### Task 3.3 — Full dense run + audit

Run the full dense suite and audit:

```bash
uv run python test/stress/run_stress.py --density dense
uv run python test/stress/audit_stress.py --run-dir tmp/stress/latest
```

If bugs are found, file issues. If no bugs found, report "no bugs found" with evidence.

## File Inventory

| File | Phase | Purpose |
|------|-------|---------|
| `test/stress/__init__.py` | 1 | Package init |
| `test/stress/models.py` | 1 | Sequence, ToolCall, ContentCheck dataclasses |
| `test/stress/generator_edit_pairs.py` | 1 | Edit pair sequence generator |
| `test/stress/generator_clipboard.py` | 1 | Clipboard sequence generator |
| `test/stress/generator_diff.py` | 1 | Diff apply sequence generator |
| `test/stress/generator_crosstalk.py` | 1 | Crosstalk sequence generator |
| `test/stress/generator_mtime.py` | 1 | Mtime/cross-session sequence generator |
| `test/stress/run_stress.py` | 1 | Sequence executor against in-memory server |
| `test/stress/audit_stress.py` | 2 | Mechanical checks + findings manifest |
| `test/stress/semantic-dispatch-procedure.md` | 2 | Orchestrator dispatch protocol reference |
| `test/stress/test_models.py` | 1 | Unit tests for data models |
| `test/stress/test_generator_edit_pairs.py` | 1 | Tests for edit pair generator |
| `test/stress/test_generator_clipboard.py` | 1 | Tests for clipboard generator |
| `test/stress/test_generator_diff.py` | 1 | Tests for diff generator |
| `test/stress/test_generator_crosstalk.py` | 1 | Tests for crosstalk generator |
| `test/stress/test_generator_mtime.py` | 1 | Tests for mtime generator |
| `test/stress/test_runner.py` | 1 | Tests for runner |
| `test/stress/test_audit.py` | 2 | Tests for audit |
| `test/stress/test_phase1_integration.py` | 1 | Phase 1 integration test |
| `test/stress/test_sparse_suite.py` | 3 | pytest wrapper for sparse suite |

## Commands

```bash
# Run unit tests
uv run pytest test/stress/test_models.py -x -q

# Run generator tests
uv run pytest test/stress/test_generator_edit_pairs.py -x -q
uv run pytest test/stress/test_generator_clipboard.py -x -q
uv run pytest test/stress/test_generator_diff.py -x -q
uv run pytest test/stress/test_generator_crosstalk.py -x -q
uv run pytest test/stress/test_generator_mtime.py -x -q

# Run runner test
uv run pytest test/stress/test_runner.py -x -q

# Run audit test
uv run pytest test/stress/test_audit.py -x -q

# Run sparse suite
uv run python test/stress/run_stress.py --density sparse

# Run dense suite
uv run python test/stress/run_stress.py --density dense

# Run audit on a specific run
uv run python test/stress/audit_stress.py --run-dir tmp/stress/<run-id>

# Run sparse suite as pytest target
uv run pytest test/stress/test_sparse_suite.py -x -q

# Run all stress tests
uv run pytest test/stress/ -x -q
```
