# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Shared document primitives for Bijux Proteomics."""

from __future__ import annotations

from bijux_proteomics_foundation.errors import (
    ContractConflictError,
    ContractNotFoundError,
    ContractValidationError,
    FoundationContractError,
    MigrationExecutionError,
    MigrationPathError,
)
from bijux_proteomics_foundation.ids import (
    AssayId,
    BatchId,
    CandidateId,
    ClaimId,
    CycleId,
    EvidenceId,
    ExperimentId,
    GateId,
    IdentifierKind,
    ModificationId,
    PeptideId,
    PromotionId,
    ProteinId,
    ProgramId,
    ReviewId,
    RunId,
    SpectrumId,
    TargetId,
    build_identifier,
    classify_identifier,
    ensure_identifier_kind,
)
from bijux_proteomics_foundation.migrations import MigrationRegistry, SchemaMigration
from bijux_proteomics_foundation.schema import (
    DocumentSchema,
    SchemaCompatibility,
    assess_schema_compatibility,
)
from bijux_proteomics_foundation.serialization import JsonModel

__all__ = [
    "AssayId",
    "BatchId",
    "CandidateId",
    "ClaimId",
    "CycleId",
    "ContractConflictError",
    "ContractNotFoundError",
    "ContractValidationError",
    "DocumentSchema",
    "SchemaCompatibility",
    "assess_schema_compatibility",
    "EvidenceId",
    "ExperimentId",
    "FoundationContractError",
    "GateId",
    "IdentifierKind",
    "JsonModel",
    "MigrationExecutionError",
    "MigrationRegistry",
    "MigrationPathError",
    "ModificationId",
    "PeptideId",
    "PromotionId",
    "ProteinId",
    "ProgramId",
    "ReviewId",
    "RunId",
    "SchemaMigration",
    "SpectrumId",
    "TargetId",
    "build_identifier",
    "classify_identifier",
    "ensure_identifier_kind",
]
