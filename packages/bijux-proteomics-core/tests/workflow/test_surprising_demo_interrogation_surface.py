# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.workflow import (
    SurprisingDemoQueryKind,
    SurprisingDemoQueryStatus,
    build_surprising_demo_example_requests,
    build_surprising_demo_interrogation_report,
    ensure_surprising_demo_outputs,
    render_surprising_demo_interrogation_answers_tsv,
    render_surprising_demo_interrogation_summary_tsv,
)


def test_build_surprising_demo_interrogation_report_answers_all_shipped_examples(
    tmp_path: Path,
) -> None:
    demo_output_dir = tmp_path / "surprising_demo_query_run"
    ensure_surprising_demo_outputs(demo_output_dir)
    requests = build_surprising_demo_example_requests(demo_output_dir)

    report = build_surprising_demo_interrogation_report(demo_output_dir, requests)
    answers_by_kind = {answer.query_kind: answer for answer in report.answers}

    assert report.summary.query_count == 4
    assert report.summary.answered_query_count == 4
    assert report.summary.not_found_query_count == 0
    assert all(answer.status is SurprisingDemoQueryStatus.ANSWERED for answer in report.answers)
    assert "confidence_reasons" in render_surprising_demo_interrogation_answers_tsv(report)
    assert "answered_query_count" in render_surprising_demo_interrogation_summary_tsv(report)

    protein_answer = answers_by_kind[SurprisingDemoQueryKind.WHY_PROTEIN_CHANGED]
    assert protein_answer.subject_id == "P11111"
    assert "statistical_result:protein:control_vs_treated:P11111" in protein_answer.evidence_ids
    assert "biological_protein_cards:protein-card:P11111" in protein_answer.source_row_refs
    assert "evidence_tier:high_support" in protein_answer.confidence_reasons

    site_answer = answers_by_kind[SurprisingDemoQueryKind.WHY_SITE_AMBIGUOUS]
    assert site_answer.subject_id == "P11111:S17:Phospho"
    assert "P11111:Phospho:17|18|19" in site_answer.evidence_ids
    assert (
        "advanced_ptm_site_group_matrix:P11111:Phospho:17|18|19"
        in site_answer.source_row_refs
    )
    assert "excluded_from_exact_site_matrix" in site_answer.confidence_reasons
    assert "candidate_positions:17;18;19" in site_answer.confidence_reasons

    sample_answer = answers_by_kind[SurprisingDemoQueryKind.WHY_SAMPLE_FAILED]
    assert sample_answer.subject_id == "control_r1"
    assert "ACDMPEP/3" in sample_answer.evidence_ids
    assert "PEPTIDEK/2" in sample_answer.evidence_ids
    assert (
        "targeted_assay_qc_unreliable_targets:ACDMPEP/3:control_r1"
        in sample_answer.source_row_refs
    )
    assert any(
        reason.startswith("reason:fewer than two coeluting transitions")
        for reason in sample_answer.confidence_reasons
    )

    target_answer = answers_by_kind[SurprisingDemoQueryKind.WHAT_VALIDATES_TARGET]
    assert target_answer.subject_id == "protein:P001"
    assert "assay:P001:PEPTIDEK" in target_answer.evidence_ids
    assert (
        "targeted_validation_evidence:assay:P001:PEPTIDEK"
        in target_answer.source_row_refs
    )
    assert "validation_verdict:inconclusive" in target_answer.confidence_reasons
    assert "assay_reliability:unreliable" in target_answer.confidence_reasons
