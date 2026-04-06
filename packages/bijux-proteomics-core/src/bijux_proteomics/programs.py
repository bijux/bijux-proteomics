# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Compatibility exports for the protein program domain."""

from __future__ import annotations

from bijux_proteomics.assays import AssayRequirement
from bijux_proteomics.constraints import ScientificConstraint
from bijux_proteomics.context import (
    ProgramContext,
    ProgramDeliveryContext,
    ProgramPortfolioContext,
)
from bijux_proteomics.criteria import MeasurementDirection, SuccessCriterion
from bijux_proteomics.lifecycle import (
    LifecycleTransition,
    ProgramLifecycle,
    advance_stage,
    allowed_next_stages,
)
from bijux_proteomics.operating_model import (
    DecisionOwnerRole,
    OperatingModel,
    ReviewCadence,
)
from bijux_proteomics.program_spec import (
    EvidenceNeed,
    ProgramSpec,
    ProgramStage,
    StageEligibility,
    assess_stage_eligibility,
    create_program_spec,
    program_summary,
    revise_program,
)
from bijux_proteomics.repositories import (
    DuplicateReviewDecisionError,
    ProgramNotFoundError,
    ReviewDecision,
    ReviewGateEvaluation,
    ReviewGateState,
    ReviewOutcome,
    decision_timeline,
    ensure_unique_gate_decision,
    evaluate_review_gate,
    evaluate_review_gates,
    latest_gate_decision,
    list_decisions_by_outcome,
    list_gate_decisions,
    require_program,
    validate_review_decision,
)
from bijux_proteomics.reviews import ReviewGate
from bijux_proteomics.targets import (
    OutcomeSeverity,
    ProteinTarget,
    TargetAnnotation,
    TargetOutcome,
    target_summary,
)

__all__ = [
    "AssayRequirement",
    "DecisionOwnerRole",
    "DuplicateReviewDecisionError",
    "EvidenceNeed",
    "LifecycleTransition",
    "MeasurementDirection",
    "OperatingModel",
    "OutcomeSeverity",
    "ProgramContext",
    "ProgramDeliveryContext",
    "ProgramPortfolioContext",
    "ProgramLifecycle",
    "ProgramNotFoundError",
    "ProgramSpec",
    "ProgramStage",
    "StageEligibility",
    "ProteinTarget",
    "TargetAnnotation",
    "TargetOutcome",
    "ReviewGate",
    "ReviewDecision",
    "ReviewCadence",
    "ReviewGateEvaluation",
    "ReviewGateState",
    "ReviewOutcome",
    "ScientificConstraint",
    "SuccessCriterion",
    "create_program_spec",
    "decision_timeline",
    "list_decisions_by_outcome",
    "list_gate_decisions",
    "ensure_unique_gate_decision",
    "evaluate_review_gate",
    "evaluate_review_gates",
    "latest_gate_decision",
    "require_program",
    "validate_review_decision",
    "advance_stage",
    "allowed_next_stages",
    "assess_stage_eligibility",
    "program_summary",
    "revise_program",
    "target_summary",
]
