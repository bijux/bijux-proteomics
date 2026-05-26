# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.review import (
    BiologicalClaimCandidate,
    BiologicalClaimDirection,
    BiologicalClaimKind,
    BiologicalClaimValidationPolicy,
    build_biological_claim_validation_report,
)
from bijux_proteomics.review.evidence_graph_confidence import (
    EvidenceGraphConfidenceTier,
)
from bijux_proteomics.review.evidence_graph_downgrades import FinalClaimEvidenceTier


def test_biological_claim_validation_supports_only_directional_and_robust_claims() -> (
    None
):
    report = build_biological_claim_validation_report(
        (
            BiologicalClaimCandidate(
                claim_id="protein-claim:P11111",
                claim_kind=BiologicalClaimKind.PROTEIN_ABUNDANCE_CHANGE,
                subject_id="P11111",
                subject_label="TP53",
                claim_text="Protein TP53 decreased in treatment vs control",
                condition_a="control",
                condition_b="treatment",
                asserted_direction=BiologicalClaimDirection.DOWN,
                significant=True,
                adjusted_p_value=0.01,
                effect_size=1.4,
                robustness_score=0.82,
                evidence_tier=FinalClaimEvidenceTier.HIGH_CONFIDENCE,
                confidence_tier=EvidenceGraphConfidenceTier.HIGH,
                source_ids=("protein-mechanism-card:P11111", "statistical_result:P11111"),
                source_row_refs=("protein_stats.tsv:4", "protein_matrix.tsv:4"),
                note="strong protein decrease",
            ),
            BiologicalClaimCandidate(
                claim_id="pathway-claim:R-HSA-1",
                claim_kind=BiologicalClaimKind.PATHWAY_ACTIVITY_CHANGE,
                subject_id="R-HSA-1",
                subject_label="Stress response",
                claim_text="Pathway Stress response activated in treatment vs control",
                condition_a="control",
                condition_b="treatment",
                asserted_direction=BiologicalClaimDirection.UP,
                effect_size=0.64,
                pathway_confidence_status="high_confidence",
                pathway_delta=0.64,
                source_ids=("pathway-activity:R-HSA-1",),
                derived_no_source_reason=(
                    "pathway activity claims aggregate governed pathway activity comparisons rather than preserving one direct input row"
                ),
                note="directional pathway activation",
            ),
            BiologicalClaimCandidate(
                claim_id="regulator-claim:MAPK14",
                claim_kind=BiologicalClaimKind.REGULATOR_ACTIVITY,
                subject_id="MAPK14",
                subject_label="MAPK14",
                claim_text="Kinase MAPK14 active in treatment vs control",
                condition_a="control",
                condition_b="treatment",
                asserted_direction=BiologicalClaimDirection.UP,
                regulator_evidence_type="kinase_substrate",
                regulator_signal_surface="site_regulation",
                regulator_score=0.77,
                source_ids=("regulator-inference:MAPK14",),
                derived_no_source_reason=(
                    "regulator activity claims aggregate governed upstream-target evidence and downstream signal surfaces rather than preserving one direct input row"
                ),
                note="substrate direction supports kinase activity",
            ),
            BiologicalClaimCandidate(
                claim_id="protein-claim:P22222",
                claim_kind=BiologicalClaimKind.PROTEIN_ABUNDANCE_CHANGE,
                subject_id="P22222",
                subject_label="AKT1",
                claim_text="Protein AKT1 decreased in treatment vs control",
                condition_a="control",
                condition_b="treatment",
                asserted_direction=BiologicalClaimDirection.DOWN,
                significant=True,
                adjusted_p_value=0.03,
                effect_size=1.1,
                robustness_score=0.32,
                imputation_dependent=True,
                evidence_tier=FinalClaimEvidenceTier.WEAK,
                confidence_tier=EvidenceGraphConfidenceTier.LOW,
                source_ids=("protein-mechanism-card:P22222",),
                source_row_refs=("protein_stats.tsv:7",),
                note="weak protein decrease",
            ),
            BiologicalClaimCandidate(
                claim_id="pathway-claim:R-HSA-2",
                claim_kind=BiologicalClaimKind.PATHWAY_ACTIVITY_CHANGE,
                subject_id="R-HSA-2",
                subject_label="DNA repair",
                claim_text="Pathway DNA repair activated in treatment vs control",
                condition_a="control",
                condition_b="treatment",
                asserted_direction=BiologicalClaimDirection.UP,
                effect_size=0.08,
                pathway_confidence_status="low_confidence",
                pathway_delta=0.08,
                source_ids=("pathway-activity:R-HSA-2",),
                derived_no_source_reason=(
                    "pathway activity claims aggregate governed pathway activity comparisons rather than preserving one direct input row"
                ),
                note="weak pathway change",
            ),
            BiologicalClaimCandidate(
                claim_id="regulator-claim:MAPK1",
                claim_kind=BiologicalClaimKind.REGULATOR_ACTIVITY,
                subject_id="MAPK1",
                subject_label="MAPK1",
                claim_text="Kinase MAPK1 active in treatment vs control",
                condition_a="control",
                condition_b="treatment",
                asserted_direction=BiologicalClaimDirection.UP,
                regulator_evidence_type="kinase_substrate",
                regulator_signal_surface="protein_abundance",
                regulator_score=0.72,
                source_ids=("regulator-inference:MAPK1",),
                derived_no_source_reason=(
                    "regulator activity claims aggregate governed upstream-target evidence and downstream signal surfaces rather than preserving one direct input row"
                ),
                note="kinase should not validate from abundance only",
            ),
        ),
        policy=BiologicalClaimValidationPolicy(
            max_adjusted_p_value=0.1,
            min_robustness_score=0.55,
            min_pathway_activity_delta=0.2,
            min_regulator_score=0.55,
        ),
    )

    supported_ids = {entry.claim_id for entry in report.supported_claims}
    rejected_by_id = {entry.claim_id: entry for entry in report.rejected_claims}

    assert supported_ids == {
        "protein-claim:P11111",
        "pathway-claim:R-HSA-1",
        "regulator-claim:MAPK14",
    }
    assert report.summary.supported_claim_count == 3
    assert report.summary.rejected_claim_count == 3
    assert "low_robustness" in {
        reason.value for reason in rejected_by_id["protein-claim:P22222"].reason_codes
    }
    assert "imputation_dependent" in {
        reason.value for reason in rejected_by_id["protein-claim:P22222"].reason_codes
    }
    assert "low_pathway_confidence" in {
        reason.value for reason in rejected_by_id["pathway-claim:R-HSA-2"].reason_codes
    }
    assert "kinase_requires_site_surface" in {
        reason.value for reason in rejected_by_id["regulator-claim:MAPK1"].reason_codes
    }
    supported_by_id = {entry.claim_id: entry for entry in report.supported_claims}
    assert supported_by_id["protein-claim:P11111"].source_row_refs
    assert (
        supported_by_id["pathway-claim:R-HSA-1"].derived_no_source_reason is not None
    )


def test_biological_claim_validation_rejects_non_significant_protein_claims() -> None:
    report = build_biological_claim_validation_report(
        (
            BiologicalClaimCandidate(
                claim_id="protein-claim:P33333",
                claim_kind=BiologicalClaimKind.PROTEIN_ABUNDANCE_CHANGE,
                subject_id="P33333",
                subject_label="STAT3",
                claim_text="Protein STAT3 increased in treatment vs control",
                condition_a="control",
                condition_b="treatment",
                asserted_direction=BiologicalClaimDirection.UP,
                significant=False,
                adjusted_p_value=0.22,
                effect_size=0.9,
                robustness_score=0.74,
                evidence_tier=FinalClaimEvidenceTier.MODERATE,
                confidence_tier=EvidenceGraphConfidenceTier.MODERATE,
                source_ids=("protein-mechanism-card:P33333",),
                source_row_refs=("protein_stats.tsv:12",),
                note="nominal but not significant",
            ),
        )
    )

    assert not report.supported_claims
    assert report.rejected_claims[0].claim_id == "protein-claim:P33333"
    assert report.rejected_claims[0].status.value == "rejected"
    assert "not_significant" in {
        reason.value for reason in report.rejected_claims[0].reason_codes
    }
    assert report.rejected_claims[0].source_row_refs == ("protein_stats.tsv:12",)
