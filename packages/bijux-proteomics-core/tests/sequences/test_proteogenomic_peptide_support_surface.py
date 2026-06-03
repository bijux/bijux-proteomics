# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.sequences import (
    FastaParseMode,
    ProteogenomicPeptideReference,
    ProteogenomicPeptideSupportClass,
    build_proteogenomic_peptide_support_report,
    parse_fasta_document,
    parse_proteogenomic_variant_peptide_table,
    render_proteogenomic_peptide_support_tsv,
)


def test_parse_proteogenomic_variant_peptide_table_preserves_explicit_variant_support_and_rejections(
    tmp_path: Path,
) -> None:
    table_path = tmp_path / "variant_peptides.tsv"
    table_path.write_text(
        "\n".join(
            (
                "peptide_sequence\tvariant_protein_ref\treference_protein_ref\tvariant_label",
                "ALTPEPTIDEK\tQ9AAA4\tP12345\tp.G12V",
                "\tQ9AAA5\tQ9AAA1\tp.E5K",
                "ALTPEPTIDEK\tQ9AAA4\tP12345\tp.G12V",
            )
        )
        + "\n",
        encoding="utf-8",
    )

    report = parse_proteogenomic_variant_peptide_table(table_path)

    assert report.summary.accepted_record_count == 1
    assert report.summary.rejected_row_count == 2
    assert report.accepted_records[0].variant_protein_ref == "Q9AAA4"
    assert report.accepted_records[0].reference_protein_ref == "P12345"
    assert (
        report.rejected_rows[0].reason
        == "variant peptide row requires peptide_sequence"
    )
    assert "duplicate variant peptide support row" in report.rejected_rows[1].reason


def test_build_proteogenomic_peptide_support_report_classifies_reference_variant_shared_and_ambiguous_evidence(
    tmp_path: Path,
) -> None:
    reference_records = parse_fasta_document(
        (
            ">sp|P12345|REF1_HUMAN Reference 1 GN=REF1\nMREFPEPTIDEKAA\n"
            ">sp|Q9AAA1|REF2_HUMAN Reference 2 GN=REF2\nMSHAREDPEPKAA\n"
        ),
        mode=FastaParseMode.STRICT,
    ).accepted_records
    variant_records = parse_fasta_document(
        (
            ">sp|Q9AAA2|VAR1_HUMAN Variant 1 GN=VAR1\nMVARPEPTIDEKAA\n"
            ">sp|Q9AAA3|VAR2_HUMAN Variant 2 GN=VAR2\nMSHAREDPEPKAA\n"
        ),
        mode=FastaParseMode.STRICT,
    ).accepted_records

    variant_table_path = tmp_path / "variant_support.tsv"
    variant_table_path.write_text(
        (
            "peptide_sequence\tvariant_protein_ref\treference_protein_ref\tvariant_label\n"
            "ALTPEPTIDEK\tQ9AAA4\tP12345\tp.G12V\n"
        ),
        encoding="utf-8",
    )
    report = build_proteogenomic_peptide_support_report(
        (
            ProteogenomicPeptideReference(
                evidence_key="reference-only",
                peptide_sequences=("REFPEPTIDEK",),
                target_protein_refs=("P12345",),
            ),
            ProteogenomicPeptideReference(
                evidence_key="variant-only",
                peptide_sequences=("VARPEPTIDEK", "ALTPEPTIDEK"),
                target_protein_refs=("Q9AAA2",),
            ),
            ProteogenomicPeptideReference(
                evidence_key="shared",
                peptide_sequences=("SHAREDPEPK",),
                target_protein_refs=("Q9AAA1", "Q9AAA3"),
            ),
            ProteogenomicPeptideReference(
                evidence_key="ambiguous",
                peptide_sequences=("MISSINGPEPK", "REFPEPTIDEK"),
                target_protein_refs=("P12345",),
            ),
        ),
        reference_protein_records=reference_records,
        variant_protein_records=variant_records,
        variant_peptide_records=parse_proteogenomic_variant_peptide_table(
            variant_table_path
        ).accepted_records,
    )

    entries = {entry.evidence_key: entry for entry in report.entries}
    assert entries["reference-only"].support_class is (
        ProteogenomicPeptideSupportClass.REFERENCE_ONLY
    )
    assert entries["variant-only"].support_class is (
        ProteogenomicPeptideSupportClass.VARIANT_ONLY
    )
    assert entries["shared"].support_class is ProteogenomicPeptideSupportClass.SHARED
    assert entries["ambiguous"].support_class is (
        ProteogenomicPeptideSupportClass.AMBIGUOUS
    )
    assert entries["variant-only"].variant_only_peptides == (
        "VARPEPTIDEK",
        "ALTPEPTIDEK",
    )
    assert entries["variant-only"].matched_variant_protein_refs == (
        "Q9AAA2",
        "Q9AAA4",
    )
    assert entries["shared"].shared_peptides == ("SHAREDPEPK",)
    assert entries["ambiguous"].support_reason.startswith(
        "at least one observed peptide could not be resolved"
    )
    assert report.summary.variant_only_count == 1
    assert "support_class" in render_proteogenomic_peptide_support_tsv(report)
