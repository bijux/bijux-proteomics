# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.sequences import (
    FastaParseMode,
    ProteinIdentityLevel,
    parse_fasta_document,
)
from bijux_proteomics.sequences.protein_identity_resolution import (
    ProteinIdentityReference,
    build_protein_identity_resolution_report,
    render_protein_identity_resolution_tsv,
)


def test_protein_identity_resolution_distinguishes_isoform_protein_gene_family_and_ambiguous_support() -> (
    None
):
    fasta = parse_fasta_document(
        (
            ">sp|P11111|GENE1_HUMAN Canonical GN=GENE1\n"
            "MAAAAKPEPTIDEKCCMMNK\n"
            ">sp|P11111-2|GENE1_HUMAN Isoform GN=GENE1\n"
            "MDDDDKPEPTIDEKCCMMNK\n"
            ">sp|Q22222|GENE1B_HUMAN Related GN=GENE1\n"
            "MNNNNKPEPTIDEK\n"
            ">custom_family_alpha Family member\n"
            "MFAMILYK\n"
            ">custom_family_beta Family member\n"
            "MFAMILYK\n"
            ">sp|O99999|GENE2_HUMAN Other GN=GENE2\n"
            "MCCMMNK\n"
        ),
        mode=FastaParseMode.STRICT,
    )

    report = build_protein_identity_resolution_report(
        (
            ProteinIdentityReference(
                evidence_key="isoform",
                target_protein_ref="P11111-2",
                candidate_protein_refs=("P11111-2", "P11111"),
                peptide_sequences=("PEPTIDEK", "DDDDK"),
            ),
            ProteinIdentityReference(
                evidence_key="protein",
                target_protein_ref="P11111",
                candidate_protein_refs=("P11111", "P11111-2"),
                peptide_sequences=("PEPTIDEK", "AAAAK"),
            ),
            ProteinIdentityReference(
                evidence_key="gene",
                target_protein_ref="P11111",
                candidate_protein_refs=("P11111", "P11111-2", "Q22222"),
                peptide_sequences=("PEPTIDEK",),
            ),
            ProteinIdentityReference(
                evidence_key="family",
                target_protein_ref="CUSTOM_FAMILY_ALPHA",
                candidate_protein_refs=("CUSTOM_FAMILY_ALPHA", "CUSTOM_FAMILY_BETA"),
                peptide_sequences=("FAMILYK",),
            ),
            ProteinIdentityReference(
                evidence_key="ambiguous",
                target_protein_ref="P11111",
                candidate_protein_refs=("P11111", "O99999"),
                peptide_sequences=("CCMMNK",),
            ),
        ),
        protein_records=fasta.accepted_records,
    )

    by_key = {entry.evidence_key: entry for entry in report.entries}

    assert by_key["isoform"].identity_level is ProteinIdentityLevel.ISOFORM_LEVEL
    assert by_key["protein"].identity_level is ProteinIdentityLevel.PROTEIN_LEVEL
    assert by_key["gene"].identity_level is ProteinIdentityLevel.GENE_LEVEL
    assert by_key["family"].identity_level is ProteinIdentityLevel.FAMILY_LEVEL
    assert by_key["ambiguous"].identity_level is ProteinIdentityLevel.AMBIGUOUS
    assert by_key["gene"].peptide_evidence[0].support_class.value == "gene_shared"
    assert by_key["family"].peptide_evidence[0].support_class.value == "family_shared"


def test_protein_identity_resolution_refuses_exact_isoform_when_peptides_are_only_isoform_shared() -> (
    None
):
    fasta = parse_fasta_document(
        (
            ">sp|P11111|GENE1_HUMAN Canonical GN=GENE1\n"
            "MPEPTIDEK\n"
            ">sp|P11111-2|GENE1_HUMAN Isoform GN=GENE1\n"
            "MPEPTIDEK\n"
        ),
        mode=FastaParseMode.STRICT,
    )

    report = build_protein_identity_resolution_report(
        (
            ProteinIdentityReference(
                evidence_key="shared-isoform",
                target_protein_ref="P11111-2",
                candidate_protein_refs=("P11111-2", "P11111"),
                peptide_sequences=("PEPTIDEK",),
            ),
        ),
        protein_records=fasta.accepted_records,
    )

    entry = report.entries[0]

    assert entry.identity_level is ProteinIdentityLevel.PROTEIN_LEVEL
    assert "do not isolate one exact isoform" in entry.identity_reason


def test_protein_identity_resolution_tsv_preserves_identity_level_and_peptide_support() -> (
    None
):
    fasta = parse_fasta_document(
        ">sp|P11111-2|GENE1_HUMAN Isoform GN=GENE1\nMDDDDK\n",
        mode=FastaParseMode.STRICT,
    )
    report = build_protein_identity_resolution_report(
        (
            ProteinIdentityReference(
                evidence_key="isoform",
                target_protein_ref="P11111-2",
                candidate_protein_refs=("P11111-2",),
                peptide_sequences=("DDDDK",),
            ),
        ),
        protein_records=fasta.accepted_records,
    )

    rendered = render_protein_identity_resolution_tsv(report)

    assert "identity_level" in rendered
    assert "isoform_level" in rendered
    assert "DDDDK:isoform_specific" in rendered
