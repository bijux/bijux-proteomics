# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Requested-versus-observed learning artifacts for benchmark follow-up loops."""

from __future__ import annotations

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel
from bijux_proteomics_knowledge.references.workflows.benchmarks import (
    KnowledgeWorkflowFamily,
)
from bijux_proteomics_lab.reconciliation.follow_up import OperationalFollowUpPath

__all__ = [
    "BenchmarkFollowUpLearningArtifact",
    "build_benchmark_follow_up_learning_artifact",
]


class BenchmarkFollowUpLearningArtifact(JsonModel):
    """Concrete requested-versus-observed artifact from a benchmark follow-up loop."""

    model_config = ConfigDict(extra="forbid")

    artifact_id: str = Field(..., min_length=1)
    artifact_path: str = Field(..., min_length=1)
    benchmark_id: str = Field(..., min_length=1)
    workflow_family: KnowledgeWorkflowFamily
    candidate_id: str = Field(..., min_length=1)
    batch_id: str = Field(..., min_length=1)
    requested_assay_ids: tuple[str, ...] = Field(default_factory=tuple)
    observed_assay_ids: tuple[str, ...] = Field(default_factory=tuple)
    matched_assay_ids: tuple[str, ...] = Field(default_factory=tuple)
    missing_requested_assay_ids: tuple[str, ...] = Field(default_factory=tuple)
    unexpected_observed_assay_ids: tuple[str, ...] = Field(default_factory=tuple)
    blocked_assay_ids: tuple[str, ...] = Field(default_factory=tuple)
    weakened_assay_ids: tuple[str, ...] = Field(default_factory=tuple)
    promoted_evidence_ids: tuple[str, ...] = Field(default_factory=tuple)
    belief_posture: str = Field(..., min_length=1)
    recommended_action: str = Field(..., min_length=1)
    ready_for_feedback: bool
    learning_points: tuple[str, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


def _dedupe(values: list[str]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(values))


def build_benchmark_follow_up_learning_artifact(
    *,
    benchmark_id: str,
    workflow_family: KnowledgeWorkflowFamily,
    operational_path: OperationalFollowUpPath,
) -> BenchmarkFollowUpLearningArtifact:
    """Build one learning artifact from a benchmark-style operational follow-up path."""

    requested_assay_ids = tuple(operational_path.execution_request.requested_assay_ids)
    delta_by_assay_id = {
        delta.assay_id: delta for delta in operational_path.reconciliation.assay_deltas
    }
    observed_assay_ids = tuple(
        assay_id
        for assay_id in requested_assay_ids
        if delta_by_assay_id[assay_id].observed
    ) + tuple(
        delta.assay_id
        for delta in operational_path.reconciliation.assay_deltas
        if not delta.requested and delta.observed
    )
    matched_assay_ids = tuple(
        assay_id
        for assay_id in requested_assay_ids
        if delta_by_assay_id[assay_id].observed
    )
    missing_requested_assay_ids = tuple(
        assay_id
        for assay_id in requested_assay_ids
        if not delta_by_assay_id[assay_id].observed
    )
    unexpected_observed_assay_ids = tuple(
        delta.assay_id
        for delta in operational_path.reconciliation.assay_deltas
        if not delta.requested and delta.observed
    )
    feedback = operational_path.reconciliation.intelligence_feedback
    learning_points: list[str] = []
    if matched_assay_ids:
        learning_points.append(
            "matched assays show where the planned follow-up loop actually executed as designed"
        )
    if missing_requested_assay_ids:
        learning_points.append(
            "missing requested assays mark execution gaps that should block future promotion"
        )
    if unexpected_observed_assay_ids:
        learning_points.append(
            "unexpected observed assays reveal scope drift between plan and outcome"
        )
    if feedback.blocked_assay_ids:
        learning_points.append(
            "blocked assays must feed back into future lab planning instead of being hidden behind a successful batch headline"
        )
    if feedback.weakened_assay_ids:
        learning_points.append(
            "weakened assays show where the loop reduced belief instead of simply confirming the original story"
        )
    if operational_path.reconciliation.ready_for_feedback:
        learning_points.append(
            "the reconciliation is specific enough to adjust downstream recommendation posture"
        )

    return BenchmarkFollowUpLearningArtifact(
        artifact_id=f"benchmark_follow_up_learning:{workflow_family.value}",
        artifact_path=(
            "artifacts/lab/flagship-follow-up-learning/"
            f"{workflow_family.value}.json"
        ),
        benchmark_id=benchmark_id,
        workflow_family=workflow_family,
        candidate_id=operational_path.candidate_id,
        batch_id=operational_path.reconciliation.batch_id,
        requested_assay_ids=requested_assay_ids,
        observed_assay_ids=observed_assay_ids,
        matched_assay_ids=matched_assay_ids,
        missing_requested_assay_ids=missing_requested_assay_ids,
        unexpected_observed_assay_ids=unexpected_observed_assay_ids,
        blocked_assay_ids=feedback.blocked_assay_ids,
        weakened_assay_ids=feedback.weakened_assay_ids,
        promoted_evidence_ids=feedback.promoted_evidence_ids,
        belief_posture=operational_path.reconciliation.belief_posture,
        recommended_action=feedback.recommended_action,
        ready_for_feedback=operational_path.reconciliation.ready_for_feedback,
        learning_points=_dedupe(learning_points),
        note=(
            "This artifact keeps the requested-versus-observed benchmark loop inspectable so future lab planning can learn from outcomes instead of only planning the next packet."
        ),
    )
