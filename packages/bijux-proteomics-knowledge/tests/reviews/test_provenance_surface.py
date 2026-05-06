# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_knowledge.references.workflows.benchmarks import (
    KnowledgeWorkflowFamily,
)
from bijux_proteomics_knowledge.reviews.provenance import (
    ReferenceDisagreementSeverity,
    build_reference_disagreement_report,
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
