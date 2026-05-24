# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

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


def test_sequences_package_exports_fasta_invalid_sequence_profile_surface() -> None:
    report = sequences.parse_fasta_document(
        (
            ">sp|P12345|DEMO_HUMAN Canonical GN=DEMO\nMPEPTIDEK\n"
            ">custom_empty Empty example\n\n"
            ">custom_invalid Invalid example\nACDU?\n"
        ),
        mode=sequences.FastaParseMode.STRICT,
    )
    profile = sequences.build_fasta_database_profile(
        report.accepted_records,
        rejected_records=report.rejected_records,
    )

    assert hasattr(sequences, "render_fasta_profile_invalid_sequence_tsv")
    assert [row.source_identifier for row in profile.invalid_sequence_report] == [
        "custom_empty",
        "custom_invalid",
    ]


def test_sequences_package_exports_peptide_detectability_owner_surface() -> None:
    report = sequences.build_peptide_detectability_report(
        "AKTIDEK",
        charge=2,
        protease="trypsin",
        uniqueness_class=sequences.PeptideUniquenessClass.UNIQUE,
        observed_psm_count=5,
    )
    rendered = sequences.render_peptide_detectability_tsv(report)

    assert hasattr(sequences, "build_peptide_detectability_report")
    assert hasattr(sequences, "render_peptide_detectability_tsv")
    assert report.detectability_tier is sequences.PeptideDetectabilityTier.HIGH
    assert "detectability_score" in rendered


def test_sequences_package_exports_peptide_chemical_liability_owner_surface() -> None:
    report = sequences.build_peptide_chemical_liability_report(
        "MNNQVVVVVVILKKDG",
        charge=4,
        protease="trypsin",
    )
    rendered = sequences.render_peptide_chemical_liability_tsv(report)

    assert hasattr(sequences, "build_peptide_chemical_liability_report")
    assert hasattr(sequences, "render_peptide_chemical_liability_tsv")
    assert report.liability_tier is sequences.PeptideChemicalLiabilityTier.AVOID
    assert "instability_motif" in rendered


def test_sequences_package_exports_protein_region_context_owner_surface() -> None:
    report = sequences.parse_protein_region_context_tsv(
        Path(__file__).resolve().parent.parent
        / "fixtures"
        / "sequences"
        / "protein_region_context.tsv"
    )
    rendered = sequences.render_protein_region_context_summary_tsv(report)

    assert hasattr(sequences, "build_protein_site_region_context_report")
    assert hasattr(sequences, "build_protein_peptide_region_context_report")
    assert report.summary.signal_peptide_record_count == 1
    assert "binding_region_record_count" in rendered
