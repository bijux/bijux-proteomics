# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics import sequences
from bijux_proteomics.sequences.digestion import PeptideDigestionMode


def test_sequences_package_exports_digestion_owner_surface() -> None:
    peptides = sequences.digest_sequence(
        "AKRPQKAAAR",
        mode=PeptideDigestionMode.FULL,
    )

    assert hasattr(sequences, "digest_sequence")
    assert hasattr(sequences, "get_protease_rule")
    assert hasattr(sequences, "parse_custom_protease_rule")
    assert [peptide.sequence for peptide in peptides] == ["AK", "RPQK", "AAAR"]
