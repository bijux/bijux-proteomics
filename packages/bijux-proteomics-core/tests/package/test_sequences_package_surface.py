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


def test_sequences_package_exports_peptide_uniqueness_index_owner_surface() -> None:
    report = sequences.parse_fasta_document(
        (
            ">sp|P11111|TP53_HUMAN Canonical GN=TP53\nAKAK\n"
            ">sp|P11111-2|TP53_HUMAN Isoform GN=TP53\nAKAK\n"
        ),
        mode=sequences.FastaParseMode.STRICT,
    )
    index = sequences.build_peptide_uniqueness_index(
        report.accepted_records,
        protease="trypsin",
        digestion_mode=PeptideDigestionMode.FULL,
    )

    assert hasattr(sequences, "build_peptide_uniqueness_index")
    assert hasattr(sequences, "export_peptide_uniqueness_index_tsv")
    assert index.summary.isoform_shared_count == 1


def test_sequences_package_exports_fasta_duplicate_accession_policy() -> None:
    strict_report = sequences.parse_fasta_document(
        (
            ">sp|P12345|DEMO_HUMAN Canonical\nMPEPTIDEK\n"
            ">sp|P12345|DEMO_HUMAN_DUP Duplicate\nMPEPTIDER\n"
        ),
        mode=sequences.FastaParseMode.PERMISSIVE,
    )
    permissive_report = sequences.parse_fasta_document(
        (
            ">sp|P12345|DEMO_HUMAN Canonical GN=DEMO OS=Homo sapiens\nMPEPTIDEK\n"
            ">sp|P12345|DEMO_HUMAN_DUP Duplicate GN=DEMO OS=Homo sapiens\nMPEPTIDER\n"
        ),
        mode=sequences.FastaParseMode.PERMISSIVE,
        duplicate_accession_policy=(
            sequences.DuplicateAccessionPolicy.ACCEPT_WITH_WARNING
        ),
    )

    assert hasattr(sequences, "DuplicateAccessionPolicy")
    assert strict_report.duplicate_accession_policy is (
        sequences.DuplicateAccessionPolicy.REJECT
    )
    assert len(strict_report.accepted_records) == 1
    assert len(permissive_report.accepted_records) == 2
