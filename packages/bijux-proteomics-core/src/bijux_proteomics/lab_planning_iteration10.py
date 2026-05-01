# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Lab planning capability surfaces for iteration 10."""

from __future__ import annotations

from enum import StrEnum

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel


class AssayProgressionState(StrEnum):
    """Lifecycle states for assay progression planning."""

    DISCOVERY = "discovery"
    VERIFICATION = "verification"
    VALIDATION = "validation"
    TARGETED_FOLLOW_UP = "targeted_follow_up"
    COMPLETED = "completed"
    BLOCKED = "blocked"


class AssayProgressionTransition(JsonModel):
    """One progression transition with deterministic rationale."""

    model_config = ConfigDict(extra="forbid")

    from_state: AssayProgressionState
    to_state: AssayProgressionState
    rationale: str = Field(..., min_length=1)


class AssayProgressionModel(JsonModel):
    """Assay progression record with auditable transitions."""

    model_config = ConfigDict(extra="forbid")

    assay_id: str = Field(..., min_length=1)
    current_state: AssayProgressionState
    transitions: tuple[AssayProgressionTransition, ...] = Field(default_factory=tuple)


_ALLOWED_NEXT_STATES: dict[AssayProgressionState, set[AssayProgressionState]] = {
    AssayProgressionState.DISCOVERY: {
        AssayProgressionState.VERIFICATION,
        AssayProgressionState.BLOCKED,
    },
    AssayProgressionState.VERIFICATION: {
        AssayProgressionState.VALIDATION,
        AssayProgressionState.TARGETED_FOLLOW_UP,
        AssayProgressionState.BLOCKED,
    },
    AssayProgressionState.VALIDATION: {
        AssayProgressionState.TARGETED_FOLLOW_UP,
        AssayProgressionState.COMPLETED,
        AssayProgressionState.BLOCKED,
    },
    AssayProgressionState.TARGETED_FOLLOW_UP: {
        AssayProgressionState.VALIDATION,
        AssayProgressionState.COMPLETED,
        AssayProgressionState.BLOCKED,
    },
    AssayProgressionState.COMPLETED: set(),
    AssayProgressionState.BLOCKED: {
        AssayProgressionState.DISCOVERY,
        AssayProgressionState.VERIFICATION,
        AssayProgressionState.VALIDATION,
        AssayProgressionState.TARGETED_FOLLOW_UP,
    },
}


def transition_assay_progression(
    model: AssayProgressionModel,
    *,
    to_state: AssayProgressionState,
    rationale: str,
) -> AssayProgressionModel:
    """Move assay progression state while enforcing explicit planning boundaries."""

    allowed = _ALLOWED_NEXT_STATES[model.current_state]
    if to_state not in allowed:
        raise ValueError(
            f"cannot move assay from {model.current_state.value!r} to {to_state.value!r}"
        )
    transitions = list(model.transitions)
    transitions.append(
        AssayProgressionTransition(
            from_state=model.current_state,
            to_state=to_state,
            rationale=rationale,
        )
    )
    return model.model_copy(
        update={
            "current_state": to_state,
            "transitions": tuple(transitions),
        }
    )


class AssayDesignProfile(JsonModel):
    """One assay design option for comparison."""

    model_config = ConfigDict(extra="forbid")

    design_id: str = Field(..., min_length=1)
    multiplex_channels: int = Field(..., ge=1)
    fraction_count: int = Field(..., ge=1)
    control_count: int = Field(..., ge=0)
    replicate_count: int = Field(..., ge=1)
    capacity_demand: float = Field(..., ge=0.0)
    expected_evidence_gain: float = Field(..., ge=0.0, le=1.0)


class AssayDesignComparisonEntry(JsonModel):
    """One scored assay design comparison entry."""

    model_config = ConfigDict(extra="forbid")

    design_id: str = Field(..., min_length=1)
    score: float
    rationale: str = Field(..., min_length=1)


class AssayDesignComparisonReport(JsonModel):
    """Comparison report across assay design options."""

    model_config = ConfigDict(extra="forbid")

    entries: tuple[AssayDesignComparisonEntry, ...] = Field(default_factory=tuple)
    preferred_design_id: str | None = None


def compare_assay_designs(
    profiles: tuple[AssayDesignProfile, ...],
) -> AssayDesignComparisonReport:
    """Compare multiplex/fractionation/controls/replication/capacity/evidence gain."""

    scored: list[AssayDesignComparisonEntry] = []
    for profile in profiles:
        score = (
            (profile.expected_evidence_gain * 100.0)
            + (profile.control_count * 2.0)
            + (profile.replicate_count * 1.5)
            + min(6.0, float(profile.multiplex_channels) / 2.0)
            + min(8.0, float(profile.fraction_count))
            - (profile.capacity_demand * 4.0)
        )
        scored.append(
            AssayDesignComparisonEntry(
                design_id=profile.design_id,
                score=score,
                rationale=(
                    "score balances expected evidence gain, controls, replication, "
                    "multiplex/fraction coverage, and capacity pressure"
                ),
            )
        )

    ranked = tuple(sorted(scored, key=lambda entry: (-entry.score, entry.design_id)))
    return AssayDesignComparisonReport(
        entries=ranked,
        preferred_design_id=ranked[0].design_id if ranked else None,
    )


class LabRiskKind(StrEnum):
    """Risk kinds covered by the lab planning risk library."""

    INSUFFICIENT_MATERIAL = "insufficient_material"
    MISSING_CONTROLS = "missing_controls"
    POOR_REPLICATION = "poor_replication"
    INSTRUMENT_LIMIT = "instrument_limit"
    AMBIGUOUS_TARGET_PEPTIDES = "ambiguous_target_peptides"


class LabRiskRule(JsonModel):
    """One reusable lab risk rule with severity and mitigation guidance."""

    model_config = ConfigDict(extra="forbid")

    risk_id: str = Field(..., min_length=1)
    kind: LabRiskKind
    severity: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)
    mitigation: str = Field(..., min_length=1)


class LabRiskAssessmentContext(JsonModel):
    """Minimal context used to evaluate lab risks."""

    model_config = ConfigDict(extra="forbid")

    available_material_ng: float = Field(..., ge=0.0)
    required_material_ng: float = Field(..., ge=0.0)
    control_count: int = Field(..., ge=0)
    replicate_count: int = Field(..., ge=0)
    instrument_capacity_hours: float = Field(..., ge=0.0)
    requested_hours: float = Field(..., ge=0.0)
    ambiguous_target_peptide_count: int = Field(..., ge=0)


class LabRiskAssessmentReport(JsonModel):
    """Triggered risks from the risk library for one assay planning context."""

    model_config = ConfigDict(extra="forbid")

    triggered_risks: tuple[LabRiskRule, ...] = Field(default_factory=tuple)


def build_default_lab_risk_library() -> tuple[LabRiskRule, ...]:
    """Build the default risk library for common lab-planning failure modes."""

    return (
        LabRiskRule(
            risk_id="risk-material",
            kind=LabRiskKind.INSUFFICIENT_MATERIAL,
            severity="high",
            message="available material is below required assay input",
            mitigation="reduce assay scope or collect additional material",
        ),
        LabRiskRule(
            risk_id="risk-controls",
            kind=LabRiskKind.MISSING_CONTROLS,
            severity="high",
            message="assay design has no control samples",
            mitigation="add control lanes/wells before handoff",
        ),
        LabRiskRule(
            risk_id="risk-replication",
            kind=LabRiskKind.POOR_REPLICATION,
            severity="medium",
            message="replication depth is below minimum planning threshold",
            mitigation="increase biological or technical replicates",
        ),
        LabRiskRule(
            risk_id="risk-instrument",
            kind=LabRiskKind.INSTRUMENT_LIMIT,
            severity="high",
            message="requested runtime exceeds available instrument capacity",
            mitigation="split batches or reschedule instrument queue",
        ),
        LabRiskRule(
            risk_id="risk-ambiguous-peptide",
            kind=LabRiskKind.AMBIGUOUS_TARGET_PEPTIDES,
            severity="medium",
            message="target peptide mapping remains ambiguous",
            mitigation="prioritize unique transitions or orthogonal assays",
        ),
    )


def evaluate_lab_risks(
    context: LabRiskAssessmentContext,
    *,
    risk_library: tuple[LabRiskRule, ...] | None = None,
) -> LabRiskAssessmentReport:
    """Evaluate assay context against risk-library conditions."""

    library = risk_library if risk_library is not None else build_default_lab_risk_library()
    triggered: list[LabRiskRule] = []

    for rule in library:
        if (
            rule.kind is LabRiskKind.INSUFFICIENT_MATERIAL
            and context.available_material_ng < context.required_material_ng
        ):
            triggered.append(rule)
        elif rule.kind is LabRiskKind.MISSING_CONTROLS and context.control_count == 0:
            triggered.append(rule)
        elif rule.kind is LabRiskKind.POOR_REPLICATION and context.replicate_count < 2:
            triggered.append(rule)
        elif (
            rule.kind is LabRiskKind.INSTRUMENT_LIMIT
            and context.requested_hours > context.instrument_capacity_hours
        ):
            triggered.append(rule)
        elif (
            rule.kind is LabRiskKind.AMBIGUOUS_TARGET_PEPTIDES
            and context.ambiguous_target_peptide_count > 0
        ):
            triggered.append(rule)

    return LabRiskAssessmentReport(triggered_risks=tuple(triggered))


class LabCapacityModelWithUncertainty(JsonModel):
    """Capacity model over hours/samples/fractions/queue/budget with uncertainty."""

    model_config = ConfigDict(extra="forbid")

    instrument_hours_available: float = Field(..., ge=0.0)
    instrument_hours_required: float = Field(..., ge=0.0)
    sample_count: int = Field(..., ge=0)
    fraction_count: int = Field(..., ge=0)
    queue_depth: int = Field(..., ge=0)
    budget_available: float = Field(..., ge=0.0)
    budget_required: float = Field(..., ge=0.0)
    schedule_uncertainty: float = Field(..., ge=0.0, le=1.0)
    budget_uncertainty: float = Field(..., ge=0.0, le=1.0)
    time_utilization_ratio: float = Field(..., ge=0.0)
    budget_utilization_ratio: float = Field(..., ge=0.0)
    constrained: bool


def build_capacity_model_with_uncertainty(
    *,
    instrument_hours_available: float,
    instrument_hours_required: float,
    sample_count: int,
    fraction_count: int,
    queue_depth: int,
    budget_available: float,
    budget_required: float,
    schedule_uncertainty: float,
    budget_uncertainty: float,
) -> LabCapacityModelWithUncertainty:
    """Build deterministic capacity model including uncertainty-adjusted utilization."""

    available_time = max(0.1, instrument_hours_available * (1.0 - schedule_uncertainty))
    available_budget = max(0.1, budget_available * (1.0 - budget_uncertainty))
    time_utilization_ratio = instrument_hours_required / available_time
    budget_utilization_ratio = budget_required / available_budget

    return LabCapacityModelWithUncertainty(
        instrument_hours_available=instrument_hours_available,
        instrument_hours_required=instrument_hours_required,
        sample_count=sample_count,
        fraction_count=fraction_count,
        queue_depth=queue_depth,
        budget_available=budget_available,
        budget_required=budget_required,
        schedule_uncertainty=schedule_uncertainty,
        budget_uncertainty=budget_uncertainty,
        time_utilization_ratio=time_utilization_ratio,
        budget_utilization_ratio=budget_utilization_ratio,
        constrained=(time_utilization_ratio > 1.0 or budget_utilization_ratio > 1.0),
    )
