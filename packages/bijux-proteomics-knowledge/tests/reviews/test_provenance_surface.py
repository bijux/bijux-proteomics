# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_knowledge.references.workflows.benchmarks import (
    KnowledgeWorkflowFamily,
)
from bijux_proteomics_knowledge.reviews.provenance import (
    ReferenceDisagreementSeverity,
    build_reference_disagreement_report,
    build_workflow_contradiction_stress_suite,
)


def test_build_reference_disagreement_report_surfaces_workflow_scope_pressure() -> None:
    report = build_reference_disagreement_report(KnowledgeWorkflowFamily.LFQ)

    assert report.workflow_family is KnowledgeWorkflowFamily.LFQ
    assert report.entries
    assert all(
        entry.benchmark_id == "benchmark:lfq_quantification_repeatability"
        for entry in report.entries
    )
    assert all(entry.downgrade_reason for entry in report.entries)
    assert any(
        entry.severity is ReferenceDisagreementSeverity.HIGH for entry in report.entries
    )


def test_build_workflow_contradiction_stress_suite_requires_bounded_grounding() -> (
    None
):
    suite = build_workflow_contradiction_stress_suite(KnowledgeWorkflowFamily.TARGETED)

    assert suite.workflow_family is KnowledgeWorkflowFamily.TARGETED
    assert suite.entries
    assert all(
        entry.expected_grounding_state == "bounded_by_contradiction"
        for entry in suite.entries
    )
    assert all(entry.downgrade_reason for entry in suite.entries)
