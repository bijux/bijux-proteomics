# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Experiment outcome and rerun contracts."""

from __future__ import annotations

from enum import StrEnum
from statistics import mean, median

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import AssayId, BatchId, JsonModel
from bijux_proteomics_knowledge import (
    EvidenceKind,
    EvidenceSourceType,
    EvidenceStrength,
    NormalizedEvidenceInput,
)
from bijux_proteomics_lab.repositories import LabFeedbackRecord


class FailureClass(StrEnum):
    """Failure classes for assay and batch execution."""

    TECHNICAL = "technical"
    BIOLOGICAL = "biological"
    MATERIAL = "material"
    INTERPRETATION = "interpretation"


class AssayResultState(StrEnum):
    """Normalized assay result states beyond binary pass/fail."""

    PASSED = "passed"
    FAILED_BIOLOGICAL = "failed_biological"
    FAILED_TECHNICAL = "failed_technical"
    FAILED_REPRODUCIBILITY = "failed_reproducibility"
    INCONCLUSIVE = "inconclusive"


class QcState(StrEnum):
    """QC state for assay observations."""

    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"


class RerunPolicy(StrEnum):
    """Rerun recommendation after an outcome is observed."""

    NEVER = "never"
    ON_TECHNICAL_FAILURE = "on_technical_failure"
    ON_REPRODUCIBILITY_FAILURE = "on_reproducibility_failure"
    ON_BIOLOGICAL_FAILURE = "on_biological_failure"
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
    BETWEEN = "between"


class AssayAcceptanceRule(JsonModel):
    """Acceptance threshold for one assay metric."""

    model_config = ConfigDict(extra="forbid")

    assay_id: AssayId = Field(..., description="Assay identifier.")
    metric: str = Field(..., min_length=1, description="Metric to evaluate.")
    operator: AcceptanceOperator = Field(..., description="Threshold operator.")
    threshold: float = Field(..., description="Acceptance threshold.")
    upper_threshold: float | None = Field(
        default=None,
        description="Upper bound used when the operator requires a range.",
    )
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
    result_state: AssayResultState = Field(
        default=AssayResultState.PASSED,
        description="Normalized assay result state.",
    )
    observation_summary: str = Field(
        ...,
        min_length=1,
        description="Human-readable summary of the outcome.",
    )
    failure_class: FailureClass | None = Field(
        default=None,
        description="Failure class when the assay does not pass.",
    )
    replicate_count: int = Field(
        default=1,
        ge=1,
        description="Number of replicates represented by this outcome.",
    )
    uncertainty: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Uncertainty associated with the outcome.",
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
    replicate_values: list[float] = Field(
        default_factory=list,
        description="Raw replicate values captured for this observation.",
    )
    qc_state: QcState = Field(default=QcState.PASSED, description="QC state for this observation.")
    qc_passed: bool = Field(
        default=True,
        description="Whether assay-level QC checks passed.",
    )
    dispersion: float | None = Field(
        default=None,
        ge=0.0,
        description="Observed dispersion (for example CV or SD) across replicates.",
    )
    normalization_method: str | None = Field(
        default=None,
        description="Normalization method applied before interpretation.",
    )
    detection_limit: float | None = Field(
        default=None,
        description="Detection limit for the measured endpoint.",
    )
    below_detection_limit: bool = Field(
        default=False,
        description="Whether the measured signal was below detection limit.",
    )
    batch_effect_note: str | None = Field(
        default=None,
        description="Optional note describing batch-effect concerns for interpretation.",
    )
    interpretation_confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Confidence in the interpreted observation quality.",
    )


class ExperimentOutcomeSummary(JsonModel):
    """Compact summary of experiment outcomes by result state."""

    model_config = ConfigDict(extra="forbid")

    batch_id: BatchId = Field(..., description="Batch identifier.")
    total_assays: int = Field(..., ge=0, description="Total assay outcomes in the batch.")
    passed_count: int = Field(..., ge=0, description="Count of passed assays.")
    failed_biological_count: int = Field(..., ge=0, description="Count of biological failures.")
    failed_technical_count: int = Field(..., ge=0, description="Count of technical failures.")
    failed_reproducibility_count: int = Field(..., ge=0, description="Count of reproducibility failures.")
    inconclusive_count: int = Field(..., ge=0, description="Count of inconclusive results.")


class ObservationSummary(JsonModel):
    """Replicate-aware summary of a lab observation."""

    model_config = ConfigDict(extra="forbid")

    assay_id: AssayId = Field(..., description="Assay identifier.")
    metric: str = Field(..., min_length=1, description="Observed metric.")
    mean_value: float = Field(..., description="Mean value across replicates.")
    median_value: float = Field(..., description="Median value across replicates.")
    replicate_count: int = Field(..., ge=1, description="Replicate count used for summary.")
    dispersion: float | None = Field(default=None, ge=0.0, description="Reported or inferred dispersion.")
    below_detection_limit: bool = Field(default=False, description="Whether signal is below detection.")


class EvidencePromotionReadiness(JsonModel):
    """Promotion readiness for one assay outcome entering knowledge systems."""

    model_config = ConfigDict(extra="forbid")

    assay_id: AssayId = Field(..., description="Assay identifier.")
    ready: bool = Field(..., description="Whether the outcome is ready for evidence promotion.")
    blockers: list[str] = Field(default_factory=list, description="Blockers preventing promotion.")
    recommended_action: str = Field(..., min_length=1, description="Next action before promotion.")


class ClaimBeliefDelta(JsonModel):
    """Belief delta recommendation derived from one assay outcome."""

    model_config = ConfigDict(extra="forbid")

    claim_id: str = Field(..., min_length=1, description="Claim identifier to update.")
    delta: float = Field(..., description="Signed confidence delta recommendation.")
    rationale: str = Field(..., min_length=1, description="Scientific rationale for the delta.")


class OutcomePromotionPolicy(JsonModel):
    """Policy controlling how assay outcomes are promoted into evidence payloads."""

    model_config = ConfigDict(extra="forbid")

    policy_id: str = Field(..., min_length=1, description="Stable policy identifier.")
    passed_base_confidence: float = Field(
        default=0.9,
        ge=0.0,
        le=1.0,
        description="Base confidence for passed outcomes before uncertainty penalties.",
    )
    failed_base_confidence: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Base confidence for failed outcomes before uncertainty penalties.",
    )
    uncertainty_penalty_factor: float = Field(
        default=0.4,
        ge=0.0,
        le=1.0,
        description="Penalty multiplier applied to uncertainty.",
    )


class BatchOutcomeAssessment(JsonModel):
    """Aggregate decision assessment for a full experiment batch outcome."""

    model_config = ConfigDict(extra="forbid")

    batch_id: BatchId = Field(..., description="Batch identifier.")
    total_assays: int = Field(..., ge=0, description="Total assays in batch.")
    promotion_ready_count: int = Field(..., ge=0, description="Count of outcomes ready for evidence promotion.")
    technical_or_repro_failures: int = Field(
        ...,
        ge=0,
        description="Count of technical or reproducibility failures that block interpretation.",
    )
    rerun_policy: RerunPolicy = Field(..., description="Recommended rerun policy for the batch.")
    notes: list[str] = Field(default_factory=list, description="Summary notes for reviewers.")


class ObservationValidationIssue(JsonModel):
    """Validation issue for assay observation record quality."""

    model_config = ConfigDict(extra="forbid")

    code: str = Field(..., min_length=1, description="Stable issue code.")
    message: str = Field(..., min_length=1, description="Human-readable issue message.")


class OutcomeFeedbackMapping(JsonModel):
    """Mapping summary between assay outcomes and generated feedback records."""

    model_config = ConfigDict(extra="forbid")

    batch_id: BatchId = Field(..., description="Batch identifier.")
    feedback_ids: list[str] = Field(default_factory=list, description="Generated feedback record identifiers.")
    assay_ids: list[AssayId] = Field(default_factory=list, description="Assays represented by generated feedback.")


def recommend_rerun_policy(outcome: ExperimentOutcome) -> RerunPolicy:
    """Recommend a rerun policy from observed failures."""
    if any(
        assay.result_state is AssayResultState.FAILED_TECHNICAL
        or assay.failure_class is FailureClass.TECHNICAL
        for assay in outcome.assay_outcomes
        if not assay.passed
    ):
        return RerunPolicy.ON_TECHNICAL_FAILURE
    if any(
        assay.result_state is AssayResultState.FAILED_REPRODUCIBILITY
        for assay in outcome.assay_outcomes
        if not assay.passed
    ):
        return RerunPolicy.ON_REPRODUCIBILITY_FAILURE
    if any(
        assay.result_state is AssayResultState.FAILED_BIOLOGICAL
        or assay.failure_class is FailureClass.BIOLOGICAL
        for assay in outcome.assay_outcomes
        if not assay.passed
    ):
        return RerunPolicy.ON_BIOLOGICAL_FAILURE
    if any(
        not assay.passed or assay.result_state is AssayResultState.INCONCLUSIVE
        for assay in outcome.assay_outcomes
    ):
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
    if not observation.qc_passed or observation.qc_state is QcState.FAILED:
        return AssayOutcome(
            assay_id=observation.assay_id,
            passed=False,
            result_state=AssayResultState.FAILED_TECHNICAL,
            observation_summary=f"{observation.metric} failed assay QC checks",
            failure_class=FailureClass.TECHNICAL,
            replicate_count=max(1, len(observation.replicate_values) or 1),
            uncertainty=0.6,
        )
    if observation.qc_state is QcState.WARNING:
        warning_uncertainty = max(0.2, 1.0 - observation.interpretation_confidence)
        return AssayOutcome(
            assay_id=observation.assay_id,
            passed=False,
            result_state=AssayResultState.INCONCLUSIVE,
            observation_summary=f"{observation.metric} requires review due to QC warning state",
            failure_class=FailureClass.INTERPRETATION,
            replicate_count=max(1, len(observation.replicate_values) or 1),
            uncertainty=warning_uncertainty,
        )
    if observation.batch_effect_note:
        batch_uncertainty = max(0.25, 1.0 - observation.interpretation_confidence)
        return AssayOutcome(
            assay_id=observation.assay_id,
            passed=False,
            result_state=AssayResultState.INCONCLUSIVE,
            observation_summary=f"{observation.metric} impacted by batch-effect concern: {observation.batch_effect_note}",
            failure_class=FailureClass.INTERPRETATION,
            replicate_count=max(1, len(observation.replicate_values) or 1),
            uncertainty=batch_uncertainty,
        )
    if observation.below_detection_limit:
        return AssayOutcome(
            assay_id=observation.assay_id,
            passed=False,
            result_state=AssayResultState.INCONCLUSIVE,
            observation_summary=f"{observation.metric} signal is below detection limit",
            failure_class=FailureClass.INTERPRETATION,
            replicate_count=max(1, len(observation.replicate_values) or 1),
            uncertainty=0.7,
        )
    if rule.unit is not None and observation.unit is not None and observation.unit != rule.unit:
        return AssayOutcome(
            assay_id=observation.assay_id,
            passed=False,
            result_state=AssayResultState.INCONCLUSIVE,
            observation_summary=(
                f"{observation.metric} unit mismatch ({observation.unit} vs expected {rule.unit})"
            ),
            failure_class=FailureClass.INTERPRETATION,
        )

    if rule.operator is AcceptanceOperator.GREATER_EQUAL:
        passed = observation.value >= rule.threshold
    elif rule.operator is AcceptanceOperator.LESS_EQUAL:
        passed = observation.value <= rule.threshold
    else:
        if rule.upper_threshold is None:
            raise ValueError("between operator requires upper_threshold")
        lower = min(rule.threshold, rule.upper_threshold)
        upper = max(rule.threshold, rule.upper_threshold)
        passed = lower <= observation.value <= upper
    summary = (
        f"{observation.metric}={observation.value:g}"
        f"{observation.unit or ''} {'met' if passed else 'missed'} "
        f"{rule.operator.value} {rule.threshold:g}{rule.unit or ''}"
    )
    if (
        observation.dispersion is not None
        and observation.dispersion > 0.3
        and len(observation.replicate_values) >= 3
    ):
        return AssayOutcome(
            assay_id=observation.assay_id,
            passed=False,
            result_state=AssayResultState.FAILED_REPRODUCIBILITY,
            observation_summary=f"{observation.metric} showed high replicate dispersion ({observation.dispersion:g})",
            failure_class=FailureClass.INTERPRETATION,
            replicate_count=max(1, len(observation.replicate_values) or 1),
            uncertainty=0.65,
        )
    return AssayOutcome(
        assay_id=observation.assay_id,
        passed=passed,
        result_state=AssayResultState.PASSED if passed else AssayResultState.FAILED_BIOLOGICAL,
        observation_summary=summary,
        failure_class=None if passed else FailureClass.BIOLOGICAL,
        replicate_count=max(1, len(observation.replicate_values) or 1),
    )


def promote_outcome_to_evidence(
    outcome: AssayOutcome,
    *,
    target_id: str,
    batch_id: str,
    policy: OutcomePromotionPolicy | None = None,
) -> NormalizedEvidenceInput:
    """Convert one assay outcome into normalized evidence for knowledge ingestion."""
    policy = policy or OutcomePromotionPolicy(policy_id="default-outcome-promotion-policy")
    base_confidence = policy.passed_base_confidence if outcome.passed else policy.failed_base_confidence
    confidence = max(0.1, base_confidence - (outcome.uncertainty * policy.uncertainty_penalty_factor))
    decision_tags = ["progression"]
    if outcome.result_state is AssayResultState.FAILED_TECHNICAL:
        decision_tags.append("technical_risk")
    if outcome.result_state is AssayResultState.INCONCLUSIVE:
        decision_tags.append("uncertainty")
    if outcome.result_state is AssayResultState.FAILED_BIOLOGICAL:
        decision_tags.append("biological_risk")
    if outcome.result_state is AssayResultState.FAILED_REPRODUCIBILITY:
        decision_tags.append("reproducibility_risk")
    return NormalizedEvidenceInput(
        evidence_id=f"assay:{batch_id}:{outcome.assay_id}",
        kind=EvidenceKind.ASSAY,
        title=f"Assay outcome {outcome.assay_id}",
        source=f"lab-batch:{batch_id}",
        source_type=EvidenceSourceType.LAB_ASSAY,
        claim=outcome.observation_summary,
        related_targets=[target_id],
        decision_tags=decision_tags,
        confidence=round(confidence, 4),
        strength=EvidenceStrength.DECISIVE if outcome.passed else EvidenceStrength.EXPLORATORY,
    )


def summarize_experiment_outcome(outcome: ExperimentOutcome) -> ExperimentOutcomeSummary:
    """Summarize one experiment outcome into normalized state counts."""
    return ExperimentOutcomeSummary(
        batch_id=outcome.batch_id,
        total_assays=len(outcome.assay_outcomes),
        passed_count=sum(1 for assay in outcome.assay_outcomes if assay.result_state is AssayResultState.PASSED),
        failed_biological_count=sum(
            1 for assay in outcome.assay_outcomes if assay.result_state is AssayResultState.FAILED_BIOLOGICAL
        ),
        failed_technical_count=sum(
            1 for assay in outcome.assay_outcomes if assay.result_state is AssayResultState.FAILED_TECHNICAL
        ),
        failed_reproducibility_count=sum(
            1
            for assay in outcome.assay_outcomes
            if assay.result_state is AssayResultState.FAILED_REPRODUCIBILITY
        ),
        inconclusive_count=sum(1 for assay in outcome.assay_outcomes if assay.result_state is AssayResultState.INCONCLUSIVE),
    )


def summarize_observation(observation: AssayObservationRecord) -> ObservationSummary:
    """Summarize replicate-level observation statistics for interpretation."""
    values = observation.replicate_values or [observation.value]
    return ObservationSummary(
        assay_id=observation.assay_id,
        metric=observation.metric,
        mean_value=round(mean(values), 6),
        median_value=round(median(values), 6),
        replicate_count=len(values),
        dispersion=observation.dispersion,
        below_detection_limit=observation.below_detection_limit,
    )


def assess_evidence_promotion_readiness(outcome: AssayOutcome) -> EvidencePromotionReadiness:
    """Assess whether an assay outcome should be promoted as decision-grade evidence."""
    blockers: list[str] = []
    if outcome.result_state in {
        AssayResultState.FAILED_TECHNICAL,
        AssayResultState.FAILED_REPRODUCIBILITY,
        AssayResultState.INCONCLUSIVE,
    }:
        blockers.append(f"result_state={outcome.result_state.value}")
    if outcome.uncertainty > 0.5:
        blockers.append(f"uncertainty={outcome.uncertainty:.2f} exceeds promotion threshold")
    if outcome.replicate_count < 2:
        blockers.append("replicate_count below promotion minimum")
    ready = not blockers and outcome.passed
    if ready:
        action = "promote outcome to knowledge evidence bundle"
    elif outcome.result_state is AssayResultState.FAILED_TECHNICAL:
        action = "rerun assay after resolving technical failure"
    elif outcome.result_state is AssayResultState.FAILED_REPRODUCIBILITY:
        action = "repeat assay with improved replicate consistency controls"
    else:
        action = "curate interpretation and collect additional orthogonal evidence"
    return EvidencePromotionReadiness(
        assay_id=outcome.assay_id,
        ready=ready,
        blockers=blockers,
        recommended_action=action,
    )


def recommend_claim_belief_deltas(
    outcome: AssayOutcome,
    *,
    linked_claim_ids: list[str],
) -> list[ClaimBeliefDelta]:
    """Recommend bounded claim-confidence deltas from one assay outcome."""
    if not linked_claim_ids:
        return []
    if outcome.result_state is AssayResultState.PASSED and outcome.passed:
        base_delta = max(0.05, 0.2 - (outcome.uncertainty * 0.1))
        rationale = "assay passed and supports linked claim direction"
    elif outcome.result_state in {
        AssayResultState.FAILED_BIOLOGICAL,
        AssayResultState.FAILED_TECHNICAL,
        AssayResultState.FAILED_REPRODUCIBILITY,
    }:
        base_delta = -0.2
        rationale = f"assay produced {outcome.result_state.value} outcome"
    else:
        base_delta = -0.05
        rationale = "assay outcome is inconclusive and weakens confidence modestly"
    return [
        ClaimBeliefDelta(
            claim_id=claim_id,
            delta=round(base_delta, 4),
            rationale=rationale,
        )
        for claim_id in linked_claim_ids
    ]


def assess_batch_outcome(outcome: ExperimentOutcome) -> BatchOutcomeAssessment:
    """Assess aggregate readiness and rerun posture for an experiment batch."""
    promotion_ready = sum(
        1
        for assay in outcome.assay_outcomes
        if assess_evidence_promotion_readiness(assay).ready
    )
    technical_or_repro = sum(
        1
        for assay in outcome.assay_outcomes
        if assay.result_state in {AssayResultState.FAILED_TECHNICAL, AssayResultState.FAILED_REPRODUCIBILITY}
    )
    policy = recommend_rerun_policy(outcome)
    notes: list[str] = []
    if technical_or_repro > 0:
        notes.append("technical or reproducibility failures should be resolved before confidence updates")
    if promotion_ready < len(outcome.assay_outcomes):
        notes.append("not all assays are promotion-ready")
    if not notes:
        notes.append("batch outcome is promotion-ready for closed-loop updates")
    return BatchOutcomeAssessment(
        batch_id=outcome.batch_id,
        total_assays=len(outcome.assay_outcomes),
        promotion_ready_count=promotion_ready,
        technical_or_repro_failures=technical_or_repro,
        rerun_policy=policy,
        notes=notes,
    )


def validate_assay_observation_record(observation: AssayObservationRecord) -> list[ObservationValidationIssue]:
    """Validate assay observation consistency before acceptance evaluation."""
    issues: list[ObservationValidationIssue] = []
    if observation.replicate_values and len(observation.replicate_values) < 2:
        issues.append(
            ObservationValidationIssue(
                code="replicate-count-low",
                message="replicate_values should include at least two values when provided",
            )
        )
    if observation.dispersion is not None and not observation.replicate_values:
        issues.append(
            ObservationValidationIssue(
                code="dispersion-without-replicates",
                message="dispersion was provided without replicate values",
            )
        )
    if observation.below_detection_limit and observation.detection_limit is None:
        issues.append(
            ObservationValidationIssue(
                code="detection-limit-missing",
                message="below_detection_limit requires detection_limit to be specified",
            )
        )
    if observation.qc_state is QcState.FAILED and observation.qc_passed:
        issues.append(
            ObservationValidationIssue(
                code="qc-state-inconsistent",
                message="qc_state failed is inconsistent with qc_passed=True",
            )
        )
    return issues


def generate_feedback_records_from_outcome(
    outcome: ExperimentOutcome,
    *,
    program_id: str,
    cycle_id: str,
) -> tuple[list[LabFeedbackRecord], OutcomeFeedbackMapping]:
    """Generate structured feedback records from assay outcomes."""
    records: list[LabFeedbackRecord] = []
    for assay in outcome.assay_outcomes:
        records.append(
            LabFeedbackRecord(
                feedback_id=f"feedback:{outcome.batch_id}:{assay.assay_id}",
                program_id=program_id,
                cycle_id=cycle_id,
                summary=assay.observation_summary,
                related_assay_ids=[assay.assay_id],
                related_evidence_ids=[f"assay:{outcome.batch_id}:{assay.assay_id}"],
            )
        )
    mapping = OutcomeFeedbackMapping(
        batch_id=outcome.batch_id,
        feedback_ids=[record.feedback_id for record in records],
        assay_ids=[assay.assay_id for assay in outcome.assay_outcomes],
    )
    return records, mapping
