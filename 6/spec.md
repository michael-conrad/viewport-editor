# Synced from GitHub Issue #6

## Parent Plan

#4 — MVP: Viewport-Editor MCP Server

## Concern

End-to-end behavioral integration testing across all subsystems — viewport, buffer, edit, file ops, clipboard, search, regex, diff — using opencode-cli test harness with goal-directed instruction cards.

## SCs Covered

9 behavioral integration scenarios (SC-1 through SC-9) verifying agent-in-the-loop execution of all viewport-editor tools.

## Testing Approach

**Behavioral integration tests** — not `pytest` unit tests. Each scenario sends a natural-language instruction card to opencode-cli, which dispatches `viewport-editor` MCP tools. The agent reads `inputSchema` to construct calls. Evaluation is two-layer:

1. **Protocol correctness** — `stderr.log` shows correct tool dispatch sequence via skill dispatch lines
2. **Functional correctness** — file on disk matches expected content per inline success criteria

## Tool Descriptions (Updated)

Server tool docstrings were updated to differentiate from built-in `edit`:

- `viewport`: "Open a focused window into a file and navigate it without loading the entire file into context"
- `edit`: "Edit text inside a viewport's buffer without loading or rewriting the entire file"

## Test Infrastructure

| Component | Location | Purpose |
|-----------|----------|---------|
| Setup script | `tests/scripts/setup-viewport-test.sh` | Clone, MCP config injection, fixture wiring, XDG home |
| Behavioral scripts | `tests/behaviors/viewport-*.sh` (9 files) | Each calls `opencode-cli run` with instruction card, produces artifacts for evaluation |
| Text fixtures | `tests/fixtures/ebooks/` | 3 Gutenberg texts (LF, CRLF, CR) + config.yaml (LF) + example.py (LF) + chapter.md (CRLF) |

**Fixture line endings by design:**

| Fixture | Line Ending | Purpose |
|---------|-------------|---------|
| `dorian-gray.txt` | LF | Plain prose (Gutenberg) |
| `frankenstein.txt` | CRLF | Plain prose (Windows) |
| `moby-dick.txt` | CR | Plain prose (Mac Classic) |
| `config.yaml` | LF | Structured YAML navigation — section headers, key search |
| `example.py` | LF | Code navigation — def/class targets, symbol search |
| `chapter.md` | CRLF | Markdown header navigation — `#`/`##` sections |

**Setup script flow:** Clone viewport-editor into isolated test home → inject MCP config with `uv run --project` command → copy ebook + code fixtures → create `workdir/` as `--project-root` → write agent instruction card to artifact directory.

## SC-to-Task Traceability

| # | Scenario | Script | Success Criterion |
|---|----------|--------|-------------------|
| 1 | Full buffered workflow | `viewport-buffered-workflow.sh` | **Protocol:** stderr shows open → edit:replace → diff:show shows pending → file:save writes to disk → viewport:close. **Functional:** after file:save, disk file matches expected edited content per instruction card. |
| 2 | Full autosave=on workflow | `viewport-autosave-on.sh` | **Protocol:** stderr shows open with autosave=on → edit:replace → NO explicit file:save call. **Functional:** disk file reflects edit immediately after edit (no explicit save needed). |
| 3 | Autosave toggle workflow | `viewport-autosave-toggle.sh` | **Protocol:** stderr shows open autosave=off → edit → diff:show shows pending → toggle autosave=on → flush to disk. **Functional:** after toggle, disk file reflects edit state. |
| 4 | N-session isolation | `viewport-session-isolation.sh` | **Protocol:** stderr shows 2 sessions opened on same file, each editing independently. **Functional:** no cross-session contamination — each session's edits are independent. |
| 5 | Conflict detection save rejection | `viewport-conflict-detection.sh` | **Protocol:** stderr shows external modification triggers hard conflict on save (block), soft warning on edit. **Functional:** save rejected with error, edit proceeds with warning. |
| 6 | Clipboard cross-viewport workflow | `viewport-clipboard-cross-viewport.sh` | **Protocol:** stderr shows copy from viewport A → paste into viewport B. **Functional:** content from A appears in B with provenance tracking. |
| 7 | Clipboard stash-pop workflow | `viewport-stash-pop-swap.sh` | **Protocol:** stderr shows copy → stash → pop → swap sequence. **Functional:** clipboard restored correctly from stash at each step. |
| 8 | Search and navigate workflow | `viewport-search-navigate.sh` | **Protocol:** stderr shows search:find for pattern → jump → edit at found location → regex search → diff:show. **Functional:** both edits appear in diff, locations match search results. |
| 9 | Code and config navigation | `viewport-code-navigation.sh` | **Protocol:** stderr shows jump to def/class → symbol search → regex test/escape → edit within function body → jump to constant → diff → file:save. **Functional:** all edits present in final diff and persisted to disk. |

Each artifact directory contains: manifest.yaml, stdout.log, stderr.log, exit_code, session.yaml.

## Dependencies

- **Requires:** #18, #17, #22, #23, #24, #25, #26, #27, #28
- **Blocks:** Nothing (final phase)

## Verification (behavioral)

**Full suite (implicit cumulative regression guard):**
`bash tests/behaviors/viewport-buffered-workflow.sh && bash tests/behaviors/viewport-autosave-on.sh && bash tests/behaviors/viewport-autosave-toggle.sh && bash tests/behaviors/viewport-session-isolation.sh && bash tests/behaviors/viewport-conflict-detection.sh && bash tests/behaviors/viewport-clipboard-cross-viewport.sh && bash tests/behaviors/viewport-stash-pop-swap.sh && bash tests/behaviors/viewport-search-navigate.sh && bash tests/behaviors/viewport-code-navigation.sh` — all 9 behavioral scenarios pass.

**Per-scenario run:** `bash tests/behaviors/viewport-<scenario>.sh`

**Evidence artifacts are exempt from ./tmp/ cleanup per the spec §Behavioral Evidence Capture Protocol and survive until PR merge cleanup.**

## Workflow Pipeline (Pre-RED to PR Cleanup)

### Pre-Work
1. Create feature branch `feature/6-integration-tests`
2. Tag submodule SHA at `.opencode`
3. Sync dev: `git checkout dev && git pull && git checkout -b feature/6-integration-tests`
4. Pre-flight: verify ALL prior modules exist and ALL prior tests pass

### Coherence Gate (Pre-RED)
1. Verify all phases 1-4 modules exist with expected API surface
2. Confirm no superseding issues
3. On BLOCKED: HALT. On PASS: proceed.

### RED Phase → GREEN Phase → Completeness Gate → Adversarial Audit → Finishing Checklist → Review Prep → Post-PR Cleanup

(Standard pipeline per project workflow)

---

🤖 Co-authored with AI: OpenCode (deepseek-v4-flash)