# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from typing import cast

from bijux_proteomics.chemistry import (
    FragmentIonSeries,
    calculate_fragment_ions,
    calculate_peptide_mz,
)
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
from bijux_proteomics.io import (
    SpectralLibraryEntry,
    SpectralLibraryFormat,
    SpectrumModel,
    SpectrumPeak,
)
from bijux_proteomics.sequences import parse_fasta_document
from bijux_proteomics.sequences.core import NormalizedProteinRecord
from bijux_proteomics.targeted import TargetedPanelCandidateKind
from bijux_proteomics.workflow import (
    DiscoveryAssayFeasibilityStatus,
    DiscoveryAssaySourceResult,
    DiscoveryAssayTargetInput,
    design_assay_from_discovery,
    render_discovery_to_assay_assay_tsv,
    render_discovery_to_assay_omitted_targets_tsv,
    render_discovery_to_assay_panel_tsv,
    render_discovery_to_assay_rejected_peptides_tsv,
    render_discovery_to_assay_validation_candidate_cards_tsv,
    render_discovery_to_assay_validation_candidate_summary_tsv,
)


def _protein_records() -> tuple[NormalizedProteinRecord, ...]:
    return cast(
        tuple[NormalizedProteinRecord, ...],
        parse_fasta_document(
            ">sp|P00001|KIN1 GN=KIN1\n"
            "PEPTIDERAAASHALEDKAAAMMMWNQK\n"
            ">sp|O00003|OFF1 GN=OFF1\n"
            "KAAASHALEDK\n"
        ).accepted_records,
    )


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
            replicate_consistency=0.80,
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
            psm_count=8,
            spectrum_count=8,
            run_count=4,
            detection_frequency=1.0,
            replicate_consistency=0.93,
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


def _library_entry_for_peptide(peptide: str) -> SpectralLibraryEntry:
    precursor_mz = calculate_peptide_mz(peptide, charge=2)
    theoretical = calculate_fragment_ions(
        peptide,
        charges=(1,),
        series=(FragmentIonSeries.Y, FragmentIonSeries.B),
    )
    mz_by_label = {
        f"{fragment.series.value}{fragment.ordinal}+{fragment.charge}": fragment.mz_monoisotopic
        for fragment in theoretical
    }
    return SpectralLibraryEntry(
        library_entry_id=f"library:{peptide}",
        source_format=SpectralLibraryFormat.MGF,
        spectrum_id=f"library:{peptide}",
        precursor_mz=precursor_mz,
        precursor_charge=2,
        peptide_sequence=peptide,
        canonical_peptide=peptide,
        modification_count=0,
        protein_refs=("P00001",),
        target_decoy_label=TargetDecoyLabel.TARGET,
        spectrum=SpectrumModel(
            spectrum_id=f"library:{peptide}",
            precursor_mz=precursor_mz,
            precursor_charge=2,
            retention_time_seconds=12.5 * 60.0,
            peaks=(
                SpectrumPeak(mz=mz_by_label["y7+1"], intensity=1000.0),
                SpectrumPeak(mz=mz_by_label["y6+1"], intensity=850.0),
                SpectrumPeak(mz=mz_by_label["y5+1"], intensity=700.0),
                SpectrumPeak(mz=mz_by_label["b5+1"], intensity=250.0),
            ),
        ),
    )


def test_design_assay_from_discovery_blocks_targets_without_acceptable_peptides_and_keeps_sites_visible() -> (
    None
):
    report = design_assay_from_discovery(
        DiscoveryAssaySourceResult(
            peptide_evidence_entries=_observed_entries(),
            protein_records=_protein_records(),
            spectral_library_entries=(_library_entry_for_peptide("PEPTIDER"),),
        ),
        (
            DiscoveryAssayTargetInput(
                candidate_id="protein:P00001",
                candidate_kind=TargetedPanelCandidateKind.PROTEIN,
                display_label="KIN1 protein target",
                target_protein_ref="P00001",
                target_protein_group_id="protein_group_1",
                protein_refs=("P00001",),
                gene_symbol="KIN1",
                priority_rank=1,
                final_score=0.93,
                penalty_total=0.0,
                rank_reason_codes=("assay_ready",),
                discovery_peptides=("PEPTIDER", "AAASHALEDK", "AAAMMMWNQK"),
            ),
            DiscoveryAssayTargetInput(
                candidate_id="protein:P404",
                candidate_kind=TargetedPanelCandidateKind.PROTEIN,
                display_label="missing blocked target",
                target_protein_ref="P404",
                target_protein_group_id="protein_group_2",
                protein_refs=("P404",),
                gene_symbol="MISS1",
                priority_rank=2,
                final_score=0.62,
                penalty_total=0.12,
                rank_reason_codes=("sequence_missing",),
                discovery_peptides=("AAASHALEDK",),
            ),
            DiscoveryAssayTargetInput(
                candidate_id="ptm_site:P00001:S15",
                candidate_kind=TargetedPanelCandidateKind.PTM_SITE,
                display_label="KIN1 S15 phospho-site",
                target_protein_ref="P00001",
                target_protein_group_id="protein_group_1",
                protein_refs=("P00001",),
                gene_symbol="KIN1",
                site_key="P00001:S15:phosphorylation",
                priority_rank=3,
                final_score=0.71,
                penalty_total=0.04,
                rank_reason_codes=("site_specific",),
                discovery_peptides=("PEPTIDER",),
            ),
        ),
        top_peptides_per_target=1,
    )

    targets = {entry.candidate_id: entry for entry in report.target_entries}

    assert report.summary.target_count == 3
    assert report.summary.assay_ready_target_count == 1
    assert report.summary.target_with_acceptable_peptide_count == 2
    assert report.manifest.artifacts.targets_tsv == "discovery_to_assay_targets.tsv"
    assert report.artifacts["targets_tsv"] == "discovery_to_assay_targets.tsv"
    assert {warning.warning_code for warning in report.warnings} == {
        "blocked_targets_present",
        "partial_assay_coverage",
    }
    assert {entry.entity_id for entry in report.rejected_evidence} == {
        "protein:P404",
        "ptm_site:P00001:S15",
    }
    assert {entry.reason_code for entry in report.rejected_evidence} == {
        "missing_peptide",
        "review-needs-assay-evidence",
    }

    assert (
        targets["protein:P00001"].assay_feasibility
        is DiscoveryAssayFeasibilityStatus.ASSAY_READY
    )
    assert targets["protein:P00001"].acceptable_peptide_count == 1
    assert targets["protein:P00001"].retained_assay_count == 1
    assert targets["protein:P00001"].expected_retention_time_available is True

    assert (
        targets["protein:P404"].assay_feasibility
        is DiscoveryAssayFeasibilityStatus.PEPTIDE_UNAVAILABLE
    )
    assert targets["protein:P404"].acceptable_peptide_count == 0
    assert targets["protein:P404"].retained_assay_count == 0

    assert (
        targets["ptm_site:P00001:S15"].assay_feasibility
        is DiscoveryAssayFeasibilityStatus.SITE_SPECIFIC_FOLLOW_UP_REQUIRED
    )
    assert targets["ptm_site:P00001:S15"].acceptable_peptide_count == 1
    assert targets["ptm_site:P00001:S15"].retained_assay_count == 0

    cards = {
        entry.candidate_id: entry for entry in report.validation_candidate_cards.cards
    }
    assert report.validation_candidate_cards.summary.candidate_count == 3
    assert (
        report.validation_candidate_cards.summary.ready_for_targeted_validation_count
        == 1
    )
    assert report.validation_candidate_cards.summary.blocked_by_assay_design_count == 2
    assert cards["protein:P00001"].final_status.value == "ready_for_targeted_validation"
    assert cards["protein:P404"].final_status.value == "blocked_by_assay_design"
    assert cards["protein:P404"].omitted_reason == targets["protein:P404"].note
    assert "no acceptable peptide survived" in cards["protein:P404"].omitted_reason
    assert cards["ptm_site:P00001:S15"].final_status.value == "blocked_by_assay_design"
    assert (
        "blocked_by_assay_design"
        in render_discovery_to_assay_validation_candidate_cards_tsv(report)
    )
    assert (
        "ready_for_targeted_validation_count\t1"
        in render_discovery_to_assay_validation_candidate_summary_tsv(report)
    )

    assert {
        entry.biomarker_candidate_id
        for entry in report.panel_design_report.assay_entries
    } == {"protein:P00001"}
    assert "fragment_mz" in render_discovery_to_assay_panel_tsv(report)
    assert "expected_retention_time_minutes" in render_discovery_to_assay_assay_tsv(
        report
    )
    assert "chemically_unsuitable" in render_discovery_to_assay_rejected_peptides_tsv(
        report
    )
    assert "ptm_site:P00001:S15" in render_discovery_to_assay_omitted_targets_tsv(
        report
    )


def test_design_assay_from_discovery_marks_transition_limited_targets_without_exported_assays() -> (
    None
):
    report = design_assay_from_discovery(
        DiscoveryAssaySourceResult(
            peptide_evidence_entries=_observed_entries()[:1],
            protein_records=parse_fasta_document(
                ">sp|P00001|KIN1 GN=KIN1\nPEPTIDERAAAK\n"
            ).accepted_records,
            spectral_library_entries=(_library_entry_for_peptide("PEPTIDER"),),
        ),
        (
            DiscoveryAssayTargetInput(
                candidate_id="protein:P00001",
                candidate_kind=TargetedPanelCandidateKind.PROTEIN,
                display_label="KIN1 transition-limited target",
                target_protein_ref="P00001",
                target_protein_group_id="protein_group_1",
                protein_refs=("P00001",),
                gene_symbol="KIN1",
                priority_rank=1,
                final_score=0.88,
                penalty_total=0.0,
                rank_reason_codes=("assay_ready",),
                discovery_peptides=("PEPTIDER",),
            ),
        ),
        top_peptides_per_target=1,
        minimum_transition_count=3,
        maximum_transition_count=6,
        minimum_export_transitions=7,
    )

    target = report.target_entries[0]

    assert (
        target.assay_feasibility is DiscoveryAssayFeasibilityStatus.TRANSITION_LIMITED
    )
    assert target.acceptable_peptide_count == 1
    assert target.transition_supported_peptide_count == 1
    assert target.retained_assay_count == 0
    assert target.panel_transition_count == 0
    assert report.rejected_evidence[0].reason_code == "partial_assay_coverage"
    assert (
        report.rejected_evidence[0].related_artifact
        == "discovery_to_assay_omitted_targets.tsv"
    )
    assert report.panel_design_report.assay_entries == ()
    assert report.validation_candidate_cards.summary.blocked_by_assay_design_count == 1
    assert (
        report.validation_candidate_cards.cards[0].final_status.value
        == "blocked_by_assay_design"
    )
    assert "no retained targeted assay survived peptide selection" in (
        render_discovery_to_assay_omitted_targets_tsv(report)
    )
