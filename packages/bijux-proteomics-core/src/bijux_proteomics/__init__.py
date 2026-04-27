# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Bijux Proteomics program and execution primitives."""

from __future__ import annotations

from bijux_proteomics.assays import AssayRequirement
from bijux_proteomics.constraints import (
    ConstraintCategory,
    ScientificConstraint,
    build_protein_native_constraints,
)
from bijux_proteomics.context import (
    ProgramContext,
    ProgramDeliveryContext,
    ProgramPortfolioContext,
)
from bijux_proteomics.criteria import (
    MeasurementDirection,
    MetricFamily,
    SuccessCriterion,
    criterion_passes,
)
from bijux_proteomics.exceptions import (
    BijuxProteomicsError,
    InvalidLifecycleTransitionError,
    ProgramValidationError,
    ReviewGateBlockedError,
)
from bijux_proteomics.execution_backend import ExecutionBackend, ExecutionRequest
from bijux_proteomics.liabilities import LiabilityCategory, ProgramLiability
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
    DecisionQuery,
    DuplicateReviewDecisionError,
    ProgramNotFoundError,
    ProgramRepository,
    ProgramRevisionConflictError,
    ReviewDecision,
    ReviewDecisionRepository,
    ReviewGateEvaluation,
    ReviewGateState,
    ReviewOutcome,
    decision_timeline,
    ensure_program_revision,
    ensure_review_clearance,
    ensure_unique_gate_decision,
    evaluate_review_gate,
    evaluate_review_gates,
    latest_gate_decision,
    list_decisions_by_outcome,
    list_gate_decisions,
    query_decisions,
    require_program,
    validate_review_decision,
)
from bijux_proteomics.reviews import ReviewGate
from bijux_proteomics.runner import ProgramExecutionRequest, execute_program
from bijux_proteomics.runtime_adapter import (
    AgenticProteinsBackend,
    MissingExecutionBackendError,
)
from bijux_proteomics.sequences import (
    FastaSequenceRecord,
    ProteinSequence,
    parse_fasta_records,
    parse_uniprot_accession,
    sequence_length,
    UniProtAccession,
)
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
from bijux_proteomics.workflow_blueprint import (
    ScientificWorkflowBlueprint,
    WorkflowStageKind,
    WorkflowStepBlueprint,
    workflow_blueprint_for_program,
    workflow_blueprint_summary,
)
from bijux_proteomics_foundation import DocumentSchema, JsonModel

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
    "FastaSequenceRecord",
    "UniProtAccession",
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
    "build_protein_native_constraints",
    "AgenticProteinsBackend",
    "MissingExecutionBackendError",
    "SuccessCriterion",
    "criterion_passes",
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
    "parse_fasta_records",
    "parse_uniprot_accession",
    "target_summary",
    "validate_review_decision",
    "validate_program",
    "validate_program_readiness",
    "validate_assay_dependencies",
    "WorkflowStageKind",
    "WorkflowStepBlueprint",
    "ScientificWorkflowBlueprint",
    "workflow_blueprint_for_program",
    "workflow_blueprint_summary",
]
