# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Known comparator wins and losses tied to flagship workflow confrontations."""

from __future__ import annotations

from enum import StrEnum

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation.serialization.json_contracts import JsonModel
from bijux_proteomics_knowledge.references.workflows.benchmarks import (
    KnowledgeWorkflowFamily,
)
from bijux_proteomics_knowledge.references.workflows.comparator_confrontations import (
    ComparatorConfrontationOutcome,
    build_workflow_comparator_confrontation_report,
)


class ComparatorPositionKind(StrEnum):
    """Whether the position is a known win or a known loss."""

    KNOWN_LOSS = "known_loss"
    KNOWN_WIN = "known_win"


class ComparatorPositionEntry(JsonModel):
    """One explicit scientific situation where the repo wins or loses."""

    model_config = ConfigDict(extra="forbid")

    position_id: str = Field(..., min_length=1)
    kind: ComparatorPositionKind
    workflow_family: KnowledgeWorkflowFamily
    benchmark_id: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1)
    current_position: str = Field(..., min_length=1)
    evidence_refs: tuple[str, ...] = Field(default_factory=tuple)
    follow_through_backlog_goal: str = Field(..., min_length=1)


class ComparatorPositionReport(JsonModel):
    """Known comparator wins and losses across workflow families."""

    model_config = ConfigDict(extra="forbid")

    entries: tuple[ComparatorPositionEntry, ...] = Field(default_factory=tuple)


def build_comparator_position_report() -> ComparatorPositionReport:
    """Build explicit known wins and losses from the workflow confrontations."""

    entries: list[ComparatorPositionEntry] = []
    confrontations = build_workflow_comparator_confrontation_report().entries
    for confrontation in confrontations:
        for index, finding in enumerate(confrontation.findings, start=1):
            if finding.outcome is ComparatorConfrontationOutcome.REPO_WEAKER:
                entries.append(
                    ComparatorPositionEntry(
                        position_id=f"comparator_position:{confrontation.workflow_family.value}:loss:{index}",
                        kind=ComparatorPositionKind.KNOWN_LOSS,
                        workflow_family=confrontation.workflow_family,
                        benchmark_id=confrontation.benchmark_id,
                        title=f"{confrontation.workflow_family.value} loses on {finding.axis}",
                        current_position=finding.scientific_difference,
                        evidence_refs=(
                            confrontation.confrontation_id,
                            finding.finding_id,
                        ),
                        follow_through_backlog_goal=confrontation.next_escalation,
                    )
                )
            if finding.outcome is ComparatorConfrontationOutcome.REPO_STRICTER:
                entries.append(
                    ComparatorPositionEntry(
                        position_id=f"comparator_position:{confrontation.workflow_family.value}:win:{index}",
                        kind=ComparatorPositionKind.KNOWN_WIN,
                        workflow_family=confrontation.workflow_family,
                        benchmark_id=confrontation.benchmark_id,
                        title=f"{confrontation.workflow_family.value} is stricter on {finding.axis}",
                        current_position=finding.scientific_difference,
                        evidence_refs=(
                            confrontation.confrontation_id,
                            finding.finding_id,
                        ),
                        follow_through_backlog_goal="keep the stronger downgrade and provenance behavior visible while harder public benchmark packages are built",
                    )
                )
    return ComparatorPositionReport(entries=tuple(entries))


__all__ = [
    "ComparatorPositionEntry",
    "ComparatorPositionKind",
    "ComparatorPositionReport",
    "build_comparator_position_report",
]
