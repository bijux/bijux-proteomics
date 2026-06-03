# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Canonical artifact serialization helpers for reviewable lab handoffs."""

from __future__ import annotations

from typing import Any

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import (
    DocumentSchema as SchemaMetadata,
)
from bijux_proteomics_foundation import (
    JsonModel,
    hash_payload,
)


class ModelPayloadDiff(JsonModel):
    """Stable field-level diff between two normalized model payloads."""

    added_fields: tuple[str, ...] = ()
    removed_fields: tuple[str, ...] = ()
    changed_fields: tuple[str, ...] = ()


class CanonicalArtifactEnvelope(JsonModel):
    """Canonical transport envelope for one reviewable lab artifact payload."""

    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    artifact_kind: str
    schema_metadata: SchemaMetadata = Field(alias="schema")
    fingerprint: str
    payload_raw_json: dict[str, Any] = Field(alias="payload")


def diff_model_payloads(left: JsonModel, right: JsonModel) -> ModelPayloadDiff:
    """Compute a deterministic field-level diff between two model payloads."""
    ignored_fields = {"document_schema"}
    left_payload = {k: v for k, v in left.to_dict().items() if k not in ignored_fields}
    right_payload = {
        k: v for k, v in right.to_dict().items() if k not in ignored_fields
    }
    left_keys = set(left_payload.keys())
    right_keys = set(right_payload.keys())
    changed = sorted(
        key
        for key in sorted(left_keys & right_keys)
        if left_payload[key] != right_payload[key]
    )
    return ModelPayloadDiff(
        added_fields=tuple(sorted(right_keys - left_keys)),
        removed_fields=tuple(sorted(left_keys - right_keys)),
        changed_fields=tuple(changed),
    )


def build_canonical_artifact_envelope(
    model: JsonModel,
    *,
    artifact_kind: str,
    schema: SchemaMetadata,
) -> CanonicalArtifactEnvelope:
    """Build a canonical transport envelope for one lab artifact payload."""
    payload = model.to_dict()
    fingerprint = hash_payload(payload)
    return CanonicalArtifactEnvelope(
        artifact_kind=artifact_kind,
        schema_metadata=schema,
        fingerprint=fingerprint,
        payload_raw_json=payload,
    )


def verify_canonical_artifact_envelope(envelope: CanonicalArtifactEnvelope) -> bool:
    """Verify that a canonical artifact envelope still matches its payload fingerprint."""
    expected = hash_payload(envelope.payload_raw_json)
    return expected == envelope.fingerprint


__all__ = [
    "CanonicalArtifactEnvelope",
    "ModelPayloadDiff",
    "build_canonical_artifact_envelope",
    "diff_model_payloads",
    "verify_canonical_artifact_envelope",
]
