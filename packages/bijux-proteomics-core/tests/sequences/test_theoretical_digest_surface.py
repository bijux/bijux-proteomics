# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.chemistry import (
    ModificationPosition,
    VariableModification,
    get_modification,
)
from bijux_proteomics.sequences import FastaParseMode, parse_fasta_document
from bijux_proteomics.sequences.digestion import PeptideDigestionMode
from bijux_proteomics.sequences.theoretical_digest import (
    build_theoretical_digest_bundle,
)


def _fasta_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "fasta" / name


def test_theoretical_digest_bundle_maps_coordinates_back_to_source_sequences() -> None:
    report = parse_fasta_document(
        _fasta_fixture("valid_records.fasta").read_text(),
        mode=FastaParseMode.STRICT,
    )

    bundle = build_theoretical_digest_bundle(
        report.accepted_records,
        protease="trypsin",
        missed_cleavages=1,
        digestion_mode=PeptideDigestionMode.FULL,
        min_length=3,
        max_length=25,
    )
    residues_by_identifier = {
        record.source_identifier: record.residues for record in report.accepted_records
    }

    assert bundle.summary.coordinate_map_valid is True
    assert bundle.summary.input_record_count == report.total_records
    assert bundle.summary.output_candidate_peptide_count == len(bundle.digest_peptides)
    assert bundle.summary.output_mapping_count == len(bundle.peptide_to_protein)
    for mapping in bundle.peptide_to_protein:
        residues = residues_by_identifier[mapping.source_identifier]
        assert residues[mapping.start - 1 : mapping.end] == mapping.matched_sequence
        assert mapping.matched_sequence == mapping.stripped_sequence


def test_theoretical_digest_bundle_respects_protein_terminal_modification_context() -> (
    None
):
    report = parse_fasta_document(
        (
            ">sp|P12345|TERM Protein terminal\nPEPTIDEKAAK\n"
            ">sp|Q8N158|INTERNAL Internal context\nAAKPEPTIDEKAAK\n"
        ),
        mode=FastaParseMode.STRICT,
    )
    protein_n_term_modification = VariableModification(
        name="ProtBlock",
        position=ModificationPosition.PROTEIN_N_TERM,
        mass_delta_monoisotopic=10.0,
        mass_delta_average=10.0,
        controlled_id="CUSTOM:PROT_BLOCK",
    )

    bundle = build_theoretical_digest_bundle(
        report.accepted_records,
        protease="trypsin",
        missed_cleavages=0,
        digestion_mode=PeptideDigestionMode.FULL,
        variable_modifications=(protein_n_term_modification,),
    )
    modified_entry = next(
        peptide
        for peptide in bundle.digest_peptides
        if peptide.stripped_sequence == "PEPTIDEK"
        and peptide.canonical_notation != peptide.stripped_sequence
    )
    modified_mappings = [
        mapping
        for mapping in bundle.peptide_to_protein
        if mapping.canonical_notation == modified_entry.canonical_notation
    ]

    assert modified_entry.protein_accession_count == 1
    assert modified_entry.terminal_contexts == ("protein_n_term",)
    assert [mapping.source_accession for mapping in modified_mappings] == ["P12345"]
    assert all(mapping.at_protein_n_term for mapping in modified_mappings)


def test_theoretical_digest_bundle_preserves_modification_policy_and_candidate_masses() -> (
    None
):
    report = parse_fasta_document(
        ">sp|P12346|CHEM Protein chemistry\nACDMK\n",
        mode=FastaParseMode.STRICT,
    )

    bundle = build_theoretical_digest_bundle(
        report.accepted_records,
        protease="trypsin",
        missed_cleavages=0,
        digestion_mode=PeptideDigestionMode.FULL,
        static_modifications=(get_modification("Carbamidomethyl"),),
        variable_modifications=(get_modification("Oxidation"),),
    )
    by_notation = {
        peptide.canonical_notation: peptide for peptide in bundle.digest_peptides
    }

    assert bundle.modification_policy.static_modification_names == ("Carbamidomethyl",)
    assert bundle.modification_policy.variable_modification_names == ("Oxidation",)
    assert bundle.summary.output_candidate_peptide_count == 2
    assert (
        by_notation["ACDMK"].neutral_mass < by_notation["ACDM[Oxidation]K"].neutral_mass
    )
