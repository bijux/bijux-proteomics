# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Reusable JSON-backed contract helpers for durable Bijux payloads."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Self, cast

from pydantic import BaseModel

from bijux_proteomics_foundation.serialization.canonical_json import (
    flatten_tsv_mapping,
    normalize_json_value,
)


class JsonModel(BaseModel):
    """Base model with convenience helpers for reusable SDK objects."""

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-compatible dictionary."""
        return cast(
            dict[str, Any],
            normalize_json_value(self.model_dump(mode="json", by_alias=True)),
        )

    def to_json(self) -> str:
        """Return a formatted JSON string."""
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=True)

    def to_stable_json(self) -> str:
        """Return deterministically ordered JSON for reproducible diffs."""
        return json.dumps(self.to_dict(), indent=2, sort_keys=True, ensure_ascii=True)

    def to_jsonl_line(self) -> str:
        """Return one deterministic JSON Lines record."""
        return json.dumps(
            self.to_dict(),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        )

    def to_flat_dict(self) -> dict[str, str]:
        """Return a flattened scalar map suitable for TSV output."""
        return flatten_tsv_mapping(self.to_dict())

    def to_tsv_row(self, *, columns: list[str] | None = None) -> tuple[str, str]:
        """Return TSV header and row strings for flattened payload fields."""
        flattened = self.to_flat_dict()
        columns = sorted(columns or flattened.keys())
        header = "\t".join(columns)
        row = "\t".join(flattened.get(column, "") for column in columns)
        return header, row

    def content_fingerprint(self) -> str:
        """Return a deterministic SHA-256 fingerprint for model content."""
        from bijux_proteomics_foundation.serialization.stable_hashes import hash_model

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

    def save_jsonl(self, path: Path) -> Path:
        """Persist one JSON Lines record to a file."""
        path.write_text(self.to_jsonl_line() + "\n")
        return path

    def save_tsv(self, path: Path, *, columns: list[str] | None = None) -> Path:
        """Persist one TSV row with a deterministic header."""
        header, row = self.to_tsv_row(columns=columns)
        path.write_text(f"{header}\n{row}\n")
        return path

    @classmethod
    def load_json(cls, path: Path) -> Self:
        """Load the model from a JSON file."""
        return cls.from_json(path.read_text())


def fingerprint_model(model: JsonModel) -> str:
    """Return the stable fingerprint for one model.

    Inputs:
    ``model`` must be a ``JsonModel`` instance with a stable ``to_dict``
    representation.

    Outputs:
    Returns the hexadecimal fingerprint string for the model's canonical
    payload.

    Failure Modes:
    Propagates serialization and hashing errors if the model cannot be reduced
    to the stable JSON contract expected by foundation hashing.

    Scientific Caveats:
    The fingerprint captures deterministic payload identity only; it does not
    prove scientific validity, provenance trust, or semantic equivalence.
    """
    from bijux_proteomics_foundation.serialization.stable_hashes import hash_model

    return hash_model(model)


__all__ = ["JsonModel", "fingerprint_model"]
