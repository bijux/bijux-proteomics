# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Domain-level validation for protein programs."""

from __future__ import annotations

from bijux_proteomics_foundation import (
    IdentifierKind,
    JsonModel,
    ensure_identifier_kind,
)
from pydantic import ConfigDict, Field

from bijux_proteomics.program_spec import ProgramSpec, ProgramStage


class ProgramValidationIssue(JsonModel):
    """One domain validation issue for a program."""

    model_config = ConfigDict(extra="forbid")

    code: str = Field(..., min_length=1, description="Stable validation issue code.")
    message: str = Field(..., min_length=1, description="Human-readable issue text.")


def validate_program(program: ProgramSpec) -> list[ProgramValidationIssue]:
    """Return all detected domain issues for a program."""
    issues = validate_program_readiness(program)
    issues.extend(validate_assay_dependencies(program))
    issues.extend(validate_identifier_contracts(program))
    return issues


def validate_program_readiness(program: ProgramSpec) -> list[ProgramValidationIssue]:
    """Return program-level issues that block coherent lifecycle execution."""
    issues: list[ProgramValidationIssue] = []
    gate_ids = [gate.gate_id for gate in program.review_gates]
    assay_ids = [assay.assay_id for assay in program.assay_panel]
    criterion_ids = [criterion.criterion_id for criterion in program.success_criteria]
    criterion_metrics = {criterion.metric for criterion in program.success_criteria}
    criterion_metric_list = [criterion.metric for criterion in program.success_criteria]
    assay_readouts = {assay.readout for assay in program.assay_panel}
    blocking_assays = [assay for assay in program.assay_panel if assay.blocking]

    if (
        program.stage in {ProgramStage.REVIEW, ProgramStage.LAB_READY}
        and not program.review_gates
    ):
        issues.append(
            ProgramValidationIssue(
                code="review-gates-missing",
                message="review and lab-ready programs should define review gates",
            )
        )
    if program.stage is ProgramStage.LAB_READY and not program.assay_panel:
        issues.append(
            ProgramValidationIssue(
                code="assay-panel-missing",
                message="lab-ready programs should define an assay panel",
            )
        )
    if program.operating_model.human_review_required and not program.review_gates:
        issues.append(
            ProgramValidationIssue(
                code="human-review-unmodeled",
                message="human review is required but no review gates are present",
            )
        )
    if program.operating_model.lab_feedback_required and not program.assay_panel:
        issues.append(
            ProgramValidationIssue(
                code="lab-feedback-unmodeled",
                message="lab feedback is required but no assay panel is present",
            )
        )
    if (
        program.stage is ProgramStage.REVIEW
        and program.operating_model.human_review_required
        and not any(gate.blocking for gate in program.review_gates)
    ):
        issues.append(
            ProgramValidationIssue(
                code="blocking-review-gate-missing",
                message="review-stage programs should include at least one blocking review gate",
            )
        )
    if (
        program.stage is ProgramStage.LAB_READY
        and program.operating_model.lab_feedback_required
        and not blocking_assays
    ):
        issues.append(
            ProgramValidationIssue(
                code="blocking-assay-missing",
                message="lab-ready programs should include at least one blocking assay",
            )
        )
    if (
        program.stage is ProgramStage.LAB_READY
        and not program.translational_assumptions
    ):
        issues.append(
            ProgramValidationIssue(
                code="translational-assumptions-missing",
                message="lab-ready programs should define translational assumptions",
            )
        )
    if (
        program.stage in {ProgramStage.REVIEW, ProgramStage.LAB_READY}
        and not program.modality_context
    ):
        issues.append(
            ProgramValidationIssue(
                code="modality-context-missing",
                message="review and lab-ready programs should define modality_context",
            )
        )
    if (
        program.stage in {ProgramStage.REVIEW, ProgramStage.LAB_READY}
        and not program.key_unknowns
    ):
        issues.append(
            ProgramValidationIssue(
                code="key-unknowns-missing",
                message="review and lab-ready programs should define key_unknowns",
            )
        )
    if program.stage is ProgramStage.LAB_READY and not program.critical_failure_modes:
        issues.append(
            ProgramValidationIssue(
                code="critical-failure-modes-missing",
                message="lab-ready programs should define critical_failure_modes",
            )
        )
    if program.review_gates and not program.operating_model.decision_owner_roles:
        issues.append(
            ProgramValidationIssue(
                code="decision-owners-missing",
                message="programs with review gates should name decision owner roles",
            )
        )
    if not program.evidence_needs:
        issues.append(
            ProgramValidationIssue(
                code="evidence-needs-empty",
                message="programs should declare evidence needs explicitly",
            )
        )
    if program.assay_panel and not program.success_criteria:
        issues.append(
            ProgramValidationIssue(
                code="success-criteria-missing",
                message="programs with assay work should define success criteria",
            )
        )
    if program.assay_panel and program.success_criteria:
        unmapped_metrics = sorted(
            metric for metric in criterion_metrics if metric not in assay_readouts
        )
        if unmapped_metrics:
            issues.append(
                ProgramValidationIssue(
                    code="criterion-assay-unmapped",
                    message=(
                        "success criteria are missing mapped assay readouts: "
                        + ", ".join(unmapped_metrics)
                    ),
                )
            )
    issues.extend(
        ProgramValidationIssue(
            code="constraint-mitigation-missing",
            message=(
                f"blocking constraint '{constraint.constraint_id}' should define a mitigation_plan"
            ),
        )
        for constraint in program.constraints
        if constraint.blocker and not constraint.mitigation_plan
    )
    issues.extend(
        ProgramValidationIssue(
            code="liability-owner-missing",
            message=f"blocking liability '{liability.liability_id}' should declare owner_role",
        )
        for liability in program.liabilities
        if liability.blocker and not liability.owner_role
    )
    issues.extend(
        ProgramValidationIssue(
            code="liability-evidence-missing",
            message=f"blocking liability '{liability.liability_id}' should reference supporting evidence ids",
        )
        for liability in program.liabilities
        if liability.blocker and not liability.evidence_ids
    )
    for liability in program.liabilities:
        if liability.blocker and liability.mitigation:
            mitigation_text = liability.mitigation.lower()
            if not any(
                assay.assay_id.lower() in mitigation_text
                for assay in program.assay_panel
            ):
                issues.append(
                    ProgramValidationIssue(
                        code="liability-mitigation-assay-unmapped",
                        message=(
                            f"blocking liability '{liability.liability_id}' mitigation should reference a planned assay_id"
                        ),
                    )
                )
    if program.stage in {ProgramStage.REVIEW, ProgramStage.LAB_READY}:
        if not program.target.target_class:
            issues.append(
                ProgramValidationIssue(
                    code="target-class-missing",
                    message="review and lab-ready programs should define target_class",
                )
            )
        if not program.target.subcellular_localization:
            issues.append(
                ProgramValidationIssue(
                    code="target-localization-missing",
                    message="review and lab-ready programs should define target subcellular_localization",
                )
            )
    for gate in program.review_gates:
        if len(gate.decision_inputs) != len(set(gate.decision_inputs)):
            issues.append(
                ProgramValidationIssue(
                    code="review-inputs-duplicate",
                    message=f"review gate '{gate.gate_id}' repeats one or more decision inputs",
                )
            )
        if gate.blocking and not gate.required_roles:
            issues.append(
                ProgramValidationIssue(
                    code="blocking-gate-roles-missing",
                    message=f"blocking review gate '{gate.gate_id}' should declare required roles",
                )
            )
        missing_inputs = [
            decision_input
            for decision_input in gate.decision_inputs
            if decision_input not in assay_ids
            and decision_input not in criterion_metrics
            and decision_input
            not in {"evidence_bundle", "ranked_candidates", "review_packet"}
        ]
        if missing_inputs:
            issues.append(
                ProgramValidationIssue(
                    code="review-input-unmapped",
                    message=(
                        f"review gate '{gate.gate_id}' references unmapped inputs: "
                        + ", ".join(missing_inputs)
                    ),
                )
            )
        if program.stage is ProgramStage.LAB_READY and gate.blocking:
            mapped_assay_inputs = [
                decision_input
                for decision_input in gate.decision_inputs
                if decision_input in assay_ids
            ]
            non_blocking_inputs = [
                assay.assay_id
                for assay in program.assay_panel
                if assay.assay_id in mapped_assay_inputs and not assay.blocking
            ]
            if non_blocking_inputs:
                issues.append(
                    ProgramValidationIssue(
                        code="blocking-gate-needs-blocking-assays",
                        message=(
                            f"blocking review gate '{gate.gate_id}' references non-blocking assays: "
                            + ", ".join(sorted(non_blocking_inputs))
                        ),
                    )
                )
    if len(gate_ids) != len(set(gate_ids)):
        issues.append(
            ProgramValidationIssue(
                code="review-gate-ids-duplicate",
                message="review gates should use unique identifiers",
            )
        )
    if len(assay_ids) != len(set(assay_ids)):
        issues.append(
            ProgramValidationIssue(
                code="assay-ids-duplicate",
                message="assays should use unique identifiers",
            )
        )
    if len(criterion_ids) != len(set(criterion_ids)):
        issues.append(
            ProgramValidationIssue(
                code="criterion-ids-duplicate",
                message="success criteria should use unique identifiers",
            )
        )
    if len(criterion_metric_list) != len(set(criterion_metric_list)):
        issues.append(
            ProgramValidationIssue(
                code="criterion-metrics-duplicate",
                message="success criteria should not duplicate the same metric key",
            )
        )
    needs = {need.value for need in program.evidence_needs}
    if program.review_gates and "assay" not in needs:
        issues.append(
            ProgramValidationIssue(
                code="review-needs-assay-evidence",
                message="programs with review gates should include assay evidence needs",
            )
        )
    if program.assay_panel and "assay" not in needs:
        issues.append(
            ProgramValidationIssue(
                code="assay-panel-needs-assay-evidence",
                message="programs with assay panels should include assay evidence needs",
            )
        )
    return issues


def validate_assay_dependencies(program: ProgramSpec) -> list[ProgramValidationIssue]:
    """Return issues where assay, criterion, and stage semantics drift apart."""
    issues: list[ProgramValidationIssue] = []
    readouts = {assay.readout for assay in program.assay_panel}
    assay_ids = {assay.assay_id for assay in program.assay_panel}

    for criterion in program.success_criteria:
        if criterion.metric not in readouts and criterion.metric not in assay_ids:
            issues.append(
                ProgramValidationIssue(
                    code="criterion-without-assay",
                    message=(
                        f"success criterion '{criterion.criterion_id}' does not map to any assay "
                        "readout or assay identifier"
                    ),
                )
            )
        if criterion.direction.value == "bound" and criterion.threshold <= 0:
            issues.append(
                ProgramValidationIssue(
                    code="bound-criterion-invalid-threshold",
                    message=(
                        f"bound criterion '{criterion.criterion_id}' should use a positive threshold"
                    ),
                )
            )
        if criterion.direction.value == "bound" and criterion.upper_threshold is None:
            issues.append(
                ProgramValidationIssue(
                    code="bound-criterion-upper-threshold-missing",
                    message=(
                        f"bound criterion '{criterion.criterion_id}' should declare an upper_threshold"
                    ),
                )
            )
    if program.stage is ProgramStage.LEARNING and not program.assay_panel:
        issues.append(
            ProgramValidationIssue(
                code="learning-stage-assays-missing",
                message="learning-stage programs should retain assay definitions for feedback capture",
            )
        )
    return issues


def validate_identifier_contracts(program: ProgramSpec) -> list[ProgramValidationIssue]:
    """Validate identifier kind prefixes for core program entities."""
    issues: list[ProgramValidationIssue] = []

    def _check(value: str, kind: IdentifierKind, code: str, message: str) -> None:
        try:
            ensure_identifier_kind(value, kind)
        except ValueError:
            issues.append(ProgramValidationIssue(code=code, message=message))

    _check(
        program.program_id,
        IdentifierKind.PROGRAM,
        "program-id-prefix-invalid",
        "program_id should use a 'prog-' prefix",
    )
    _check(
        program.target.target_id,
        IdentifierKind.TARGET,
        "target-id-prefix-invalid",
        "target_id should use a 'target-' prefix",
    )
    for assay in program.assay_panel:
        _check(
            assay.assay_id,
            IdentifierKind.ASSAY,
            "assay-id-prefix-invalid",
            f"assay_id '{assay.assay_id}' should use an 'assay-' prefix",
        )
    return issues
