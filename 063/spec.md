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

**Current architecture:** 6 tools with action dispatch parameters (viewport, edit, file, diff, search, regex). To perform a file read, the agent must call `viewport-editor_viewport` with `action="open"`, then parse the YAML response. To write, it must call `viewport-editor_edit` with `action="replace-all"`, then `viewport-editor_file` with `action="save"`. No tool name matches any agent intent verb directly.

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
| SC-17 | write/edit overlap confusion does not exceed 30% across all 4 target models | `behavioral` |
| SC-18 | All 7 existing tool descriptions are re-written in agent-facing, constraint-stating style | `string` |

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

Full research catalogue at `tmp/tool-naming-research-card-catalogue.md` with 8 cards covering:

- **BiasBusters (arXiv 2510.00307):** Confirms semantic alignment as the strongest driver of tool selection. Small description changes shift choices. Mitigation via subset-filtering.
- **mcp-naming-bias experiments:** All models (Claude, GPT-4o, Gemini, DeepSeek, Mistral, Qwen, Llama) show 100% semantic matching when tool name matches prompt intent. Claude shows least position bias.
- **Anthropic "Writing Effective Tools":** Recommends composite actions over split tools. Namespacing by domain prefix. Tool descriptions as constraint statements. Prefix vs suffix has non-trivial effects on selection.
- **AWS domain-noun-verb pattern:** `github_issue_create` — rationale is alphabetical clustering for human browsing, not agent psychology.
- **SEP-986:** Allows `_`, `-`, `/`, `.` in tool names.
- **Arcade.dev:** Verb-object naming preferred. `create_meeting` over `schedule`.
- **LLM Control Language (opencode-config#161):** Verb class reliability (RQ4), Over-Specification Paradox (S* ~0.509), constructional determinacy — all apply directly to tool naming and description engineering.
