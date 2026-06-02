# Viewport-Editor Behavioral Integration Tests — Evaluation Guide

This document defines the evaluation criteria for the 7 viewport-editor behavioral
integration test scenarios. Each scenario produces an artifact directory under
`./tmp/behavioral-evidence-<scenario>-<phase>-<model>/` containing:

- `stdout.log` — Agent prose response
- `stderr.log` — Tool dispatch trace (MCP tool invocations and responses)
- `session.yaml` — SQLite session dump (decision trace)
- `manifest.yaml` — Run metadata

Evaluation is **two-layer**: protocol correctness (did the agent call the right
tools in the right order?) and functional correctness (is the file on disk correct?).

## Evaluation Method

```bash
# Run a single scenario
bash .opencode/tests/behaviors/<scenario>.sh

# After run, evaluate artifacts
cd ./tmp/behavioral-evidence-<scenario>-GREEN-<model>/
```

### Protocol Correctness

Check `stderr.log` for MCP tool dispatches. The agent must use the `viewport-editor`
MCP tool (not built-in `edit`/`read`/`write` tools) for viewport operations.

Key dispatch patterns to verify:

1. Tool calls include `viewport-editor` namespace
2. Correct `action` parameter values (open, close, replace, save, etc.)
3. Correct parameter names match the server's inputSchema
4. Session IDs are used correctly (especially for session-isolation scenario)

### Functional Correctness

Check the workdir files after the agent finishes:

```bash
# Verify the file contains the expected changes
cat $VIEWPORT_TEST_REPO/fixtures/dorian-gray.txt | head -5
cat $VIEWPORT_TEST_REPO/fixtures/frankenstein.txt | head -5
```

---

## SC-1: Buffered Workflow (`viewport-buffered-workflow.sh`)

### Protocol Correctness

| Step | Expected stderr pattern | Notes |
|------|------------------------|-------|
| Open | `viewport-editor.*action.*open` | autosave=false must be present |
| Edit | `viewport-editor.*edit.*replace` | old_text='Dorian', new_text='DORIAN' |
| Diff show | `viewport-editor.*diff.*show` | Must show pending changes |
| File save | `viewport-editor.*file.*save` | Must appear before close |
| Viewport close | `viewport-editor.*viewport.*close` | Final step |

### Functional Correctness

- After save: `fixtures/dorian-gray.txt` must contain at least one occurrence of 'DORIAN'
- Before save (from diff output): changes must be staged in buffer, confirmed by diff output showing the change

---

## SC-2: Autosave ON (`viewport-autosave-on.sh`)

### Protocol Correctness

| Step | Expected stderr pattern | Notes |
|------|------------------------|-------|
| Open | `viewport-editor.*action.*open` | autosave=true must be present |
| Edit | `viewport-editor.*edit.*replace` | old_text='Frankenstein', new_text='FRANKENSTEIN' |
| Close | `viewport-editor.*viewport.*close` | No explicit save needed |

### Functional Correctness

- `fixtures/frankenstein.txt` must contain 'FRANKENSTEIN' (autosave flushed to disk immediately)
- Agent should NOT call file:save — autosave handles it

---

## SC-3: Autosave Toggle (`viewport-autosave-toggle.sh`)

### Protocol Correctness

| Step | Expected stderr pattern | Notes |
|------|------------------------|-------|
| Open (no autosave) | `viewport-editor.*action.*open` | autosave=false |
| First edit | `viewport-editor.*edit.*replace` | old_text='lazy', new_text='LAZY' |
| Diff show | `viewport-editor.*diff.*show` | Confirm buffered, not on disk |
| Toggle autosave | `viewport-editor.*viewport.*autosave` | enabled=true |
| Second edit | `viewport-editor.*edit.*replace` | old_text='brown', new_text='BROWN' |
| Close | `viewport-editor.*viewport.*close` | Second edit should be on disk via autosave |

### Functional Correctness

- `sample.txt` must contain 'LAZY' (from edit 1, saved via autosave after toggle or explicit save)
- `sample.txt` must contain 'BROWN' (from edit 2, auto-flushed)

---

## SC-4: Session Isolation (`viewport-session-isolation.sh`)

### Protocol Correctness

| Step | Expected stderr pattern | Notes |
|------|------------------------|-------|
| Open session-alpha | `viewport-editor.*open.*session-alpha` | session_id='session-alpha' |
| Edit in alpha | `viewport-editor.*edit.*replace.*session_id.*session-alpha` | fox → FOX |
| Open session-beta | `viewport-editor.*open.*session-beta` | session_id='session-beta' |
| List in beta | `viewport-editor.*viewport.*list.*session-beta` | Must show original content |
| Edit in beta | `viewport-editor.*edit.*replace.*session_id.*session-beta` | dog → DOG |
| List in alpha | `viewport-editor.*viewport.*list.*session-alpha` | Must show FOX but NOT DOG |
| Save both | `viewport-editor.*file.*save` (x2) | One per session |
| Close both | `viewport-editor.*viewport.*close` (x2) | One per session |

### Functional Correctness

- After save: `sample.txt` must contain both 'FOX' and 'DOG' (both sessions saved)
- The list operations in each session must show that edits are isolated while buffered

---

## SC-5: Conflict Detection (`viewport-conflict-detection.sh`)

### Protocol Correctness

| Step | Expected stderr pattern | Notes |
|------|------------------------|-------|
| Open file | `viewport-editor.*open.*conflict-test.txt` | autosave=false |
| Edit file | `viewport-editor.*edit.*replace-all` | 'Original' → 'Modified' |
| External modification | agent uses bash tool | `sed -i` on conflict-test.txt |
| Save attempt | `viewport-editor.*file.*save` | Should detect conflict |
| Diff show | `viewport-editor.*diff.*show` | Should show conflict state |

### Functional Correctness

- The save operation should return a conflict/error response
- The agent must report that the server detected a conflict between buffer and disk

---

## SC-6: Clipboard Cross-Viewport (`viewport-clipboard-cross-viewport.sh`)

### Protocol Correctness

| Step | Expected stderr pattern | Notes |
|------|------------------------|-------|
| Open sample.txt | `viewport-editor.*open.*sample.txt` | |
| Copy lines | `viewport-editor.*clipboard.*copy` | start_line=2, end_line=3 |
| Open paste-target.txt | `viewport-editor.*open.*paste-target.txt` | Same session |
| Paste lines | `viewport-editor.*clipboard.*paste` | target_line=2 |
| Diff show | `viewport-editor.*diff.*show` | On paste-target viewport |
| Save | `viewport-editor.*file.*save` | |
| Close both | `viewport-editor.*viewport.*close` (x2) | |

### Functional Correctness

- `paste-target.txt` must contain the pasted lines from `sample.txt`
- The pasted content should appear at the target line position

---

## SC-7: Stash/Pop/Swap (`viewport-stash-pop-swap.sh`)

### Protocol Correctness

| Step | Expected stderr pattern | Notes |
|------|------------------------|-------|
| Open file | `viewport-editor.*open.*sample.txt` | |
| Copy line 1 | `viewport-editor.*clipboard.*copy` | start_line=1, end_line=1 |
| Stash as 'line-one' | `viewport-editor.*clipboard.*stash.*line-one` | |
| Copy lines 4-5 | `viewport-editor.*clipboard.*copy` | start_line=4, end_line=5 |
| Stash as 'lines-four-five' | `viewport-editor.*clipboard.*stash.*lines-four-five` | |
| Stash-list | `viewport-editor.*clipboard.*stash-list` | Must show 2 stashes |
| Pop 'line-one' | `viewport-editor.*clipboard.*pop.*line-one` | |
| Show clipboard | `viewport-editor.*clipboard.*show` | Must contain line 1 content |
| Pop 'lines-four-five' | `viewport-editor.*clipboard.*pop.*lines-four-five` | |
| Show clipboard | `viewport-editor.*clipboard.*show` | Must contain lines 4-5 content |
| Stash as 'swapped' | `viewport-editor.*clipboard.*stash.*swapped` | |
| Pop 'line-one' again | `viewport-editor.*clipboard.*pop.*line-one` | |
| Close | `viewport-editor.*viewport.*close` | |

### Functional Correctness

- stash-list must show both named stashes after steps 3 and 5
- Each pop must restore the correct stashed content
- The agent must report that stash/pop operations work as expected

---

## Co-authored With AI

OpenCode (ollama-cloud/glm-5.1)