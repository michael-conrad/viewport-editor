# Stress Test Report: final-run

## Summary

- **Density:** dense
- **Total sequences:** 272
- **Duration:** 4.1s
- **Passed mechanical audit:** 235/272
- **Failed mechanical (AI dispatched):** 37/37
- **AI Semantic Verdicts:** 37/37 **PASS** — no bugs detected

## Conclusion

**No bugs found.** All 272 sequences executed without crash. All 37 mechanically-flagged findings confirmed as correct tool behavior via sequential clean-room sub-agent dispatch.

Every logged error is an expected rejection of invalid operations:
- `EditTargetNotFoundError` when prior edits (replace-all, delete-lines) consumed the target text
- `LineRangeError` when prior edits (delete-lines, insert-lines) shifted line count, making subsequent ranges out of bounds
- `ViewportError` on clipboard pop from nonexistent stash slot

The viewport-editor plugin correctly handles all tested patterns:
- Sequential edits at overlapping and non-overlapping positions
- replace-all poisoning of subsequent replace targets
- delete-lines reducing file length and invalidating subsequent operations
- Clipboard stash/pop lifecycle
- Triple-chain edit sequences
- Mtime conflict detection (logged errors are correct tool behavior)

## Files

- **Run logs:** `tmp/stress/final-run/`
- **Mechanical report:** `tmp/stress/final-run/mechanical_report.md`
- **Audit manifest:** `tmp/stress/final-run/findings_manifest.json`
- **Semantic dispatch procedure:** `test/stress/semantic-dispatch-procedure.md`