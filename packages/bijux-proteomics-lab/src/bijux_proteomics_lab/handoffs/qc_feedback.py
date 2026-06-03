# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Typed lab-to-core run QC feedback handoff for scientific result downgrades."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence
from enum import StrEnum

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel
from bijux_proteomics_lab.outcomes.observations import (
    AssayObservationRecord,
    ObservationQualityProfile,
    QcState,
    assess_observation_quality,
)


class LabRunQcFeedbackStatus(StrEnum):
    """Stable run-level QC states exported from the lab package."""

    PASSED = "passed"
    CAUTION = "caution"
    FAILED = "failed"


class LabRunQcFeedbackReasonCode(StrEnum):
    """Stable reason codes explaining why run QC affects downstream confidence."""

    QC_FAILED = "qc_failed"
    QC_WARNING = "qc_warning"
    LOW_REPRODUCIBILITY = "low_reproducibility"
    LOW_INTERPRETABILITY = "low_interpretability"
    BELOW_DETECTION_LIMIT = "below_detection_limit"
    BATCH_EFFECT = "batch_effect"


class LabRunQcObservation(JsonModel):
    """One assay observation scoped to the run it should govern downstream."""

    model_config = ConfigDict(extra="forbid")

    run_id: str = Field(..., min_length=1)
    sample_id: str = Field(..., min_length=1)
    observation: AssayObservationRecord


class LabRunQcFeedbackEntry(JsonModel):
    """One run-level QC feedback decision exported for downstream scientific graphs."""

    model_config = ConfigDict(extra="forbid")

    run_id: str = Field(..., min_length=1)
    sample_id: str = Field(..., min_length=1)
    status: LabRunQcFeedbackStatus
    composite_quality: float = Field(..., ge=0.0, le=1.0)
    supporting_assay_ids: tuple[str, ...] = Field(default_factory=tuple)
    supporting_metrics: tuple[str, ...] = Field(default_factory=tuple)
    reason_codes: tuple[LabRunQcFeedbackReasonCode, ...] = Field(default_factory=tuple)
    source_refs: tuple[str, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


class LabRunQcFeedbackReport(JsonModel):
    """Typed run-level QC handoff consumed by downstream scientific workflows."""

    model_config = ConfigDict(extra="forbid")

    entries: tuple[LabRunQcFeedbackEntry, ...] = Field(default_factory=tuple)
    passed_count: int = Field(..., ge=0)
    caution_count: int = Field(..., ge=0)
    failed_count: int = Field(..., ge=0)
    note: str = Field(..., min_length=1)


def build_lab_run_qc_feedback_report(
    observations: tuple[LabRunQcObservation, ...],
) -> LabRunQcFeedbackReport:
    """Summarize assay observations into run-level QC feedback for core workflows."""

    grouped: dict[str, list[LabRunQcObservation]] = defaultdict(list)
    for observation in observations:
        grouped[observation.run_id].append(observation)

    entries: list[LabRunQcFeedbackEntry] = []
    for run_id in sorted(grouped):
        scoped = grouped[run_id]
        sample_ids = {item.sample_id for item in scoped}
        if len(sample_ids) != 1:
            raise ValueError(
                f"run qc feedback requires one sample per run handoff: {run_id}"
            )
        sample_id = next(iter(sample_ids))
        assay_ids = sorted({item.observation.assay_id for item in scoped})
        metrics = sorted(
            {
                f"{item.observation.assay_id}:{item.observation.metric}"
                for item in scoped
            }
        )
        quality_profiles = [
            assess_observation_quality(item.observation) for item in scoped
        ]
        reason_codes = _reason_codes_for_run(scoped, quality_profiles)
        status = _status_for_run(scoped)
        entries.append(
            LabRunQcFeedbackEntry(
                run_id=run_id,
                sample_id=sample_id,
                status=status,
                composite_quality=min(
                    profile.composite_quality for profile in quality_profiles
                ),
                supporting_assay_ids=tuple(assay_ids),
                supporting_metrics=tuple(metrics),
                reason_codes=reason_codes,
                source_refs=tuple(
                    sorted(
                        f"lab_qc:{run_id}:{item.observation.assay_id}:{item.observation.metric}"
                        for item in scoped
                    )
                ),
                note=_build_run_note(run_id, status, assay_ids, reason_codes),
            )
        )

    return LabRunQcFeedbackReport(
        entries=tuple(entries),
        passed_count=sum(
            1 for entry in entries if entry.status is LabRunQcFeedbackStatus.PASSED
        ),
        caution_count=sum(
            1 for entry in entries if entry.status is LabRunQcFeedbackStatus.CAUTION
        ),
        failed_count=sum(
            1 for entry in entries if entry.status is LabRunQcFeedbackStatus.FAILED
        ),
        note=(
            "lab run qc feedback condenses assay-level qc observations into one typed "
            "run-level contract so downstream scientific workflows can downgrade "
            "confidence consistently"
        ),
    )


def _status_for_run(
    observations: list[LabRunQcObservation],
) -> LabRunQcFeedbackStatus:
    if any(
        item.observation.qc_state is QcState.FAILED or not item.observation.qc_passed
        for item in observations
    ):
        return LabRunQcFeedbackStatus.FAILED
    if any(item.observation.qc_state is QcState.WARNING for item in observations):
        return LabRunQcFeedbackStatus.CAUTION
    return LabRunQcFeedbackStatus.PASSED


def _reason_codes_for_run(
    observations: list[LabRunQcObservation],
    quality_profiles: Sequence[ObservationQualityProfile],
) -> tuple[LabRunQcFeedbackReasonCode, ...]:
    reasons: set[LabRunQcFeedbackReasonCode] = set()
    if any(
        item.observation.qc_state is QcState.FAILED or not item.observation.qc_passed
        for item in observations
    ):
        reasons.add(LabRunQcFeedbackReasonCode.QC_FAILED)
    if any(item.observation.qc_state is QcState.WARNING for item in observations):
        reasons.add(LabRunQcFeedbackReasonCode.QC_WARNING)
    if any((item.observation.dispersion or 0.0) >= 0.25 for item in observations):
        reasons.add(LabRunQcFeedbackReasonCode.LOW_REPRODUCIBILITY)
    if any(item.observation.below_detection_limit for item in observations):
        reasons.add(LabRunQcFeedbackReasonCode.BELOW_DETECTION_LIMIT)
    if any(item.observation.batch_effect_note for item in observations):
        reasons.add(LabRunQcFeedbackReasonCode.BATCH_EFFECT)
    if any(profile.interpretability < 0.6 for profile in quality_profiles):
        reasons.add(LabRunQcFeedbackReasonCode.LOW_INTERPRETABILITY)
    return tuple(sorted(reasons, key=lambda reason: reason.value))


def _build_run_note(
    run_id: str,
    status: LabRunQcFeedbackStatus,
    assay_ids: list[str],
    reason_codes: tuple[LabRunQcFeedbackReasonCode, ...],
) -> str:
    assay_summary = ", ".join(assay_ids)
    if not reason_codes:
        return (
            f"lab QC marks run {run_id} as {status.value} across assays {assay_summary}"
        )
    reason_summary = ", ".join(reason.value for reason in reason_codes)
    return (
        f"lab QC marks run {run_id} as {status.value} across assays {assay_summary} "
        f"because {reason_summary}"
    )
