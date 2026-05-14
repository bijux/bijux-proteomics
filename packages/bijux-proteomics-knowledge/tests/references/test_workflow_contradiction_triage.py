# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_knowledge.references.workflows.benchmarks import (
    KnowledgeWorkflowFamily,
)
from bijux_proteomics_knowledge.references.workflows.contradiction_triage import (
    ContradictionConsequenceLevel,
    build_workflow_contradiction_triage_report,
    list_workflow_contradiction_triage_reports,
)


def test_workflow_contradiction_triage_reports_cover_each_family() -> None:
    reports = list_workflow_contradiction_triage_reports()

    assert {report.workflow_family for report in reports} == set(
        KnowledgeWorkflowFamily
    )


def test_workflow_contradiction_triage_ranks_highest_consequence_first() -> None:
    report = build_workflow_contradiction_triage_report(
        KnowledgeWorkflowFamily.TARGETED
    )

    assert report.entries
    assert report.entries[0].scientific_rank == 1
    assert (
        report.entries[0].consequence_level
        is ContradictionConsequenceLevel.RELEASE_BLOCKING
    )
    assert report.entries[0].evidence_refs
    assert "release language" in report.note
