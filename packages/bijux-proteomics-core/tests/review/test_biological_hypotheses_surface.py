# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.review.biological_hypotheses import (
    BiologicalHypothesisCandidate,
    BiologicalHypothesisKind,
    BiologicalHypothesisRejectionReason,
    build_biological_hypothesis_report,
    render_biological_hypothesis_tsv,
    render_rejected_biological_hypothesis_candidate_tsv,
)


def test_biological_hypothesis_report_requires_evidence_node_ids() -> None:
    report = build_biological_hypothesis_report(
        (
            BiologicalHypothesisCandidate(
                hypothesis_id="protein-hypothesis:P04637",
                hypothesis_kind=BiologicalHypothesisKind.PROTEIN_MECHANISM,
                subject_id="P04637",
                subject_label="TP53",
                claim="TP53 decreased in treatment vs control",
                supporting_protein_refs=("P04637",),
                evidence_node_ids=(
                    "protein:P04637",
                    "statistical_result:protein:control_vs_treatment:P04637",
                ),
                base_confidence_score=0.78,
                source_ids=("protein-mechanism-card:P04637",),
                note="graph-backed protein mechanism support",
            ),
            BiologicalHypothesisCandidate(
                hypothesis_id="pathway-hypothesis:custom:response",
                hypothesis_kind=BiologicalHypothesisKind.PATHWAY_ACTIVITY,
                subject_id="custom:response",
                subject_label="Stress response",
                claim="Stress response pathway activated in treatment vs control",
                supporting_protein_refs=("P04637", "O14920"),
                supporting_pathway_ids=("custom:response",),
                base_confidence_score=0.71,
                source_ids=("pathway-activity:custom:response",),
                note="pathway candidate without graph node ids",
            ),
        )
    )

    assert report.summary.candidate_count == 2
    assert report.summary.hypothesis_count == 1
    assert report.summary.rejected_candidate_count == 1
    assert report.hypotheses[0].evidence_node_ids == (
        "protein:P04637",
        "statistical_result:protein:control_vs_treatment:P04637",
    )
    assert (
        report.rejected_candidates[0].rejection_reason
        is BiologicalHypothesisRejectionReason.MISSING_EVIDENCE_NODE_IDS
    )


def test_biological_hypothesis_report_preserves_support_opposition_and_suggestions() -> (
    None
):
    report = build_biological_hypothesis_report(
        (
            BiologicalHypothesisCandidate(
                hypothesis_id="regulator-hypothesis:MAPK14",
                hypothesis_kind=BiologicalHypothesisKind.REGULATOR_ACTIVITY,
                subject_id="MAPK14",
                subject_label="MAPK14",
                claim="Kinase MAPK14 active in treatment vs control",
                supporting_protein_refs=("P04637",),
                supporting_site_keys=("P04637:S15:Phospho",),
                opposing_evidence=("limited peptide support",),
                evidence_node_ids=(
                    "protein:P04637",
                    "statistical_result:protein:control_vs_treatment:P04637",
                ),
                base_confidence_score=0.74,
                source_ids=(
                    "regulator-claim:MAPK14:kinase_substrate:site_regulation",
                    "protein-mechanism-card:P04637",
                ),
                note="site-supported regulator hypothesis",
            ),
        )
    )

    assert report.summary.high_confidence_hypothesis_count == 1
    hypothesis = report.hypotheses[0]
    assert hypothesis.confidence_score > 0.8
    assert hypothesis.supporting_site_keys == ("P04637:S15:Phospho",)
    assert hypothesis.opposing_evidence == ("limited peptide support",)
    assert "targeted phosphopeptide assay" in hypothesis.next_experiment_suggestion
    assert "evidence_node_ids" in render_biological_hypothesis_tsv(report)
    assert "rejection_reason" in render_rejected_biological_hypothesis_candidate_tsv(
        report
    )
