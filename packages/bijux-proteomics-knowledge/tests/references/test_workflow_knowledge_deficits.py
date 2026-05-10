# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_knowledge.references.workflows.benchmarks import (
    KnowledgeWorkflowFamily,
)
from bijux_proteomics_knowledge.references.workflows.knowledge_deficits import (
    KnowledgeDeficitSeverity,
    build_workflow_knowledge_deficit_report,
    list_workflow_knowledge_deficit_reports,
)


def test_workflow_knowledge_deficit_reports_cover_each_family() -> None:
    reports = list_workflow_knowledge_deficit_reports()

    assert {report.workflow_family for report in reports} == set(KnowledgeWorkflowFamily)


def test_workflow_knowledge_deficit_report_exposes_all_gap_planes() -> None:
    report = build_workflow_knowledge_deficit_report(KnowledgeWorkflowFamily.DIA)

    assert report.public_data_gaps == ()
    assert report.comparator_gaps
    assert report.literature_gaps
    assert report.runtime_proof_gaps
    assert "scientific base" in report.note.lower()


def test_workflow_knowledge_deficit_report_marks_targeted_gap_as_release_blocking() -> (
    None
):
    report = build_workflow_knowledge_deficit_report(KnowledgeWorkflowFamily.TARGETED)

    assert report.highest_severity is KnowledgeDeficitSeverity.HIGH
    assert any("Skyline" in item.closure_condition or "comparator" in item.closure_condition for item in report.comparator_gaps)


def test_dda_knowledge_deficit_report_no_longer_claims_curated_mini_study_gap() -> None:
    report = build_workflow_knowledge_deficit_report(KnowledgeWorkflowFamily.DDA)

    assert report.public_data_gaps == ()
