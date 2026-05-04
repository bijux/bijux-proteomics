# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Compatibility exports for the protein program domain."""

from __future__ import annotations

from bijux_proteomics.domain.assays import AssayRequirement
from bijux_proteomics.domain.constraints import ScientificConstraint
from bijux_proteomics.domain.context import (
    ProgramContext,
    ProgramDeliveryContext,
    ProgramPortfolioContext,
)
from bijux_proteomics.domain.criteria import (
    MeasurementDirection,
    MetricFamily,
    SuccessCriterion,
    build_assay_grounded_criteria,
)
from bijux_proteomics.domain.liabilities import LiabilityCategory, ProgramLiability
from bijux_proteomics.domain.lifecycle import (
    LifecycleTransition,
    ProgramLifecycle,
    advance_stage,
    allowed_next_stages,
)
from bijux_proteomics.domain.operating_model import (
    DecisionOwnerRole,
    OperatingModel,
    ReviewCadence,
)
from bijux_proteomics.domain.program_spec import (
    EvidenceNeed,
    ProgramSpec,
    ProgramStage,
    StageEligibility,
    assess_stage_eligibility,
    create_program_spec,
    program_summary,
    revise_program,
)
from bijux_proteomics.domain.repositories import (
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
from bijux_proteomics.domain.reviews import ReviewGate
from bijux_proteomics.domain.targets import (
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
    "LiabilityCategory",
    "MeasurementDirection",
    "MetricFamily",
    "OperatingModel",
    "OutcomeSeverity",
    "ProgramContext",
    "ProgramDeliveryContext",
    "ProgramPortfolioContext",
    "ProgramLifecycle",
    "ProgramNotFoundError",
    "ProgramSpec",
    "ProgramLiability",
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
    "build_assay_grounded_criteria",
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
