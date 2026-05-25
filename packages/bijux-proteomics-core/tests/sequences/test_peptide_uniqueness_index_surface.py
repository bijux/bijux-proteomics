# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import pytest

from bijux_proteomics.sequences import (
    FastaParseMode,
    PeptideDigestionMode,
    PeptideUniquenessClass,
    build_builtin_contaminant_records,
    build_peptide_uniqueness_index,
    generate_decoy_records,
    load_builtin_contaminant_records,
    parse_fasta_document,
)


def test_build_peptide_uniqueness_index_distinguishes_target_uniqueness_classes() -> (
    None
):
    report = parse_fasta_document(
        (
            ">sp|P10001|UNIQ_HUMAN Unique GN=UNIQ\nMPEPAAAK\n"
            ">sp|P11111|TP53_HUMAN Canonical GN=TP53\nAKAK\n"
            ">sp|P11111-2|TP53_HUMAN Isoform GN=TP53\nAKAK\n"
            ">sp|Q20001|FAM1_HUMAN Family one GN=FAMX\nSHADEQK\n"
            ">sp|Q20002|FAM2_HUMAN Family two GN=FAMX\nSHADEQK\n"
            ">sp|Q30001|SHR1_HUMAN Shared one GN=SHR1\nPEPTSHK\n"
            ">sp|Q30002|SHR2_HUMAN Shared two GN=SHR2\nPEPTSHK\n"
        ),
        mode=FastaParseMode.STRICT,
    )

    index = build_peptide_uniqueness_index(
        report.accepted_records,
        protease="trypsin",
        missed_cleavages=0,
        digestion_mode=PeptideDigestionMode.FULL,
    )
    by_peptide = {entry.peptide_sequence: entry for entry in index.entries}

    assert by_peptide["MPEPAAAK"].uniqueness_class is PeptideUniquenessClass.UNIQUE
    assert by_peptide["AK"].uniqueness_class is PeptideUniquenessClass.ISOFORM_SHARED
    assert by_peptide["AK"].protein_families == ("P11111",)
    assert by_peptide["SHADEQK"].uniqueness_class is (
        PeptideUniquenessClass.FAMILY_SHARED
    )
    assert by_peptide["SHADEQK"].gene_symbols == ("FAMX",)
    assert by_peptide["PEPTSHK"].uniqueness_class is PeptideUniquenessClass.SHARED


def test_build_peptide_uniqueness_index_distinguishes_contaminant_decoy_and_mixed() -> (
    None
):
    report = parse_fasta_document(
        (
            ">sp|P50001|MIXED_HUMAN Mixed target GN=MIX\nMILDEK\n"
            ">DECOY_sp|P50002|MIXED_HUMAN Decoy GN=MIX\nMILDEK\n"
            ">sp|P60001|TARGET_HUMAN Target GN=TARGET\nTARGETK\n"
        ),
        mode=FastaParseMode.STRICT,
    )
    decoy_records = generate_decoy_records(
        report.accepted_records[-1:],
    )
    contaminant_record = build_builtin_contaminant_records()[0]
    with pytest.warns(
        DeprecationWarning, match="build_builtin_contaminant_records"
    ):
        legacy_contaminant_record = load_builtin_contaminant_records()[0]

    assert legacy_contaminant_record == contaminant_record
    index = build_peptide_uniqueness_index(
        (
            *report.accepted_records,
            *decoy_records,
            contaminant_record,
        ),
        protease="trypsin",
        missed_cleavages=0,
        digestion_mode=PeptideDigestionMode.FULL,
    )

    mixed_entry = next(
        entry for entry in index.entries if entry.peptide_sequence == "MILDEK"
    )
    assert mixed_entry.uniqueness_class is PeptideUniquenessClass.MIXED

    target_sequences = {
        entry.peptide_sequence
        for entry in index.entries
        if entry.uniqueness_class is not PeptideUniquenessClass.DECOY
    }
    decoy_entry = next(
        entry
        for entry in index.entries
        if entry.uniqueness_class is PeptideUniquenessClass.DECOY
        and entry.peptide_sequence not in target_sequences
    )
    assert decoy_entry.protein_accessions == ("DECOY_P60001",)

    contaminant_entry = next(
        entry
        for entry in index.entries
        if entry.uniqueness_class is PeptideUniquenessClass.CONTAMINANT
    )
    assert contaminant_entry.protein_accessions == (
        contaminant_record.canonical_accession,
    )


def test_build_peptide_uniqueness_index_can_collapse_il_equivalent_peptides() -> None:
    report = parse_fasta_document(
        (
            ">sp|P70001|LEFT_HUMAN Left GN=LEFT\nMPEPTIDEK\n"
            ">sp|P70002|RIGHT_HUMAN Right GN=RIGHT\nMPEPTLDEK\n"
        ),
        mode=FastaParseMode.STRICT,
    )

    exact_index = build_peptide_uniqueness_index(
        report.accepted_records,
        protease="trypsin",
        digestion_mode=PeptideDigestionMode.FULL,
    )
    il_index = build_peptide_uniqueness_index(
        report.accepted_records,
        protease="trypsin",
        digestion_mode=PeptideDigestionMode.FULL,
        treat_isoleucine_as_leucine=True,
    )

    assert {entry.lookup_sequence for entry in exact_index.entries} == {
        "MPEPTIDEK",
        "MPEPTLDEK",
    }
    assert {entry.lookup_sequence for entry in il_index.entries} == {"MPEPTLDEK"}
    merged_entry = il_index.entries[0]
    assert merged_entry.source_sequences == ("MPEPTIDEK", "MPEPTLDEK")
    assert merged_entry.uniqueness_class is PeptideUniquenessClass.SHARED
