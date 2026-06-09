# [SPEC] Composite Action Tools for Agent Intent Matching

## Problem

AI agents consistently prefer the platform's built-in tools (`read`, `edit`, `write`, `grep`) over the viewport-editor's custom tools. This defeats the purpose of having a staged-buffer editing system with conflict detection, since agents bypass it entirely.

**Root cause:** The agent's tool selection bias operates on four dimensions, and the viewport-editor loses on ALL of them simultaneously:

| Dimension | Built-in tools | Viewport-editor tools |
|-----------|---------------|----------------------|
| **Semantic match** | Tool name IS the intent verb (`read`, `write`, `edit`) | Tool names describe implementation mechanism (`viewport`, `edit`, `file`, `diff`) — not intent |
| **Position bias** | Built-ins appear first in the tool listing | Viewport-editor tools appear later |
| **Pre-training exposure** | High-frequency English verbs seen millions of times in training data | Novel names with zero pre-training exposure |
| **Call count** | 1 call per operation | 3+ calls per operation (open → edit/replace → file/save) |

**Research corroboration:** The BiasBusters paper (arXiv 2510.00307, ICLR 2026) confirms that semantic alignment between user queries and tool names is the strongest driver of selection. The mcp-naming-bias study shows semantic matching overrides position bias 100% of the time across all tested models (Claude, GPT-4o, Gemini, DeepSeek, Mistral, Qwen, Llama). Anthropic's "Writing Effective Tools for Agents" guide explicitly recommends composite actions that consolidate multi-step workflows into single tools named after the agent's *intent*, not the *implementation*.

**Current architecture:** 6 tools with action dispatch parameters (viewport, edit, file, diff, search, regex). To perform a file read, the agent must call `viewport-editor_viewport` with `action="open"`, then parse the YAML response. To write, it must call `viewport-editor_edit` with `action="replace-all"`, then `viewport-editor_file` with `action="save"`. No tool name matches any agent intent verb directly. See [Card 6: The Semantic Gap](spec-artifacts/research/card-catalogue.md#card-6-the-semantic-gap--viewport-editor-vs-built-in) for the full diagnostic mapping of agent intent vs current tool surface.

## Solution

Add **5 composite-action MCP tools** named after agent intent verbs. Each is a standalone MCP tool entry (not an action on an existing tool) that internally delegates to the existing viewport/edit/file pipeline but presents as a single-call verb:

| New Tool | Agent Intent | Internal Workflow | Analogous Built-in |
|----------|-------------|-------------------|--------------------|
| `read` / `read_file` | "I want to read a file" | open viewport → return content | `read(path, offset, limit)` |
| `write` / `write_file` | "I want to create/replace a file" | open viewport → replace-all content → save → close | `write(path, content)` |
| `edit` / `edit_text` | "I want to make a targeted edit" | open viewport → replace(s) → save → close | `edit(path, old, new)` |
| `find` / `find_text` | "I want to search file contents" | search:find → return results | `grep(pattern)` |
| `diff` | "I want to see what changed" | diff:show → return diff | none (unique) |

**Naming convention:** The MCP config key (e.g., `viewport-editor`) already provides the platform-level namespace. The agent sees `viewport-editor_read`, not bare `read`. Adding an extra prefix like `vp_` is redundant. Two naming variants will be tested:

- **`verb`** — `read`, `write`, `edit`, `find`, `diff` — shortest, cleanest, unambiguous within this server
- **`verb_noun`** — `read_file`, `write_file`, `edit_text`, `find_text` — explicit when disambiguation is needed

`diff` has no `verb_noun` variant — `diff` is already unambiguous and `diff_file` adds no signal.

The existing 7 tools remain unchanged — these are additive. The composite tools are the **entry point** for agents; the low-level tools (`viewport`, `edit`, `file`, `diff`, `clipboard`, `search`, `regex`) remain available for fine-grained control, staging, and diff review.

**IMPORTANT: Final naming and descriptions are NOT decided by this spec. They MUST be determined by iterative empirical testing per the Iterative Testing Protocol (see spec-artifacts/).** Verb choice, specificity level, comparison framing, and coexistence strategy are all variables to be tested, not design decisions.

### Design Principles

- **Single-call semantics:** The agent makes 1 tool call for the most common operations, not 3.
- **Staging-by-default:** The composite tools use the viewport buffer internally. They do NOT bypass the staging system — they just manage the viewport lifecycle transparently.
- **Diff visibility:** After composite operations, the agent can still inspect staged changes via `diff:show` before closing, since the viewport remains open during the buffer-flush window.
- **No redundant prefix:** MCP config key already provides namespace. Tool names are `verb` or `verb_noun` only.
- **Parameter naming:** Follows the same `line_start`/`line_end` convention established in spec #39.

## Tool Definitions (Provisional — Subject to Testing)

### Tool 1: `read` / `read_file`
```
Read a file's contents via a scoped viewport window. Supports offset/limit for partial reads.

Parameters:
  file_path (string, required): Relative path from project root
  line_start (integer, optional, default 1): First line to read
  line_end (integer, optional, default 100): Last line to read

Returns: File content, viewport metadata (line range, mtime, size), and conflict warnings.
```

Internal flow: Calls `viewport:open` with the file path → returns the YAML content block. The viewport remains open for follow-up edits.

### Tool 2: `write` / `write_file`
```
Create a new file or overwrite an existing file with the given content. 
Internally stages content through the buffer with conflict detection.

Parameters:
  file_path (string, required): Relative path from project root
  content (string, required): Full file content to write

Returns: Confirmation with mtime, size, and any conflict warnings.

Error conditions:
- File modified externally since last read (conflict)
- Path traversal outside project root
```

Internal flow: Opens viewport → replaces entire content → saves → closes viewport. If the file doesn't exist, creates it.

### Tool 3: `edit` / `edit_text`
```
Perform a targeted text replacement in a file. 
Stages through the buffer with conflict detection.

Parameters:
  file_path (string, required): Relative path from project root
  old_text (string, required): Text to replace
  new_text (string, required): Replacement text

Returns: Confirmation with match count and any conflict warnings.

Error conditions:
- File not found
- `old_text` not found (zero matches)
- Multiple ambiguous matches without specificity
- File modified externally (conflict)
```

Internal flow: Opens viewport → calls `edit:replace-all` → saves → closes viewport.

### Tool 4: `find` / `find_text`
```
Search file contents for a pattern. Supports substring (default) and regex matching.

Parameters:
  pattern (string, required): Text or regex pattern to search for
  file_path (string, optional): Scope to a single file
  regex (boolean, optional, default false): Enable regex matching

Returns: Structured results with line numbers, file paths, and matching text.
```

Internal flow: Calls `search:find` with the given parameters → returns structured results.

### Tool 5: `diff`
```
Show the unified diff of pending buffer changes for a file. 
Use before save to review what changed.

Parameters:
  file_path (string, required): Relative path from project root

Returns: Unified diff of staged changes, or empty if no pending changes.
```

Internal flow: Opens viewport if not already open → calls `diff:show` → returns diff.

## Existing Tools Preserved

All 7 existing tools (`viewport`, `edit`, `file`, `diff`, `clipboard`, `search`, `regex`) remain unchanged. The agent selects between:

- **Composite path (recommended):** `read` / `write` / `edit` / `find` / `diff` for simple operations — 1 call, intent-matching names
- **Fine-grained path:** `viewport:open` → `edit:replace` → `diff:show` → `file:save` for complex multi-edit workflows requiring review

The composite tools handle the common case. The existing tools handle the edge cases and advanced workflows (clipboard operations, diff apply, regex testing, multi-viewport staging).

## Spec Requirements

### R1: Existing tool descriptions must be re-written in agent-facing style

The 7 existing tools (`viewport`, `edit`, `file`, `diff`, `clipboard`, `search`, `regex`) currently use mechanism-language descriptions:

> "Viewport text editor — buffer-isolated file access for auditable, undoable edits."

These descriptions counteract the composite tools' intent-language strategy. When an agent browses the full tool listing, mechanism language dilutes the intent alignment of the composites. All 7 existing tool descriptions must be re-written in the same agent-facing, constraint-stating style as the composite tools. This is a separate pass from the composite tool implementation — descriptions are text-only changes, not code changes.

### R2: write/edit overlap must be pre-addressed

`write` and `edit` overlap in agent intent space. An agent with prompt "fix this typo in server.py" could match either tool. The spec must pre-address this before implementation:

- **Option A (merge):** Remove `edit` and fold targeted replacement into `write` via a `mode` parameter (`mode=replace` vs `mode=overwrite`). Reduces tool count but adds a parameter.
- **Option B (differentiate by scope):** `edit` handles changes under N characters (single-line, targeted). `write` handles full-file replacement. Descriptions must explicitly state the boundary.
- **Option C (test-driven):** Deploy both and measure selection confusion. If confusion exceeds 30%, fall back to Option A or B.

**Decision:** Option C is the default. The iterative testing protocol (V1) will measure selection confusion between `write` and `edit` for prompts that could match either. If confusion exceeds 30% across models, the implementation must adopt Option A or B before deployment.

### R3: DeepSeek gating criterion for V1 testing

DeepSeek shows 100% position-0 bias in the mcp-naming-bias experiments — the strongest position bias of any tested model. If semantic matching truly overrides position bias, DeepSeek should still select the composite tool at >80% rate when the name matches the prompt intent. If it does not, the research generalization fails for the most position-biased model in the test set.

**Rule:** V1 verb-class testing must run against `ollama/deepseek-v4-flash:cloud` first. If selection rate is below 80% for any composite tool, halt testing and re-evaluate the naming strategy before proceeding to other models. A failure here means semantic matching alone is insufficient to overcome position bias for this model class, and additional strategies (description engineering, platform-level tool filtering) must be explored.

### R4: Positive framing mandate for all tool descriptions

The mcp-naming-bias experiments show that negative-sentiment names (`deprecated`) are avoided 0% of the time across all models, while positive-sentiment names (`recommended`) dominate selection (100% for Claude, DeepSeek, Mistral). This applies to description text as well as tool names.

**Rule:** All tool descriptions — both composite and existing — MUST use positive framing only. Prohibited patterns include:
- "Unlike the built-in read..." (negative comparison)
- "Avoids data loss" (negative framing — implies danger)
- "Prevents corruption" (negative framing)
- "Instead of X..." (comparison framing)

Required patterns:
- "Staged editing for safe review" (positive outcome)
- "Conflict detection included" (feature statement)
- "Preferred for file operations" (positive sentiment)
- "Supports offset/limit for partial reads" (capability statement)

This is a hard requirement, not a test variable. The V3 comparison framing test will confirm the optimal positive variant, but negative framing is prohibited regardless of test outcome.

### R5: Description specificity must be determined empirically (V2 testing)

The Over-Specification Paradox (S* ~0.509 from opencode-config#161) shows that too much detail in descriptions can paradoxically reduce reliability. Anthropic's guide confirms that small description refinements produce dramatic effects on tool selection. The optimal specificity level varies by model.

**Rule:** V2 testing must test three description specificity levels for each composite tool:

- **Minimal:** `"Read file contents."` — bare imperative, no constraints
- **Constraint-statement:** `"Read a file's contents via a scoped viewport window. Supports line_start/line_end for partial reads."` — Anthropic-recommended pattern: state what it does, state the constraints
- **Elaborated:** Full paragraph with parameter details, use cases, and edge cases — risks hitting the S* over-specification threshold

The winning level is determined by selection rate across all 4 models. The constraint-statement level is the expected winner per Anthropic's findings, but must be confirmed empirically. If the elaborated level wins for any model, investigate whether the S* threshold varies by model architecture.

## Evaluation Methodology

### Test Configs and Directory Structure

Tool configs are per-variant YAML files in `test/tool-selection/configs/`. Each config specifies the tool name, description text, variant label, and metadata needed by the test harness. Configs are prompt-level — since composite tools don't exist yet, descriptions are embedded in scenario prompts rather than MCP server definitions.

```
test/tool-selection/
  run.sh                          — Convenience runner (--variable, --model, --iterations, --gating, --quick, --dry-run)
  run_v1_verb_class.sh            — V1: verb vs verb_noun across 5 tools
  run_v2_description.sh           — V2: minimal vs constraint vs elaborated
  run_v3_framing.sh               — V3: bare vs positive differentiation
  run_v4_position.sh              — V4: composite-first vs composite-last vs composite-middle
  run_v5_coexistence.sh           — V5: neutral vs instructional vs preference-hinting
  configs/
    v1_verb_class/
      read-verb.yaml
      read-verb_noun.yaml
      write-verb.yaml
      write-verb_noun.yaml
      edit-verb.yaml
      edit-verb_noun.yaml
      find-verb.yaml
      find-verb_noun.yaml
      diff.yaml                   (no noun variant)
    v2_description/
      read-minimal.yaml
      read-constraint.yaml
      read-elaborated.yaml
      ...per-tool...
    v3_framing/
      read-bare.yaml
      read-positive_diff.yaml
      ...per-tool...
    v4_position/
      composite-first.yaml
      composite-last.yaml
      composite-middle.yaml
    v5_coexistence/
      read-neutral.yaml
      read-instructional.yaml
      read-preference-hinting.yaml
      ...per-tool...
  README.md                       — How to run tests, interpret results
```

### Config File Schema

```yaml
# Common fields for all configs
variable: v1                      # v1|v2|v3|v4|v5
variant: verb                     # Variant label (e.g. "verb", "verb_noun", "minimal")
tool: read                        # MCP tool name
composite: true
target_intent: "read a file"      # Agent intent this tool targets
expected_alternative: "read"      # Built-in tool this competes with
description: "..."                # Tool description text (the variable being tested)
```

### Scenario Naming Convention

Each `behavior_run()` call uses a scenario name encoding: variable, tool, variant, model, iteration number.

Format: `v<VAR>-<TOOL>-<VARIANT>-<MODEL_SLUG>-<ITERATION>`

Examples:
- `v1-read-verb-deepseek-01`
- `v1-read-verb_noun-deepseek-01`
- `v2-read-constraint-nemotron-05`
- `v3-read-positive_diff-qwen-10`

This produces artifact directories like:
`tmp/behavioral-evidence-v1-read-verb-deepseek-01-GREEN-ollama-deepseek-v4-flash-cloud/`

### Iteration Logic

Each run script iterates over (configs × models × iterations) with a flat loop:
```
for config in configs/v1_verb_class/*.yaml:
  for model in [deepseek, gpt-oss, nemotron, qwen]:
    for iteration in 1..20:
      scenario_name = encode(config.variable, config.tool, config.variant, model, iteration)
      behavior_run(scenario_name, build_prompt(config), model)
```

The bash tool sets the sole timeout boundary. No internal timer. No `timeout` command wrapping. No assertions.

### Trace Report (Post-Cycle Aggregation)

Timeout discipline is a hard requirement per bug #1076. The bash tool's native timeout parameter is the **sole timeout boundary** — no `timeout` command wrapping inside the bash invocation, and `behavior_run()` MUST NOT use an internal timer. Nested timeouts (bash tool timeout + internal timer inside the script) cause the shell to be killed while `opencode-cli run` and its MCP subprocesses continue as orphaned children. Bash tool timeout must be either 0 (no timeout) or set to the maximum acceptable wall-clock duration for the full run including retries.

**SSE Read Timeout:** The `opencode.jsonc` model configuration for all ollama/ models must set a reasonable `sse_read_timeout` value to prevent "blackholed" connections (connections that accept but never send data) from blocking test runs indefinitely. This is a platform-level setting in the opencode configuration, not a test harness concern. The test environment's opencode.jsonc must be verified to have this configured before any V1–V5 testing begins.

### Clean-Room Sub-Agent Evaluation

Evaluation is performed by a clean-room sub-agent dispatched from the implementation pipeline. The sub-agent receives:

- The artifact directory path (containing stdout.log, stderr.log, manifest.yaml)
- A structured evaluation prompt specifying what to assess

The sub-agent reads the artifacts and applies semantic judgment to determine:

- **selected_tool:** Which tool the agent ultimately called (from stderr tool dispatch trace)
- **deliberation_evidence:** Whether the agent's reasoning trace (stdout) shows it considered multiple tools before selecting one
- **almost_correct:** The agent nearly selected the composite tool but switched away, or nearly selected the built-in but switched to the composite
- **confusion_indicators:** Specific phrases or reasoning patterns suggesting the agent misunderstood the tool's purpose or scope
- **reasoning_quality:** Qualitative assessment of whether the agent's tool selection reasoning was sound

The sub-agent receives ONLY the artifact directory path and the evaluation prompt — no orchestrator reasoning, no expected outcomes, no cached results. This is a clean-room assessment per the DISPATCH_GATE protocol.

### Result Artifact Storage

Evaluation results are stored as a structured file (YAML or JSON) in the same artifact directory as the test run they evaluate:

```
tmp/behavioral-evidence-<scenario>-<phase>-<model>/
  manifest.yaml        — Test run metadata
  stdout.log           — Agent prose response
  stderr.log           — Tool dispatch trace
  evaluation.yaml      — Sub-agent evaluation results (added after evaluation pass)
```

This keeps the evaluation results co-located with the source artifacts they assess. The evaluation.yaml file contains the sub-agent's findings per the schema above, plus a reference to the sub-agent model used for evaluation.

### Frugal Result Contracts

Per the orchestrator context discipline (020-go-prohibitions.md §1.1), the evaluation sub-agent returns only a routing-significant result contract:

```yaml
status: DONE
finding_summary: "V1 verb-class: read verb variant achieved 85% selection across 4 models. write/edit overlap at 22% — below 30% threshold."
artifact_path: tmp/behavioral-evidence-v1-verb-class-deepseek/
blocker_reason: null
```

Full evaluation details (per-run breakdowns, confusion matrices, qualitative findings) go into `evaluation.yaml` in the artifact directory — never into the result contract.

### Trace Report (Post-Cycle Aggregation)

After each full test cycle (all V1–V5 runs for all models), a dedicated clean-room sub-agent reads ALL `evaluation.yaml` files from all artifact directories and produces a trace report. This is a separate step from per-run evaluation — it aggregates across variables, variants, models, and iterations.

**Trace report contents:**

- Per-variable summary tables: variant tested, selection rate per model, declared winner
- Per-model bias profile: how each model responded across all variables
- Confusion matrix for write/edit overlap (V1)
- Lessons learned: qualitative findings from evaluator notes across all runs
- Winning configuration lock: final naming, description level, framing, and coexistence strategy per tool

**Storage:** `test/tool-selection/trace-report.yaml` (structured data) and `test/tool-selection/trace-report.md` (human-readable narrative). Both regenerated on each cycle — old trace report wiped, new one produced from current artifacts.

**Frugal contract:** The trace sub-agent returns only `status: DONE` or `blocker_reason` if data is insufficient to declare winners. Full details go into the trace report files — never into the result contract.

## Branch and Tagging Strategy

### Feature Branch

A dedicated feature branch `feature/63-composite-tools` tracks all work for this spec: test scripts, implementation code, and description rewrites. The test harness sources the correct tool definitions via `opencode.jsonc` configuration — no PR merge boundaries needed between phases. The branch accumulates all changes atomically.

### Rollback Tags

Git tags mark each major checkpoint for rollback:

| Tag | Point | Contents |
|-----|-------|----------|
| `63/checkpoint/testing-start` | Before any V1 testing begins | Clean dev branch state, spec finalized |
| `63/checkpoint/v1-complete` | After V1 verb-class testing done | Winning verb variant determined, evaluation.yaml stored |
| `63/checkpoint/v2-complete` | After V2 description specificity done | Winning description level determined |
| `63/checkpoint/v3-complete` | After V3 comparison framing done | Winning framing determined |
| `63/checkpoint/v4-complete` | After V4 position testing done | Position effect data collected |
| `63/checkpoint/v5-complete` | After V5 coexistence testing done | Winning strategy determined |
| `63/checkpoint/implementation-start` | Before writing any composite tool code | All testing results finalized, winning config locked |
| `63/checkpoint/composite-tools` | After 5 composite tools implemented | All 5 tools registered, tests pass |
| `63/checkpoint/descriptions` | After 7 existing tool descriptions rewritten | All descriptions in agent-facing style |

Tag format: `63/checkpoint/<phase>` per the git-workflow convention. Tags are lightweight (not annotated) and local-only unless pushed explicitly.

## Implementation

### New Code

Only `src/viewport_editor/server.py` changes — 5 new `@mcp.tool()` registrations, each delegating to a composite handler function. The handler functions call the existing `ViewportManager` API:

```python
@mcp.tool()
def read(ctx: Context, file_path: str, line_start: int = 1, line_end: int = 100) -> str:
    """Read a file's contents via a scoped viewport window with conflict detection."""
    ...

@mcp.tool()
def write(ctx: Context, file_path: str, content: str) -> str:
    """Create or overwrite a file with the given content. Stages through buffer with conflict detection."""
    ...

@mcp.tool()
def edit(ctx: Context, file_path: str, old_text: str, new_text: str) -> str:
    """Perform a targeted text replacement in a file. Stages through buffer with conflict detection."""
    ...

@mcp.tool()
def find(ctx: Context, pattern: str, file_path: str = "", regex: bool = False) -> str:
    """Search file contents for a pattern. Supports substring and regex matching."""
    ...

@mcp.tool()
def diff(ctx: Context, file_path: str) -> str:
    """Show the unified diff of pending buffer changes for a file."""
    ...
```

### No Data Model Changes

The composite tools reuse existing ViewportManager methods. No new models, buffers, or state required.

### Error Handling

| Failure Mode | Detection | Response |
|-------------|-----------|----------|
| File not found (read/edit) | FileNotFoundError from viewport:open | isError, "file not found: {path}" |
| old_text not found (edit) | ReplaceTargetNotFoundError | isError, "old text not found in {file}" |
| Multiple matches (edit) | ReplaceAmbiguousMatchError | isError, "multiple matches — use read and a more specific old_text" |
| File changed externally | Conflict check on save | isError with conflict details |
| Pattern not found (find) | Empty result set | "no matches found" (not an error) |

## Motivation (Why 5 Tools, Not 18)

Adding 5 composite tools follows the same consolidation principle as the original 6-tool design. Each composite tool covers a distinct agent intent:

- `read` = "I need to see file contents"
- `write` = "I need to create or fully replace a file"
- `edit` = "I need to change specific text in a file"
- `find` = "I need to search file contents"
- `diff` = "I need to review pending changes"

These 5 verbs cover >95% of file operations an agent performs. The remaining operations (clipboard, diff apply, multi-edit staging, regex testing) are advanced workflows that benefit from the existing tool granularity.

## SC Coverage

| ID | Criterion | Evidence Type |
|----|-----------|---------------|
| SC-1 | `read` returns file content for an existing file with line_start, line_end, visible text, mtime, size | `behavioral` |
| SC-2 | `read` with offset/limit returns the specified line range | `behavioral` |
| SC-3 | `read` returns error for non-existent file | `behavioral` |
| SC-4 | `write` creates a new file with the specified content | `behavioral` |
| SC-5 | `write` overwrites an existing file with the specified content | `behavioral` |
| SC-6 | `write` detects external file modification and reports conflict | `behavioral` |
| SC-7 | `edit` replaces old_text with new_text in the specified file | `behavioral` |
| SC-8 | `edit` returns error when old_text is not found | `behavioral` |
| SC-9 | `edit` returns error on ambiguous matches | `behavioral` |
| SC-10 | After `write` or `edit`, the viewport is closed (no dangling sessions) | `behavioral` |
| SC-11 | `find` returns structured results with line numbers for substring match | `behavioral` |
| SC-12 | `find` with regex=true returns regex match results | `behavioral` |
| SC-13 | `diff` returns unified diff of pending buffer changes for an open file | `behavioral` |
| SC-14 | `diff` returns empty result when no pending changes | `behavioral` |
| SC-15 | All 5 composite tools use naming convention determined by iterative testing | `string` |
| SC-16a | Agent selects composite `read` over built-in `read` at >80% rate with optimal naming variant — tested with `ollama/deepseek-v4-flash:cloud` | `behavioral` |
| SC-16b | Agent selects composite `write` over built-in `write` at >80% rate with optimal naming variant — tested with `ollama/deepseek-v4-flash:cloud` | `behavioral` |
| SC-16c | Agent selects composite `edit` over built-in `edit` at >80% rate with optimal naming variant — tested with `ollama/deepseek-v4-flash:cloud` | `behavioral` |
| SC-16d | Agent selects composite `find` over built-in `grep` at >80% rate with optimal naming variant — tested with `ollama/deepseek-v4-flash:cloud` | `behavioral` |
| SC-16e | Iterative tuning achieves max selection rate across all 4 target models — results recorded in `tmp/tool-naming-test-results.md` | `behavioral` |

> **Evidence base:** SC-16a through SC-16e test whether the semantic gap identified in [Card 6](spec-artifacts/research/card-catalogue.md#card-6-the-semantic-gap--viewport-editor-vs-built-in) has been closed. The card maps each agent intent to the current multi-call workflow and the proposed single-call composite — these SCs verify that the composite tools are actually selected over the built-in alternatives.
| SC-17 | write/edit overlap confusion does not exceed 30% across all 4 target models | `behavioral` |
| SC-18 | All 7 existing tool descriptions are re-written in agent-facing, constraint-stating style | `string` |
| SC-19 | All tool descriptions use positive framing only — no negative comparisons, no danger/avoidance language | `string` |
| SC-20 | V1 verb-class testing runs against DeepSeek first as gating criterion; halt and re-evaluate if <80% selection | `behavioral` |
| SC-21 | Description specificity determined by V2 testing across 3 levels (minimal, constraint-statement, elaborated) — constraint-statement is expected winner | `behavioral` |
| SC-22 | Evaluation uses clean-room sub-agent semantic inspection — not grep on stderr — for all selection rate and confusion measurements | `behavioral` |
| SC-23 | Evaluation results stored as `evaluation.yaml` co-located with source artifacts in the same artifact directory | `string` |
| SC-24 | Evaluation sub-agent result contract is frugal — status + finding_summary + artifact_path only; full details in evaluation.yaml | `string` |

### SC-16e Model Set

Iterative testing runs against these 4 models to validate cross-model generalization:

| Model | Name | Notes |
|-------|------|-------|
| `ollama/deepseek-v4-flash:cloud` | DeepSeek V4 Flash (cloud) | Primary target — primary development model |
| `ollama/gpt-oss:20b-128k` | GPT-OSS 20B | Weaker model — tests edge of comprehension |
| `ollama/nemotron3:33b-128k` | Nemotron 3 33B | Mid-range — tests naming effectiveness at scale |
| `ollama/qwen3.6:35b-256k` | Qwen 3.6 35B | Long-context variant — tests with large tool listing |

Test methodology per the Iterative Testing Protocol: 20 iterations per variant per model, selection rate measurement per variable.

## Relevant Research (Card Catalogue)

Full research catalogue at `spec-artifacts/research/card-catalogue.md` with 8 cards covering:

- **BiasBusters (arXiv 2510.00307):** Confirms semantic alignment as the strongest driver of tool selection. Small description changes shift choices. Mitigation via subset-filtering.
- **mcp-naming-bias experiments:** All models (Claude, GPT-4o, Gemini, DeepSeek, Mistral, Qwen, Llama) show 100% semantic matching when tool name matches prompt intent. Claude shows least position bias.
- **Anthropic "Writing Effective Tools":** Recommends composite actions over split tools. Namespacing by domain prefix. Tool descriptions as constraint statements. Prefix vs suffix has non-trivial effects on selection.
- **AWS domain-noun-verb pattern:** `github_issue_create` — rationale is alphabetical clustering for human browsing, not agent psychology.
- **SEP-986:** Allows `_`, `-`, `/`, `.` in tool names.
- **Arcade.dev:** Verb-object naming preferred. `create_meeting` over `schedule`.
- **LLM Control Language (opencode-config#161):** Verb class reliability (RQ4), Over-Specification Paradox (S* ~0.509), constructional determinacy — all apply directly to tool naming and description engineering.
