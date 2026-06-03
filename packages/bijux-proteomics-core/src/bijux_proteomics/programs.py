# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Package-level program contract for companion packages and workflow clients."""

from __future__ import annotations

from pydantic import ConfigDict, Field

from bijux_proteomics.domain.criteria import (
    MeasurementDirection,
    MetricFamily,
    SuccessCriterion,
)
from bijux_proteomics.domain.program_spec import (
    EvidenceNeed,
    ProgramSpec,
    ProgramStage,
    StageEligibility,
    assess_stage_eligibility,
    create_program_spec,
    program_summary,
    revise_program,
)
from bijux_proteomics.domain.targets import (
    OutcomeSeverity,
    ProteinTarget,
    TargetAnnotation,
    TargetOutcome,
    target_summary,
)
from bijux_proteomics_foundation import JsonModel


class ProgramBrief(JsonModel):
    """Review-ready summary over one program and its target context."""

    model_config = ConfigDict(extra="forbid")

    program_id: str = Field(..., min_length=1, description="Stable program identifier.")
    stage: ProgramStage
    objective: str = Field(..., min_length=1, description="Program objective.")
    target_id: str = Field(..., min_length=1, description="Stable target identifier.")
    target_name: str = Field(
        ..., min_length=1, description="Human-readable target name."
    )
    measurement_metrics: tuple[str, ...] = Field(
        default_factory=tuple,
        description="Ordered measurement metrics named by the program criteria.",
    )
    maximize_metrics: tuple[str, ...] = Field(
        default_factory=tuple,
        description="Metrics whose direction is maximize.",
    )
    minimize_metrics: tuple[str, ...] = Field(
        default_factory=tuple,
        description="Metrics whose direction is minimize.",
    )
    blocked_outcome_codes: tuple[str, ...] = Field(
        default_factory=tuple,
        description="High-signal blocked outcome codes carried by the target.",
    )
    evidence_needs: tuple[str, ...] = Field(
        default_factory=tuple,
        description="Evidence families that must be covered for the program.",
    )


def list_program_measurement_metrics(program: ProgramSpec) -> tuple[str, ...]:
    """Return the ordered unique measurement metrics required by one program."""
    metrics: list[str] = []
    seen: set[str] = set()
    for criterion in program.success_criteria:
        if criterion.metric not in seen:
            seen.add(criterion.metric)
            metrics.append(criterion.metric)
    return tuple(metrics)


def build_program_brief(program: ProgramSpec) -> ProgramBrief:
    """Build a compact review-ready brief for one program."""
    target_context = target_summary(program.target)
    maximize_metrics = tuple(
        criterion.metric
        for criterion in program.success_criteria
        if criterion.direction is MeasurementDirection.MAXIMIZE
    )
    minimize_metrics = tuple(
        criterion.metric
        for criterion in program.success_criteria
        if criterion.direction is MeasurementDirection.MINIMIZE
    )
    blocked_code_values = target_context.get("high_risk_block_codes", ())
    if isinstance(blocked_code_values, (list, tuple)):
        blocked_outcome_codes = tuple(
            code for code in blocked_code_values if isinstance(code, str)
        )
    else:
        blocked_outcome_codes = ()
    return ProgramBrief(
        program_id=program.program_id,
        stage=program.stage,
        objective=program.objective,
        target_id=program.target.target_id,
        target_name=program.target.name,
        measurement_metrics=list_program_measurement_metrics(program),
        maximize_metrics=maximize_metrics,
        minimize_metrics=minimize_metrics,
        blocked_outcome_codes=blocked_outcome_codes,
        evidence_needs=tuple(need.value for need in program.evidence_needs),
    )


__all__ = [
    "EvidenceNeed",
    "MeasurementDirection",
    "MetricFamily",
    "OutcomeSeverity",
    "ProgramBrief",
    "ProgramSpec",
    "ProgramStage",
    "ProteinTarget",
    "StageEligibility",
    "SuccessCriterion",
    "TargetAnnotation",
    "TargetOutcome",
    "assess_stage_eligibility",
    "build_program_brief",
    "create_program_spec",
    "list_program_measurement_metrics",
    "program_summary",
    "revise_program",
    "target_summary",
]
