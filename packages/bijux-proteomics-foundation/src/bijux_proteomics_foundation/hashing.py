# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Compatibility wrapper for stable hashing primitives."""

from __future__ import annotations

from bijux_proteomics_foundation.serialization.hashing import (
    StableHashAlgorithm,
    StableHashPolicy,
    default_hash_policy,
    hash_model,
    hash_payload,
    hash_text,
)

__all__ = [
    "StableHashAlgorithm",
    "StableHashPolicy",
    "default_hash_policy",
    "hash_model",
    "hash_payload",
    "hash_text",
]
