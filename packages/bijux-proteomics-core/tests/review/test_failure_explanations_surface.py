# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.review import (
    FailureExplanationCategory,
    FailureExplanationRequest,
    FailureExplanationStatus,
    build_failure_explanation_report,
    format_failure_explanation_for_cli,
    render_failure_explanation_tsv,
)


def test_failure_explanation_engine_distinguishes_expected_scientific_failures() -> (
    None
):
    report = build_failure_explanation_report(
        (
            FailureExplanationRequest(
                failure_id="schema",
                workflow_name="spectronaut-import",
                failure_text="Spectronaut schema error: export must include a header row",
            ),
            FailureExplanationRequest(
                failure_id="design",
                workflow_name="biological-report",
                failure_text="design table contains rejected rows",
            ),
            FailureExplanationRequest(
                failure_id="evidence",
                workflow_name="result-question-answer",
                failure_text="no PTM differential row matched site_key 'P11111:S5:Phospho'",
            ),
            FailureExplanationRequest(
                failure_id="statistics",
                workflow_name="biological-report",
                failure_text="design matrix is confounded or rank-deficient; aliased columns: batch, condition",
            ),
            FailureExplanationRequest(
                failure_id="annotation",
                workflow_name="pathway-enrichment",
                failure_text="protein lacks gene annotation required for gene-based pathway memberships",
            ),
        )
    )

    assert report.summary.explanation_count == 5
    assert report.summary.explained_count == 5
    assert report.summary.schema_error_count == 1
    assert report.summary.invalid_design_count == 1
    assert report.summary.insufficient_evidence_count == 1
    assert report.summary.statistical_impossibility_count == 1
    assert report.summary.missing_annotation_count == 1

    by_id = {entry.failure_id: entry for entry in report.explanations}
    assert by_id["schema"].failure_category is FailureExplanationCategory.SCHEMA_ERROR
    assert by_id["design"].failure_category is FailureExplanationCategory.INVALID_DESIGN
    assert (
        by_id["evidence"].failure_category
        is FailureExplanationCategory.INSUFFICIENT_EVIDENCE
    )
    assert (
        by_id["statistics"].failure_category
        is FailureExplanationCategory.STATISTICAL_IMPOSSIBILITY
    )
    assert (
        by_id["annotation"].failure_category
        is FailureExplanationCategory.MISSING_ANNOTATION
    )
    assert by_id["design"].status is FailureExplanationStatus.EXPLAINED
    assert "fix input" in format_failure_explanation_for_cli(by_id["design"]).lower()
    assert "scientific_condition_code" in render_failure_explanation_tsv(report)


def test_failure_explanation_engine_refuses_to_invent_unknown_categories() -> None:
    report = build_failure_explanation_report(
        (
            FailureExplanationRequest(
                failure_id="unknown",
                workflow_name="custom-workflow",
                failure_text="workflow stopped after an unexpected ledger merge mismatch",
            ),
        )
    )

    explanation = report.explanations[0]
    assert explanation.status is FailureExplanationStatus.UNCLASSIFIED
    assert explanation.failure_category is None
    assert (
        "did not match a known scientific category"
        in format_failure_explanation_for_cli(explanation)
    )
