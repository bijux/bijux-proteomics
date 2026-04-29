# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Experiment-design and protocol planning helpers."""

from __future__ import annotations

from collections import Counter, defaultdict
from enum import StrEnum
import math
from random import Random
from statistics import NormalDist

from pydantic import ConfigDict, Field

from bijux_proteomics import ExperimentalDesignEntry
from bijux_proteomics_foundation import DocumentSchema, JsonModel


class DesignIssueSeverity(StrEnum):
    """Severity tier for experiment-design validation."""

    WARN = "warn"
    FAIL = "fail"


class ContrastRejectionReason(StrEnum):
    """Reason a proposed contrast is not valid yet."""

    INSUFFICIENT_REPLICATES = "insufficient_replicates"
    BATCH_CONFOUNDED = "batch_confounded"
    SINGLE_CONDITION = "single_condition"


class MultiplexChannelRole(StrEnum):
    """Role assigned to one multiplex channel."""

    SAMPLE = "sample"
    POOLED_REFERENCE = "pooled_reference"
    QC_BRIDGE = "qc_bridge"


class CarryoverRiskLevel(StrEnum):
    """Severity level for one run-order transition."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class SamplePreparationMetadata(JsonModel):
    """Sample-preparation context that should travel with lab planning."""

    model_config = ConfigDict(extra="forbid")

    protocol_id: str = Field(..., min_length=1)
    digestion_protocol: str = Field(..., min_length=1)
    cleanup_method: str = Field(..., min_length=1)
    fractionation_strategy: str | None = None
    labeling_strategy: str | None = None
    enrichment_strategy: str | None = None
    spike_in_strategy: str | None = None
    operator: str | None = None
    notes: tuple[str, ...] = Field(default_factory=tuple)


class InstrumentMethodMetadata(JsonModel):
    """Instrument-method context required for reviewable execution plans."""

    model_config = ConfigDict(extra="forbid")

    method_id: str = Field(..., min_length=1)
    instrument: str = Field(..., min_length=1)
    acquisition_mode: str = Field(..., min_length=1)
    gradient_minutes: float = Field(..., gt=0.0)
    ms1_resolution: int = Field(..., ge=1)
    ms2_resolution: int | None = Field(default=None, ge=1)
    collision_energy: float = Field(..., gt=0.0)
    fragmentation_method: str = Field(default="HCD", min_length=1)
    isolation_window_mz: float | None = Field(default=None, gt=0.0)
    ion_mobility_enabled: bool = False
    notes: tuple[str, ...] = Field(default_factory=tuple)


class ExperimentDesignValidationIssue(JsonModel):
    """One actionable design-validation issue."""

    model_config = ConfigDict(extra="forbid")

    code: str = Field(..., min_length=1)
    severity: DesignIssueSeverity
    summary: str = Field(..., min_length=1)
    sample_ids: tuple[str, ...] = Field(default_factory=tuple)
    conditions: tuple[str, ...] = Field(default_factory=tuple)


class ContrastRecommendation(JsonModel):
    """One proposed pairwise contrast and its validity state."""

    model_config = ConfigDict(extra="forbid")

    condition_a: str = Field(..., min_length=1)
    condition_b: str = Field(..., min_length=1)
    valid: bool
    replicate_counts: dict[str, int] = Field(default_factory=dict)
    shared_batches: tuple[str, ...] = Field(default_factory=tuple)
    rejection_reasons: tuple[ContrastRejectionReason, ...] = Field(default_factory=tuple)
    rationale: str = Field(..., min_length=1)


class ExperimentDesignValidationReport(JsonModel):
    """Validation and contrast-readiness report for one design table."""

    model_config = ConfigDict(extra="forbid")

    document_schema: DocumentSchema = Field(
        default_factory=lambda: DocumentSchema(created_by="bijux-proteomics-lab")
    )
    sample_count: int = Field(..., ge=0)
    condition_count: int = Field(..., ge=0)
    fraction_count: int = Field(..., ge=0)
    valid_contrasts: tuple[ContrastRecommendation, ...] = Field(default_factory=tuple)
    rejected_contrasts: tuple[ContrastRecommendation, ...] = Field(default_factory=tuple)
    issues: tuple[ExperimentDesignValidationIssue, ...] = Field(default_factory=tuple)
    interpretation_summary: str = Field(..., min_length=1)


class PowerAnalysisAdvisory(JsonModel):
    """Advisory power-analysis estimate for a two-condition comparison."""

    model_config = ConfigDict(extra="forbid")

    condition_a: str = Field(..., min_length=1)
    condition_b: str = Field(..., min_length=1)
    current_replicates: dict[str, int] = Field(default_factory=dict)
    standardized_effect_size: float = Field(..., gt=0.0)
    target_power: float = Field(..., gt=0.0, lt=1.0)
    alpha: float = Field(..., gt=0.0, lt=1.0)
    estimated_power: float = Field(..., ge=0.0, le=1.0)
    recommended_replicates_per_condition: int = Field(..., ge=2)
    advisory_summary: str = Field(..., min_length=1)


class RandomizedRunSlot(JsonModel):
    """One run-order slot after batch randomization."""

    model_config = ConfigDict(extra="forbid")

    order_index: int = Field(..., ge=1)
    sample_id: str = Field(..., min_length=1)
    condition: str = Field(..., min_length=1)
    batch: str | None = None
    fraction: int = Field(..., ge=1)


class BatchRandomizationPlan(JsonModel):
    """Deterministic run order that balances conditions within batches."""

    model_config = ConfigDict(extra="forbid")

    seed: int = Field(..., ge=0)
    slot_count: int = Field(..., ge=0)
    slots: tuple[RandomizedRunSlot, ...] = Field(default_factory=tuple)
    condition_counts: dict[str, int] = Field(default_factory=dict)
    notes: tuple[str, ...] = Field(default_factory=tuple)


class FractionAssignment(JsonModel):
    """Fraction-level run assignment for one sample."""

    model_config = ConfigDict(extra="forbid")

    sample_id: str = Field(..., min_length=1)
    condition: str = Field(..., min_length=1)
    fraction: int = Field(..., ge=1)
    run_label: str = Field(..., min_length=1)
    spectra_file: str = Field(..., min_length=1)


class FractionationPlan(JsonModel):
    """Deterministic plan linking samples, fractions, and run labels."""

    model_config = ConfigDict(extra="forbid")

    sample_count: int = Field(..., ge=0)
    total_fraction_count: int = Field(..., ge=0)
    assignments: tuple[FractionAssignment, ...] = Field(default_factory=tuple)
    notes: tuple[str, ...] = Field(default_factory=tuple)


class MultiplexChannelAssignment(JsonModel):
    """One sample-to-channel assignment in a multiplexed design."""

    model_config = ConfigDict(extra="forbid")

    channel: str = Field(..., min_length=1)
    role: MultiplexChannelRole
    sample_id: str | None = None
    condition: str | None = None
    batch: str | None = None


class MultiplexLabelingPlan(JsonModel):
    """Balanced channel assignment for multiplex labeling experiments."""

    model_config = ConfigDict(extra="forbid")

    plex_size: int = Field(..., ge=1)
    assignments: tuple[MultiplexChannelAssignment, ...] = Field(default_factory=tuple)
    condition_channel_counts: dict[str, int] = Field(default_factory=dict)
    balanced: bool
    notes: tuple[str, ...] = Field(default_factory=tuple)


class SpikeInQcInsertion(JsonModel):
    """One inserted QC or spike-in slot."""

    model_config = ConfigDict(extra="forbid")

    order_index: int = Field(..., ge=1)
    sample_id: str = Field(..., min_length=1)
    role: str = Field(..., min_length=1)


class SpikeInQcSamplePlan(JsonModel):
    """Run order with periodic QC and optional spike-in insertions."""

    model_config = ConfigDict(extra="forbid")

    base_run_count: int = Field(..., ge=0)
    expanded_run_order: tuple[str, ...] = Field(default_factory=tuple)
    insertions: tuple[SpikeInQcInsertion, ...] = Field(default_factory=tuple)
    notes: tuple[str, ...] = Field(default_factory=tuple)


class CarryoverRiskFlag(JsonModel):
    """One flagged transition with likely carryover pressure."""

    model_config = ConfigDict(extra="forbid")

    preceding_sample_id: str = Field(..., min_length=1)
    following_sample_id: str = Field(..., min_length=1)
    preceding_tier: str = Field(..., min_length=1)
    following_tier: str = Field(..., min_length=1)
    risk_level: CarryoverRiskLevel
    rationale: str = Field(..., min_length=1)


class CarryoverRiskAdvisory(JsonModel):
    """Advisory report over run-order carryover exposure."""

    model_config = ConfigDict(extra="forbid")

    total_transitions: int = Field(..., ge=0)
    flagged_transitions: tuple[CarryoverRiskFlag, ...] = Field(default_factory=tuple)
    interpretation_summary: str = Field(..., min_length=1)


class LabProtocolEvidenceBundle(JsonModel):
    """Reviewable evidence bundle for lab protocol intent and planning."""

    model_config = ConfigDict(extra="forbid")

    document_schema: DocumentSchema = Field(
        default_factory=lambda: DocumentSchema(created_by="bijux-proteomics-lab")
    )
    bundle_id: str = Field(..., min_length=1)
    sample_preparation: SamplePreparationMetadata
    instrument_method: InstrumentMethodMetadata
    design_validation: ExperimentDesignValidationReport
    randomization_plan: BatchRandomizationPlan
    fractionation_plan: FractionationPlan
    multiplex_plan: MultiplexLabelingPlan | None = None
    qc_plan: SpikeInQcSamplePlan | None = None
    carryover_advisory: CarryoverRiskAdvisory | None = None


def _replicate_counts(entries: tuple[ExperimentalDesignEntry, ...]) -> dict[str, int]:
    return dict(Counter(entry.condition for entry in entries))


def _shared_batches(
    left_entries: list[ExperimentalDesignEntry],
    right_entries: list[ExperimentalDesignEntry],
) -> tuple[str, ...]:
    left_batches = {entry.batch for entry in left_entries if entry.batch}
    right_batches = {entry.batch for entry in right_entries if entry.batch}
    return tuple(sorted((left_batches & right_batches)))


def validate_experiment_design(
    entries: tuple[ExperimentalDesignEntry, ...],
    *,
    min_replicates: int = 2,
) -> ExperimentDesignValidationReport:
    """Validate design structure and pairwise contrast readiness."""
    issues: list[ExperimentDesignValidationIssue] = []
    conditions = sorted({entry.condition for entry in entries})
    grouped: dict[str, list[ExperimentalDesignEntry]] = defaultdict(list)
    duplicate_tracker: dict[tuple[str, int], list[str]] = defaultdict(list)
    per_sample_batches: dict[str, set[str]] = defaultdict(set)
    for entry in entries:
        grouped[entry.condition].append(entry)
        duplicate_tracker[(entry.sample_id, entry.fraction)].append(entry.spectra_file)
        if entry.batch:
            per_sample_batches[entry.sample_id].add(entry.batch)
    for (sample_id, fraction), files in sorted(duplicate_tracker.items()):
        if len(files) > 1:
            issues.append(
                ExperimentDesignValidationIssue(
                    code="duplicate-sample-fraction",
                    severity=DesignIssueSeverity.FAIL,
                    summary=(
                        f"sample {sample_id!r} fraction {fraction} appears more than once in the design."
                    ),
                    sample_ids=(sample_id,),
                )
            )
    for sample_id, batches in sorted(per_sample_batches.items()):
        if len(batches) > 1:
            issues.append(
                ExperimentDesignValidationIssue(
                    code="sample-across-batches",
                    severity=DesignIssueSeverity.WARN,
                    summary=f"sample {sample_id!r} spans multiple batches: {', '.join(sorted(batches))}.",
                    sample_ids=(sample_id,),
                )
            )
    if len(conditions) < 2:
        issues.append(
            ExperimentDesignValidationIssue(
                code="single-condition",
                severity=DesignIssueSeverity.FAIL,
                summary="design requires at least two conditions for contrast analysis.",
                conditions=tuple(conditions),
            )
        )
    valid_contrasts: list[ContrastRecommendation] = []
    rejected_contrasts: list[ContrastRecommendation] = []
    for index, left in enumerate(conditions):
        for right in conditions[index + 1 :]:
            left_entries = grouped[left]
            right_entries = grouped[right]
            shared_batches = _shared_batches(left_entries, right_entries)
            reasons: list[ContrastRejectionReason] = []
            if len(left_entries) < min_replicates or len(right_entries) < min_replicates:
                reasons.append(ContrastRejectionReason.INSUFFICIENT_REPLICATES)
            left_batches = {entry.batch for entry in left_entries if entry.batch}
            right_batches = {entry.batch for entry in right_entries if entry.batch}
            if left_batches and right_batches and not shared_batches:
                reasons.append(ContrastRejectionReason.BATCH_CONFOUNDED)
            recommendation = ContrastRecommendation(
                condition_a=left,
                condition_b=right,
                valid=not reasons,
                replicate_counts={left: len(left_entries), right: len(right_entries)},
                shared_batches=shared_batches,
                rejection_reasons=tuple(reasons),
                rationale=(
                    "replicates and batch overlap support the contrast"
                    if not reasons
                    else ", ".join(reason.value for reason in reasons)
                ),
            )
            if recommendation.valid:
                valid_contrasts.append(recommendation)
            else:
                rejected_contrasts.append(recommendation)
                for reason in reasons:
                    issues.append(
                        ExperimentDesignValidationIssue(
                            code=f"contrast-{reason.value}",
                            severity=(
                                DesignIssueSeverity.FAIL
                                if reason is ContrastRejectionReason.BATCH_CONFOUNDED
                                else DesignIssueSeverity.WARN
                            ),
                            summary=(
                                f"contrast {left!r} vs {right!r} is rejected because {reason.value}."
                            ),
                            conditions=(left, right),
                        )
                    )
    condition_summary = ", ".join(
        f"{condition}={count}" for condition, count in sorted(_replicate_counts(entries).items())
    ) or "no conditions"
    return ExperimentDesignValidationReport(
        sample_count=len({entry.sample_id for entry in entries}),
        condition_count=len(conditions),
        fraction_count=len({(entry.sample_id, entry.fraction) for entry in entries}),
        valid_contrasts=tuple(valid_contrasts),
        rejected_contrasts=tuple(rejected_contrasts),
        issues=tuple(issues),
        interpretation_summary=(
            f"{len(valid_contrasts)} valid contrasts, {len(rejected_contrasts)} rejected contrasts; "
            f"replicate counts: {condition_summary}."
        ),
    )


def build_power_analysis_advisory(
    entries: tuple[ExperimentalDesignEntry, ...],
    *,
    condition_a: str,
    condition_b: str,
    standardized_effect_size: float,
    target_power: float = 0.8,
    alpha: float = 0.05,
) -> PowerAnalysisAdvisory:
    """Estimate current and recommended replication for a two-condition design."""
    counts = _replicate_counts(entries)
    left = counts.get(condition_a, 0)
    right = counts.get(condition_b, 0)
    current_n = max(min(left, right), 1)
    normal = NormalDist()
    z_alpha = normal.inv_cdf(1.0 - alpha / 2.0)
    z_beta = normal.inv_cdf(target_power)
    recommended = max(2, math.ceil(2.0 * ((z_alpha + z_beta) ** 2) / (standardized_effect_size**2)))
    estimated = normal.cdf(math.sqrt(current_n / 2.0) * standardized_effect_size - z_alpha)
    return PowerAnalysisAdvisory(
        condition_a=condition_a,
        condition_b=condition_b,
        current_replicates={condition_a: left, condition_b: right},
        standardized_effect_size=standardized_effect_size,
        target_power=target_power,
        alpha=alpha,
        estimated_power=round(max(0.0, min(1.0, estimated)), 4),
        recommended_replicates_per_condition=recommended,
        advisory_summary=(
            f"{condition_a} vs {condition_b} currently has {left}/{right} replicates; "
            f"approximately {recommended} per condition are recommended for {target_power:.0%} power."
        ),
    )


def plan_batch_randomization(
    entries: tuple[ExperimentalDesignEntry, ...],
    *,
    seed: int,
) -> BatchRandomizationPlan:
    """Create a deterministic run order that spreads conditions within each batch."""
    rng = Random(seed)
    grouped_by_batch: dict[str, list[ExperimentalDesignEntry]] = defaultdict(list)
    for entry in entries:
        grouped_by_batch[entry.batch or "unassigned"].append(entry)
    slots: list[RandomizedRunSlot] = []
    order_index = 1
    for batch in sorted(grouped_by_batch):
        per_condition: dict[str, list[ExperimentalDesignEntry]] = defaultdict(list)
        for entry in grouped_by_batch[batch]:
            per_condition[entry.condition].append(entry)
        for bucket in per_condition.values():
            rng.shuffle(bucket)
        condition_order = sorted(per_condition)
        previous_condition: str | None = None
        while any(per_condition.values()):
            available = [condition for condition in condition_order if per_condition[condition]]
            available.sort(
                key=lambda condition: (
                    condition == previous_condition,
                    len(per_condition[condition]),
                    condition,
                )
            )
            selected_condition = available[-1]
            if previous_condition == selected_condition and len(available) > 1:
                selected_condition = available[-2]
            selected = per_condition[selected_condition].pop()
            slots.append(
                RandomizedRunSlot(
                    order_index=order_index,
                    sample_id=selected.sample_id,
                    condition=selected.condition,
                    batch=selected.batch,
                    fraction=selected.fraction,
                )
            )
            previous_condition = selected.condition
            order_index += 1
    counts = dict(Counter(slot.condition for slot in slots))
    return BatchRandomizationPlan(
        seed=seed,
        slot_count=len(slots),
        slots=tuple(slots),
        condition_counts=counts,
        notes=("conditions are alternated within batch where possible",),
    )


def build_fractionation_plan(
    entries: tuple[ExperimentalDesignEntry, ...],
) -> FractionationPlan:
    """Link samples and fractions to deterministic run labels."""
    assignments = tuple(
        FractionAssignment(
            sample_id=entry.sample_id,
            condition=entry.condition,
            fraction=entry.fraction,
            run_label=f"{entry.sample_id}-f{entry.fraction:02d}",
            spectra_file=entry.spectra_file,
        )
        for entry in sorted(entries, key=lambda item: (item.sample_id, item.fraction, item.spectra_file))
    )
    return FractionationPlan(
        sample_count=len({entry.sample_id for entry in entries}),
        total_fraction_count=len(assignments),
        assignments=assignments,
        notes=("run labels are deterministic over sample and fraction identity",),
    )


def plan_multiplex_labeling(
    entries: tuple[ExperimentalDesignEntry, ...],
    *,
    channels: tuple[str, ...],
    pooled_reference_channel: str | None = None,
    qc_bridge_channel: str | None = None,
) -> MultiplexLabelingPlan:
    """Assign samples to multiplex channels while balancing conditions."""
    reserved_channels = {channel for channel in (pooled_reference_channel, qc_bridge_channel) if channel}
    sample_channels = [channel for channel in channels if channel not in reserved_channels]
    unique_entries: list[ExperimentalDesignEntry] = []
    seen_samples: set[str] = set()
    for entry in sorted(entries, key=lambda item: (item.condition, item.sample_id, item.fraction)):
        if entry.sample_id not in seen_samples:
            unique_entries.append(entry)
            seen_samples.add(entry.sample_id)
    if len(unique_entries) > len(sample_channels):
        raise ValueError("not enough free multiplex channels for the provided samples")
    per_condition: dict[str, list[ExperimentalDesignEntry]] = defaultdict(list)
    for entry in unique_entries:
        per_condition[entry.condition].append(entry)
    assignments: list[MultiplexChannelAssignment] = []
    queue: list[ExperimentalDesignEntry] = []
    while any(per_condition.values()):
        for condition in sorted(per_condition, key=lambda key: (-len(per_condition[key]), key)):
            if per_condition[condition]:
                queue.append(per_condition[condition].pop(0))
    for channel, entry in zip(sample_channels, queue, strict=False):
        assignments.append(
            MultiplexChannelAssignment(
                channel=channel,
                role=MultiplexChannelRole.SAMPLE,
                sample_id=entry.sample_id,
                condition=entry.condition,
                batch=entry.batch,
            )
        )
    if pooled_reference_channel:
        assignments.append(
            MultiplexChannelAssignment(
                channel=pooled_reference_channel,
                role=MultiplexChannelRole.POOLED_REFERENCE,
                sample_id="pooled-reference",
            )
        )
    if qc_bridge_channel:
        assignments.append(
            MultiplexChannelAssignment(
                channel=qc_bridge_channel,
                role=MultiplexChannelRole.QC_BRIDGE,
                sample_id="qc-bridge",
            )
        )
    assignments.sort(key=lambda item: channels.index(item.channel))
    condition_counts = dict(
        Counter(assignment.condition for assignment in assignments if assignment.condition is not None)
    )
    spread = 0 if not condition_counts else max(condition_counts.values()) - min(condition_counts.values())
    return MultiplexLabelingPlan(
        plex_size=len(channels),
        assignments=tuple(assignments),
        condition_channel_counts=condition_counts,
        balanced=spread <= 1,
        notes=("reference and QC bridge channels are reserved explicitly",),
    )


def plan_spike_in_qc_samples(
    run_order: tuple[str, ...],
    *,
    qc_sample_id: str,
    every_n_runs: int = 4,
    spike_in_sample_id: str | None = None,
) -> SpikeInQcSamplePlan:
    """Insert QC and optional spike-in samples into a base run order."""
    expanded: list[str] = []
    insertions: list[SpikeInQcInsertion] = []
    for index, sample_id in enumerate(run_order, start=1):
        expanded.append(sample_id)
        if index % every_n_runs == 0:
            expanded.append(qc_sample_id)
            insertions.append(
                SpikeInQcInsertion(
                    order_index=len(expanded),
                    sample_id=qc_sample_id,
                    role="qc",
                )
            )
            if spike_in_sample_id:
                expanded.append(spike_in_sample_id)
                insertions.append(
                    SpikeInQcInsertion(
                        order_index=len(expanded),
                        sample_id=spike_in_sample_id,
                        role="spike_in",
                    )
                )
    return SpikeInQcSamplePlan(
        base_run_count=len(run_order),
        expanded_run_order=tuple(expanded),
        insertions=tuple(insertions),
        notes=(f"qc inserted every {every_n_runs} runs",),
    )


def assess_carryover_risk(
    run_order: tuple[str, ...],
    *,
    abundance_tiers: dict[str, str],
) -> CarryoverRiskAdvisory:
    """Flag risky transitions from high-abundance into sensitive samples."""
    severity_map = {"blank": 0, "low": 1, "medium": 2, "high": 3}
    flags: list[CarryoverRiskFlag] = []
    for left, right in zip(run_order, run_order[1:], strict=False):
        left_tier = abundance_tiers.get(left, "medium")
        right_tier = abundance_tiers.get(right, "medium")
        left_value = severity_map.get(left_tier, 2)
        right_value = severity_map.get(right_tier, 2)
        delta = left_value - right_value
        if delta <= 0:
            continue
        risk_level = (
            CarryoverRiskLevel.HIGH
            if delta >= 2 or (left_tier == "high" and right_tier == "blank")
            else CarryoverRiskLevel.MEDIUM
        )
        flags.append(
            CarryoverRiskFlag(
                preceding_sample_id=left,
                following_sample_id=right,
                preceding_tier=left_tier,
                following_tier=right_tier,
                risk_level=risk_level,
                rationale=(
                    f"{left_tier} abundance sample precedes {right_tier} abundance sample; wash carryover risk should be reviewed."
                ),
            )
        )
    return CarryoverRiskAdvisory(
        total_transitions=max(len(run_order) - 1, 0),
        flagged_transitions=tuple(flags),
        interpretation_summary=(
            f"{len(flags)} of {max(len(run_order) - 1, 0)} run-order transitions show carryover risk."
        ),
    )


def build_lab_protocol_evidence_bundle(
    *,
    bundle_id: str,
    sample_preparation: SamplePreparationMetadata,
    instrument_method: InstrumentMethodMetadata,
    design_validation: ExperimentDesignValidationReport,
    randomization_plan: BatchRandomizationPlan,
    fractionation_plan: FractionationPlan,
    multiplex_plan: MultiplexLabelingPlan | None = None,
    qc_plan: SpikeInQcSamplePlan | None = None,
    carryover_advisory: CarryoverRiskAdvisory | None = None,
) -> LabProtocolEvidenceBundle:
    """Bundle protocol-planning evidence into one reviewable payload."""
    return LabProtocolEvidenceBundle(
        bundle_id=bundle_id,
        sample_preparation=sample_preparation,
        instrument_method=instrument_method,
        design_validation=design_validation,
        randomization_plan=randomization_plan,
        fractionation_plan=fractionation_plan,
        multiplex_plan=multiplex_plan,
        qc_plan=qc_plan,
        carryover_advisory=carryover_advisory,
    )
