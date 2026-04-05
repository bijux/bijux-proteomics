# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Serialization helpers for package models."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Self

from pydantic import BaseModel


class JsonModel(BaseModel):
    """Base model with convenience helpers for SDK-style reuse."""

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-compatible dictionary."""
        return self.model_dump(mode="json")

    def to_json(self) -> str:
        """Return a formatted JSON string."""
        return self.model_dump_json(indent=2)

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

    @classmethod
    def load_json(cls, path: Path) -> Self:
        """Load the model from a JSON file."""
        return cls.from_json(path.read_text())
