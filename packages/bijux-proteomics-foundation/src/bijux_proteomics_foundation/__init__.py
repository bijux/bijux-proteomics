# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Small public import surface for shared Bijux foundation primitives."""

from __future__ import annotations

from bijux_proteomics_foundation.compatibility import (
    SchemaCompatibility,
    assess_schema_compatibility,
)
from bijux_proteomics_foundation.documents import DocumentSchema
from bijux_proteomics_foundation.errors import (
    ContractConflictError,
    ContractNotFoundError,
)
from bijux_proteomics_foundation.serialization.hashing import (
    hash_model,
    hash_payload,
    hash_text,
)
from bijux_proteomics_foundation.serialization.canonicalization import to_canonical_json
from bijux_proteomics_foundation.identity.identifiers import (
    AssayId,
    BatchId,
    build_identifier,
    CandidateId,
    ClaimId,
    CycleId,
    EvidenceId,
    GateId,
    IdentifierKind,
    ProgramId,
    PromotionId,
    ReviewId,
    TargetId,
)
from bijux_proteomics_foundation.json_models import JsonModel, fingerprint_model

__all__ = [
    "AssayId",
    "BatchId",
    "build_identifier",
    "CandidateId",
    "ClaimId",
    "ContractConflictError",
    "ContractNotFoundError",
    "CycleId",
    "DocumentSchema",
    "EvidenceId",
    "GateId",
    "IdentifierKind",
    "JsonModel",
    "ProgramId",
    "PromotionId",
    "ReviewId",
    "SchemaCompatibility",
    "TargetId",
    "assess_schema_compatibility",
    "fingerprint_model",
    "hash_model",
    "hash_payload",
    "hash_text",
    "to_canonical_json",
]
