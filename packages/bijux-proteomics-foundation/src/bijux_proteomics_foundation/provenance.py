# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Stable provenance pointers for files, records, and derived artifacts."""

from __future__ import annotations

from enum import StrEnum

from pydantic import ConfigDict, Field, field_validator

from bijux_proteomics_foundation.ordering import stable_order_strings
from bijux_proteomics_foundation.serialization import JsonModel


class ProvenancePointerKind(StrEnum):
    """Supported provenance locator kinds."""

    FILE = "file"
    RECORD = "record"
    REFERENCE = "reference"
    DOCUMENT = "document"
    ARTIFACT = "artifact"


class ProvenancePointer(JsonModel):
    """One stable pointer to source or derived provenance."""

    model_config = ConfigDict(extra="forbid")

    pointer_kind: ProvenancePointerKind
    locator: str = Field(..., min_length=1)
    role: str = Field(..., min_length=1)
    source_system: str = Field(default="bijux-proteomics", min_length=1)
    fingerprint: str | None = None
    labels: tuple[str, ...] = Field(default_factory=tuple)

    @field_validator("labels")
    @classmethod
    def _order_labels(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return stable_order_strings(value)
