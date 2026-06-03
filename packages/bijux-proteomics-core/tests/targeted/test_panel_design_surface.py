# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.identification.contracts import TargetDecoyLabel
from bijux_proteomics.identification.peptide_evidence import PeptideEvidenceClass
from bijux_proteomics.io import (
    SpectralLibraryEntry,
    SpectralLibraryFormat,
    SpectrumModel,
    SpectrumPeak,
)
from bijux_proteomics.sequences import (
    PeptideChemicalLiabilityTier,
    PeptideDetectabilityTier,
    PeptideUniquenessClass,
)
from bijux_proteomics.targeted import (
    TargetedAssayInterferenceReason,
    TargetedAssayInterferenceRiskTier,
    TargetedPanelAssayInput,
    TargetedPanelBiomarkerCandidateInput,
    TargetedPanelCandidateKind,
    TargetedPanelSelectedPeptideInput,
    TargetedPanelTransitionInput,
    TargetedPanelWarningCode,
    build_targeted_panel_design_report,
    render_targeted_panel_design_assay_tsv,
    render_targeted_panel_design_omitted_candidate_tsv,
    render_targeted_panel_design_panel_tsv,
)


def _selected_peptide(
    *,
    protein_ref: str,
    protein_group_id: str,
    peptide: str,
    uniqueness_class: PeptideUniquenessClass = PeptideUniquenessClass.UNIQUE,
) -> TargetedPanelSelectedPeptideInput:
    return TargetedPanelSelectedPeptideInput(
        target_protein_ref=protein_ref,
        target_protein_group_id=protein_group_id,
        gene_symbol=protein_ref,
        peptide_sequence=peptide,
        canonical_peptide=peptide,
        rank=1,
        observed_in_discovery=True,
        observed_psm_count=6,
        run_count=4,
        detection_frequency=1.0,
        replicate_consistency=0.95,
        primary_evidence_class=PeptideEvidenceClass.STRONG,
        uniqueness_class=uniqueness_class,
        uniqueness_score=1.0
        if uniqueness_class is PeptideUniquenessClass.UNIQUE
        else 0.45,
        detectability_score=0.9,
        detectability_tier=PeptideDetectabilityTier.HIGH,
        suitability_score=0.9,
        liability_tier=PeptideChemicalLiabilityTier.PREFERRED,
        liability_codes=(),
        selection_score=0.92,
        selection_reasons=("selected for targeted follow-up",),
    )


def _assay(
    *,
    assay_entry_id: str,
    protein_ref: str,
    protein_group_id: str,
    peptide: str,
    interference_tier: TargetedAssayInterferenceRiskTier = TargetedAssayInterferenceRiskTier.LOW,
    source_library_entry_id: str | None = None,
    exported_transition_count: int = 3,
    selected_transition_count: int = 3,
) -> TargetedPanelAssayInput:
    return TargetedPanelAssayInput(
        assay_entry_id=assay_entry_id,
        target_protein_ref=protein_ref,
        target_protein_group_id=protein_group_id,
        gene_symbol=protein_ref,
        peptide_sequence=peptide,
        canonical_peptide=peptide,
        peptide_rank=1,
        precursor_charge=2,
        precursor_mz=501.25,
        selected_transition_count=selected_transition_count,
        exported_transition_count=exported_transition_count,
        interference_risk_score=0.08
        if interference_tier is TargetedAssayInterferenceRiskTier.LOW
        else 0.52,
        interference_risk_tier=interference_tier,
        downgrade_reasons=(
            ()
            if interference_tier is TargetedAssayInterferenceRiskTier.LOW
            else (TargetedAssayInterferenceReason.LIBRARY_FRAGMENT_OVERLAP,)
        ),
        panel_export_allowed=True,
        panel_export_caveat=(
            "assay is retained for panel export because interference evidence remains below the governed refusal threshold"
            if interference_tier is TargetedAssayInterferenceRiskTier.LOW
            else "assay is retained but still carries measurable interference risk"
        ),
        source_library_entry_id=source_library_entry_id,
    )


def _transition(
    *,
    assay_entry_id: str,
    protein_ref: str,
    protein_group_id: str,
    peptide: str,
    fragment_label: str,
    fragment_mz: float,
    rank: int,
    export_allowed: bool = True,
) -> TargetedPanelTransitionInput:
    return TargetedPanelTransitionInput(
        assay_entry_id=assay_entry_id,
        target_protein_ref=protein_ref,
        target_protein_group_id=protein_group_id,
        gene_symbol=protein_ref,
        peptide_sequence=peptide,
        canonical_peptide=peptide,
        precursor_charge=2,
        precursor_mz=501.25,
        fragment_label=fragment_label,
        ion_type="y",
        fragment_ordinal=7 - rank,
        fragment_charge=1,
        fragment_sequence=peptide[max(0, len(peptide) - 7 + rank - 1) :],
        fragment_mz=fragment_mz,
        expected_relative_intensity=0.9 - (0.1 * rank),
        selected_transition_rank=rank,
        interference_risk_score=0.12,
        interference_risk_tier=TargetedAssayInterferenceRiskTier.LOW,
        downgrade_reasons=(),
        export_allowed=export_allowed,
        export_caveat="transition is retained for targeted panel export",
    )


def _library_entry(
    *,
    library_entry_id: str,
    protein_ref: str,
    peptide: str,
    retention_time_minutes: float,
) -> SpectralLibraryEntry:
    return SpectralLibraryEntry(
        library_entry_id=library_entry_id,
        source_format=SpectralLibraryFormat.MGF,
        spectrum_id=f"library:{peptide}",
        precursor_mz=501.25,
        precursor_charge=2,
        peptide_sequence=peptide,
        canonical_peptide=peptide,
        modification_count=0,
        protein_refs=(protein_ref,),
        target_decoy_label=TargetDecoyLabel.TARGET,
        spectrum=SpectrumModel(
            spectrum_id=f"library:{peptide}",
            precursor_mz=501.25,
            precursor_charge=2,
            retention_time_seconds=retention_time_minutes * 60.0,
            peaks=(
                SpectrumPeak(mz=701.4, intensity=1000.0),
                SpectrumPeak(mz=602.3, intensity=850.0),
            ),
        ),
    )


def test_targeted_panel_design_builds_reviewable_transition_rows_with_rt_and_warnings() -> (
    None
):
    report = build_targeted_panel_design_report(
        biomarker_candidates=(
            TargetedPanelBiomarkerCandidateInput(
                candidate_id="protein:P11111",
                candidate_kind=TargetedPanelCandidateKind.PROTEIN,
                display_label="ROBUST1",
                target_protein_ref="P11111",
                priority_rank=1,
                final_score=0.92,
                penalty_total=0.0,
                rank_reason_codes=("assay_ready",),
            ),
            TargetedPanelBiomarkerCandidateInput(
                candidate_id="protein:P22222",
                candidate_kind=TargetedPanelCandidateKind.PROTEIN,
                display_label="WARN2",
                target_protein_ref="P22222",
                priority_rank=2,
                final_score=0.64,
                penalty_total=0.18,
                rank_reason_codes=("weak_robustness",),
            ),
            TargetedPanelBiomarkerCandidateInput(
                candidate_id="ptm_site:P33333:S21",
                candidate_kind=TargetedPanelCandidateKind.PTM_SITE,
                display_label="P33333 S21 phospho-site",
                target_protein_ref="P33333",
                site_key="P33333:S21:phosphorylation",
                priority_rank=3,
                final_score=0.71,
                penalty_total=0.0,
                rank_reason_codes=("site_specific",),
            ),
        ),
        selected_peptides=(
            _selected_peptide(
                protein_ref="P11111",
                protein_group_id="protein_group_1",
                peptide="PEPTIDER",
            ),
            _selected_peptide(
                protein_ref="P22222",
                protein_group_id="protein_group_2",
                peptide="AAASHALEDK",
                uniqueness_class=PeptideUniquenessClass.SHARED,
            ),
        ),
        assay_entries=(
            _assay(
                assay_entry_id="assay:P11111:PEPTIDER",
                protein_ref="P11111",
                protein_group_id="protein_group_1",
                peptide="PEPTIDER",
                source_library_entry_id="library:P11111:PEPTIDER",
            ),
            _assay(
                assay_entry_id="assay:P22222:AAASHALEDK",
                protein_ref="P22222",
                protein_group_id="protein_group_2",
                peptide="AAASHALEDK",
                interference_tier=TargetedAssayInterferenceRiskTier.MEDIUM,
                selected_transition_count=4,
                exported_transition_count=3,
            ),
        ),
        transition_entries=(
            _transition(
                assay_entry_id="assay:P11111:PEPTIDER",
                protein_ref="P11111",
                protein_group_id="protein_group_1",
                peptide="PEPTIDER",
                fragment_label="y7+1",
                fragment_mz=701.4,
                rank=1,
            ),
            _transition(
                assay_entry_id="assay:P11111:PEPTIDER",
                protein_ref="P11111",
                protein_group_id="protein_group_1",
                peptide="PEPTIDER",
                fragment_label="y6+1",
                fragment_mz=602.3,
                rank=2,
            ),
            _transition(
                assay_entry_id="assay:P22222:AAASHALEDK",
                protein_ref="P22222",
                protein_group_id="protein_group_2",
                peptide="AAASHALEDK",
                fragment_label="y8+1",
                fragment_mz=812.5,
                rank=1,
            ),
        ),
        spectral_library_entries=(
            _library_entry(
                library_entry_id="library:P11111:PEPTIDER",
                protein_ref="P11111",
                peptide="PEPTIDER",
                retention_time_minutes=18.4,
            ),
        ),
    )

    assert report.summary.retained_assay_count == 2
    assert report.summary.panel_transition_count == 3
    assert report.summary.omitted_candidate_count == 1
    assert report.assay_entries[0].biomarker_candidate_id == "protein:P11111"
    assert report.assay_entries[0].expected_retention_time_minutes == 18.4
    assert report.assay_entries[0].retention_window_start_minutes == 16.9
    assert report.assay_entries[1].biomarker_candidate_id == "protein:P22222"
    assert (
        TargetedPanelWarningCode.CANDIDATE_PENALIZED
        in report.assay_entries[1].warning_codes
    )
    assert (
        TargetedPanelWarningCode.ELEVATED_INTERFERENCE_RISK
        in report.assay_entries[1].warning_codes
    )
    assert (
        TargetedPanelWarningCode.NON_UNIQUE_TARGET
        in report.assay_entries[1].warning_codes
    )
    assert (
        TargetedPanelWarningCode.MISSING_EXPECTED_RETENTION_TIME
        in report.assay_entries[1].warning_codes
    )
    assert (
        TargetedPanelWarningCode.REDUCED_TRANSITION_SUPPORT
        in report.assay_entries[1].warning_codes
    )
    assert report.omitted_candidates[0].candidate_id == "ptm_site:P33333:S21"
    assert (
        "site-specific targeted assay design"
        in report.omitted_candidates[0].omission_reason
    )

    panel_tsv = render_targeted_panel_design_panel_tsv(report)
    assay_tsv = render_targeted_panel_design_assay_tsv(report)
    omitted_tsv = render_targeted_panel_design_omitted_candidate_tsv(report)
    assert "expected_retention_time_minutes" in panel_tsv
    assert "uniqueness_class" in panel_tsv
    assert "warning_codes" in panel_tsv
    assert "PEPTIDER" in panel_tsv
    assert "candidate_penalized" in assay_tsv
    assert "ptm_site:P33333:S21" in omitted_tsv
