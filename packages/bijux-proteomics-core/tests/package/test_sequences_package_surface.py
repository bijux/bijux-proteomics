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


def test_sequences_package_exports_builtin_contaminant_builder_surface() -> None:
    records = sequences.build_builtin_contaminant_records()

    assert hasattr(sequences, "build_builtin_contaminant_records")
    assert hasattr(sequences, "load_builtin_contaminant_records")
    assert len(records) == 4
    assert all(record.contaminant for record in records)


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
    assert hasattr(sequences, "write_theoretical_digest_bundle")
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


def test_sequences_package_exports_reusable_protein_index_surface(
    tmp_path: Path,
) -> None:
    index_path = tmp_path / "protein_index.json"
    index = sequences.build_protein_index(
        (
            ">sp|P11111|ALPHA_HUMAN Alpha GN=ALPHA\nMPEPTIDEK\n"
            ">sp|P22222|BETA_HUMAN Beta GN=BETA\nAAAKPEPTIDER\n"
        ),
        enzyme="trypsin",
        missed_cleavages=0,
        out_path=index_path,
    )
    reloaded = sequences.load_protein_index(index_path)

    assert hasattr(sequences, "build_protein_index")
    assert hasattr(sequences, "load_protein_index")
    assert hasattr(sequences, "lookup_peptide_proteins")
    assert hasattr(sequences, "lookup_protein_peptides")
    assert sequences.lookup_peptide_proteins(reloaded, "MPEPTIDEK") == ("P11111",)
    assert sequences.lookup_protein_peptides(index, "P22222") == ("AAAKPEPTIDER",)


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


def test_sequences_package_exports_protein_identity_resolution_owner_surface() -> None:
    fasta = sequences.parse_fasta_document(
        (
            ">sp|P11111|GENE1_HUMAN Canonical GN=GENE1\nMPEPTIDEK\n"
            ">sp|P11111-2|GENE1_HUMAN Isoform GN=GENE1\nMPEPTIDEK\n"
        ),
        mode=sequences.FastaParseMode.STRICT,
    )
    report = sequences.build_protein_identity_resolution_report(
        (
            sequences.ProteinIdentityReference(
                evidence_key="shared-isoform",
                target_protein_ref="P11111-2",
                candidate_protein_refs=("P11111-2", "P11111"),
                peptide_sequences=("PEPTIDEK",),
            ),
        ),
        protein_records=fasta.accepted_records,
    )
    rendered = sequences.render_protein_identity_resolution_tsv(report)

    assert hasattr(sequences, "build_protein_identity_resolution_report")
    assert hasattr(sequences, "render_protein_identity_resolution_tsv")
    assert (
        report.entries[0].identity_level is sequences.ProteinIdentityLevel.PROTEIN_LEVEL
    )
    assert "shared-isoform" in rendered


def test_sequences_package_exports_proteogenomic_peptide_support_owner_surface(
    tmp_path: Path,
) -> None:
    reference_records = sequences.parse_fasta_document(
        ">sp|P12345|REF1_HUMAN Reference 1\nMREFPEPTIDEKAA\n",
        mode=sequences.FastaParseMode.STRICT,
    ).accepted_records
    variant_records = sequences.parse_fasta_document(
        ">sp|Q9AAA1|VAR1_HUMAN Variant 1\nMALTPEPTIDEKAA\n",
        mode=sequences.FastaParseMode.STRICT,
    ).accepted_records
    variant_table_path = tmp_path / "variant_support.tsv"
    variant_table_path.write_text(
        (
            "peptide_sequence\tvariant_protein_ref\treference_protein_ref\tvariant_label\n"
            "ALTPEPTIDEK\tQ9AAA1\tP12345\tp.G12V\n"
        ),
        encoding="utf-8",
    )
    report = sequences.build_proteogenomic_peptide_support_report(
        (
            sequences.ProteogenomicPeptideReference(
                evidence_key="variant-peptide",
                peptide_sequences=("ALTPEPTIDEK",),
                target_protein_refs=("Q9AAA1",),
            ),
        ),
        reference_protein_records=reference_records,
        variant_protein_records=variant_records,
        variant_peptide_records=sequences.parse_proteogenomic_variant_peptide_table(
            variant_table_path
        ).accepted_records,
    )
    rendered = sequences.render_proteogenomic_peptide_support_tsv(report)

    assert hasattr(sequences, "build_proteogenomic_peptide_support_report")
    assert hasattr(sequences, "parse_proteogenomic_variant_peptide_table")
    assert (
        report.entries[0].support_class
        is sequences.ProteogenomicPeptideSupportClass.VARIANT_ONLY
    )
    assert "variant-peptide" in rendered
