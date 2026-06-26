# Stress Test Mechanical Report

**Run:** validation-sparse
**Total sequences:** 104
**Passed:** 90
**Failed (flag raised):** 14
**Timestamp:** 2026-06-12T18:33:24.416538+00:00

## Failed Sequences (14)

| Sequence | Category | Flags |
|----------|----------|-------|
| clipboard-008 | clipboard | expected_error_step_2 |
| edit-pair-0002 | edit_pairs | edit_target_not_found_step_2 |
| edit-pair-0013 | edit_pairs | edit_target_not_found_step_2; missing_expected_content: 'REPLACED' |
| edit-pair-0014 | edit_pairs | edit_target_not_found_step_2; missing_expected_content: 'REPLACED' |
| edit-pair-0015 | edit_pairs | edit_target_not_found_step_2 |
| edit-pair-0016 | edit_pairs | edit_target_not_found_step_2 |
| edit-pair-0038 | edit_pairs | edit_target_not_found_step_2; missing_expected_content: 'REPLACED' |
| edit-pair-0043 | edit_pairs | line_range_step_2 |
| edit-pair-0045 | edit_pairs | line_range_step_2 |
| edit-pair-0047 | edit_pairs | line_range_step_2 |
| edit-pair-0048 | edit_pairs | line_range_step_2 |
| edit-pair-0073 | edit_pairs | edit_target_not_found_step_3 |
| edit-pair-0074 | edit_pairs | edit_target_not_found_step_2; edit_target_not_found_step_3 |
| edit-pair-0075 | edit_pairs | line_range_step_3 |

## All Sequences

| Sequence | Result | Flags |
|----------|--------|-------|
| clipboard-001 | ✅ PASS |  |
| clipboard-002 | ✅ PASS |  |
| clipboard-003 | ✅ PASS |  |
| clipboard-004 | ✅ PASS |  |
| clipboard-005 | ✅ PASS |  |
| clipboard-006 | ✅ PASS |  |
| clipboard-007 | ✅ PASS |  |
| clipboard-008 | ⚠ FAIL | expected_error_step_2 |
| crosstalk-001 | ✅ PASS |  |
| crosstalk-002 | ✅ PASS |  |
| diff-001 | ✅ PASS |  |
| diff-002 | ✅ PASS |  |
| diff-003 | ✅ PASS |  |
| diff-004 | ✅ PASS |  |
| diff-005 | ✅ PASS |  |
| diff-006 | ✅ PASS |  |
| diff-007 | ✅ PASS |  |
| edit-pair-0001 | ✅ PASS |  |
| edit-pair-0002 | ⚠ FAIL | edit_target_not_found_step_2 |
| edit-pair-0003 | ✅ PASS |  |
| edit-pair-0004 | ✅ PASS |  |
| edit-pair-0005 | ✅ PASS |  |
| edit-pair-0006 | ✅ PASS |  |
| edit-pair-0007 | ✅ PASS |  |
| edit-pair-0008 | ✅ PASS |  |
| edit-pair-0009 | ✅ PASS |  |
| edit-pair-0010 | ✅ PASS |  |
| edit-pair-0011 | ✅ PASS |  |
| edit-pair-0012 | ✅ PASS |  |
| edit-pair-0013 | ⚠ FAIL | edit_target_not_found_step_2; missing_expected_content: 'REPLACED' |
| edit-pair-0014 | ⚠ FAIL | edit_target_not_found_step_2; missing_expected_content: 'REPLACED' |
| edit-pair-0015 | ⚠ FAIL | edit_target_not_found_step_2 |
| edit-pair-0016 | ⚠ FAIL | edit_target_not_found_step_2 |
| edit-pair-0017 | ✅ PASS |  |
| edit-pair-0018 | ✅ PASS |  |
| edit-pair-0019 | ✅ PASS |  |
| edit-pair-0020 | ✅ PASS |  |
| edit-pair-0021 | ✅ PASS |  |
| edit-pair-0022 | ✅ PASS |  |
| edit-pair-0023 | ✅ PASS |  |
| edit-pair-0024 | ✅ PASS |  |
| edit-pair-0025 | ✅ PASS |  |
| edit-pair-0026 | ✅ PASS |  |
| edit-pair-0027 | ✅ PASS |  |
| edit-pair-0028 | ✅ PASS |  |
| edit-pair-0029 | ✅ PASS |  |
| edit-pair-0030 | ✅ PASS |  |
| edit-pair-0031 | ✅ PASS |  |
| edit-pair-0032 | ✅ PASS |  |
| edit-pair-0033 | ✅ PASS |  |
| edit-pair-0034 | ✅ PASS |  |
| edit-pair-0035 | ✅ PASS |  |
| edit-pair-0036 | ✅ PASS |  |
| edit-pair-0037 | ✅ PASS |  |
| edit-pair-0038 | ⚠ FAIL | edit_target_not_found_step_2; missing_expected_content: 'REPLACED' |
| edit-pair-0039 | ✅ PASS |  |
| edit-pair-0040 | ✅ PASS |  |
| edit-pair-0041 | ✅ PASS |  |
| edit-pair-0042 | ✅ PASS |  |
| edit-pair-0043 | ⚠ FAIL | line_range_step_2 |
| edit-pair-0044 | ✅ PASS |  |
| edit-pair-0045 | ⚠ FAIL | line_range_step_2 |
| edit-pair-0046 | ✅ PASS |  |
| edit-pair-0047 | ⚠ FAIL | line_range_step_2 |
| edit-pair-0048 | ⚠ FAIL | line_range_step_2 |
| edit-pair-0049 | ✅ PASS |  |
| edit-pair-0050 | ✅ PASS |  |
| edit-pair-0051 | ✅ PASS |  |
| edit-pair-0052 | ✅ PASS |  |
| edit-pair-0053 | ✅ PASS |  |
| edit-pair-0054 | ✅ PASS |  |
| edit-pair-0055 | ✅ PASS |  |
| edit-pair-0056 | ✅ PASS |  |
| edit-pair-0057 | ✅ PASS |  |
| edit-pair-0058 | ✅ PASS |  |
| edit-pair-0059 | ✅ PASS |  |
| edit-pair-0060 | ✅ PASS |  |
| edit-pair-0061 | ✅ PASS |  |
| edit-pair-0062 | ✅ PASS |  |
| edit-pair-0063 | ✅ PASS |  |
| edit-pair-0064 | ✅ PASS |  |
| edit-pair-0065 | ✅ PASS |  |
| edit-pair-0066 | ✅ PASS |  |
| edit-pair-0067 | ✅ PASS |  |
| edit-pair-0068 | ✅ PASS |  |
| edit-pair-0069 | ✅ PASS |  |
| edit-pair-0070 | ✅ PASS |  |
| edit-pair-0071 | ✅ PASS |  |
| edit-pair-0072 | ✅ PASS |  |
| edit-pair-0073 | ⚠ FAIL | edit_target_not_found_step_3 |
| edit-pair-0074 | ⚠ FAIL | edit_target_not_found_step_2; edit_target_not_found_step_3 |
| edit-pair-0075 | ⚠ FAIL | line_range_step_3 |
| edit-pair-0076 | ✅ PASS |  |
| edit-pair-0077 | ✅ PASS |  |
| edit-pair-0078 | ✅ PASS |  |
| edit-pair-0079 | ✅ PASS |  |
| edit-pair-0080 | ✅ PASS |  |
| edit-pair-0081 | ✅ PASS |  |
| edit-pair-0082 | ✅ PASS |  |
| edit-pair-0083 | ✅ PASS |  |
| edit-pair-0084 | ✅ PASS |  |
| mtime-001 | ✅ PASS |  |
| mtime-002 | ✅ PASS |  |
| mtime-003 | ✅ PASS |  |