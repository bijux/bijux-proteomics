# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.sequences import PeptideUniquenessClass
from bijux_proteomics.targeted.assay_interference import (
    TargetedAssayInterferenceRiskTier,
)
from bijux_proteomics.targeted.biomarker_stability import BiomarkerStabilityReasonCode
from bijux_proteomics.targeted.panel_design import (
    TargetedPanelCandidateKind,
    TargetedPanelWarningCode,
)
from bijux_proteomics.targeted.result_validation import (
    TargetedValidationReasonCode,
    TargetedValidationVerdict,
)
from bijux_proteomics.targeted.validation_evidence_cards import (
    ValidationEvidenceCardStatus,
    ValidationEvidenceDiscoveryInput,
    ValidationEvidenceOmittedCandidateInput,
    ValidationEvidencePanelAssayInput,
    ValidationEvidenceRedundancyInput,
    ValidationEvidenceResultAssayInput,
    ValidationEvidenceResultInput,
    ValidationEvidenceStabilityInput,
    ValidationEvidenceWarningCode,
    build_validation_evidence_card_report,
    render_validation_evidence_card_tsv,
    render_validation_evidence_card_warning_tsv,
)


def test_validation_evidence_cards_derive_final_status_from_governed_evidence() -> None:
    report = build_validation_evidence_card_report(
        _discovery_candidates(),
        panel_assays=_panel_assays(),
        omitted_candidates=_omitted_candidates(),
        targeted_validation_results=_validation_results(),
        targeted_validation_assay_evidence=_validation_assay_evidence(),
        stability_entries=_stability_entries(),
        redundancy_entries=_redundancy_entries(),
    )

    assert report.summary.candidate_count == 4
    assert report.summary.confirmed_count == 1
    assert report.summary.inconclusive_count == 1
    assert report.summary.deprioritized_as_redundant_count == 1
    assert report.summary.blocked_by_assay_design_count == 1

    cards_by_id = {entry.candidate_id: entry for entry in report.cards}
    assert (
        cards_by_id["protein:P11111"].final_status
        is ValidationEvidenceCardStatus.CONFIRMED
    )
    assert (
        cards_by_id["protein:P22222"].final_status
        is ValidationEvidenceCardStatus.DEPRIORITIZED_AS_REDUNDANT
    )
    assert (
        cards_by_id["ptm_site:P33333:S21"].final_status
        is ValidationEvidenceCardStatus.BLOCKED_BY_ASSAY_DESIGN
    )
    assert (
        cards_by_id["protein:P44444"].final_status
        is ValidationEvidenceCardStatus.INCONCLUSIVE
    )
    assert (
        ValidationEvidenceWarningCode.STABILITY_DOWNGRADED
        in cards_by_id["protein:P44444"].warning_codes
    )
    assert (
        ValidationEvidenceWarningCode.REDUNDANT_CANDIDATE
        in cards_by_id["protein:P22222"].warning_codes
    )
    assert cards_by_id["protein:P11111"].biological_role_labels == (
        "pathway:stress_response",
        "domain:kinase",
    )


def test_validation_evidence_card_renderers_preserve_biological_role_and_warning_ledgers() -> (
    None
):
    report = build_validation_evidence_card_report(
        _discovery_candidates(),
        panel_assays=_panel_assays(),
        omitted_candidates=_omitted_candidates(),
        targeted_validation_results=_validation_results(),
        targeted_validation_assay_evidence=_validation_assay_evidence(),
        stability_entries=_stability_entries(),
        redundancy_entries=_redundancy_entries(),
    )

    cards_tsv = render_validation_evidence_card_tsv(report)
    warnings_tsv = render_validation_evidence_card_warning_tsv(report)

    assert "candidate_id\tcandidate_kind\tdisplay_label" in cards_tsv
    assert "pathway:stress_response;domain:kinase" in cards_tsv
    assert "deprioritized_as_redundant" in cards_tsv
    assert "stability_downgraded" in warnings_tsv
    assert "assay_design_omitted" in warnings_tsv


def _discovery_candidates() -> tuple[ValidationEvidenceDiscoveryInput, ...]:
    return (
        ValidationEvidenceDiscoveryInput(
            candidate_id="protein:P11111",
            candidate_kind=TargetedPanelCandidateKind.PROTEIN,
            display_label="KIN1",
            target_protein_ref="P11111",
            priority_rank=1,
            final_score=0.92,
            weighted_evidence_total=0.92,
            penalty_total=0.02,
            uncertainty=0.04,
            effect_size=1.7,
            adjusted_p_value=0.002,
            support_count=4,
            annotation_labels=("pathway:stress_response", "domain:kinase"),
            rank_reason_codes=("assay_ready",),
            source_ids=("protein-card:KIN1",),
            ranking_note="strong kinase biomarker candidate",
        ),
        ValidationEvidenceDiscoveryInput(
            candidate_id="protein:P22222",
            candidate_kind=TargetedPanelCandidateKind.PROTEIN,
            display_label="KIN2",
            target_protein_ref="P22222",
            priority_rank=2,
            final_score=0.81,
            weighted_evidence_total=0.81,
            penalty_total=0.08,
            uncertainty=0.07,
            effect_size=1.2,
            adjusted_p_value=0.01,
            support_count=3,
            annotation_labels=("pathway:stress_response",),
            rank_reason_codes=("assay_ready",),
            source_ids=("protein-card:KIN2",),
            ranking_note="correlated neighbor candidate",
        ),
        ValidationEvidenceDiscoveryInput(
            candidate_id="ptm_site:P33333:S21",
            candidate_kind=TargetedPanelCandidateKind.PTM_SITE,
            display_label="P33333 S21",
            target_protein_ref="P33333",
            site_key="P33333:S21:phosphorylation",
            priority_rank=3,
            final_score=0.79,
            weighted_evidence_total=0.79,
            penalty_total=0.03,
            uncertainty=0.05,
            effect_size=1.1,
            adjusted_p_value=0.005,
            support_count=5,
            annotation_labels=("mechanism:site_specific", "ortholog:conserved"),
            rank_reason_codes=("assay_ready",),
            source_ids=("ptm-card:P33333:S21",),
            ranking_note="site-specific phosphosite candidate",
        ),
        ValidationEvidenceDiscoveryInput(
            candidate_id="protein:P44444",
            candidate_kind=TargetedPanelCandidateKind.PROTEIN,
            display_label="KIN4",
            target_protein_ref="P44444",
            priority_rank=4,
            final_score=0.77,
            weighted_evidence_total=0.77,
            penalty_total=0.01,
            uncertainty=0.06,
            effect_size=0.9,
            adjusted_p_value=0.02,
            support_count=2,
            annotation_labels=("pathway:repair",),
            rank_reason_codes=("assay_ready",),
            source_ids=("protein-card:KIN4",),
            ranking_note="candidate requires stability review",
        ),
    )


def _panel_assays() -> tuple[ValidationEvidencePanelAssayInput, ...]:
    return (
        ValidationEvidencePanelAssayInput(
            assay_entry_id="assay:P11111:PEPTIDER",
            biomarker_candidate_id="protein:P11111",
            biomarker_candidate_kind=TargetedPanelCandidateKind.PROTEIN,
            biomarker_display_label="KIN1",
            biomarker_priority_rank=1,
            target_protein_ref="P11111",
            target_protein_group_id="protein_group_1",
            gene_symbol="KIN1",
            peptide_sequence="PEPTIDER",
            canonical_peptide="PEPTIDER",
            uniqueness_class=PeptideUniquenessClass.UNIQUE,
            uniqueness_score=1.0,
            precursor_charge=2,
            precursor_mz=501.25,
            expected_retention_time_minutes=12.5,
            retention_window_start_minutes=11.0,
            retention_window_end_minutes=14.0,
            selected_transition_count=3,
            exported_transition_count=3,
            assay_interference_risk_tier=TargetedAssayInterferenceRiskTier.LOW,
            warning_note="assay retained for panel export",
        ),
        ValidationEvidencePanelAssayInput(
            assay_entry_id="assay:P22222:AAAAK",
            biomarker_candidate_id="protein:P22222",
            biomarker_candidate_kind=TargetedPanelCandidateKind.PROTEIN,
            biomarker_display_label="KIN2",
            biomarker_priority_rank=2,
            target_protein_ref="P22222",
            target_protein_group_id="protein_group_2",
            gene_symbol="KIN2",
            peptide_sequence="AAAAK",
            canonical_peptide="AAAAK",
            uniqueness_class=PeptideUniquenessClass.UNIQUE,
            uniqueness_score=1.0,
            precursor_charge=2,
            precursor_mz=451.25,
            expected_retention_time_minutes=18.4,
            retention_window_start_minutes=17.0,
            retention_window_end_minutes=20.0,
            selected_transition_count=3,
            exported_transition_count=3,
            assay_interference_risk_tier=TargetedAssayInterferenceRiskTier.LOW,
            warning_note="assay retained for panel export",
        ),
        ValidationEvidencePanelAssayInput(
            assay_entry_id="assay:P44444:LOWUNIQ",
            biomarker_candidate_id="protein:P44444",
            biomarker_candidate_kind=TargetedPanelCandidateKind.PROTEIN,
            biomarker_display_label="KIN4",
            biomarker_priority_rank=4,
            target_protein_ref="P44444",
            target_protein_group_id="protein_group_4",
            gene_symbol="KIN4",
            peptide_sequence="LOWUNIQ",
            canonical_peptide="LOWUNIQ",
            uniqueness_class=PeptideUniquenessClass.SHARED,
            uniqueness_score=0.4,
            precursor_charge=2,
            precursor_mz=601.25,
            expected_retention_time_minutes=22.1,
            retention_window_start_minutes=20.5,
            retention_window_end_minutes=23.5,
            selected_transition_count=2,
            exported_transition_count=2,
            assay_interference_risk_tier=TargetedAssayInterferenceRiskTier.MEDIUM,
            warning_codes=(TargetedPanelWarningCode.NON_UNIQUE_TARGET,),
            warning_note="shared assay retained with caveat",
        ),
    )


def _omitted_candidates() -> tuple[ValidationEvidenceOmittedCandidateInput, ...]:
    return (
        ValidationEvidenceOmittedCandidateInput(
            candidate_id="ptm_site:P33333:S21",
            candidate_kind=TargetedPanelCandidateKind.PTM_SITE,
            display_label="P33333 S21",
            target_protein_ref="P33333",
            site_key="P33333:S21:phosphorylation",
            priority_rank=3,
            omission_reason="site-specific candidate remains omitted because no governed site-resolved targeted assay is available",
        ),
    )


def _validation_results() -> tuple[ValidationEvidenceResultInput, ...]:
    return (
        ValidationEvidenceResultInput(
            candidate_id="protein:P11111",
            verdict=TargetedValidationVerdict.CONFIRMED,
            validation_log2_effect=1.5,
            assay_evidence_count=1,
            confirmed_assay_count=1,
            contradicted_assay_count=0,
            inconclusive_assay_count=0,
            reason_codes=(
                TargetedValidationReasonCode.VALIDATION_EFFECT_MATCHES_DISCOVERY,
            ),
            note="targeted validation matches discovery direction and effect",
        ),
        ValidationEvidenceResultInput(
            candidate_id="protein:P44444",
            verdict=TargetedValidationVerdict.INCONCLUSIVE,
            validation_log2_effect=0.1,
            assay_evidence_count=1,
            confirmed_assay_count=0,
            contradicted_assay_count=0,
            inconclusive_assay_count=1,
            reason_codes=(
                TargetedValidationReasonCode.NON_UNIQUE_VALIDATION_ASSAY,
                TargetedValidationReasonCode.WEAK_VALIDATION_EFFECT,
            ),
            note="shared assay and weak targeted effect leave the candidate unresolved",
        ),
    )


def _validation_assay_evidence() -> tuple[ValidationEvidenceResultAssayInput, ...]:
    return (
        ValidationEvidenceResultAssayInput(
            candidate_id="protein:P11111",
            assay_entry_id="assay:P11111:PEPTIDER",
            peptide_sequence="PEPTIDER",
            canonical_peptide="PEPTIDER",
            precursor_charge=2,
            uniqueness_class=PeptideUniquenessClass.UNIQUE,
            validation_log2_effect=1.5,
            verdict=TargetedValidationVerdict.CONFIRMED,
            reason_codes=(
                TargetedValidationReasonCode.VALIDATION_EFFECT_MATCHES_DISCOVERY,
            ),
            note="unique assay confirms the discovery signal",
        ),
        ValidationEvidenceResultAssayInput(
            candidate_id="protein:P44444",
            assay_entry_id="assay:P44444:LOWUNIQ",
            peptide_sequence="LOWUNIQ",
            canonical_peptide="LOWUNIQ",
            precursor_charge=2,
            uniqueness_class=PeptideUniquenessClass.SHARED,
            validation_log2_effect=0.1,
            verdict=TargetedValidationVerdict.INCONCLUSIVE,
            reason_codes=(
                TargetedValidationReasonCode.NON_UNIQUE_VALIDATION_ASSAY,
                TargetedValidationReasonCode.WEAK_VALIDATION_EFFECT,
            ),
            note="shared assay does not resolve the discovery claim",
        ),
    )


def _stability_entries() -> tuple[ValidationEvidenceStabilityInput, ...]:
    return (
        ValidationEvidenceStabilityInput(
            candidate_id="protein:P44444",
            stability_score=0.58,
            stability_penalty=0.19,
            downgraded=True,
            instability_reasons=(
                BiomarkerStabilityReasonCode.SAMPLE_TYPE_SENSITIVE_SIGNAL,
            ),
            ranking_note="subgroup behavior suggests sample-type-sensitive instability",
        ),
    )


def _redundancy_entries() -> tuple[ValidationEvidenceRedundancyInput, ...]:
    return (
        ValidationEvidenceRedundancyInput(
            candidate_id="protein:P11111",
            cluster_id="cluster:001",
            representative_candidate_id="protein:P11111",
            representative=True,
            dropped=False,
            shared_sample_count=4,
            max_redundant_correlation=0.97,
            redundancy_reason_codes=("high_signal_correlation",),
            ranking_note="representative retained for correlated cluster",
        ),
        ValidationEvidenceRedundancyInput(
            candidate_id="protein:P22222",
            cluster_id="cluster:001",
            representative_candidate_id="protein:P11111",
            representative=False,
            dropped=True,
            shared_sample_count=4,
            max_redundant_correlation=0.97,
            redundancy_reason_codes=(
                "high_signal_correlation",
                "lower_scoring_cluster_member",
            ),
            ranking_note="dropped in favor of the representative correlated marker",
        ),
    )
