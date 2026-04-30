# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.digestion import (
    PeptideProteinIndexEntry,
    PeptideUniqueness,
)
from bijux_proteomics.peptide_uniqueness_audit import (
    PeptideUniquenessAuditClass,
    build_peptide_uniqueness_audit_report,
)


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
