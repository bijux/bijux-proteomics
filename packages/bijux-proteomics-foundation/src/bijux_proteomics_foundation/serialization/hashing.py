# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Stable hashing policies for reproducible scientific objects."""

from __future__ import annotations

from enum import StrEnum
import hashlib
import json
from typing import Any

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation.json_models import JsonModel
from bijux_proteomics_foundation.ordering import stable_order_value


class StableHashAlgorithm(StrEnum):
    """Supported stable hashing algorithms."""

    SHA256 = "sha256"


class StableHashPolicy(JsonModel):
    """Named hashing policy for durable scientific payloads."""

    model_config = ConfigDict(extra="forbid")

    policy_id: str = Field(..., min_length=1, description="Stable policy identifier.")
    algorithm: StableHashAlgorithm = Field(
        default=StableHashAlgorithm.SHA256,
        description="Hashing algorithm used for the digest.",
    )
    separators: tuple[str, str] = Field(
        default=(",", ":"),
        description="JSON separators used for canonical serialization.",
    )


def default_hash_policy() -> StableHashPolicy:
    """Return the default hashing policy for scientific objects."""
    return StableHashPolicy(policy_id="scientific-object-sha256-v1")


def _hash_bytes(payload: bytes, algorithm: StableHashAlgorithm) -> str:
    if algorithm is StableHashAlgorithm.SHA256:
        return hashlib.sha256(payload).hexdigest()
    raise ValueError(f"unsupported stable hash algorithm: {algorithm}")


def hash_text(
    payload: str,
    *,
    algorithm: StableHashAlgorithm = StableHashAlgorithm.SHA256,
) -> str:
    """Hash one utf-8 text payload with a stable algorithm."""
    return _hash_bytes(payload.encode("utf-8"), algorithm)


def hash_payload(
    payload: dict[str, Any],
    *,
    policy: StableHashPolicy | None = None,
) -> str:
    """Hash one canonical JSON payload under a named policy."""
    policy = policy or default_hash_policy()
    encoded = json.dumps(
        stable_order_value(payload),
        sort_keys=True,
        default=str,
        ensure_ascii=True,
        separators=policy.separators,
    ).encode("utf-8")
    return _hash_bytes(encoded, policy.algorithm)


def hash_model(
    model: JsonModel,
    *,
    policy: StableHashPolicy | None = None,
) -> str:
    """Hash one JsonModel payload under a named policy."""
    return hash_payload(model.to_dict(), policy=policy)


__all__ = [
    "StableHashAlgorithm",
    "StableHashPolicy",
    "default_hash_policy",
    "hash_model",
    "hash_payload",
    "hash_text",
]
