# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

import pytest

from bijux_proteomics.sequences import (
    DecoyGenerationMode,
    FastaParseMode,
    build_builtin_contaminant_records,
    generate_decoy_records,
    load_builtin_contaminant_records,
    parse_fasta_document,
)
from bijux_proteomics.sequences.digestion import (
    PeptideProteinIndexEntry,
    PeptideUniqueness,
    digest_protein_records,
)
from bijux_proteomics.sequences.peptide_uniqueness_audit import (
    PeptideDatabaseMembership,
    PeptideUniquenessAuditClass,
    build_peptide_database_lookup_report,
    build_peptide_uniqueness_audit_report,
)
from bijux_proteomics.sequences.peptide_uniqueness_index import PeptideUniquenessClass


def test_build_peptide_uniqueness_audit_report_separates_isoform_and_group_specific() -> (
    None
):
    report = build_peptide_uniqueness_audit_report(
        (
            PeptideProteinIndexEntry(
                sequence="PEPTIDEA",
                protein_accessions=("P001",),
                protein_families=("FAM_A",),
                source_identifiers=("sp|P001|",),
                uniqueness=PeptideUniqueness.UNIQUE,
            ),
            PeptideProteinIndexEntry(
                sequence="PEPTIDEB",
                protein_accessions=("P010-1", "P010-2"),
                protein_families=("FAM_B",),
                source_identifiers=("sp|P010-1|", "sp|P010-2|"),
                uniqueness=PeptideUniqueness.SHARED_ISOFORM_FAMILY,
            ),
            PeptideProteinIndexEntry(
                sequence="PEPTIDEC",
                protein_accessions=("P020", "P021"),
                protein_families=("FAM_C", "FAM_D"),
                source_identifiers=("sp|P020|", "sp|P021|"),
                uniqueness=PeptideUniqueness.SHARED,
            ),
        ),
        protein_group_by_accession={"P020": "GROUP_X", "P021": "GROUP_X"},
    )

    assert report.unique_count == 1
    assert report.isoform_specific_count == 1
    assert report.protein_group_specific_count == 1
    assert report.shared_count == 0
    classes = {entry.sequence: entry.audit_class for entry in report.entries}
    assert classes["PEPTIDEA"] is PeptideUniquenessAuditClass.UNIQUE
    assert classes["PEPTIDEB"] is PeptideUniquenessAuditClass.ISOFORM_SPECIFIC
    assert classes["PEPTIDEC"] is PeptideUniquenessAuditClass.PROTEIN_GROUP_SPECIFIC


def test_build_peptide_database_lookup_report_handles_modifications_il_and_missed_cleavages() -> (
    None
):
    report = parse_fasta_document(
        ">sp|P10001|ALPHA_HUMAN Alpha OS=Homo sapiens GN=ALPHA\nMPEPTLDEKAK\n",
        mode=FastaParseMode.STRICT,
    )

    no_il = build_peptide_database_lookup_report(
        ("M[+15.9949]PEPTIDEK",),
        report.accepted_records,
    )
    no_il_entry = no_il.entries[0]
    assert no_il_entry.canonical_peptide == "MPEPTIDEK"
    assert no_il_entry.modification_stripped is True
    assert no_il_entry.database_membership is PeptideDatabaseMembership.MISSING

    with_il = build_peptide_database_lookup_report(
        ("M[+15.9949]PEPTIDEK",),
        report.accepted_records,
        treat_isoleucine_as_leucine=True,
    )
    with_il_entry = with_il.entries[0]
    assert with_il_entry.lookup_sequence == "MPEPTLDEK"
    assert with_il_entry.il_equivalence_applied is True
    assert with_il_entry.database_membership is PeptideDatabaseMembership.TARGET
    assert with_il_entry.uniqueness_class is PeptideUniquenessClass.UNIQUE
    assert with_il_entry.audit_class is PeptideUniquenessAuditClass.UNIQUE
    assert with_il_entry.missed_cleavage_counts == (0,)

    no_missed_cleavage = build_peptide_database_lookup_report(
        ("MPEPTLDEKAK",),
        report.accepted_records,
    )
    assert (
        no_missed_cleavage.entries[0].database_membership
        is PeptideDatabaseMembership.MISSING
    )

    one_missed_cleavage = build_peptide_database_lookup_report(
        ("MPEPTLDEKAK",),
        report.accepted_records,
        missed_cleavages=1,
    )
    assert one_missed_cleavage.entries[0].database_membership is (
        PeptideDatabaseMembership.TARGET
    )
    assert one_missed_cleavage.entries[0].missed_cleavage_counts == (1,)


def test_build_peptide_database_lookup_report_tracks_groups_and_membership_classes() -> (
    None
):
    report = parse_fasta_document(
        (
            ">sp|P20001|ALPHA_HUMAN Alpha OS=Homo sapiens GN=ALPHA\nAKSHADEQKQQ\n"
            ">sp|P20002|BETA_HUMAN Beta OS=Homo sapiens GN=BETA\nMKSHADEQKLL\n"
            ">sp|P30001|GAMMA_HUMAN Gamma OS=Homo sapiens GN=GAMMA\nQQQQKAAAK\n"
        ),
        mode=FastaParseMode.STRICT,
    )
    decoy_records = generate_decoy_records(
        report.accepted_records[:1],
        mode=DecoyGenerationMode.REVERSE,
    )
    contaminant_record = build_builtin_contaminant_records()[0]
    with pytest.warns(DeprecationWarning, match="build_builtin_contaminant_records"):
        legacy_contaminant_record = load_builtin_contaminant_records()[0]
    combined_records = (
        *report.accepted_records,
        *decoy_records,
        contaminant_record,
    )

    assert legacy_contaminant_record == contaminant_record
    target_sequences = {
        peptide.sequence for peptide in digest_protein_records(report.accepted_records)
    }
    decoy_query = next(
        peptide.sequence
        for peptide in digest_protein_records(decoy_records)
        if peptide.sequence not in target_sequences
    )
    non_contaminant_sequences = target_sequences.union(
        {peptide.sequence for peptide in digest_protein_records(decoy_records)}
    )
    contaminant_query = next(
        peptide.sequence
        for peptide in digest_protein_records((contaminant_record,))
        if peptide.sequence not in non_contaminant_sequences
    )

    lookup = build_peptide_database_lookup_report(
        ("SHADEQK", decoy_query, contaminant_query),
        combined_records,
        protein_group_by_accession={
            "P20001": "GROUP_SHARED",
            "P20002": "GROUP_SHARED",
        },
    )

    by_peptide = {entry.input_peptide: entry for entry in lookup.entries}
    shared_entry = by_peptide["SHADEQK"]
    assert (
        shared_entry.audit_class is PeptideUniquenessAuditClass.PROTEIN_GROUP_SPECIFIC
    )
    assert shared_entry.uniqueness_class is PeptideUniquenessClass.SHARED
    assert shared_entry.protein_groups == ("GROUP_SHARED",)
    assert shared_entry.protein_group_count == 1
    assert shared_entry.database_membership is PeptideDatabaseMembership.TARGET
    assert shared_entry.protein_accessions == ("P20001", "P20002")

    assert (
        by_peptide[decoy_query].database_membership is PeptideDatabaseMembership.DECOY
    )
    assert by_peptide[decoy_query].uniqueness_class is PeptideUniquenessClass.DECOY
    assert by_peptide[contaminant_query].database_membership is (
        PeptideDatabaseMembership.CONTAMINANT
    )
    assert by_peptide[contaminant_query].uniqueness_class is (
        PeptideUniquenessClass.CONTAMINANT
    )
    assert lookup.target_count == 1
    assert lookup.decoy_count == 1
    assert lookup.contaminant_count == 1
