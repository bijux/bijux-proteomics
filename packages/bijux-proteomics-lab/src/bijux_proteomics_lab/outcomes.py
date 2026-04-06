# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Experiment outcome and rerun contracts."""

from __future__ import annotations

from enum import StrEnum

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import AssayId, BatchId, JsonModel
from bijux_proteomics_knowledge import (
    EvidenceKind,
    EvidenceSourceType,
    EvidenceStrength,
    NormalizedEvidenceInput,
)


class FailureClass(StrEnum):
    """Failure classes for assay and batch execution."""

    TECHNICAL = "technical"
    BIOLOGICAL = "biological"
    MATERIAL = "material"
    INTERPRETATION = "interpretation"


class RerunPolicy(StrEnum):
    """Rerun recommendation after an outcome is observed."""

    NEVER = "never"
    ON_TECHNICAL_FAILURE = "on_technical_failure"
    ON_INCONCLUSIVE_RESULT = "on_inconclusive_result"


class AssayCategory(StrEnum):
    """Taxonomy of assay roles in the lab workflow."""

    BINDING = "binding"
    ACTIVITY = "activity"
    STABILITY = "stability"
    DEVELOPABILITY = "developability"


class AcceptanceOperator(StrEnum):
    """Operator used to judge an assay observation."""

    GREATER_EQUAL = "greater_equal"
    LESS_EQUAL = "less_equal"


class AssayAcceptanceRule(JsonModel):
    """Acceptance threshold for one assay metric."""

    model_config = ConfigDict(extra="forbid")

    assay_id: AssayId = Field(..., description="Assay identifier.")
    metric: str = Field(..., min_length=1, description="Metric to evaluate.")
    operator: AcceptanceOperator = Field(..., description="Threshold operator.")
    threshold: float = Field(..., description="Acceptance threshold.")
    unit: str | None = Field(default=None, description="Expected unit of measure.")


class AssayDefinition(JsonModel):
    """Definition of an assay and how its output should be judged."""

    model_config = ConfigDict(extra="forbid")

    assay_id: AssayId = Field(..., description="Assay identifier.")
    category: AssayCategory = Field(..., description="Taxonomy category.")
    purpose: str = Field(..., min_length=1, description="Why the assay exists.")
    acceptance_rule: AssayAcceptanceRule = Field(
        ...,
        description="Acceptance contract for the assay output.",
    )


class AssayOutcome(JsonModel):
    """Observed result for one assay in a batch."""

    model_config = ConfigDict(extra="forbid")

    assay_id: AssayId = Field(..., description="Assay identifier.")
    passed: bool = Field(..., description="Whether the assay met acceptance.")
    observation_summary: str = Field(
        ...,
        min_length=1,
        description="Human-readable summary of the outcome.",
    )
    failure_class: FailureClass | None = Field(
        default=None,
        description="Failure class when the assay does not pass.",
    )


class ExperimentOutcome(JsonModel):
    """Outcome for a scheduled experiment batch."""

    model_config = ConfigDict(extra="forbid")

    batch_id: BatchId = Field(..., description="Batch identifier.")
    assay_outcomes: list[AssayOutcome] = Field(
        default_factory=list,
        description="Per-assay outcomes for the batch.",
    )
    rerun_policy: RerunPolicy = Field(..., description="Recommended rerun policy.")


class AssayObservationRecord(JsonModel):
    """Observed measurement that can be evaluated against an assay definition."""

    model_config = ConfigDict(extra="forbid")

    assay_id: AssayId = Field(..., description="Assay identifier.")
    metric: str = Field(..., min_length=1, description="Observed metric.")
    value: float = Field(..., description="Observed value.")
    unit: str | None = Field(default=None, description="Observed unit.")


def recommend_rerun_policy(outcome: ExperimentOutcome) -> RerunPolicy:
    """Recommend a rerun policy from observed failures."""
    if any(
        assay.failure_class is FailureClass.TECHNICAL
        for assay in outcome.assay_outcomes
        if not assay.passed
    ):
        return RerunPolicy.ON_TECHNICAL_FAILURE
    if any(not assay.passed for assay in outcome.assay_outcomes):
        return RerunPolicy.ON_INCONCLUSIVE_RESULT
    return RerunPolicy.NEVER


def evaluate_assay_acceptance(
    definition: AssayDefinition,
    observation: AssayObservationRecord,
) -> AssayOutcome:
    """Evaluate one observation against the assay acceptance contract."""
    rule = definition.acceptance_rule
    if observation.assay_id != definition.assay_id:
        raise ValueError("assay observation does not match the assay definition")
    if observation.metric != rule.metric:
        raise ValueError("assay observation metric does not match the acceptance rule")

    passed = (
        observation.value >= rule.threshold
        if rule.operator is AcceptanceOperator.GREATER_EQUAL
        else observation.value <= rule.threshold
    )
    summary = (
        f"{observation.metric}={observation.value:g}"
        f"{observation.unit or ''} {'met' if passed else 'missed'} "
        f"{rule.operator.value} {rule.threshold:g}{rule.unit or ''}"
    )
    return AssayOutcome(
        assay_id=observation.assay_id,
        passed=passed,
        observation_summary=summary,
        failure_class=None if passed else FailureClass.BIOLOGICAL,
    )


def promote_outcome_to_evidence(
    outcome: AssayOutcome,
    *,
    target_id: str,
    batch_id: str,
) -> NormalizedEvidenceInput:
    """Convert one assay outcome into normalized evidence for knowledge ingestion."""
    return NormalizedEvidenceInput(
        evidence_id=f"assay:{batch_id}:{outcome.assay_id}",
        kind=EvidenceKind.ASSAY,
        title=f"Assay outcome {outcome.assay_id}",
        source=f"lab-batch:{batch_id}",
        source_type=EvidenceSourceType.LAB_ASSAY,
        claim=outcome.observation_summary,
        related_targets=[target_id],
        decision_tags=["progression"],
        confidence=0.9 if outcome.passed else 0.5,
        strength=EvidenceStrength.DECISIVE if outcome.passed else EvidenceStrength.EXPLORATORY,
    )
