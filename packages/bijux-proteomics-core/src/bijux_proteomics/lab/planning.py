# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Study-owned laboratory planning and targeted-method contracts."""

from __future__ import annotations

from enum import StrEnum
import json

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

    library = (
        risk_library if risk_library is not None else build_default_lab_risk_library()
    )
    triggered: list[LabRiskRule] = []

    for rule in library:
        if (
            (
                rule.kind is LabRiskKind.INSUFFICIENT_MATERIAL
                and context.available_material_ng < context.required_material_ng
            )
            or rule.kind is LabRiskKind.MISSING_CONTROLS
            and context.control_count == 0
            or rule.kind is LabRiskKind.POOR_REPLICATION
            and context.replicate_count < 2
            or (
                rule.kind is LabRiskKind.INSTRUMENT_LIMIT
                and context.requested_hours > context.instrument_capacity_hours
            )
            or (
                rule.kind is LabRiskKind.AMBIGUOUS_TARGET_PEPTIDES
                and context.ambiguous_target_peptide_count > 0
            )
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


class TargetedTransitionFragment(JsonModel):
    """One fragment transition for targeted proteomics assays."""

    model_config = ConfigDict(extra="forbid")

    ion_label: str = Field(..., min_length=1)
    fragment_mz: float = Field(..., gt=0.0)
    relative_intensity: float = Field(..., ge=0.0)


class TargetedTransitionEntry(JsonModel):
    """One targeted transition entry with peptide and retention context."""

    model_config = ConfigDict(extra="forbid")

    transition_id: str = Field(..., min_length=1)
    peptide_sequence: str = Field(..., min_length=1)
    charge_state: int = Field(..., ge=1)
    precursor_mz: float = Field(..., gt=0.0)
    retention_window_start_min: float = Field(..., ge=0.0)
    retention_window_end_min: float = Field(..., ge=0.0)
    fragments: tuple[TargetedTransitionFragment, ...] = Field(default_factory=tuple)
    instrument_caveats: tuple[str, ...] = Field(default_factory=tuple)


class TargetedTransitionListModel(JsonModel):
    """Targeted transition list with method and instrument caveat metadata."""

    model_config = ConfigDict(extra="forbid")

    method: str = Field(..., min_length=1)
    entries: tuple[TargetedTransitionEntry, ...] = Field(default_factory=tuple)


class TargetedTransitionListValidationIssue(JsonModel):
    """Validation issue for targeted transition list contracts."""

    model_config = ConfigDict(extra="forbid")

    code: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)
    transition_id: str | None = None


class TargetedTransitionListValidationReport(JsonModel):
    """Validation report for targeted transition list model."""

    model_config = ConfigDict(extra="forbid")

    valid: bool
    issues: tuple[TargetedTransitionListValidationIssue, ...] = Field(
        default_factory=tuple
    )


def validate_targeted_transition_list(
    model: TargetedTransitionListModel,
) -> TargetedTransitionListValidationReport:
    """Validate peptide/charge/fragment/RT-window transitions and caveat coverage."""

    issues: list[TargetedTransitionListValidationIssue] = []
    for entry in model.entries:
        if entry.retention_window_end_min <= entry.retention_window_start_min:
            issues.append(
                TargetedTransitionListValidationIssue(
                    code="invalid_retention_window",
                    message="retention window end must be greater than start",
                    transition_id=entry.transition_id,
                )
            )
        if not entry.fragments:
            issues.append(
                TargetedTransitionListValidationIssue(
                    code="missing_fragments",
                    message="transition must include at least one fragment ion",
                    transition_id=entry.transition_id,
                )
            )
    return TargetedTransitionListValidationReport(
        valid=not issues, issues=tuple(issues)
    )


class TargetedWorkflowMethod(StrEnum):
    """Targeted workflow methods with explicit planning boundaries."""

    PRM = "prm"
    SRM = "srm"
    MRM = "mrm"


class TargetedWorkflowBoundaryInput(JsonModel):
    """Inputs needed to evaluate targeted workflow boundary readiness."""

    model_config = ConfigDict(extra="forbid")

    method: TargetedWorkflowMethod
    has_transition_list: bool
    has_retention_windows: bool
    has_collision_energy_profile: bool
    has_instrument_method_template: bool


class TargetedWorkflowBoundaryReport(JsonModel):
    """Support/refusal result for PRM/SRM/MRM targeted workflows."""

    model_config = ConfigDict(extra="forbid")

    method: TargetedWorkflowMethod
    supported: bool
    assumptions: tuple[str, ...] = Field(default_factory=tuple)
    refusal_reason: str | None = None


class TargetedPlatformSupportState(StrEnum):
    """Practical support posture for one targeted platform and method combination."""

    SUPPORTED = "supported"
    PARTIAL = "partial"
    REFUSED = "refused"


class TargetedPlatformAssumptionInput(JsonModel):
    """Method, platform, and assumption context for targeted follow-up support."""

    model_config = ConfigDict(extra="forbid")

    platform_id: str = Field(..., min_length=1)
    method: TargetedWorkflowMethod
    has_transition_list: bool
    has_retention_windows: bool
    has_collision_energy_profile: bool
    has_instrument_method_template: bool
    has_heavy_reference: bool
    has_calibration_standards: bool
    has_vendor_tuning_profile: bool


class TargetedPlatformSupportEntry(JsonModel):
    """One platform support entry with explicit missing assumptions and partial rules."""

    model_config = ConfigDict(extra="forbid")

    platform_id: str = Field(..., min_length=1)
    method: TargetedWorkflowMethod
    support_state: TargetedPlatformSupportState
    required_assumptions: tuple[str, ...] = Field(default_factory=tuple)
    missing_assumptions: tuple[str, ...] = Field(default_factory=tuple)
    partial_support_definition: str = Field(..., min_length=1)
    note: str = Field(..., min_length=1)


class TargetedPlatformSupportMatrixReport(JsonModel):
    """Support matrix over targeted method/platform assumptions."""

    model_config = ConfigDict(extra="forbid")

    entries: tuple[TargetedPlatformSupportEntry, ...] = Field(default_factory=tuple)
    supported_count: int = Field(..., ge=0)
    partial_count: int = Field(..., ge=0)
    refused_count: int = Field(..., ge=0)


def evaluate_targeted_workflow_boundary(
    payload: TargetedWorkflowBoundaryInput,
) -> TargetedWorkflowBoundaryReport:
    """Support or refuse targeted workflows with explicit method assumptions."""

    assumptions = [
        "transition list quality is reviewable before execution",
        "retention windows reflect comparable LC conditions",
        "instrument templates are reviewed by lab operators",
    ]
    missing: list[str] = []
    if not payload.has_transition_list:
        missing.append("transition_list")
    if not payload.has_retention_windows:
        missing.append("retention_windows")
    if not payload.has_collision_energy_profile:
        missing.append("collision_energy_profile")
    if not payload.has_instrument_method_template:
        missing.append("instrument_method_template")

    if missing:
        return TargetedWorkflowBoundaryReport(
            method=payload.method,
            supported=False,
            assumptions=tuple(assumptions),
            refusal_reason=(
                "workflow is refused because required targeted-method assumptions are missing: "
                + ", ".join(missing)
            ),
        )

    return TargetedWorkflowBoundaryReport(
        method=payload.method,
        supported=True,
        assumptions=tuple(assumptions),
        refusal_reason=None,
    )


def build_targeted_platform_support_matrix(
    payloads: tuple[TargetedPlatformAssumptionInput, ...],
) -> TargetedPlatformSupportMatrixReport:
    """Classify targeted platform support with explicit partial and refusal boundaries."""

    entries: list[TargetedPlatformSupportEntry] = []
    required_assumptions = (
        "transition_list",
        "retention_windows",
        "collision_energy_profile",
        "instrument_method_template",
        "heavy_reference",
        "calibration_standards",
        "vendor_tuning_profile",
    )
    hard_blocking = {
        "transition_list",
        "retention_windows",
        "collision_energy_profile",
    }
    for payload in payloads:
        observed = {
            "transition_list": payload.has_transition_list,
            "retention_windows": payload.has_retention_windows,
            "collision_energy_profile": payload.has_collision_energy_profile,
            "instrument_method_template": payload.has_instrument_method_template,
            "heavy_reference": payload.has_heavy_reference,
            "calibration_standards": payload.has_calibration_standards,
            "vendor_tuning_profile": payload.has_vendor_tuning_profile,
        }
        missing = tuple(name for name in required_assumptions if not observed[name])
        if any(name in hard_blocking for name in missing):
            support_state = TargetedPlatformSupportState.REFUSED
            note = "targeted follow-up is refused because the method lacks one or more hard assay preconditions"
        elif missing:
            support_state = TargetedPlatformSupportState.PARTIAL
            note = "targeted follow-up remains reviewable, but platform-specific standards or templates are still incomplete"
        else:
            support_state = TargetedPlatformSupportState.SUPPORTED
            note = "targeted follow-up satisfies transition, timing, standards, heavy-reference, and platform-tuning assumptions"
        entries.append(
            TargetedPlatformSupportEntry(
                platform_id=payload.platform_id,
                method=payload.method,
                support_state=support_state,
                required_assumptions=required_assumptions,
                missing_assumptions=missing,
                partial_support_definition=(
                    "partial targeted support means the assay is specific enough to review, but missing templates, heavy references, calibration standards, "
                    "or vendor tuning still block strong platform-ready follow-up claims"
                ),
                note=note,
            )
        )

    supported_count = sum(
        entry.support_state is TargetedPlatformSupportState.SUPPORTED
        for entry in entries
    )
    partial_count = sum(
        entry.support_state is TargetedPlatformSupportState.PARTIAL for entry in entries
    )
    refused_count = len(entries) - supported_count - partial_count
    return TargetedPlatformSupportMatrixReport(
        entries=tuple(entries),
        supported_count=supported_count,
        partial_count=partial_count,
        refused_count=refused_count,
    )


class LimsHandoffEntry(JsonModel):
    """One versioned LIMS-import handoff row."""

    model_config = ConfigDict(extra="forbid")

    sample_id: str = Field(..., min_length=1)
    target_id: str = Field(..., min_length=1)
    method: str = Field(..., min_length=1)
    plate_well: str = Field(..., min_length=2)
    replicate_id: str = Field(..., min_length=1)


class LimsHandoffProfile(JsonModel):
    """Versioned LIMS handoff export profile with JSON and TSV payloads."""

    model_config = ConfigDict(extra="forbid")

    profile_version: str = Field(..., min_length=1)
    handoff_id: str = Field(..., min_length=1)
    json_payload: str = Field(..., min_length=1)
    tsv_payload: str = Field(..., min_length=1)


def build_lims_handoff_profile(
    *,
    profile_version: str,
    handoff_id: str,
    entries: tuple[LimsHandoffEntry, ...],
) -> LimsHandoffProfile:
    """Export versioned handoff data suitable for LIMS-style imports."""

    rows = tuple(sorted(entries, key=lambda entry: (entry.sample_id, entry.target_id)))
    payload = {
        "profile_version": profile_version,
        "handoff_id": handoff_id,
        "entries": [entry.to_dict() for entry in rows],
    }
    tsv_header = "sample_id\ttarget_id\tmethod\tplate_well\treplicate_id"
    tsv_rows = [
        "\t".join(
            (
                entry.sample_id,
                entry.target_id,
                entry.method,
                entry.plate_well,
                entry.replicate_id,
            )
        )
        for entry in rows
    ]
    return LimsHandoffProfile(
        profile_version=profile_version,
        handoff_id=handoff_id,
        json_payload=json.dumps(payload, sort_keys=True, separators=(",", ":")),
        tsv_payload="\n".join([tsv_header, *tsv_rows]) + ("\n" if tsv_rows else ""),
    )


class LabReviewPacketInput(JsonModel):
    """Structured input required to render a lab decision brief."""

    model_config = ConfigDict(extra="forbid")

    packet_id: str = Field(..., min_length=1)
    assay_rationale: str = Field(..., min_length=1)
    target_evidence_ids: tuple[str, ...] = Field(default_factory=tuple)
    control_ids: tuple[str, ...] = Field(default_factory=tuple)
    risk_ids: tuple[str, ...] = Field(default_factory=tuple)
    capacity_summary: str = Field(..., min_length=1)
    handoff_files: tuple[str, ...] = Field(default_factory=tuple)


class LabReviewPacketRendered(JsonModel):
    """Rendered lab decision brief bundle for planning and board review."""

    model_config = ConfigDict(extra="forbid")

    packet_id: str = Field(..., min_length=1)
    packet_json: str = Field(..., min_length=1)
    packet_markdown: str = Field(..., min_length=1)


def build_lab_review_packet_rendering(
    payload: LabReviewPacketInput,
) -> LabReviewPacketRendered:
    """Render assay rationale/evidence/controls/risk/capacity/handoff packet views."""

    packet = {
        "packet_id": payload.packet_id,
        "assay_rationale": payload.assay_rationale,
        "target_evidence_ids": list(payload.target_evidence_ids),
        "control_ids": list(payload.control_ids),
        "risk_ids": list(payload.risk_ids),
        "capacity_summary": payload.capacity_summary,
        "handoff_files": list(payload.handoff_files),
    }
    markdown_lines = [
        f"# Lab Review Packet {payload.packet_id}",
        "",
        f"- Assay rationale: {payload.assay_rationale}",
        f"- Target evidence: {', '.join(payload.target_evidence_ids) if payload.target_evidence_ids else 'none'}",
        f"- Controls: {', '.join(payload.control_ids) if payload.control_ids else 'none'}",
        f"- Risks: {', '.join(payload.risk_ids) if payload.risk_ids else 'none'}",
        f"- Capacity: {payload.capacity_summary}",
        f"- Handoff files: {', '.join(payload.handoff_files) if payload.handoff_files else 'none'}",
    ]
    return LabReviewPacketRendered(
        packet_id=payload.packet_id,
        packet_json=json.dumps(packet, sort_keys=True, separators=(",", ":")),
        packet_markdown="\n".join(markdown_lines) + "\n",
    )


def render_lab_review_packet(payload: LabReviewPacketInput) -> LabReviewPacketRendered:
    """Compatibility wrapper for the legacy lab review packet renderer name."""

    return build_lab_review_packet_rendering(payload)


class WetLabAutomationBoundaryInput(JsonModel):
    """Input payload used to enforce wet-lab automation boundaries."""

    model_config = ConfigDict(extra="forbid")

    planning_payload_id: str = Field(..., min_length=1)
    requested_execution: bool
    adapter_proof_id: str | None = None


class WetLabAutomationBoundaryReport(JsonModel):
    """Boundary decision separating advisory planning from executable automation."""

    model_config = ConfigDict(extra="forbid")

    planning_payload_id: str = Field(..., min_length=1)
    allowed_execution: bool
    planning_label: str = Field(..., min_length=1)
    execution_label: str = Field(..., min_length=1)
    reason: str = Field(..., min_length=1)


def enforce_wet_lab_automation_boundary(
    payload: WetLabAutomationBoundaryInput,
) -> WetLabAutomationBoundaryReport:
    """Prevent instrument-ready automation when adapter proof is not present."""

    if payload.requested_execution and not payload.adapter_proof_id:
        return WetLabAutomationBoundaryReport(
            planning_payload_id=payload.planning_payload_id,
            allowed_execution=False,
            planning_label="advisory",
            execution_label="refused",
            reason=(
                "execution is refused because no adapter proof exists; planning output remains advisory"
            ),
        )

    if payload.requested_execution and payload.adapter_proof_id:
        return WetLabAutomationBoundaryReport(
            planning_payload_id=payload.planning_payload_id,
            allowed_execution=True,
            planning_label="advisory",
            execution_label="executable",
            reason="execution allowed because adapter proof is present",
        )

    return WetLabAutomationBoundaryReport(
        planning_payload_id=payload.planning_payload_id,
        allowed_execution=False,
        planning_label="advisory",
        execution_label="not_requested",
        reason="execution was not requested",
    )
