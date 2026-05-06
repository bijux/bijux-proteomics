# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import bijux_proteomics_foundation
from bijux_proteomics_foundation import (
    DocumentSchema,
    JsonModel,
    fingerprint_model,
    hash_model,
    hash_payload,
    hash_text,
    to_canonical_json,
)


def test_foundation_root_exports_stay_curated_and_reviewable() -> None:
    assert bijux_proteomics_foundation.__all__ == [
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


def test_foundation_root_exports_point_at_durable_owner_modules() -> None:
    assert DocumentSchema.__module__ == (
        "bijux_proteomics_foundation.serialization.document_schema"
    )
    assert JsonModel.__module__ == (
        "bijux_proteomics_foundation.serialization.json_contracts"
    )
    assert fingerprint_model.__module__ == (
        "bijux_proteomics_foundation.serialization.json_contracts"
    )
    assert hash_model.__module__ == (
        "bijux_proteomics_foundation.serialization.stable_hashes"
    )
    assert hash_payload.__module__ == (
        "bijux_proteomics_foundation.serialization.stable_hashes"
    )
    assert hash_text.__module__ == (
        "bijux_proteomics_foundation.serialization.stable_hashes"
    )
    assert to_canonical_json.__module__ == (
        "bijux_proteomics_foundation.serialization.canonical_json"
    )
