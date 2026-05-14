# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Per-family comparator scorecards built from flagship confrontation reports."""

from __future__ import annotations

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation.serialization.json_contracts import JsonModel
from bijux_proteomics_knowledge.references.workflows.benchmarks import (
    KnowledgeWorkflowFamily,
)
from bijux_proteomics_knowledge.references.workflows.comparator_confrontations import (
    ComparatorConfrontationOutcome,
    build_workflow_comparator_confrontation,
)


class WorkflowComparatorScorecard(JsonModel):
    """One workflow-family scorecard summarizing confrontation posture."""

    model_config = ConfigDict(extra="forbid")

    workflow_family: KnowledgeWorkflowFamily
    benchmark_id: str = Field(..., min_length=1)
    comparator_tool: str = Field(..., min_length=1)
    better_than_comparator: tuple[str, ...] = Field(default_factory=tuple)
    worse_than_comparator: tuple[str, ...] = Field(default_factory=tuple)
    stricter_than_comparator: tuple[str, ...] = Field(default_factory=tuple)
    blocked_comparisons: tuple[str, ...] = Field(default_factory=tuple)
    scorecard_summary: str = Field(..., min_length=1)


class WorkflowComparatorScorecardReport(JsonModel):
    """Scorecards across workflow benchmark families."""

    model_config = ConfigDict(extra="forbid")

    entries: tuple[WorkflowComparatorScorecard, ...] = Field(default_factory=tuple)


def build_workflow_comparator_scorecard(
    workflow_family: KnowledgeWorkflowFamily,
) -> WorkflowComparatorScorecard:
    """Build the scorecard for one workflow family."""

    confrontation = build_workflow_comparator_confrontation(workflow_family)
    better_than = tuple(
        finding.axis
        for finding in confrontation.findings
        if finding.outcome is ComparatorConfrontationOutcome.ALIGNED
    )
    worse_than = tuple(
        finding.axis
        for finding in confrontation.findings
        if finding.outcome is ComparatorConfrontationOutcome.REPO_WEAKER
    )
    stricter_than = tuple(
        finding.axis
        for finding in confrontation.findings
        if finding.outcome is ComparatorConfrontationOutcome.REPO_STRICTER
    )
    blocked = tuple(
        finding.axis
        for finding in confrontation.findings
        if finding.outcome is ComparatorConfrontationOutcome.BLOCKED
    )
    return WorkflowComparatorScorecard(
        workflow_family=workflow_family,
        benchmark_id=confrontation.benchmark_id,
        comparator_tool=confrontation.comparator_tool.value,
        better_than_comparator=better_than,
        worse_than_comparator=worse_than,
        stricter_than_comparator=stricter_than,
        blocked_comparisons=blocked,
        scorecard_summary=confrontation.overall_conclusion,
    )


def build_workflow_comparator_scorecard_report() -> WorkflowComparatorScorecardReport:
    """Build scorecards across all workflow families with confrontations."""

    return WorkflowComparatorScorecardReport(
        entries=tuple(
            build_workflow_comparator_scorecard(workflow_family)
            for workflow_family in KnowledgeWorkflowFamily
        )
    )


__all__ = [
    "WorkflowComparatorScorecard",
    "WorkflowComparatorScorecardReport",
    "build_workflow_comparator_scorecard",
    "build_workflow_comparator_scorecard_report",
]
