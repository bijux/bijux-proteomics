# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Shared document primitives for Bijux Proteomics."""

from __future__ import annotations

from bijux_proteomics_foundation.errors import (
    ContractConflictError,
    ContractNotFoundError,
    ContractValidationError,
    FoundationContractError,
)
from bijux_proteomics_foundation.ids import (
    AssayId,
    BatchId,
    CandidateId,
    CycleId,
    EvidenceId,
    GateId,
    ProgramId,
    TargetId,
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
    "CycleId",
    "ContractConflictError",
    "ContractNotFoundError",
    "ContractValidationError",
    "DocumentSchema",
    "SchemaCompatibility",
    "assess_schema_compatibility",
    "EvidenceId",
    "FoundationContractError",
    "GateId",
    "JsonModel",
    "MigrationRegistry",
    "ProgramId",
    "SchemaMigration",
    "TargetId",
]
