# AGENTS.md — Papers

## Build Requirements

Every paper must include a `build.py` (PEP 723) at its root. The build script requires:

- `xelatex` (TeX Live)
- `biber` or `bibtex`
- `makeindex`

Build: `./papers/<slug>/build.py`

Output: `paper.pdf` at paper root (tracked in git). Build artifacts go to `build/` (fully gitignored).

## Directory Structure

```
papers/<slug>/
├── src/
│   ├── paper.tex         — main document (may include additional .tex files)
│   └── references.bib    — bibliography
├── figures/              — figures (tracked)
├── build/                — build artifacts (gitignored)
├── paper.pdf             — final PDF at paper root (tracked)
└── build.py              — PEP 723 build script
```

## Research Card Catalogues (MANDATORY)

Before writing any paper, the agent MUST conduct research using available tools (web search, arXiv, aixiv, relevant documentation) and record findings in a research card catalogue. This is not optional — papers written from memory or training data alone produce unsubstantiated claims.

The research card catalogue goes in `papers/<slug>/src/research/` and MUST include:

| Card Field | Required | Content |
|------------|----------|---------|
| Claim | Yes | The factual claim being investigated |
| Sources consulted | Yes | URLs, DOIs, or tool calls used to verify |
| Verdict | Yes | Supported, Refuted, or Inconclusive |
| Evidence | Yes | Direct quote or summary of what the source says |
| Date | Yes | When the research was conducted |

The agent MUST NOT make any factual claim in the paper that has not been verified through the research card catalogue process. Claims marked Inconclusive must be explicitly caveated in the paper text.

Research card catalogues are preserved in git and serve as the audit trail for the paper's factual claims. They are NOT included in the final PDF.

## Authorship Requirements

When producing a LaTeX paper in this repository:

- The AI agent (OpenCode) is the **author**. The agent writes the paper, designs the methodology, produces the content, and is responsible for its technical accuracy.
- Michael Conrad is the **director/supervisor**. He defines the scope, direction, requirements, and constraints under which the agent operates. He is not an author but the work is done under his direction.
- The author line reads: `\author{OpenCode (deepseek-v4-flash)}`
- The abstract includes the note: "The research, design, and writing of this work were conducted under the direction and supervision of Michael Conrad."

This convention applies to ALL papers in this repository. No exceptions. Do not list Michael Conrad as an author or co-author. Do not list the agent as a co-author with a human. The agent is the sole author.

## Provenance Headers

All source files (`src/paper.tex`, `src/references.bib`, `build.py`) MUST include SPDX and Provenance headers per the repository's code standards:

```latex
% SPDX-FileCopyrightText: 2026 Michael Conrad
% SPDX-License-Identifier: MIT
% Provenance: AI-generated
%
% Co-authored with AI: OpenCode (deepseek-v4-flash)
```

The `paper.pdf` output file is a build artifact but is tracked in git for convenience. It does not need provenance headers (binary format).

## Acknowledgments

If the paper includes an acknowledgments section, the agent may add a note about the supervision arrangement. No other acknowledgments are required unless the director specifies them.

## Research Procedure

1. Create research card catalogue directory: `mkdir -p papers/<slug>/src/research/`
2. For each factual claim the paper will make, research using available tools
3. Record findings in cards (one per claim)
4. Only after research catalogue is complete: write the paper
5. Include citations to primary sources where possible
6. Preserve research cards in git (they are the audit trail)

## Cross-References

- `AGENTS.md` (repo root) — General agent guidelines, LaTeX paper section
- `080-code-standards.md` — Provenance headers, code attribution standards
- `065-verification-honesty.md` — Verification requirements for factual claims