# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Serialization helpers for stable knowledge document exchange."""

from __future__ import annotations

import hashlib
import json

from bijux_proteomics_foundation import JsonModel


def to_canonical_json(model: JsonModel) -> str:
    """Serialize a model with deterministic key ordering."""
    return json.dumps(model.to_dict(), sort_keys=True, separators=(",", ":"))


def fingerprint_model(model: JsonModel) -> str:
    """Build a stable SHA-256 fingerprint for a serialized model."""
    return hashlib.sha256(to_canonical_json(model).encode("utf-8")).hexdigest()


__all__ = ["JsonModel", "to_canonical_json", "fingerprint_model"]
