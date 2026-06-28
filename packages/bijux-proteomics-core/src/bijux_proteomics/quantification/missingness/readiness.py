# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Decision-readiness surfaces for quantitative proteomics outputs."""

from __future__ import annotations

from enum import StrEnum

from pydantic import ConfigDict, Field

from bijux_proteomics.domain.reason_codes import (
    ReasonCodeCategory,
    require_registered_reason_codes,
)
from bijux_proteomics.io.formats import ExperimentalDesignEntry
from bijux_proteomics.quantification.contracts.matrix_models import LabelFreeQuantTable
from bijux_proteomics.quantification.contracts.study_qc import (
    build_batch_effect_advisory,
    build_replicate_correlation_report,
)
from bijux_proteomics.study import build_replicate_structure_report
from bijux_proteomics_foundation.serialization.json_contracts import JsonModel


class BatchEffectDecisionPosture(StrEnum):
    """How strongly batch behavior constrains quantitative interpretation."""

    SUPPORTED = "supported"
    REVIEW_GRADE_ONLY = "review_grade_only"
    BLOCKED = "blocked"


class QuantDecisionReadinessState(StrEnum):
    """Decision-readiness state for quantitative outputs."""

    DECISION_GRADE = "decision_grade"
    REVIEW_GRADE = "review_grade"
    BLOCKED = "blocked"


class QuantDecisionBlockingReasonCode(StrEnum):
    """Stable blockers that prevent decision-grade quantitative interpretation."""

    INSUFFICIENT_REPLICATES = "insufficient_replicates"
    BATCH_CONDITION_CONFOUNDING = "confounded_batch_condition"
    MULTI_BATCH_SHIFT = "multi_batch_shift"


class QuantDecisionAdvisoryReasonCode(StrEnum):
    """Stable advisories that downgrade quantitative interpretation to review grade."""

    BATCH_SHIFT_WARNING = "batch_shift_warning"
    WITHIN_CONDITION_REPLICATE_INSTABILITY = "within_condition_replicate_instability"


class ReplicateStructureEntry(JsonModel):
    """Replicate support for one condition inside a quantitative design."""

    model_config = ConfigDict(extra="forbid")

    condition: str = Field(..., min_length=1)
    replicate_count: int = Field(..., ge=0)
    biological_replicate_count: int = Field(..., ge=0)
    technical_replicate_count: int = Field(..., ge=0)
    injection_replicate_count: int = Field(..., ge=0)
    fractionated_sample_count: int = Field(..., ge=0)
    multiplex_channel_count: int = Field(..., ge=0)
    repeated_measure_subject_count: int = Field(..., ge=0)
    underpowered: bool


class ReplicateStructureAuditReport(JsonModel):
    """Replicate-structure audit that distinguishes coverage from decision strength."""

    model_config = ConfigDict(extra="forbid")

    entries: tuple[ReplicateStructureEntry, ...] = Field(default_factory=tuple)
    minimum_replicates_per_condition: int = Field(..., ge=1)
    balanced: bool
    underpowered_conditions: tuple[str, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


class QuantDecisionReadinessReport(JsonModel):
    """Quantitative decision-readiness with explicit replicate and batch constraints."""

    model_config = ConfigDict(extra="forbid")

    readiness_state: QuantDecisionReadinessState
    batch_effect_posture: BatchEffectDecisionPosture
    replicate_audit: ReplicateStructureAuditReport
    flagged_batch_count: int = Field(..., ge=0)
    low_correlation_pair_count: int = Field(..., ge=0)
    blocking_reasons: tuple[QuantDecisionBlockingReasonCode, ...] = Field(
        default_factory=tuple
    )
    advisory_reasons: tuple[QuantDecisionAdvisoryReasonCode, ...] = Field(
        default_factory=tuple
    )
    note: str = Field(..., min_length=1)


def build_replicate_structure_audit_report(
    design_entries: tuple[ExperimentalDesignEntry, ...],
    *,
    minimum_replicates_per_condition: int = 2,
) -> ReplicateStructureAuditReport:
    """Audit whether a quantitative design has enough replicate structure to travel."""

    structure_report = build_replicate_structure_report(
        design_entries,
        minimum_statistical_units_per_condition=minimum_replicates_per_condition,
    )
    entries = tuple(
        ReplicateStructureEntry(
            condition=entry.condition,
            replicate_count=entry.effective_statistical_unit_count,
            biological_replicate_count=entry.biological_replicate_count,
            technical_replicate_count=entry.technical_replicate_count,
            injection_replicate_count=entry.injection_replicate_count,
            fractionated_sample_count=entry.fractionated_sample_count,
            multiplex_channel_count=entry.multiplex_channel_count,
            repeated_measure_subject_count=entry.repeated_measure_subject_count,
            underpowered=entry.underpowered_for_statistics,
        )
        for entry in structure_report.condition_entries
    )
    replicate_counts = [entry.replicate_count for entry in entries]
    underpowered = tuple(entry.condition for entry in entries if entry.underpowered)
    balanced = len(set(replicate_counts)) <= 1 if replicate_counts else True
    note = (
        "replicate structure satisfies the current minimum policy after separating biological support from technical, fractionated, multiplexed, and repeated-measure structure"
        if not underpowered
        else "one or more conditions remain underpowered for decision-grade quantitative claims after technical, injection, fraction, multiplex, and repeated-measure structure are separated from statistical units"
    )
    return ReplicateStructureAuditReport(
        entries=entries,
        minimum_replicates_per_condition=minimum_replicates_per_condition,
        balanced=balanced,
        underpowered_conditions=underpowered,
        note=note,
    )


def build_quant_decision_readiness_report(
    table: LabelFreeQuantTable,
    *,
    design_entries: tuple[ExperimentalDesignEntry, ...],
    minimum_replicates_per_condition: int = 2,
    within_condition_warning_threshold: float = 0.8,
    batch_shift_threshold: float = 0.5,
    blocking_batch_count: int = 2,
) -> QuantDecisionReadinessReport:
    """Turn quantitative QC into a decision-readiness posture rather than passive caveats."""

    replicate_audit = build_replicate_structure_audit_report(
        design_entries,
        minimum_replicates_per_condition=minimum_replicates_per_condition,
    )
    replicate_report = build_replicate_correlation_report(table, design_entries)
    low_correlation_pair_count = sum(
        1
        for entry in replicate_report.entries
        if entry.condition_a == entry.condition_b
        and entry.correlation < within_condition_warning_threshold
    )
    batch_report = build_batch_effect_advisory(
        table,
        design_entries,
        shift_threshold=batch_shift_threshold,
    )
    flagged_batch_count = sum(1 for entry in batch_report.batches if entry.flagged)
    blocking_reasons: list[QuantDecisionBlockingReasonCode] = []
    advisory_reasons: list[QuantDecisionAdvisoryReasonCode] = []
    if replicate_audit.underpowered_conditions:
        blocking_reasons.append(QuantDecisionBlockingReasonCode.INSUFFICIENT_REPLICATES)
    if batch_report.batch_correction_blocked:
        blocking_reasons.append(
            QuantDecisionBlockingReasonCode.BATCH_CONDITION_CONFOUNDING
        )
    if flagged_batch_count >= blocking_batch_count:
        blocking_reasons.append(QuantDecisionBlockingReasonCode.MULTI_BATCH_SHIFT)
    elif batch_report.batch_warning is not None:
        advisory_reasons.append(QuantDecisionAdvisoryReasonCode.BATCH_SHIFT_WARNING)
    if low_correlation_pair_count > 0:
        advisory_reasons.append(
            QuantDecisionAdvisoryReasonCode.WITHIN_CONDITION_REPLICATE_INSTABILITY
        )

    if blocking_reasons:
        readiness_state = QuantDecisionReadinessState.BLOCKED
        batch_effect_posture = BatchEffectDecisionPosture.BLOCKED
    elif advisory_reasons:
        readiness_state = QuantDecisionReadinessState.REVIEW_GRADE
        batch_effect_posture = BatchEffectDecisionPosture.REVIEW_GRADE_ONLY
    else:
        readiness_state = QuantDecisionReadinessState.DECISION_GRADE
        batch_effect_posture = BatchEffectDecisionPosture.SUPPORTED
    note = (
        "quantitative output can support decision-grade claims"
        if readiness_state is QuantDecisionReadinessState.DECISION_GRADE
        else "quantitative output remains below decision-grade authority and should be treated as review-grade or blocked"
    )
    return QuantDecisionReadinessReport(
        readiness_state=readiness_state,
        batch_effect_posture=batch_effect_posture,
        replicate_audit=replicate_audit,
        flagged_batch_count=flagged_batch_count,
        low_correlation_pair_count=low_correlation_pair_count,
        blocking_reasons=tuple(
            QuantDecisionBlockingReasonCode(code)
            for code in require_registered_reason_codes(
                tuple(reason.value for reason in blocking_reasons),
                ReasonCodeCategory.WORKFLOW_BLOCK,
            )
        ),
        advisory_reasons=tuple(
            QuantDecisionAdvisoryReasonCode(code)
            for code in require_registered_reason_codes(
                tuple(reason.value for reason in advisory_reasons),
                ReasonCodeCategory.WORKFLOW_ADVISORY,
            )
        ),
        note=note,
    )


__all__ = [
    "BatchEffectDecisionPosture",
    "QuantDecisionAdvisoryReasonCode",
    "QuantDecisionBlockingReasonCode",
    "QuantDecisionReadinessReport",
    "QuantDecisionReadinessState",
    "ReplicateStructureAuditReport",
    "ReplicateStructureEntry",
    "build_quant_decision_readiness_report",
    "build_replicate_structure_audit_report",
]
