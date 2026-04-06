# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Compatibility exports for the protein program domain."""

from __future__ import annotations

from bijux_proteomics.assays import AssayRequirement
from bijux_proteomics.context import (
    ProgramContext,
    ProgramDeliveryContext,
    ProgramPortfolioContext,
)
from bijux_proteomics.constraints import ScientificConstraint
from bijux_proteomics.criteria import MeasurementDirection, SuccessCriterion
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
    ReviewDecision,
    ReviewGateEvaluation,
    ReviewGateState,
    ReviewOutcome,
    evaluate_review_gate,
    evaluate_review_gates,
)
from bijux_proteomics.targets import ProteinTarget

__all__ = [
    "AssayRequirement",
    "EvidenceNeed",
    "MeasurementDirection",
    "OperatingModel",
    "ProgramContext",
    "ProgramDeliveryContext",
    "ProgramPortfolioContext",
    "ProgramSpec",
    "ProgramStage",
    "ProteinTarget",
    "ReviewGate",
    "ReviewDecision",
    "ReviewGateEvaluation",
    "ReviewGateState",
    "ReviewOutcome",
    "ScientificConstraint",
    "SuccessCriterion",
    "create_program_spec",
    "evaluate_review_gate",
    "evaluate_review_gates",
    "program_summary",
]
