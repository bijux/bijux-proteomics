# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.identification import (
    DatabasePeptideUniqueness,
    build_peptide_uniqueness_across_database,
)
from bijux_proteomics.sequences import FastaParseMode, parse_fasta_document


def test_build_peptide_uniqueness_across_database_reports_extended_classes() -> None:
    report = parse_fasta_document(
        (
            ">sp|P11111|TP53_HUMAN Canonical GN=TP53\nAKAK\n"
            ">sp|P11111-2|TP53_HUMAN Isoform GN=TP53\nAKAK\n"
            ">sp|Q20001|FAM1_HUMAN Family one GN=FAMX\nSHADEQK\n"
            ">sp|Q20002|FAM2_HUMAN Family two GN=FAMX\nSHADEQK\n"
            ">sp|Q30001|SHR1_HUMAN Shared one GN=SHR1\nPEPTSHK\n"
            ">sp|Q30002|SHR2_HUMAN Shared two GN=SHR2\nPEPTSHK\n"
        ),
        mode=FastaParseMode.STRICT,
    )

    entries = build_peptide_uniqueness_across_database(
        ("AK", "SHADEQK", "PEPTSHK", "MISSINGK"),
        protein_records=report.accepted_records,
    )
    by_peptide = {entry.canonical_peptide: entry for entry in entries}

    assert by_peptide["AK"].uniqueness is DatabasePeptideUniqueness.ISOFORM_SHARED
    assert by_peptide["AK"].protein_families == ("P11111",)
    assert by_peptide["SHADEQK"].uniqueness is (DatabasePeptideUniqueness.FAMILY_SHARED)
    assert by_peptide["SHADEQK"].gene_symbols == ("FAMX",)
    assert by_peptide["PEPTSHK"].uniqueness is DatabasePeptideUniqueness.SHARED
    assert by_peptide["MISSINGK"].uniqueness is DatabasePeptideUniqueness.MISSING
