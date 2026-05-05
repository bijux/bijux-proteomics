# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Canonical artifact serialization helpers for reviewable lab handoffs."""

from __future__ import annotations

from bijux_proteomics_foundation import (
    DocumentSchema as SchemaMetadata,
    JsonModel,
    hash_payload,
)


def diff_model_payloads(left: JsonModel, right: JsonModel) -> dict[str, list[str]]:
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
    return {
        "added_fields": sorted(right_keys - left_keys),
        "removed_fields": sorted(left_keys - right_keys),
        "changed_fields": changed,
    }


def build_canonical_artifact_envelope(
    model: JsonModel,
    *,
    artifact_kind: str,
    schema: SchemaMetadata,
) -> dict[str, object]:
    """Build a canonical transport envelope for one lab artifact payload."""
    payload = model.to_dict()
    fingerprint = hash_payload(payload)
    return {
        "artifact_kind": artifact_kind,
        "schema": schema.to_dict(),
        "fingerprint": fingerprint,
        "payload": payload,
    }


def verify_canonical_artifact_envelope(envelope: dict[str, object]) -> bool:
    """Verify that a canonical artifact envelope still matches its payload fingerprint."""
    payload = envelope.get("payload")
    fingerprint = envelope.get("fingerprint")
    if not isinstance(payload, dict) or not isinstance(fingerprint, str):
        return False
    expected = hash_payload(payload)
    return expected == fingerprint


__all__ = [
    "build_canonical_artifact_envelope",
    "diff_model_payloads",
    "verify_canonical_artifact_envelope",
]
