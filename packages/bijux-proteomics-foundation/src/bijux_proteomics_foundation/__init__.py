# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Shared document primitives for Bijux Proteomics."""

from __future__ import annotations

from bijux_proteomics_foundation.error_models import ErrorCategory, ErrorEnvelope
from bijux_proteomics_foundation.error_models import (
    build_error_envelope_from_exception,
    summarize_exception_chain,
)
from bijux_proteomics_foundation.errors import (
    ContractConflictError,
    ContractNotFoundError,
    ContractValidationError,
    FoundationContractError,
    MigrationExecutionError,
    MigrationPathError,
)
from bijux_proteomics_foundation.evolution import (
    SchemaEvolutionAssessment,
    assess_schema_evolution,
)
from bijux_proteomics_foundation.fingerprints import (
    FingerprintRecord,
    FingerprintScope,
    build_artifact_bundle_fingerprint,
    build_benchmark_manifest_fingerprint,
    build_dataset_fingerprint,
    build_fingerprint_record,
    build_parameter_set_fingerprint,
    build_run_context_fingerprint,
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
    hash_text,
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
    LabActionId,
    ModificationId,
    PeptideId,
    ProgramId,
    PromotionId,
    ProteinId,
    PtmId,
    ReviewId,
    ReviewPacketId,
    RunId,
    SpectrumId,
    StudyId,
    TargetId,
    build_identifier,
    classify_identifier,
    ensure_identifier_kind,
)
from bijux_proteomics_foundation.migrations import MigrationRegistry, SchemaMigration
from bijux_proteomics_foundation.nullability import (
    NullabilityState,
    NullableValue,
    absent_value,
    present_value,
)
from bijux_proteomics_foundation.ordering import (
    stable_order_pairs,
    stable_order_strings,
    stable_order_value,
)
from bijux_proteomics_foundation.primitives import (
    DurationValue,
    SequenceCoordinateRange,
    SequenceCoordinateSystem,
    UtcTimestamp,
)
from bijux_proteomics_foundation.provenance import (
    ProvenancePointer,
    ProvenancePointerKind,
)
from bijux_proteomics_foundation.refusals import OperationRefusal, RefusalKind
from bijux_proteomics_foundation.results import (
    OperationDisposition,
    OperationResult,
)
from bijux_proteomics_foundation.schema import (
    DocumentSchema,
    SchemaCompatibility,
    assess_schema_compatibility,
)
from bijux_proteomics_foundation.serialization import (
    JsonModel,
    fingerprint_model,
    to_canonical_json,
)
from bijux_proteomics_foundation.states import SupportState
from bijux_proteomics_foundation.versions import (
    SchemaVersion,
    normalize_schema_version,
)

__all__ = [
    "ArtifactFormat",
    "AssayId",
    "BatchId",
    "CandidateId",
    "ClaimId",
    "ContractConflictError",
    "ContractNotFoundError",
    "ContractValidationError",
    "CycleId",
    "DocumentSchema",
    "DurationValue",
    "ErrorCategory",
    "ErrorEnvelope",
    "EvidenceId",
    "ExperimentId",
    "FingerprintRecord",
    "FingerprintScope",
    "FoundationContractError",
    "GateId",
    "IdentifierKind",
    "JsonModel",
    "LabActionId",
    "MigrationExecutionError",
    "MigrationPathError",
    "MigrationRegistry",
    "ModificationId",
    "NullabilityState",
    "NullableValue",
    "OperationRefusal",
    "OperationDisposition",
    "OperationResult",
    "PeptideId",
    "ProgramId",
    "PromotionId",
    "ProteinId",
    "ProvenancePointer",
    "ProvenancePointerKind",
    "PtmId",
    "RefusalKind",
    "ReviewId",
    "ReviewPacketId",
    "RunId",
    "SchemaCompatibility",
    "SchemaEvolutionAssessment",
    "SchemaFormatCompatibilityReport",
    "SchemaFormatContract",
    "SchemaMigration",
    "SchemaVersion",
    "SequenceCoordinateRange",
    "SequenceCoordinateSystem",
    "SpectrumId",
    "StableHashAlgorithm",
    "StableHashPolicy",
    "StudyId",
    "SupportState",
    "TargetId",
    "UtcTimestamp",
    "absent_value",
    "assess_schema_compatibility",
    "assess_schema_evolution",
    "build_artifact_bundle_fingerprint",
    "build_benchmark_manifest_fingerprint",
    "build_dataset_fingerprint",
    "build_error_envelope_from_exception",
    "build_fingerprint_record",
    "build_identifier",
    "build_parameter_set_fingerprint",
    "build_run_context_fingerprint",
    "build_schema_format_contract",
    "classify_identifier",
    "default_hash_policy",
    "default_schema_format_contracts",
    "ensure_identifier_kind",
    "evaluate_schema_format_contract",
    "fingerprint_model",
    "hash_model",
    "hash_payload",
    "hash_text",
    "normalize_schema_version",
    "present_value",
    "stable_order_pairs",
    "stable_order_strings",
    "stable_order_value",
    "summarize_exception_chain",
    "to_canonical_json",
]
