# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Stable hashing policies for reproducible scientific objects."""

from __future__ import annotations

from enum import StrEnum
import hashlib
import json
from typing import Any

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation.serialization import JsonModel


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


def hash_payload(
    payload: dict[str, Any],
    *,
    policy: StableHashPolicy | None = None,
) -> str:
    """Hash one canonical JSON payload under a named policy."""
    policy = policy or default_hash_policy()
    encoded = json.dumps(
        payload,
        sort_keys=True,
        default=str,
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
