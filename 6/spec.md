# Synced from GitHub Issue #6

## Parent Plan

#4 — MVP: Viewport-Editor MCP Server

## Concern

End-to-end behavioral integration testing across all subsystems — viewport, buffer, edit, file ops, clipboard, search, regex, diff — using opencode-cli test harness with goal-directed instruction cards.

## SCs Covered

9 behavioral integration scenarios (SC-1 through SC-9) verifying agent-in-the-loop execution of all viewport-editor tools.

## SC-to-Task Traceability

| # | Scenario | Validates | Script | Artifact Directory (model-run) |
|---|----------|-----------|--------|-------------------------------|
| 1 | Full buffered workflow integration | All edit+file+diff SCs | `viewport-buffered-workflow.sh` | `./tmp/behavioral-evidence-viewport-buffered-workflow-GREEN-ollama-glm-5.1-cloud/` |
| 2 | Full autosave=on workflow | SC-14, SC-24 | `viewport-autosave-on.sh` | `./tmp/behavioral-evidence-viewport-autosave-on-GREEN-ollama-glm-5.1-cloud/` |
| 3 | Autosave toggle workflow | SC-14, SC-32 | `viewport-autosave-toggle.sh` | `./tmp/behavioral-evidence-viewport-autosave-toggle-GREEN-ollama-deepseek-v4-flash-cloud/` |
| 4 | N-session isolation | SC-26 | `viewport-session-isolation.sh` | `./tmp/behavioral-evidence-viewport-session-isolation-GREEN-ollama-qwen3.5-397b-cloud/` |
| 5 | Conflict detection save rejection | SC-11, SC-25 | `viewport-conflict-detection.sh` | `./tmp/behavioral-evidence-viewport-conflict-detection-GREEN-ollama-qwen3.5-397b-cloud/` |
| 6 | Clipboard cross-viewport workflow | SC-39, SC-40, SC-41, SC-42 | `viewport-clipboard-cross-viewport.sh` | `./tmp/behavioral-evidence-viewport-clipboard-cross-viewport-GREEN-ollama-qwen3.5-397b-cloud/` |
| 7 | Clipboard stash-pop-swap workflow | SC-43, SC-44, SC-45 | `viewport-stash-pop-swap.sh` | `./tmp/behavioral-evidence-viewport-stash-pop-swap-GREEN-ollama-deepseek-v4-flash-cloud/` |
| 8 | Search and navigate workflow | SC-27, SC-5 | `viewport-search-navigate.sh` | `./tmp/behavioral-evidence-viewport-search-navigate-GREEN-ollama-gpt-oss-120b-cloud/` |
| 9 | Code navigation workflow | SC-28, SC-5 | `viewport-code-navigation.sh` | `./tmp/behavioral-evidence-viewport-code-navigation-GREEN-ollama-deepseek-v4-flash-cloud/` |

Each artifact directory contains: manifest.yaml, stdout.log, stderr.log, exit_code, session.yaml.

## Dependencies

- **Requires:** #18, #17, #22, #23, #24, #25, #26, #27, #28
- **Blocks:** Nothing (final phase)

## Verification (behavioral)

**Unit tests (regression guard):**
`uv run pytest test/` — 132 tests pass (P1+P2+P3+P4).

**Behavioral (model-run artifacts):**
All 9 SC scripts produce artifact directories under `./tmp/behavioral-evidence-*/` with exit_code 0, meaningful agent prose in stdout, and viewport_editor tool dispatch traces in stderr.

**Evidence artifacts are exempt from ./tmp/ cleanup per the spec §Behavioral Evidence Capture Protocol and survive until PR merge cleanup.**

Feature branch: `pair-p5-integration`

---

🤖 Co-authored with AI: OpenCode (glm-5.1)