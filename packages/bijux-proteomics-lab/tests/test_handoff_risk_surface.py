# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_lab import (
    AssayRiskCode,
    TransitionReviewDisposition,
    TargetedTransitionCandidate,
    assess_assay_risk,
    review_targeted_transition_candidates,
)


def test_assess_assay_risk_flags_scientific_and_operational_failure_modes() -> None:
    assessment = assess_assay_risk(
        assay_id="prm-panel",
        peptide_uniqueness_score=0.62,
        localization_probability=0.71,
        quant_reproducibility_score=0.58,
        assay_feasibility_score=0.49,
        predicted_failure_risk=0.66,
    )

    assert assessment.supported_for_follow_up is False
    assert assessment.overall_risk_score > 0.45
    assert {finding.code for finding in assessment.findings} == {
        AssayRiskCode.WEAK_PEPTIDE_UNIQUENESS,
        AssayRiskCode.POOR_LOCALIZATION,
        AssayRiskCode.WEAK_QUANT_REPRODUCIBILITY,
        AssayRiskCode.LIKELY_ASSAY_FAILURE,
    }


def test_review_targeted_transition_candidates_uses_feasibility_and_controls() -> None:
    review = review_targeted_transition_candidates(
        assay_id="prm-panel",
        available_controls=("pooled-reference", "retention-time-standard"),
        candidates=(
            TargetedTransitionCandidate(
                transition_id="tr-good",
                peptide_sequence="PEPTIDER",
                precursor_mz=456.2,
                product_mz=789.3,
                peptide_uniqueness_score=0.92,
                localization_probability=0.96,
                quant_reproducibility_score=0.89,
                assay_feasibility_score=0.82,
                predicted_failure_risk=0.11,
                required_controls=("pooled-reference",),
            ),
            TargetedTransitionCandidate(
                transition_id="tr-exploratory",
                peptide_sequence="PEPTIDEK",
                precursor_mz=512.3,
                product_mz=660.2,
                peptide_uniqueness_score=0.8,
                localization_probability=0.88,
                quant_reproducibility_score=0.68,
                assay_feasibility_score=0.61,
                predicted_failure_risk=0.35,
                required_controls=("pooled-reference", "heavy-standard"),
            ),
            TargetedTransitionCandidate(
                transition_id="tr-refused",
                peptide_sequence="NONUNIQUE",
                precursor_mz=533.1,
                product_mz=701.4,
                peptide_uniqueness_score=0.55,
                localization_probability=0.66,
                quant_reproducibility_score=0.45,
                assay_feasibility_score=0.41,
                predicted_failure_risk=0.72,
                required_controls=("heavy-standard",),
            ),
        ),
    )

    assert review.approved_transition_ids == ("tr-good",)
    assert review.exploratory_transition_ids == ("tr-exploratory",)
    assert review.refused_transition_ids == ("tr-refused",)
    assert review.readiness_score == 0.3333
    exploratory_entry = next(
        entry for entry in review.entries if entry.transition_id == "tr-exploratory"
    )
    assert exploratory_entry.disposition is TransitionReviewDisposition.EXPLORATORY
    assert exploratory_entry.missing_controls == ("heavy-standard",)
