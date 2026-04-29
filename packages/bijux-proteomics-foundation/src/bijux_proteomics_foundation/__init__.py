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
from bijux_proteomics_foundation.formats import (
    ArtifactFormat,
    SchemaFormatCompatibilityReport,
    SchemaFormatContract,
    build_schema_format_contract,
    default_schema_format_contracts,
    evaluate_schema_format_contract,
)
from bijux_proteomics_foundation.hashing import (
    StableHashAlgorithm,
    StableHashPolicy,
    default_hash_policy,
    hash_model,
    hash_payload,
)
from bijux_proteomics_foundation.migrations import MigrationRegistry, SchemaMigration
from bijux_proteomics_foundation.nullability import (
    NullabilityState,
    NullableValue,
    absent_value,
    present_value,
)
from bijux_proteomics_foundation.primitives import (
    DurationValue,
    SequenceCoordinateRange,
    SequenceCoordinateSystem,
    UtcTimestamp,
)
from bijux_proteomics_foundation.schema import (
    DocumentSchema,
    SchemaCompatibility,
    assess_schema_compatibility,
)
from bijux_proteomics_foundation.serialization import JsonModel
from bijux_proteomics_foundation.vocabulary import (
    DEFAULT_CONTROLLED_VOCABULARY,
    ControlledVocabularyDomain,
    ControlledVocabularyTerm,
    normalize_controlled_term,
)

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
    "ArtifactFormat",
    "GateId",
    "IdentifierKind",
    "JsonModel",
    "SchemaFormatCompatibilityReport",
    "SchemaFormatContract",
    "StableHashAlgorithm",
    "StableHashPolicy",
    "MigrationExecutionError",
    "MigrationRegistry",
    "MigrationPathError",
    "ModificationId",
    "PeptideId",
    "PromotionId",
    "ProteinId",
    "ProgramId",
    "DurationValue",
    "NullabilityState",
    "NullableValue",
    "ReviewId",
    "RunId",
    "SchemaMigration",
    "SpectrumId",
    "SequenceCoordinateRange",
    "SequenceCoordinateSystem",
    "TargetId",
    "UtcTimestamp",
    "ControlledVocabularyDomain",
    "ControlledVocabularyTerm",
    "DEFAULT_CONTROLLED_VOCABULARY",
    "normalize_controlled_term",
    "absent_value",
    "build_identifier",
    "build_schema_format_contract",
    "classify_identifier",
    "default_schema_format_contracts",
    "default_hash_policy",
    "ensure_identifier_kind",
    "evaluate_schema_format_contract",
    "hash_model",
    "hash_payload",
    "present_value",
]
