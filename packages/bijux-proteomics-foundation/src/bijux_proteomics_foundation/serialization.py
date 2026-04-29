# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Shared serialization helpers for Bijux Proteomics documents."""

from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path
from typing import Any, Self, cast

from pydantic import BaseModel


def _normalize_for_json(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            str(key): _normalize_for_json(inner)
            for key, inner in sorted(value.items(), key=lambda item: str(item[0]))
        }
    if isinstance(value, list):
        return [_normalize_for_json(item) for item in value]
    if isinstance(value, tuple):
        return [_normalize_for_json(item) for item in value]
    if isinstance(value, datetime):
        return value.isoformat().replace("+00:00", "Z")
    return value


class JsonModel(BaseModel):
    """Base model with convenience helpers for reusable SDK objects."""

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-compatible dictionary."""
        return cast(dict[str, Any], _normalize_for_json(self.model_dump(mode="json")))

    def to_json(self) -> str:
        """Return a formatted JSON string."""
        return json.dumps(self.to_dict(), indent=2)

    def to_stable_json(self) -> str:
        """Return deterministically ordered JSON for reproducible diffs."""
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    def content_fingerprint(self) -> str:
        """Return a deterministic SHA-256 fingerprint for model content."""
        from bijux_proteomics_foundation.hashing import hash_model

        return hash_model(self)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> Self:
        """Validate a model from a dictionary."""
        return cls.model_validate(payload)

    @classmethod
    def from_json(cls, payload: str) -> Self:
        """Validate a model from a JSON string."""
        return cls.model_validate_json(payload)

    def save_json(self, path: Path) -> Path:
        """Persist the model to a JSON file."""
        path.write_text(self.to_json() + "\n")
        return path

    def save_stable_json(self, path: Path) -> Path:
        """Persist deterministically ordered JSON to a file."""
        path.write_text(self.to_stable_json() + "\n")
        return path

    @classmethod
    def load_json(cls, path: Path) -> Self:
        """Load the model from a JSON file."""
        return cls.from_json(path.read_text())
