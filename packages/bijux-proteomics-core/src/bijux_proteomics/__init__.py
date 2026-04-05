# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Bijux Proteomics program and execution primitives."""

from __future__ import annotations

from bijux_proteomics.assays import AssayRequirement
from bijux_proteomics.constraints import ScientificConstraint
from bijux_proteomics.criteria import MeasurementDirection, SuccessCriterion
from bijux_proteomics.exceptions import (
    BijuxProteomicsError,
    ProgramValidationError,
    ReviewGateBlockedError,
)
from bijux_proteomics.operating_model import OperatingModel
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
    ReviewOutcome,
    ensure_review_clearance,
)
from bijux_proteomics_foundation import DocumentSchema, JsonModel
from bijux_proteomics.targets import ProteinTarget
from bijux_proteomics.runner import ProgramExecutionRequest, execute_program

__all__ = [
    "AssayRequirement",
    "EvidenceNeed",
    "BijuxProteomicsError",
    "MeasurementDirection",
    "OperatingModel",
    "ProgramRepository",
    "ProgramExecutionRequest",
    "ProgramStage",
    "ProgramSpec",
    "ProgramValidationError",
    "ProteinTarget",
    "JsonModel",
    "ReviewGate",
    "ReviewDecision",
    "ReviewDecisionRepository",
    "ReviewGateBlockedError",
    "ReviewOutcome",
    "DocumentSchema",
    "ScientificConstraint",
    "SuccessCriterion",
    "create_program_spec",
    "ensure_review_clearance",
    "execute_program",
    "program_summary",
]
