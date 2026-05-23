# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Curated public import surface for shared Bijux foundation primitives."""

from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from bijux_proteomics_foundation.identity.identifiers import (
        AssayId,
        BatchId,
        CandidateId,
        ClaimId,
        EvidenceId,
        GateId,
        ProgramId,
        TargetId,
    )
    from bijux_proteomics_foundation.serialization.canonical_json import (
        to_canonical_json,
    )
    from bijux_proteomics_foundation.serialization.document_schema import (
        DocumentSchema,
    )
    from bijux_proteomics_foundation.serialization.json_contracts import (
        JsonModel,
        fingerprint_model,
    )
    from bijux_proteomics_foundation.serialization.stable_hashes import (
        hash_model,
        hash_payload,
        hash_text,
    )

__all__ = [
    "AssayId",
    "BatchId",
    "CandidateId",
    "ClaimId",
    "DocumentSchema",
    "EvidenceId",
    "fingerprint_model",
    "GateId",
    "hash_model",
    "hash_payload",
    "hash_text",
    "JsonModel",
    "ProgramId",
    "TargetId",
    "to_canonical_json",
]

_FOUNDATION_ROOT_EXPORTS = {
    "AssayId": ("bijux_proteomics_foundation.identity.identifiers", "AssayId"),
    "BatchId": ("bijux_proteomics_foundation.identity.identifiers", "BatchId"),
    "CandidateId": (
        "bijux_proteomics_foundation.identity.identifiers",
        "CandidateId",
    ),
    "ClaimId": ("bijux_proteomics_foundation.identity.identifiers", "ClaimId"),
    "DocumentSchema": (
        "bijux_proteomics_foundation.serialization.document_schema",
        "DocumentSchema",
    ),
    "EvidenceId": (
        "bijux_proteomics_foundation.identity.identifiers",
        "EvidenceId",
    ),
    "fingerprint_model": (
        "bijux_proteomics_foundation.serialization.json_contracts",
        "fingerprint_model",
    ),
    "GateId": ("bijux_proteomics_foundation.identity.identifiers", "GateId"),
    "hash_model": (
        "bijux_proteomics_foundation.serialization.stable_hashes",
        "hash_model",
    ),
    "hash_payload": (
        "bijux_proteomics_foundation.serialization.stable_hashes",
        "hash_payload",
    ),
    "hash_text": (
        "bijux_proteomics_foundation.serialization.stable_hashes",
        "hash_text",
    ),
    "JsonModel": (
        "bijux_proteomics_foundation.serialization.json_contracts",
        "JsonModel",
    ),
    "ProgramId": ("bijux_proteomics_foundation.identity.identifiers", "ProgramId"),
    "TargetId": ("bijux_proteomics_foundation.identity.identifiers", "TargetId"),
    "to_canonical_json": (
        "bijux_proteomics_foundation.serialization.canonical_json",
        "to_canonical_json",
    ),
}


def __getattr__(name: str) -> Any:
    """Load public foundation exports lazily to avoid needless import coupling."""

    target = _FOUNDATION_ROOT_EXPORTS.get(name)
    if target is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module_name, attribute_name = target
    module = import_module(module_name)
    return getattr(module, attribute_name)
