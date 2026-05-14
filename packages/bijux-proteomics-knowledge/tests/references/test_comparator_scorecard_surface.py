# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_knowledge.references.workflows.benchmarks import (
    KnowledgeWorkflowFamily,
)
from bijux_proteomics_knowledge.references.workflows.comparator_scorecards import (
    build_workflow_comparator_scorecard,
    build_workflow_comparator_scorecard_report,
)


def test_comparator_scorecard_report_covers_each_workflow_family() -> None:
    report = build_workflow_comparator_scorecard_report()

    assert {entry.workflow_family for entry in report.entries} == set(
        KnowledgeWorkflowFamily
    )


def test_comparator_scorecard_keeps_multiplex_blocked_and_targeted_weaker_axes() -> (
    None
):
    multiplex = build_workflow_comparator_scorecard(KnowledgeWorkflowFamily.MULTIPLEX)
    targeted = build_workflow_comparator_scorecard(KnowledgeWorkflowFamily.TARGETED)

    assert "channel-level evidence" in multiplex.blocked_comparisons
    assert "calibration behavior" in targeted.worse_than_comparator
    assert "interference conclusions" in targeted.worse_than_comparator
