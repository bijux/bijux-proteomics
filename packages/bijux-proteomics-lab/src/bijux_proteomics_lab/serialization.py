# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Serialization helpers for deterministic lab artifact exchange."""

from __future__ import annotations

import hashlib
import json

from bijux_proteomics_foundation import DocumentSchema, JsonModel


def to_canonical_json(model: JsonModel) -> str:
    """Serialize a model with deterministic key ordering."""
    return json.dumps(model.to_dict(), sort_keys=True, separators=(",", ":"))


def fingerprint_model(model: JsonModel) -> str:
    """Generate a stable SHA-256 fingerprint for a lab model payload."""
    return hashlib.sha256(to_canonical_json(model).encode("utf-8")).hexdigest()


def diff_model_payloads(left: JsonModel, right: JsonModel) -> dict[str, list[str]]:
    """Compute a deterministic field-level diff between two model payloads."""
    left_payload = left.to_dict()
    right_payload = right.to_dict()
    left_keys = set(left_payload.keys())
    right_keys = set(right_payload.keys())
    changed = sorted(
        [
            key
            for key in sorted(left_keys & right_keys)
            if left_payload[key] != right_payload[key]
        ]
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
    schema: DocumentSchema,
) -> dict[str, object]:
    """Build canonical envelope for lab artifact transport and auditing."""
    payload = model.to_dict()
    fingerprint = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return {
        "artifact_kind": artifact_kind,
        "schema": schema.to_dict(),
        "fingerprint": fingerprint,
        "payload": payload,
    }


def verify_canonical_artifact_envelope(envelope: dict[str, object]) -> bool:
    """Verify canonical envelope fingerprint integrity."""
    payload = envelope.get("payload")
    fingerprint = envelope.get("fingerprint")
    if not isinstance(payload, dict) or not isinstance(fingerprint, str):
        return False
    expected = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return expected == fingerprint


__all__ = [
    "JsonModel",
    "to_canonical_json",
    "fingerprint_model",
    "diff_model_payloads",
    "build_canonical_artifact_envelope",
    "verify_canonical_artifact_envelope",
]
