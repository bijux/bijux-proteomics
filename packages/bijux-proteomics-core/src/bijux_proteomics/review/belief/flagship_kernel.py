# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Flagship scientific-kernel reports over the bounded workflow chain."""

from __future__ import annotations

from enum import StrEnum

from pydantic import ConfigDict, Field, field_validator

from bijux_proteomics.domain.reason_codes import (
    ReasonCodeCategory,
    require_registered_reason_codes,
)
from bijux_proteomics.review.explanations.scientific_conflicts import (
    ScientificConflictReport,
    ScientificUntrustworthyChecklist,
    build_scientific_untrustworthy_checklists,
    evaluate_domain_conflicts,
)
from bijux_proteomics.review.explanations.scientific_story import (
    ScientificConsistencyReport,
    WorkflowScientificSnapshot,
    evaluate_workflow_scientific_consistency,
)
from bijux_proteomics_foundation import JsonModel


class ScientificCoverageBoundaryState(StrEnum):
    """How broadly a scientific capability may be described today."""

    SUPPORTED = "supported"
    BOUNDARY_ONLY = "boundary_only"
    REFUSED = "refused"


class ScientificCoverageBoundaryEntry(JsonModel):
    """One scientifically important capability boundary for the flagship workflow."""

    model_config = ConfigDict(extra="forbid")

    capability_id: str = Field(..., min_length=1)
    state: ScientificCoverageBoundaryState
    rationale: str = Field(..., min_length=1)
    blocking_for_broad_claims: bool


class FlagshipScientificKernelReport(JsonModel):
    """Scientific-kernel report for the bounded flagship workflow family."""

    model_config = ConfigDict(extra="forbid")

    workflow_id: str = Field(..., min_length=1)
    flagship_family_id: str = Field(..., min_length=1)
    artifact_path: str = Field(..., min_length=1)
    consistency: ScientificConsistencyReport
    conflicts: ScientificConflictReport
    untrustworthy_checklists: tuple[ScientificUntrustworthyChecklist, ...] = Field(
        default_factory=tuple
    )
    coverage_boundaries: tuple[ScientificCoverageBoundaryEntry, ...] = Field(
        default_factory=tuple
    )
    kernel_ready: bool
    blocked_reasons: tuple[str, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)

    @field_validator("blocked_reasons")
    @classmethod
    def _validate_blocked_reasons(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return require_registered_reason_codes(
            value,
            ReasonCodeCategory.WORKFLOW_BLOCK,
        )


def build_flagship_scientific_kernel_report(
    snapshot: WorkflowScientificSnapshot,
    *,
    artifact_path: str = "artifacts/workflows/flagship-workflow-chain/core/scientific_kernel.json",
    flagship_family_id: str = "flagship-workflows",
) -> FlagshipScientificKernelReport:
    """Build the narrow scientific-kernel report for the flagship workflow family."""

    if not artifact_path.startswith("artifacts/"):
        raise ValueError("artifact_path must live under artifacts/")

    consistency = evaluate_workflow_scientific_consistency(snapshot)
    conflicts = evaluate_domain_conflicts(snapshot)
    checklists = build_scientific_untrustworthy_checklists()
    boundaries = (
        ScientificCoverageBoundaryEntry(
            capability_id="glycopeptide_support",
            state=ScientificCoverageBoundaryState.BOUNDARY_ONLY,
            rationale=(
                "glycopeptide handling is still governed mainly through refusal and boundary language rather than full flagship proof"
            ),
            blocking_for_broad_claims=True,
        ),
        ScientificCoverageBoundaryEntry(
            capability_id="library_search_support",
            state=ScientificCoverageBoundaryState.BOUNDARY_ONLY,
            rationale=(
                "library-search behavior is still exposed as a scoped boundary, not a fully benchmarked flagship lane"
            ),
            blocking_for_broad_claims=True,
        ),
        ScientificCoverageBoundaryEntry(
            capability_id="external_engine_behavior",
            state=ScientificCoverageBoundaryState.BOUNDARY_ONLY,
            rationale=(
                "external-engine behavior remains a constrained compatibility and disagreement surface rather than broad scientific coverage"
            ),
            blocking_for_broad_claims=True,
        ),
    )

    blocked_reasons = [
        issue.code.value for issue in consistency.issues if issue.blocking
    ]
    blocked_reasons.extend(
        finding.code.value
        for finding in conflicts.findings
        if finding.blocks_decision_grade
    )
    blocked_reasons = list(dict.fromkeys(blocked_reasons))

    return FlagshipScientificKernelReport(
        workflow_id=snapshot.workflow_id,
        flagship_family_id=flagship_family_id,
        artifact_path=artifact_path,
        consistency=consistency,
        conflicts=conflicts,
        untrustworthy_checklists=checklists,
        coverage_boundaries=boundaries,
        kernel_ready=not blocked_reasons,
        blocked_reasons=tuple(blocked_reasons),
        note=(
            "The flagship scientific kernel proves one narrow workflow family. "
            "Broad coverage claims remain blocked while glycopeptide, library-search, and "
            "external-engine behavior stay at explicit boundary scope."
        ),
    )
