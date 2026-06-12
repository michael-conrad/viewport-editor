# V3 Comparison Framing Results

## Result
Framing (bare/positive/negative) has no significant effect. The binding constraint is **directive language** — telling the model what to use the tool for overwhelms any framing signal.

## Data (DeepSeek V4 Flash, 20 trials)

| Tool | Bare | Positive | Negative |
|------|:----:|:--------:|:--------:|
| `read_file` | 65% FAIL | 65% FAIL | 55% FAIL |
| `write_file` | 95% PASS | 100% PASS | 100% PASS |

## Analysis
- All three read_file variants remove the directive "Use this for all file reading tasks including config files, source code, and logs" that was in the V2 elaborated winner
- Without directive language, read_file drops from 80% to 55-65% regardless of framing
- write_file retains 95-100% because the prompt itself ("using the recommended writing tool") provides the directive signal
- Negative framing (prohibited by SC-19) offers zero benefit over positive

## Lock Decision
**Stick with V2 elaborated descriptions.** They already use positive-only language (no "unlike," "instead of," "avoid") and include the directive usage sentences that drive selection. No framing changes needed.

The V2 elaborated descriptions comply with SC-19 and the V3 data confirms there is no benefit to adding framing variations.
