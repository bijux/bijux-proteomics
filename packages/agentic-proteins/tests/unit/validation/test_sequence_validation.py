# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from agentic_proteins.domain.sequence.validation import validate_sequence


def test_validate_sequence_rejects_invalid() -> None:
    assert validate_sequence("ZZZ") == ["invalid_sequence"]


def test_validate_sequence_rejects_empty() -> None:
    assert validate_sequence("") == ["empty_sequence"]
