# Tool Naming & Agent Adoption — Research Card Catalogue

Created: 2026-06-08
Sources: Anthropic Engineering, AWS Prescriptive Guidance, arXiv 2510.00307 (BiasBusters), MCP SEP-986, Arcade.dev, mcp-naming-bias (Yaniv Gabay), MCP Best Practices Guide

---

## Card 1: Why Agents Prefer Built-in Tools Over Custom MCP

**Source:** BiasBusters (arXiv 2510.00307) + mcp-naming-bias experiments + Anthropic tool-writing guide

### Key Findings

| Factor | Effect | Source |
|--------|--------|--------|
| **Position 0 bias** | Most models heavily favor the first tool in the list. Claude 3.5 Haiku is least biased (40%/45%/5%/10% across positions 0-3). Gemini/DcepSeek show 100% position-0 preference. | mcp-naming-bias |
| **Semantic matching overrides position** | When tool names contain words from the user prompt, ALL tested models (except Gemini) pick the semantic-match tool 100% of the time — even when it's NOT at position 0. | mcp-naming-bias |
| **Semantic alignment is the strongest driver** | "Semantic alignment between user queries and tool metadata is the strongest driver of selection." | BiasBusters §Abstract |
| **Small description perturbations shift choices** | Minor changes to tool descriptions can significantly alter which tool the model selects. | BiasBusters §Abstract |
| **Pre-training exposure amplifies provider bias** | Repeated exposure to a single endpoint during training creates preference for that tool family. | BiasBusters §Abstract |

### Implication for viewport-editor

The built-in tools (`read`, `edit`, `write`, `grep`, `glob`) are:
1. **At position 0 in their namespace** — listed first among all tools
2. **Semantically exact matches** — `read` matches "I want to read", `write` matches "I want to write"
3. **Pre-training-exposed** — LLMs have seen these verbs millions of times in training data
4. **Single-word, high-frequency verbs** — vs `viewport-editor_viewport` (multipart, namespaced, tool-name + action dispatch)

The viewport-editor tools lose on ALL FOUR bias dimensions simultaneously: they're later in the list, semantically opaque, unseen in training, and buried behind a namespace + action dispatch.

---

## Card 2: Tool Naming Standards & Conventions

**Source:** MCP SEP-986, AWS Prescriptive Guidance, Arcade.dev

### SEP-986 Tool Name Format

| Rule | Value |
|------|-------|
| Length | 1-64 characters |
| Case | Case-sensitive |
| Allowed chars | `A-Z`, `a-z`, `0-9`, `_`, `-`, `.`, `/` |
| Forbidden | Spaces, commas |
| Hierarchical | `/` and `.` for namespacing supported |

### AWS Domain-Noun-Verb Pattern

```
github_issue_create
github_issue_list
github_issue_update
└─────┘└───┘└────┘
 domain  noun  verb
```

**Rationale:** Alphabetical sorting clusters related operations. Noun = organizational boundary. Verb = operation type.

### Arcade.dev: Verb-Object vs Generic Verbs

| Good | Bad | Reason |
|------|-----|--------|
| `create_meeting` | `schedule` | Verb + object clarifies intent |
| `send_email` | `notify` | Concrete vs abstract |
| `upload_document` | `process` | Specific operation vs vague |

### Anthropic: Namespacing Matters

"Namespacing tools by service (e.g., `asana_search`, `jira_search`) and by resource (e.g., `asana_projects_search`, `asana_users_search`) can help agents select the right tools."

---

## Card 3: The Composite Action Principle

**Source:** Anthropic Engineering — Writing Tools for Agents

### Consolidation Over Decomposition

| Split tools (bad) | Consolidated tool (good) | Why |
|-------------------|--------------------------|-----|
| `list_users`, `list_events`, `create_event` | `schedule_event` | Single call vs multi-call chain |
| `read_logs` | `search_logs` | Targeted retrieval vs brute-force |
| `get_customer`, `list_transactions`, `list_notes` | `get_customer_context` | Compiled context vs scatter-gather |

### Key Insight for viewport-editor

Anthropic explicitly recommends: **"Tools can consolidate functionality, handling multiple discrete operations under the hood."** This directly supports adding composite actions to the viewport-editor that wrap the open→edit→save cycle into single-call verbs matching agent intent.

---

## Card 4: Tool Selection Bias - Model-Specific Breakdown

**Source:** mcp-naming-bias (Yaniv Gabay) — 7 models, 20+ iterations each

### Position 0 Bias (neutral names)

| Model | Pos 0 | Pos 1 | Pos 2 | Pos 3 |
|-------|-------|-------|-------|-------|
| Gemini 2.0 Flash | **100%** | 0% | 0% | 0% |
| DeepSeek Chat | **100%** | 0% | 0% | 0% |
| Mistral Nemo | **85%** | 10% | 5% | 0% |
| Qwen Plus | **80%** | 10% | 5% | 5% |
| GPT-4o-mini | **65%** | 20% | 15% | 0% |
| Llama 3.1 8B | **55%** | 10% | 15% | 20% |
| Claude 3.5 Haiku | **40%** | 45% | 5% | 10% |

### Semantic Matching (prompt: "pick any tool")

Tools: [`always`, `pick`, `first`, `option`]

| Model | `always` | `pick` | `first` | `option` |
|-------|----------|--------|---------|----------|
| GPT-4o-mini | 0% | **100%** | 0% | 0% |
| Claude Haiku | 0% | **100%** | 0% | 0% |
| DeepSeek | 0% | **100%** | 0% | 0% |
| Gemini | **70%** | 30% | 0% | 0% |

### Sentiment Bias

Tools: [`recommended`, `alternative`, `backup`, `deprecated`]

- `deprecated` was **NEVER** selected by any model (0%)
- `recommended` dominated: Claude 100%, DeepSeek 100%, Mistral 95%, Qwen 90%, GPT-4o 75%

---

## Card 5: Tool Description Engineering

**Source:** Anthropic Engineering, Arcade.dev

### What Makes an Agent-Readable Description

| Principle | Example (bad) | Example (good) |
|-----------|--------------|----------------|
| State constraints | `"Schedule meetings"` | `"Schedule a video meeting with ISO formats and one attendee."` |
| Parameter formats | `"when": {"type": "string"}` | `"datetime": {"type": "string", "description": "ISO 8601 (YYYY-MM-DDTHH:MM)"}` |
| Closed sets as enums | `"type": {"type": "string"}` | `"meeting_type": {"enum": ["demo", "review", "planning", "1:1"]}` |
| Single clear purpose | `"Manage files"` | `"Read entire file contents with offset/limit support. Does NOT modify files."` |

### Anthropic's Key Recommendation

> "When writing tool descriptions, think of how you would describe your tool to a new hire. Consider the context that you might implicitly bring and make it explicit."

> "Even small refinements to tool descriptions can yield dramatic improvements. Claude Sonnet 3.5 achieved state-of-the-art on SWE-bench Verified after precise refinements to tool descriptions."

---

## Card 6: The Semantic Gap — Viewport-Editor vs Built-in

**Source:** viewport-editor MCP tool definitions analysis

### Current Viewport Tool Names

| Tool | Action Verbs | Agent Reads As |
|------|-------------|---------------|
| `viewport-editor_viewport` | open, close, list, scroll, page-up, page-down, jump, autosave, set-display-mode | Window manager |
| `viewport-editor_edit` | replace, replace-all, insert-lines, delete-lines, swap-lines, move-lines | Text editor |
| `viewport-editor_file` | save, discard, new, save-as, delete | File manager |
| `viewport-editor_diff` | show, apply | Diff viewer |
| `viewport-editor_clipboard` | copy, cut, paste, show, stash, pop, swap, stash-list | Clipboard |
| `viewport-editor_search` | find | Search tool |
| `viewport-editor_regex` | test, escape | Regex tool |

### What Agent Actually Wants

| Agent Intent | Built-in (1 call) | Viewport (N calls) | Match Quality |
|-------------|-------------------|--------------------|---------------|
| Read a file | `read(path)` | `viewport:open` → `scroll` | Built-in wins semantically |
| Write a file | `write(path, content)` | `viewport:open` → `edit:replace` → `file:save` | Built-in wins on call count |
| Edit in place | `edit(path, old, new)` | `viewport:open` → `edit:replace` → `file:save` | Built-in wins on simplicity |
| Find text | `grep(pattern)` | `search:find` | Close match |

---

## Card 7: Mitigation Strategies (from Research)

**Source:** BiasBusters, Anthropic guide

### Strategy A: Subset-Filter + Uniform Sample (BiasBusters)

"First filter tools to a relevant subset, then sample uniformly" — reduces selection bias while maintaining task coverage.

### Strategy B: Tool Name + Description Engineering (Anthropic)

Names and descriptions are the strongest lever. Short, action-oriented names + constraint-stating descriptions outperform verbose definitions.

### Strategy C: Position Strategy (mcp-naming-bias)

Put most important tools first. Claude is least position-biased, but Gemini/DeepSeek show 100% position-0 lock-in.

### Strategy D: Composite Actions (Anthropic principles)

Consolidate multi-step workflows into single tools named after the *intent*, not the *implementation*. The agent's intent is "read file," not "open viewport, then scroll."

---

## Card 8: Tool Name Recommendation Framework

**Source:** Synthesis across all sources

### Naming Criteria (in priority order)

1. **Semantic match** — Does the name match the agent's natural language when forming intent?
2. **Verb-object structure** — Action + target (e.g., `read_file`, `search_text`)
3. **Domain prefix** — Namespacing to avoid collision with built-ins (e.g., `vp_read`, `vp_find`)
4. **Positive sentiment** — Avoid `deprecated`, `dangerous`, `discard` as primary verbs
5. **First in category** — Leverage position 0 bias within the custom tool namespace

### For viewport-editor, this suggests:

| Agent Intent | Candidate Tool Name | Maps to |
|-------------|---------------------|---------|
| Read a file | `vp_read` (or `viewport_read`) | open + scroll composite |
| Write a file | `vp_write` (or `viewport_write`) | open + edit:replace-all + save |
| Edit in place | `vp_edit` (or `viewport_edit`) | open + edit:replace + save |
| Search content | `vp_grep` (or `viewport_search`) | existing search:find |
| Diff view | `vp_diff` (or `viewport_diff`) | existing diff:show |
| Clipboard | `vp_copy`, `vp_paste` | existing clipboard |

The key: these are **separate tool entries** (not actions on a single tool) that an agent can select by name match, just like built-ins. Each internally performs the open→edit→save cycle but presents as a single-call verb.