# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.identification.peptide_evidence import PeptideEvidenceClass
from bijux_proteomics.sequences import (
    PeptideChemicalLiabilityTier,
    PeptideDetectabilityTier,
    PeptideUniquenessClass,
)
from bijux_proteomics.targeted import (
    TargetedAssayInterferenceRiskTier,
    TargetedPanelCandidateKind,
    TargetedPanelWarningCode,
    ValidationExperimentPlanningMode,
    ValidationExperimentPlanningPolicy,
    ValidationExperimentWarningCode,
    ValidationPlanningBiomarkerCandidateInput,
    ValidationPlanningOmittedCandidateInput,
    ValidationPlanningPanelAssayInput,
    ValidationPlanningPilotVarianceInput,
    ValidationPlanningSelectedPeptideInput,
    build_validation_experiment_planning_report,
    render_validation_experiment_planning_plan_tsv,
    render_validation_experiment_planning_summary_tsv,
    render_validation_experiment_planning_warning_tsv,
)


def _candidate(
    *,
    candidate_id: str,
    display_label: str,
    protein_ref: str,
    rank: int,
    effect_size: float | None,
    penalty_total: float,
    uncertainty: float,
    robustness_score: float,
    assay_feasibility_score: float,
) -> ValidationPlanningBiomarkerCandidateInput:
    return ValidationPlanningBiomarkerCandidateInput(
        candidate_id=candidate_id,
        candidate_kind=TargetedPanelCandidateKind.PROTEIN,
        display_label=display_label,
        target_protein_ref=protein_ref,
        priority_rank=rank,
        final_score=0.8,
        penalty_total=penalty_total,
        uncertainty=uncertainty,
        effect_size=effect_size,
        adjusted_p_value=0.01,
        support_count=4,
        robustness_score=robustness_score,
        assay_feasibility_score=assay_feasibility_score,
        rank_reason_codes=("assay_ready",),
        ranking_note="ranked for targeted validation",
    )


def _selected_peptide(
    *,
    protein_ref: str,
    peptide: str,
    detection_frequency: float,
    replicate_consistency: float,
    uniqueness_class: PeptideUniquenessClass,
    uniqueness_score: float,
    detectability_score: float,
    detectability_tier: PeptideDetectabilityTier,
    suitability_score: float,
    liability_tier: PeptideChemicalLiabilityTier,
) -> ValidationPlanningSelectedPeptideInput:
    return ValidationPlanningSelectedPeptideInput(
        target_protein_ref=protein_ref,
        target_protein_group_id=f"group:{protein_ref}",
        gene_symbol=protein_ref,
        peptide_sequence=peptide,
        canonical_peptide=peptide,
        rank=1,
        observed_in_discovery=True,
        observed_psm_count=5,
        run_count=4,
        detection_frequency=detection_frequency,
        replicate_consistency=replicate_consistency,
        primary_evidence_class=PeptideEvidenceClass.STRONG,
        uniqueness_class=uniqueness_class,
        uniqueness_score=uniqueness_score,
        detectability_score=detectability_score,
        detectability_tier=detectability_tier,
        suitability_score=suitability_score,
        liability_tier=liability_tier,
        liability_codes=(),
    )


def _panel_assay(
    *,
    assay_entry_id: str,
    candidate_id: str,
    display_label: str,
    protein_ref: str,
    peptide: str,
    uniqueness_class: PeptideUniquenessClass,
    uniqueness_score: float,
    risk_tier: TargetedAssayInterferenceRiskTier,
    warning_codes: tuple[TargetedPanelWarningCode, ...] = (),
    selected_transition_count: int = 3,
    exported_transition_count: int = 3,
) -> ValidationPlanningPanelAssayInput:
    return ValidationPlanningPanelAssayInput(
        assay_entry_id=assay_entry_id,
        biomarker_candidate_id=candidate_id,
        biomarker_candidate_kind=TargetedPanelCandidateKind.PROTEIN,
        biomarker_display_label=display_label,
        biomarker_priority_rank=1,
        target_protein_ref=protein_ref,
        target_protein_group_id=f"group:{protein_ref}",
        gene_symbol=protein_ref,
        peptide_sequence=peptide,
        canonical_peptide=peptide,
        uniqueness_class=uniqueness_class,
        uniqueness_score=uniqueness_score,
        selected_transition_count=selected_transition_count,
        exported_transition_count=exported_transition_count,
        assay_interference_risk_tier=risk_tier,
        warning_codes=warning_codes,
        warning_note="assay retained for targeted panel review",
    )


def test_validation_experiment_planning_flags_underpowered_and_omitted_candidates() -> (
    None
):
    report = build_validation_experiment_planning_report(
        biomarker_candidates=(
            _candidate(
                candidate_id="protein:P11111",
                display_label="ROBUST1",
                protein_ref="P11111",
                rank=1,
                effect_size=1.1,
                penalty_total=0.0,
                uncertainty=0.10,
                robustness_score=0.85,
                assay_feasibility_score=0.90,
            ),
            _candidate(
                candidate_id="protein:P22222",
                display_label="WARN2",
                protein_ref="P22222",
                rank=2,
                effect_size=0.55,
                penalty_total=0.18,
                uncertainty=0.30,
                robustness_score=0.38,
                assay_feasibility_score=0.58,
            ),
        ),
        selected_peptides=(
            _selected_peptide(
                protein_ref="P11111",
                peptide="PEPTIDER",
                detection_frequency=0.95,
                replicate_consistency=0.92,
                uniqueness_class=PeptideUniquenessClass.UNIQUE,
                uniqueness_score=1.0,
                detectability_score=0.94,
                detectability_tier=PeptideDetectabilityTier.HIGH,
                suitability_score=0.92,
                liability_tier=PeptideChemicalLiabilityTier.PREFERRED,
            ),
            _selected_peptide(
                protein_ref="P22222",
                peptide="AAASHALEDK",
                detection_frequency=0.58,
                replicate_consistency=0.62,
                uniqueness_class=PeptideUniquenessClass.SHARED,
                uniqueness_score=0.45,
                detectability_score=0.60,
                detectability_tier=PeptideDetectabilityTier.MEDIUM,
                suitability_score=0.55,
                liability_tier=PeptideChemicalLiabilityTier.CAUTION,
            ),
        ),
        panel_assays=(
            _panel_assay(
                assay_entry_id="assay:P11111:PEPTIDER",
                candidate_id="protein:P11111",
                display_label="ROBUST1",
                protein_ref="P11111",
                peptide="PEPTIDER",
                uniqueness_class=PeptideUniquenessClass.UNIQUE,
                uniqueness_score=1.0,
                risk_tier=TargetedAssayInterferenceRiskTier.LOW,
            ),
            _panel_assay(
                assay_entry_id="assay:P22222:AAASHALEDK",
                candidate_id="protein:P22222",
                display_label="WARN2",
                protein_ref="P22222",
                peptide="AAASHALEDK",
                uniqueness_class=PeptideUniquenessClass.SHARED,
                uniqueness_score=0.45,
                risk_tier=TargetedAssayInterferenceRiskTier.MEDIUM,
                warning_codes=(
                    TargetedPanelWarningCode.CANDIDATE_PENALIZED,
                    TargetedPanelWarningCode.NON_UNIQUE_TARGET,
                    TargetedPanelWarningCode.REDUCED_TRANSITION_SUPPORT,
                ),
                selected_transition_count=4,
                exported_transition_count=2,
            ),
        ),
        pilot_variance_entries=(
            ValidationPlanningPilotVarianceInput(
                entity_id="protein:P11111",
                protein_refs=("P11111",),
                observed_sample_count=8,
                missing_fraction=0.08,
                contributing_condition_count=2,
                used_global_variance_fallback=False,
                pooled_log2_stddev=0.28,
            ),
            ValidationPlanningPilotVarianceInput(
                entity_id="protein:P22222",
                protein_refs=("P22222",),
                observed_sample_count=8,
                missing_fraction=0.36,
                contributing_condition_count=0,
                used_global_variance_fallback=True,
                pooled_log2_stddev=0.42,
            ),
        ),
        omitted_candidates=(
            ValidationPlanningOmittedCandidateInput(
                candidate_id="ptm_site:P33333:S21",
                candidate_kind=TargetedPanelCandidateKind.PTM_SITE,
                display_label="P33333 S21 phospho-site",
                target_protein_ref="P33333",
                site_key="P33333:S21:phosphorylation",
                priority_rank=3,
                omission_reason="PTM-site candidate requires site-specific targeted assay design before validation planning",
            ),
        ),
        policy=ValidationExperimentPlanningPolicy(proposed_samples_per_group=6),
    )

    assert report.summary.biomarker_candidate_count == 2
    assert report.summary.planned_assay_count == 2
    assert report.summary.omitted_candidate_count == 1
    assert report.summary.warning_count >= 5
    by_assay = {entry.assay_entry_id: entry for entry in report.plan_entries}
    robust = by_assay["assay:P11111:PEPTIDER"]
    risky = by_assay["assay:P22222:AAASHALEDK"]

    assert robust.planning_mode is ValidationExperimentPlanningMode.PILOT_BACKED
    assert robust.underpowered is False
    assert robust.recommended_minimum_samples_per_group <= 6

    assert risky.planning_mode is ValidationExperimentPlanningMode.PILOT_BACKED
    assert risky.underpowered is True
    assert risky.expected_missingness_fraction >= 0.36
    assert risky.assay_risk_score >= 0.55
    assert risky.recommended_minimum_samples_per_group > 6
    assert ValidationExperimentWarningCode.UNDERPOWERED_DESIGN in risky.warning_codes
    assert ValidationExperimentWarningCode.HIGH_ASSAY_RISK in risky.warning_codes
    assert ValidationExperimentWarningCode.NON_UNIQUE_TARGET in risky.warning_codes
    assert ValidationExperimentWarningCode.VARIANCE_FALLBACK_USED in risky.warning_codes

    warning_codes = {entry.warning_code for entry in report.warnings}
    assert ValidationExperimentWarningCode.SITE_CANDIDATE_NOT_PANELIZED in warning_codes
    assert (
        "recommended_panel_samples_per_group"
        in render_validation_experiment_planning_summary_tsv(report)
    )
    assert "planning_mode" in render_validation_experiment_planning_plan_tsv(report)
    assert "warning_code" in render_validation_experiment_planning_warning_tsv(report)


def test_validation_experiment_planning_falls_back_to_heuristic_without_pilot_variance() -> (
    None
):
    report = build_validation_experiment_planning_report(
        biomarker_candidates=(
            _candidate(
                candidate_id="protein:P44444",
                display_label="EDGE4",
                protein_ref="P44444",
                rank=1,
                effect_size=0.42,
                penalty_total=0.10,
                uncertainty=0.35,
                robustness_score=0.40,
                assay_feasibility_score=0.52,
            ),
        ),
        selected_peptides=(),
        panel_assays=(
            _panel_assay(
                assay_entry_id="assay:P44444:EDGEPEP",
                candidate_id="protein:P44444",
                display_label="EDGE4",
                protein_ref="P44444",
                peptide="EDGEPEP",
                uniqueness_class=PeptideUniquenessClass.UNIQUE,
                uniqueness_score=1.0,
                risk_tier=TargetedAssayInterferenceRiskTier.HIGH,
                warning_codes=(TargetedPanelWarningCode.CANDIDATE_PENALIZED,),
            ),
        ),
        policy=ValidationExperimentPlanningPolicy(proposed_samples_per_group=5),
    )

    entry = report.plan_entries[0]

    assert entry.planning_mode is ValidationExperimentPlanningMode.HEURISTIC
    assert entry.underpowered is True
    assert entry.recommended_minimum_samples_per_group > 5
    assert ValidationExperimentWarningCode.MISSING_PILOT_VARIANCE in entry.warning_codes
    assert (
        ValidationExperimentWarningCode.MISSING_SELECTION_CONTEXT in entry.warning_codes
    )
    assert ValidationExperimentWarningCode.HIGH_ASSAY_RISK in entry.warning_codes
