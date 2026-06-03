# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Benchmark surfaces that test whether QC findings matter scientifically."""

from __future__ import annotations

from pydantic import ConfigDict, Field, field_validator

from bijux_proteomics.domain.reason_codes import (
    ReasonCodeCategory,
    require_registered_reason_code,
)
from bijux_proteomics_foundation import JsonModel


class QcDecisionOutcomeObservation(JsonModel):
    """One benchmarked pairing of a QC flag with downstream scientific outcome."""

    model_config = ConfigDict(extra="forbid")

    run_id: str = Field(..., min_length=1)
    qc_flagged: bool
    downstream_evidence_failed: bool
    downstream_lab_follow_up_failed: bool


class QcDecisionValidityBenchmarkReport(JsonModel):
    """Benchmark whether QC findings actually predict downstream scientific failure."""

    model_config = ConfigDict(extra="forbid")

    true_positive_count: int = Field(..., ge=0)
    false_positive_count: int = Field(..., ge=0)
    true_negative_count: int = Field(..., ge=0)
    false_negative_count: int = Field(..., ge=0)
    predictive_precision: float = Field(..., ge=0.0, le=1.0)
    predictive_recall: float = Field(..., ge=0.0, le=1.0)
    qc_findings_predictive: bool
    note: str = Field(..., min_length=1)


class QcControlCoverageObservation(JsonModel):
    """One workflow run with required controls and actually observed controls."""

    model_config = ConfigDict(extra="forbid")

    run_id: str = Field(..., min_length=1)
    workflow_family: str = Field(..., min_length=1)
    required_controls: tuple[str, ...] = Field(default_factory=tuple)
    observed_controls: tuple[str, ...] = Field(default_factory=tuple)
    computationally_parseable: bool


class QcControlCoverageEntry(JsonModel):
    """One run-level control-coverage verdict."""

    model_config = ConfigDict(extra="forbid")

    run_id: str = Field(..., min_length=1)
    workflow_family: str = Field(..., min_length=1)
    missing_controls: tuple[str, ...] = Field(default_factory=tuple)
    computationally_parseable: bool
    scientifically_interpretable: bool
    promotion_blocked: bool


class QcControlCoverageReport(JsonModel):
    """Control-coverage report over computationally parseable versus interpretable runs."""

    model_config = ConfigDict(extra="forbid")

    entries: tuple[QcControlCoverageEntry, ...] = Field(default_factory=tuple)
    parseable_but_uninterpretable_count: int = Field(..., ge=0)
    promotion_blocked_count: int = Field(..., ge=0)
    note: str = Field(..., min_length=1)


class QcPromotionBlockObservation(JsonModel):
    """One decision-promotion attempt under failed or advisory QC posture."""

    model_config = ConfigDict(extra="forbid")

    run_id: str = Field(..., min_length=1)
    failed_qc: bool
    attempted_decision_promotion: bool
    promotion_prevented: bool
    blocking_reason: str = Field(..., min_length=1)

    @field_validator("blocking_reason")
    @classmethod
    def _validate_blocking_reason(cls, value: str) -> str:
        return require_registered_reason_code(
            value,
            ReasonCodeCategory.QC_REASON,
            ReasonCodeCategory.WORKFLOW_BLOCK,
        )


class QcPromotionBlockReport(JsonModel):
    """Benchmark whether failed QC truly blocks downstream decision promotion."""

    model_config = ConfigDict(extra="forbid")

    failed_qc_blocked_count: int = Field(..., ge=0)
    annotation_only_failure_count: int = Field(..., ge=0)
    ready_for_decision_promotion: bool
    note: str = Field(..., min_length=1)


class QcContaminationPropagationObservation(JsonModel):
    """One run-level observation linking contamination burden to downstream consequence."""

    model_config = ConfigDict(extra="forbid")

    run_id: str = Field(..., min_length=1)
    contaminant_psm_fraction: float = Field(..., ge=0.0, le=1.0)
    identification_rate_drop_fraction: float = Field(..., ge=0.0, le=1.0)
    quant_distortion_fraction: float = Field(..., ge=0.0, le=1.0)
    interpretation_advisory_triggered: bool


class QcContaminationPropagationReport(JsonModel):
    """Benchmark whether contamination burden propagates into scientific consequences."""

    model_config = ConfigDict(extra="forbid")

    high_burden_count: int = Field(..., ge=0)
    propagated_consequence_count: int = Field(..., ge=0)
    unresolved_high_burden_count: int = Field(..., ge=0)
    contamination_is_scientifically_material: bool
    note: str = Field(..., min_length=1)


class QcDriftObservation(JsonModel):
    """One run-level and batch-level drift observation."""

    model_config = ConfigDict(extra="forbid")

    run_id: str = Field(..., min_length=1)
    batch_id: str = Field(..., min_length=1)
    run_level_drift_score: float = Field(..., ge=0.0)
    batch_level_drift_score: float = Field(..., ge=0.0)
    promotion_blocked: bool


class QcDriftBenchmarkReport(JsonModel):
    """Benchmark simultaneous run-level and cohort-level drift pressure."""

    model_config = ConfigDict(extra="forbid")

    run_level_drift_count: int = Field(..., ge=0)
    batch_level_drift_count: int = Field(..., ge=0)
    dual_drift_count: int = Field(..., ge=0)
    unblocked_dual_drift_count: int = Field(..., ge=0)
    ready_for_cohort_interpretation: bool
    note: str = Field(..., min_length=1)


class QcCarryoverObservation(JsonModel):
    """One carryover case that must stay visible across QC, lab, and reporting."""

    model_config = ConfigDict(extra="forbid")

    run_id: str = Field(..., min_length=1)
    carryover_fraction: float = Field(..., ge=0.0, le=1.0)
    blank_control_present: bool
    wash_step_documented: bool
    lab_advisory_triggered: bool
    runtime_report_flagged: bool


class QcCarryoverBenchmarkReport(JsonModel):
    """Benchmark whether carryover pressure survives across repository boundaries."""

    model_config = ConfigDict(extra="forbid")

    elevated_carryover_count: int = Field(..., ge=0)
    unresolved_carryover_count: int = Field(..., ge=0)
    spans_core_lab_runtime: bool
    ready_for_promotion: bool
    note: str = Field(..., min_length=1)


class SamplePrepDigestionObservation(JsonModel):
    """One sample-prep and digestion case linking chemistry success to experimental reality."""

    model_config = ConfigDict(extra="forbid")

    sample_id: str = Field(..., min_length=1)
    missed_cleavage_rate: float = Field(..., ge=0.0, le=1.0)
    semi_specific_fraction: float = Field(..., ge=0.0, le=1.0)
    contaminant_fraction: float = Field(..., ge=0.0, le=1.0)
    chemistry_layer_passed: bool
    sample_prep_failure_visible: bool


class SamplePrepDigestionRealismReport(JsonModel):
    """Benchmark whether digestion and sample prep stay coupled to experimental failure."""

    model_config = ConfigDict(extra="forbid")

    digestion_failure_count: int = Field(..., ge=0)
    decoupled_success_count: int = Field(..., ge=0)
    ready_for_sequence_level_claims: bool
    note: str = Field(..., min_length=1)


class WorkflowMinimumControlEntry(JsonModel):
    """Minimal controls that must exist before a workflow can leave advisory status."""

    model_config = ConfigDict(extra="forbid")

    workflow_family: str = Field(..., min_length=1)
    minimum_controls: tuple[str, ...] = Field(default_factory=tuple)
    promotion_rule: str = Field(..., min_length=1)


class WorkflowMinimumControlReport(JsonModel):
    """Minimal-control policy across serious workflow families."""

    model_config = ConfigDict(extra="forbid")

    entries: tuple[WorkflowMinimumControlEntry, ...] = Field(default_factory=tuple)


class ContaminationCleanupObservation(JsonModel):
    """One contamination case with cleanup visibility and downstream consequence."""

    model_config = ConfigDict(extra="forbid")

    run_id: str = Field(..., min_length=1)
    contamination_fraction: float = Field(..., ge=0.0, le=1.0)
    cleanup_control_present: bool
    carryover_suspected: bool
    identification_posture_changed: bool
    quant_posture_changed: bool
    interpretation_posture_changed: bool
    corrective_action_visible: bool


class ContaminationCleanupDossierReport(JsonModel):
    """Whole-repository dossier for contamination and cleanup propagation."""

    model_config = ConfigDict(extra="forbid")

    unresolved_cleanup_failure_count: int = Field(..., ge=0)
    full_propagation_count: int = Field(..., ge=0)
    scientifically_defensible: bool
    note: str = Field(..., min_length=1)


def _fraction(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return numerator / denominator


def build_qc_decision_validity_benchmark_report(
    observations: tuple[QcDecisionOutcomeObservation, ...],
) -> QcDecisionValidityBenchmarkReport:
    """Benchmark whether QC findings predict bad downstream evidence or bad lab follow-up."""

    true_positive = 0
    false_positive = 0
    true_negative = 0
    false_negative = 0
    for observation in observations:
        downstream_failed = (
            observation.downstream_evidence_failed
            or observation.downstream_lab_follow_up_failed
        )
        if observation.qc_flagged and downstream_failed:
            true_positive += 1
        elif observation.qc_flagged and not downstream_failed:
            false_positive += 1
        elif not observation.qc_flagged and downstream_failed:
            false_negative += 1
        else:
            true_negative += 1
    precision = _fraction(true_positive, true_positive + false_positive)
    recall = _fraction(true_positive, true_positive + false_negative)
    predictive = true_positive > 0 and precision >= 0.75 and recall >= 0.75
    return QcDecisionValidityBenchmarkReport(
        true_positive_count=true_positive,
        false_positive_count=false_positive,
        true_negative_count=true_negative,
        false_negative_count=false_negative,
        predictive_precision=precision,
        predictive_recall=recall,
        qc_findings_predictive=predictive,
        note=(
            "QC findings predict downstream scientific failure strongly enough to justify decision blocking"
            if predictive
            else "QC findings remain too weakly predictive and risk becoming annotation-only"
        ),
    )


def build_qc_control_coverage_report(
    observations: tuple[QcControlCoverageObservation, ...],
) -> QcControlCoverageReport:
    """Separate computationally parseable runs from scientifically interpretable runs."""

    entries: list[QcControlCoverageEntry] = []
    for observation in observations:
        missing = tuple(
            sorted(
                set(observation.required_controls) - set(observation.observed_controls)
            )
        )
        scientifically_interpretable = (
            observation.computationally_parseable and not missing
        )
        promotion_blocked = observation.computationally_parseable and bool(missing)
        entries.append(
            QcControlCoverageEntry(
                run_id=observation.run_id,
                workflow_family=observation.workflow_family,
                missing_controls=missing,
                computationally_parseable=observation.computationally_parseable,
                scientifically_interpretable=scientifically_interpretable,
                promotion_blocked=promotion_blocked,
            )
        )
    parseable_but_uninterpretable_count = sum(
        entry.computationally_parseable and not entry.scientifically_interpretable
        for entry in entries
    )
    promotion_blocked_count = sum(entry.promotion_blocked for entry in entries)
    return QcControlCoverageReport(
        entries=tuple(entries),
        parseable_but_uninterpretable_count=parseable_but_uninterpretable_count,
        promotion_blocked_count=promotion_blocked_count,
        note=(
            "control coverage distinguishes computationally parseable runs from scientifically interpretable runs before promotion"
        ),
    )


def build_qc_promotion_block_report(
    observations: tuple[QcPromotionBlockObservation, ...],
) -> QcPromotionBlockReport:
    """Benchmark whether failed QC truly blocks downstream decision promotion."""

    failed_qc_blocked_count = sum(
        observation.failed_qc and observation.promotion_prevented
        for observation in observations
    )
    annotation_only_failure_count = sum(
        observation.failed_qc
        and observation.attempted_decision_promotion
        and not observation.promotion_prevented
        for observation in observations
    )
    ready = annotation_only_failure_count == 0
    return QcPromotionBlockReport(
        failed_qc_blocked_count=failed_qc_blocked_count,
        annotation_only_failure_count=annotation_only_failure_count,
        ready_for_decision_promotion=ready,
        note=(
            "failed QC blocks downstream decision promotion rather than becoming annotation-only"
            if ready
            else "one or more failed-QC runs still slipped into decision promotion as annotation-only warnings"
        ),
    )


def build_qc_contamination_propagation_report(
    observations: tuple[QcContaminationPropagationObservation, ...],
    *,
    high_burden_threshold: float = 0.1,
    identification_drop_threshold: float = 0.15,
    quant_distortion_threshold: float = 0.2,
) -> QcContaminationPropagationReport:
    """Benchmark whether contamination burden changes identification, quant, and interpretation posture."""

    high_burden_count = 0
    propagated_consequence_count = 0
    unresolved_high_burden_count = 0
    for observation in observations:
        high_burden = observation.contaminant_psm_fraction >= high_burden_threshold
        propagated = (
            observation.identification_rate_drop_fraction
            >= identification_drop_threshold
            or observation.quant_distortion_fraction >= quant_distortion_threshold
            or observation.interpretation_advisory_triggered
        )
        if high_burden:
            high_burden_count += 1
            if propagated:
                propagated_consequence_count += 1
            else:
                unresolved_high_burden_count += 1
    material = high_burden_count > 0 and unresolved_high_burden_count == 0
    return QcContaminationPropagationReport(
        high_burden_count=high_burden_count,
        propagated_consequence_count=propagated_consequence_count,
        unresolved_high_burden_count=unresolved_high_burden_count,
        contamination_is_scientifically_material=material,
        note=(
            "contaminant burden propagates into identification, quantification, or interpretation posture instead of staying a cosmetic QC number"
            if material
            else "one or more high-contamination cases failed to change downstream scientific posture"
        ),
    )


def build_qc_drift_benchmark_report(
    observations: tuple[QcDriftObservation, ...],
    *,
    run_level_threshold: float = 1.0,
    batch_level_threshold: float = 1.0,
) -> QcDriftBenchmarkReport:
    """Benchmark simultaneous run-level and batch-level drift pressure."""

    run_level_drift_count = 0
    batch_level_drift_count = 0
    dual_drift_count = 0
    unblocked_dual_drift_count = 0
    for observation in observations:
        run_drift = observation.run_level_drift_score >= run_level_threshold
        batch_drift = observation.batch_level_drift_score >= batch_level_threshold
        if run_drift:
            run_level_drift_count += 1
        if batch_drift:
            batch_level_drift_count += 1
        if run_drift and batch_drift:
            dual_drift_count += 1
            if not observation.promotion_blocked:
                unblocked_dual_drift_count += 1
    ready = dual_drift_count == 0 or unblocked_dual_drift_count == 0
    return QcDriftBenchmarkReport(
        run_level_drift_count=run_level_drift_count,
        batch_level_drift_count=batch_level_drift_count,
        dual_drift_count=dual_drift_count,
        unblocked_dual_drift_count=unblocked_dual_drift_count,
        ready_for_cohort_interpretation=ready,
        note=(
            "run-level and batch-level drift are jointly contained before cohort interpretation"
            if ready
            else "dual drift remains scientifically dangerous because at least one affected run still escaped promotion blocking"
        ),
    )


def build_qc_carryover_benchmark_report(
    observations: tuple[QcCarryoverObservation, ...],
    *,
    elevated_carryover_threshold: float = 0.05,
) -> QcCarryoverBenchmarkReport:
    """Benchmark whether carryover stays visible from QC into lab and reporting."""

    elevated_count = 0
    unresolved_count = 0
    spans_core_lab_runtime = True
    for observation in observations:
        elevated = observation.carryover_fraction >= elevated_carryover_threshold
        if elevated:
            elevated_count += 1
            fully_visible = (
                observation.blank_control_present
                and observation.wash_step_documented
                and observation.lab_advisory_triggered
                and observation.runtime_report_flagged
            )
            if not fully_visible:
                unresolved_count += 1
        spans_core_lab_runtime = spans_core_lab_runtime and (
            observation.lab_advisory_triggered and observation.runtime_report_flagged
        )
    ready = elevated_count == 0 or unresolved_count == 0
    return QcCarryoverBenchmarkReport(
        elevated_carryover_count=elevated_count,
        unresolved_carryover_count=unresolved_count,
        spans_core_lab_runtime=spans_core_lab_runtime,
        ready_for_promotion=ready,
        note=(
            "carryover pressure survives across QC, lab advisories, and runtime reporting before promotion"
            if ready
            else "carryover still disappears between QC, lab advisories, and reporting, leaving unsafe promotion gaps"
        ),
    )


def build_sample_prep_digestion_realism_report(
    observations: tuple[SamplePrepDigestionObservation, ...],
    *,
    missed_cleavage_threshold: float = 0.25,
    semi_specific_threshold: float = 0.15,
    contaminant_threshold: float = 0.1,
) -> SamplePrepDigestionRealismReport:
    """Benchmark whether digestion success remains coupled to experimental failure modes."""

    digestion_failure_count = 0
    decoupled_success_count = 0
    for observation in observations:
        digestion_failed = (
            observation.missed_cleavage_rate >= missed_cleavage_threshold
            or observation.semi_specific_fraction >= semi_specific_threshold
            or observation.contaminant_fraction >= contaminant_threshold
        )
        if digestion_failed:
            digestion_failure_count += 1
        if observation.chemistry_layer_passed and (
            digestion_failed or observation.sample_prep_failure_visible
        ):
            decoupled_success_count += 1
    ready = digestion_failure_count == 0 and decoupled_success_count == 0
    return SamplePrepDigestionRealismReport(
        digestion_failure_count=digestion_failure_count,
        decoupled_success_count=decoupled_success_count,
        ready_for_sequence_level_claims=ready,
        note=(
            "sequence- and chemistry-layer success stays coupled to sample-prep and digestion quality before interpretation"
            if ready
            else "one or more cases still look chemically successful while sample prep or digestion failure would make the science unreliable"
        ),
    )


def build_workflow_minimum_control_report() -> WorkflowMinimumControlReport:
    """Name the minimum controls required before each workflow can leave advisory status."""

    return WorkflowMinimumControlReport(
        entries=(
            WorkflowMinimumControlEntry(
                workflow_family="dda",
                minimum_controls=("blank", "pooled_reference"),
                promotion_rule="DDA claims remain advisory until both blank and pooled-reference behavior are visible.",
            ),
            WorkflowMinimumControlEntry(
                workflow_family="dia",
                minimum_controls=("blank", "pooled_reference", "library_reference"),
                promotion_rule="DIA claims remain advisory until carryover, pooled stability, and library-conditioned behavior are all reviewable.",
            ),
            WorkflowMinimumControlEntry(
                workflow_family="lfq",
                minimum_controls=("blank", "pooled_reference", "batch_bridge"),
                promotion_rule="LFQ claims remain advisory until missingness, pooled stability, and batch bridging are all explicit.",
            ),
            WorkflowMinimumControlEntry(
                workflow_family="multiplex",
                minimum_controls=("reference_channel", "bridge_channel", "blank"),
                promotion_rule="Multiplex claims remain advisory until reference-channel, bridge-channel, and blank behavior stay visible.",
            ),
            WorkflowMinimumControlEntry(
                workflow_family="ptm",
                minimum_controls=("enrichment_blank", "site_localization_reference"),
                promotion_rule="PTM claims remain advisory until enrichment blank behavior and localization reference evidence are present.",
            ),
            WorkflowMinimumControlEntry(
                workflow_family="targeted",
                minimum_controls=("blank", "heavy_reference", "calibration_standard"),
                promotion_rule="Targeted claims remain advisory until blank, heavy-reference, and calibration-standard behavior are explicit.",
            ),
        )
    )


def build_contamination_cleanup_dossier_report(
    observations: tuple[ContaminationCleanupObservation, ...],
    *,
    contamination_threshold: float = 0.1,
) -> ContaminationCleanupDossierReport:
    """Build a dossier showing whether bad cleanup propagates through the repository."""

    unresolved_cleanup_failure_count = 0
    full_propagation_count = 0
    for observation in observations:
        elevated = observation.contamination_fraction >= contamination_threshold
        propagated = (
            observation.identification_posture_changed
            and observation.quant_posture_changed
            and observation.interpretation_posture_changed
        )
        if elevated and propagated and observation.corrective_action_visible:
            full_propagation_count += 1
        elif elevated and (
            not observation.cleanup_control_present
            or observation.carryover_suspected
            or not propagated
            or not observation.corrective_action_visible
        ):
            unresolved_cleanup_failure_count += 1
    defensible = full_propagation_count > 0 and unresolved_cleanup_failure_count == 0
    return ContaminationCleanupDossierReport(
        unresolved_cleanup_failure_count=unresolved_cleanup_failure_count,
        full_propagation_count=full_propagation_count,
        scientifically_defensible=defensible,
        note=(
            "contamination and cleanup failures propagate through identification, quantification, interpretation, and corrective action surfaces"
            if defensible
            else "one or more contamination cases still fail to propagate cleanly through cleanup controls or downstream scientific posture"
        ),
    )
