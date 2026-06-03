# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.identification.contracts import (
    TargetDecoyContaminantClass,
    TargetDecoyLabel,
)
from bijux_proteomics.identification.cross_run_reproducibility import (
    CrossRunReproducibilityClass,
)
from bijux_proteomics.identification.peptide_evidence import (
    PeptideEvidenceClass,
    PeptideEvidenceEntry,
)
from bijux_proteomics.sequences import parse_fasta_document
from bijux_proteomics.targeted import (
    DiscoveryTargetProteinEntry,
    TargetedPeptideCandidateSource,
    TargetedPeptideSelectionRejectionCode,
    build_discovery_targeted_peptide_selection_report,
)


def _protein_records():
    return parse_fasta_document(
        ">sp|P00001|KIN1 GN=KIN1\n"
        "PEPTIDERAAASHALEDKAAAMMMWNQK\n"
        ">sp|P00002|KIN2 GN=KIN2\n"
        "KTARGETVKAAALIGHTR\n"
        ">sp|O00003|OFF1 GN=OFF1\n"
        "KAAASHALEDK\n"
    ).accepted_records


def _observed_entries() -> tuple[PeptideEvidenceEntry, ...]:
    return (
        PeptideEvidenceEntry(
            peptide="PEPTIDER",
            canonical_peptide="PEPTIDER",
            primary_class=PeptideEvidenceClass.STRONG,
            peptide_q_value=0.001,
            accepted=True,
            psm_count=6,
            spectrum_count=6,
            run_count=4,
            detection_frequency=1.0,
            replicate_consistency=0.95,
            condition_specificity=0.1,
            detected_condition_count=2,
            reproducibility_class=CrossRunReproducibilityClass.REPRODUCIBLE,
            best_score=125.0,
            charge_states=(2,),
            run_ids=("run1", "run2", "run3", "run4"),
            protein_refs=("P00001",),
            target_decoy_label=TargetDecoyLabel.TARGET,
            target_decoy_contaminant_class=TargetDecoyContaminantClass.TARGET,
            explanation="strong observed peptide support",
        ),
        PeptideEvidenceEntry(
            peptide="AAASHALEDK",
            canonical_peptide="AAASHALEDK",
            primary_class=PeptideEvidenceClass.STRONG,
            peptide_q_value=0.002,
            accepted=True,
            psm_count=5,
            spectrum_count=5,
            run_count=3,
            detection_frequency=0.75,
            replicate_consistency=0.8,
            condition_specificity=0.2,
            detected_condition_count=2,
            reproducibility_class=CrossRunReproducibilityClass.REPRODUCIBLE,
            best_score=118.0,
            charge_states=(2,),
            run_ids=("run1", "run2", "run3"),
            protein_refs=("P00001", "O00003"),
            target_decoy_label=TargetDecoyLabel.TARGET,
            target_decoy_contaminant_class=TargetDecoyContaminantClass.TARGET,
            explanation="shared peptide support",
        ),
        PeptideEvidenceEntry(
            peptide="AAAMMMWNQK",
            canonical_peptide="AAAMMMWNQK",
            primary_class=PeptideEvidenceClass.STRONG,
            peptide_q_value=0.003,
            accepted=True,
            psm_count=12,
            spectrum_count=12,
            run_count=4,
            detection_frequency=1.0,
            replicate_consistency=0.95,
            condition_specificity=0.1,
            detected_condition_count=2,
            reproducibility_class=CrossRunReproducibilityClass.REPRODUCIBLE,
            best_score=130.0,
            charge_states=(2,),
            run_ids=("run1", "run2", "run3", "run4"),
            protein_refs=("P00001",),
            target_decoy_label=TargetDecoyLabel.TARGET,
            target_decoy_contaminant_class=TargetDecoyContaminantClass.TARGET,
            explanation="high-confidence but chemically risky peptide",
        ),
    )


def test_discovery_targeted_peptide_selection_prefers_observed_unique_and_falls_back_to_theoretical() -> (
    None
):
    report = build_discovery_targeted_peptide_selection_report(
        (
            DiscoveryTargetProteinEntry(
                protein_group_id="protein_group_1",
                representative_protein_ref="P00001",
                protein_refs=("P00001",),
                gene_symbol="KIN1",
                discovery_peptides=("PEPTIDER", "AAASHALEDK", "AAAMMMWNQK"),
            ),
            DiscoveryTargetProteinEntry(
                protein_group_id="protein_group_2",
                representative_protein_ref="P00002",
                protein_refs=("P00002",),
                gene_symbol="KIN2",
            ),
        ),
        _observed_entries(),
        _protein_records(),
        top_peptides_per_target=1,
    )

    assert report.summary.target_protein_count == 2
    assert report.summary.target_with_selected_peptides == 2
    assert report.summary.selected_entry_count == 2
    assert report.summary.observed_selected_entry_count == 1
    assert report.summary.theoretical_selected_entry_count == 1

    observed = report.selected_entries[0]
    assert observed.target_protein_ref == "P00001"
    assert observed.rank == 1
    assert (
        observed.candidate_source is TargetedPeptideCandidateSource.OBSERVED_DISCOVERY
    )
    assert observed.peptide_sequence == "PEPTIDER"
    assert observed.observed_in_discovery is True
    assert observed.observed_psm_count == 6
    assert observed.selection_score > 0.8

    theoretical = report.selected_entries[1]
    assert theoretical.target_protein_ref == "P00002"
    assert theoretical.rank == 1
    assert (
        theoretical.candidate_source
        is TargetedPeptideCandidateSource.THEORETICAL_DIGEST
    )
    assert theoretical.peptide_sequence == "AAALIGHTR"
    assert theoretical.observed_in_discovery is False

    rejection_codes = {
        candidate.canonical_peptide: candidate.rejection_codes
        for candidate in report.rejected_candidates
    }
    assert rejection_codes["AAASHALEDK"] == (
        TargetedPeptideSelectionRejectionCode.NON_UNIQUE,
    )
    assert rejection_codes["AAAMMMWNQK"] == (
        TargetedPeptideSelectionRejectionCode.CHEMICALLY_UNSUITABLE,
    )


def test_discovery_targeted_peptide_selection_keeps_missing_fasta_targets_visible() -> (
    None
):
    report = build_discovery_targeted_peptide_selection_report(
        (
            DiscoveryTargetProteinEntry(
                protein_group_id="protein_group_missing",
                representative_protein_ref="P404",
                protein_refs=("P404",),
                gene_symbol="MISSING",
            ),
        ),
        (),
        _protein_records(),
        top_peptides_per_target=1,
    )

    assert report.summary.selected_entry_count == 0
    assert report.summary.rejected_candidate_count == 1
    rejected = report.rejected_candidates[0]
    assert rejected.target_protein_ref == "P404"
    assert rejected.rejection_codes == (
        TargetedPeptideSelectionRejectionCode.PROTEIN_SEQUENCE_MISSING,
    )
