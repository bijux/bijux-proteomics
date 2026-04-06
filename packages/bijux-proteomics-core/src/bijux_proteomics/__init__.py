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
from bijux_proteomics.constraints import ScientificConstraint
from bijux_proteomics.criteria import MeasurementDirection, SuccessCriterion
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
    create_program_spec,
    program_summary,
)
from bijux_proteomics.reviews import ReviewGate
from bijux_proteomics.repositories import (
    ProgramRepository,
    ReviewDecision,
    ReviewDecisionRepository,
    ReviewGateEvaluation,
    ReviewGateState,
    ReviewOutcome,
    decision_timeline,
    evaluate_review_gate,
    evaluate_review_gates,
    ensure_review_clearance,
    latest_gate_decision,
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
    "ProteinTarget",
    "TargetAnnotation",
    "TargetOutcome",
    "ProteinSequence",
    "JsonModel",
    "ReviewGate",
    "ReviewDecision",
    "ReviewDecisionRepository",
    "ReviewCadence",
    "ReviewGateEvaluation",
    "ReviewGateBlockedError",
    "ReviewGateState",
    "ReviewOutcome",
    "DocumentSchema",
    "ExecutionBackend",
    "ExecutionRequest",
    "ScientificConstraint",
    "AgenticProteinsBackend",
    "MissingExecutionBackendError",
    "SuccessCriterion",
    "evaluate_review_gate",
    "evaluate_review_gates",
    "advance_stage",
    "allowed_next_stages",
    "create_program_spec",
    "decision_timeline",
    "ensure_review_clearance",
    "latest_gate_decision",
    "execute_program",
    "program_summary",
    "sequence_length",
    "target_summary",
    "validate_review_decision",
    "validate_program",
    "validate_program_readiness",
    "validate_assay_dependencies",
]
