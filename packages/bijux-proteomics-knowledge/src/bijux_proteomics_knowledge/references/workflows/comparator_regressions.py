# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Regression baselines for flagship workflow comparator confrontations."""

from __future__ import annotations

from enum import StrEnum

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation.serialization.json_contracts import JsonModel
from bijux_proteomics_knowledge.references.workflows.benchmarks import (
    KnowledgeWorkflowFamily,
)
from bijux_proteomics_knowledge.references.workflows.comparator_confrontations import (
    build_workflow_comparator_confrontation_report,
)


class ComparatorRegressionStatus(StrEnum):
    """Whether comparator posture improved, worsened, or stayed stable."""

    IMPROVED = "improved"
    WORSENED = "worsened"
    UNCHANGED = "unchanged"


class WorkflowComparatorRegressionEntry(JsonModel):
    """One workflow-family comparator regression checkpoint."""

    model_config = ConfigDict(extra="forbid")

    workflow_family: KnowledgeWorkflowFamily
    benchmark_id: str = Field(..., min_length=1)
    comparison_baseline: str = Field(..., min_length=1)
    status: ComparatorRegressionStatus
    reason: str = Field(..., min_length=1)
    watchpoints: tuple[str, ...] = Field(default_factory=tuple)
    evidence_refs: tuple[str, ...] = Field(default_factory=tuple)


class WorkflowComparatorRegressionReport(JsonModel):
    """Regression checkpoints across workflow-family comparator confrontations."""

    model_config = ConfigDict(extra="forbid")

    entries: tuple[WorkflowComparatorRegressionEntry, ...] = Field(
        default_factory=tuple
    )


def build_workflow_comparator_regression_report() -> WorkflowComparatorRegressionReport:
    """Build the first shipped regression baseline for comparator confrontations."""

    entries = tuple(
        WorkflowComparatorRegressionEntry(
            workflow_family=confrontation.workflow_family,
            benchmark_id=confrontation.benchmark_id,
            comparison_baseline="first shipped confrontation baseline",
            status=ComparatorRegressionStatus.UNCHANGED,
            reason=(
                "This tranche establishes the first explicit comparator regression baseline; "
                "later code changes should move this entry to improved or worsened only when "
                "the confrontation findings themselves change."
            ),
            watchpoints=tuple(finding.axis for finding in confrontation.findings),
            evidence_refs=(
                confrontation.confrontation_id,
                *confrontation.artifact_refs,
            ),
        )
        for confrontation in build_workflow_comparator_confrontation_report().entries
    )
    return WorkflowComparatorRegressionReport(entries=entries)


__all__ = [
    "ComparatorRegressionStatus",
    "WorkflowComparatorRegressionEntry",
    "WorkflowComparatorRegressionReport",
    "build_workflow_comparator_regression_report",
]
