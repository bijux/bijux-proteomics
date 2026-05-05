# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owner paths for deterministic serialization and hashing primitives."""

from __future__ import annotations

from importlib import import_module

__all__ = [
    "StableHashAlgorithm",
    "StableHashPolicy",
    "default_hash_policy",
    "flatten_tsv_mapping",
    "hash_model",
    "hash_payload",
    "hash_text",
    "normalize_json_value",
    "to_canonical_json",
]

_OWNER_MODULES = {
    "StableHashAlgorithm": "bijux_proteomics_foundation.serialization.hashing",
    "StableHashPolicy": "bijux_proteomics_foundation.serialization.hashing",
    "default_hash_policy": "bijux_proteomics_foundation.serialization.hashing",
    "flatten_tsv_mapping": "bijux_proteomics_foundation.serialization.canonicalization",
    "hash_model": "bijux_proteomics_foundation.serialization.hashing",
    "hash_payload": "bijux_proteomics_foundation.serialization.hashing",
    "hash_text": "bijux_proteomics_foundation.serialization.hashing",
    "normalize_json_value": "bijux_proteomics_foundation.serialization.canonicalization",
    "to_canonical_json": "bijux_proteomics_foundation.serialization.canonicalization",
}


def __getattr__(name: str) -> object:
    """Resolve serialization owner exports lazily to avoid import cycles."""
    module_name = _OWNER_MODULES.get(name)
    if module_name is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module = import_module(module_name)
    return getattr(module, name)
