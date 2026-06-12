# SPDX-FileCopyrightText: 2026 Michael Conrad
# SPDX-License-Identifier: MIT
# Provenance: AI-generated
"""Tests for edit pairs generator.

Co-authored with AI: OpenCode (deepseek-v4-flash)
"""

from test.stress.generator_edit_pairs import generate_edit_pair_sequences


def test_sparse_count() -> None:
    seqs = generate_edit_pair_sequences(density="sparse")
    # 36 ordered pairs x 2 positions x 1 size = 72
    # + 6 triple chains x 2 positions x 1 size = 12
    # Total: ~84
    assert 70 <= len(seqs) <= 100, f"sparse count {len(seqs)} out of range"


def test_dense_count() -> None:
    seqs = generate_edit_pair_sequences(density="dense")
    # 36 ordered pairs x 3 positions x 2 sizes = 216
    # + 6 triple chains x 3 positions x 2 sizes = 36
    # Total: ~252
    assert 240 <= len(seqs) <= 280, f"dense count {len(seqs)} out of range"


def test_all_sequences_have_ids() -> None:
    seqs = generate_edit_pair_sequences(density="dense")
    ids = [s.id for s in seqs]
    assert len(set(ids)) == len(ids), "duplicate sequence IDs found"


def test_all_operations_covered() -> None:
    seqs = generate_edit_pair_sequences(density="sparse")
    all_ops = set()
    for s in seqs:
        for step in s.steps:
            if step.tool == "edit":
                all_ops.add(step.params.get("action"))
    expected = {
        "replace",
        "replace-all",
        "insert-lines",
        "delete-lines",
        "swap-lines",
        "move-lines",
    }
    assert all_ops == expected, f"missing operations: {expected - all_ops}"


def test_seed_content_present() -> None:
    seqs = generate_edit_pair_sequences(density="sparse")
    for s in seqs:
        assert s.seed_content, f"empty seed content in {s.id}"
        assert "line" in s.seed_content or "ROW" in s.seed_content, (
            f"unexpected seed in {s.id}"
        )
