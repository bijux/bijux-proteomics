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


def test_sequences_package_exports_theoretical_digest_owner_surface() -> None:
    report = sequences.parse_fasta_document(
        ">sp|P12345|DEMO Demo\nACDMK\n",
        mode=sequences.FastaParseMode.STRICT,
    )
    bundle = sequences.build_theoretical_digest_bundle(
        report.accepted_records,
        protease="trypsin",
        missed_cleavages=0,
        digestion_mode=PeptideDigestionMode.FULL,
    )

    assert hasattr(sequences, "build_theoretical_digest_bundle")
    assert hasattr(sequences, "export_theoretical_digest_bundle")
    assert bundle.summary.output_candidate_peptide_count == 1
