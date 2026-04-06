# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Shared serialization helpers for Bijux Proteomics documents."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Self

from pydantic import BaseModel


class JsonModel(BaseModel):
    """Base model with convenience helpers for reusable SDK objects."""

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-compatible dictionary."""
        return self.model_dump(mode="json")

    def to_json(self) -> str:
        """Return a formatted JSON string."""
        return self.model_dump_json(indent=2)

    def to_stable_json(self) -> str:
        """Return deterministically ordered JSON for reproducible diffs."""
        payload = self.model_dump(mode="json")
        return json.dumps(payload, indent=2, sort_keys=True)

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
