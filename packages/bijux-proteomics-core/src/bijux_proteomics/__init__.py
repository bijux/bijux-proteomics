# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Bijux Proteomics program and execution primitives."""

from __future__ import annotations

from bijux_proteomics.assays import AssayRequirement
from bijux_proteomics.context import (
    ProgramContext,
    ProgramDeliveryContext,
    ProgramPortfolioContext,
)
from bijux_proteomics.constraints import ConstraintCategory, ScientificConstraint
from bijux_proteomics.criteria import MeasurementDirection, MetricFamily, SuccessCriterion
from bijux_proteomics.exceptions import (
    BijuxProteomicsError,
    InvalidLifecycleTransitionError,
    ProgramValidationError,
    ReviewGateBlockedError,
)
from bijux_proteomics.execution_backend import ExecutionBackend, ExecutionRequest
from bijux_proteomics.lifecycle import (
    LifecycleTransition,
    ProgramLifecycle,
    advance_stage,
    allowed_next_stages,
)
from bijux_proteomics.liabilities import LiabilityCategory, ProgramLiability
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
from bijux_proteomics.reviews import ReviewGate
from bijux_proteomics.repositories import (
    DuplicateReviewDecisionError,
    ProgramRevisionConflictError,
    ProgramRepository,
    ProgramNotFoundError,
    ReviewDecision,
    ReviewDecisionRepository,
    DecisionQuery,
    ReviewGateEvaluation,
    ReviewGateState,
    ReviewOutcome,
    decision_timeline,
    ensure_unique_gate_decision,
    evaluate_review_gate,
    evaluate_review_gates,
    list_decisions_by_outcome,
    list_gate_decisions,
    query_decisions,
    ensure_review_clearance,
    latest_gate_decision,
    require_program,
    ensure_program_revision,
    validate_review_decision,
)
from bijux_proteomics.runtime_adapter import (
    AgenticProteinsBackend,
    MissingExecutionBackendError,
)
from bijux_proteomics_foundation import DocumentSchema, JsonModel
from bijux_proteomics.sequences import ProteinSequence, sequence_length
from bijux_proteomics.targets import (
    OutcomeSeverity,
    ProteinTarget,
    TargetAnnotation,
    TargetOutcome,
    target_summary,
)
from bijux_proteomics.validation import (
    ProgramValidationIssue,
    validate_assay_dependencies,
    validate_program,
    validate_program_readiness,
)
from bijux_proteomics.runner import ProgramExecutionRequest, execute_program

__all__ = [
    "AssayRequirement",
    "EvidenceNeed",
    "BijuxProteomicsError",
    "DecisionOwnerRole",
    "InvalidLifecycleTransitionError",
    "LiabilityCategory",
    "LifecycleTransition",
    "MeasurementDirection",
    "MetricFamily",
    "OperatingModel",
    "OutcomeSeverity",
    "ProgramContext",
    "ProgramDeliveryContext",
    "ProgramPortfolioContext",
    "ProgramLiability",
    "ProgramLifecycle",
    "ProgramRepository",
    "ProgramExecutionRequest",
    "ProgramStage",
    "ProgramSpec",
    "ProgramValidationError",
    "ProgramValidationIssue",
    "StageEligibility",
    "ProteinTarget",
    "TargetAnnotation",
    "TargetOutcome",
    "ProteinSequence",
    "JsonModel",
    "ReviewGate",
    "ReviewDecision",
    "DecisionQuery",
    "ReviewDecisionRepository",
    "ReviewCadence",
    "ReviewGateEvaluation",
    "ReviewGateBlockedError",
    "ReviewGateState",
    "ReviewOutcome",
    "DocumentSchema",
    "ExecutionBackend",
    "ExecutionRequest",
    "DuplicateReviewDecisionError",
    "ScientificConstraint",
    "ConstraintCategory",
    "AgenticProteinsBackend",
    "MissingExecutionBackendError",
    "SuccessCriterion",
    "evaluate_review_gate",
    "evaluate_review_gates",
    "advance_stage",
    "allowed_next_stages",
    "assess_stage_eligibility",
    "create_program_spec",
    "decision_timeline",
    "list_decisions_by_outcome",
    "list_gate_decisions",
    "query_decisions",
    "ensure_unique_gate_decision",
    "ensure_review_clearance",
    "latest_gate_decision",
    "ProgramNotFoundError",
    "ProgramRevisionConflictError",
    "require_program",
    "ensure_program_revision",
    "execute_program",
    "program_summary",
    "revise_program",
    "sequence_length",
    "target_summary",
    "validate_review_decision",
    "validate_program",
    "validate_program_readiness",
    "validate_assay_dependencies",
]
