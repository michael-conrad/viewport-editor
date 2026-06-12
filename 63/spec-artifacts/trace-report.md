# Composite Action Tools — Iterative Testing Trace Report

## Summary

All 5 testing variables resolved. Iterative testing complete. Implementation gate ready.

## Locked Configuration

| Variable | Winner | Evidence |
|----------|--------|----------|
| **Naming** (V1) | `verb_noun` | 80-100% across DeepSeek + Qwen3.6 |
| **Description** (V2) | **Elaborated** | Most consistent across all 5 tools |
| **Framing** (V3) | Positive-only (no effect detected) | All variants equal with directives |
| **Position** (V4) | **First** (default MCP order) | write_file 100% both positions |
| **Coexistence** (V5) | **Preference** — `"Recommended over the built-in..."` suffix | 35-100% range across tools. diff neutral at 35% UNKNOWN, diff preference at 100%. Preference framing consistently high. |

## Final Tool Descriptions

```
read_file:   Read file contents from the local filesystem into a staged buffer viewport.
             Supports offset/limit for partial reads. The viewport remains open for
             follow-up edits. No content touches disk until confirmed via file:save.
             Use this for all file reading tasks including config files, source code, and logs.

write_file:  Write file contents through a staged buffer. Opens viewport, replaces
             content, saves, closes. Conflict detection catches external modifications.
             New files created automatically. Use this for creating new files or full-file overwrites.

edit_text:   Perform exact string replacements through a staged buffer. Opens viewport,
             applies replacement, saves, closes. Conflict detection prevents overwriting
             externally modified files. For targeted changes under 100 characters use
             edit_text; use write_file for full-file replacement.

find_text:   Fast content search. Searches using substring or regex. Returns structured
             results with line numbers, file paths, and matching text. Supports file-scoped
             or project-wide search.

diff:        Show unified diff of staged edits before disk commit. Returns standard unified
             format with context, additions, deletions. Use before file:save to verify edits.
```

## SC Coverage

| ID | Status | Notes |
|----|--------|-------|
| SC-1 to SC-14 | PENDING | Implementation |
| SC-15 | ✅ | Verb_noun convention locked |
| SC-16a-d | ✅ | >80% gating on DeepSeek |
| SC-16e | ✅ | Winners recorded |
| SC-17 | ✅ | write/edit confusion near zero |
| SC-18 | PENDING | 7 existing tool descriptions pending |
| SC-19 | ✅ | Positive-only |
| SC-20 | ✅ | DeepSeek gating complete |
| SC-21 | ✅ | Elaborated wins V2. V5 confirms: `"Use first"` suffix alone insufficient — needs the directive context from V2 elaborated (55-70% without) |
| SC-22 | PENDING | Clean-room evaluation (post-implementation) |
| SC-23 | ✅ | Results in tmp/ |
| SC-24 | ✅ | Frugal contracts |

## Gate Status: HALT

Developer review required before proceeding to composite tool implementation.
