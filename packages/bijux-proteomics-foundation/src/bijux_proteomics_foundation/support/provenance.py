# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Stable provenance pointers for files, records, and derived artifacts."""

from __future__ import annotations

from enum import StrEnum

from pydantic import AliasChoices, ConfigDict, Field, field_validator

from bijux_proteomics_foundation.serialization.json_contracts import JsonModel
from bijux_proteomics_foundation.serialization.stable_values import stable_order_strings


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
    pointer_role: str = Field(
        ...,
        min_length=1,
        validation_alias=AliasChoices("pointer_role", "role"),
        serialization_alias="pointer_role",
    )
    source_system: str = Field(default="bijux-proteomics", min_length=1)
    fingerprint: str | None = None
    pointer_labels: tuple[str, ...] = Field(
        default_factory=tuple,
        validation_alias=AliasChoices("pointer_labels", "labels"),
        serialization_alias="pointer_labels",
    )

    @field_validator("pointer_labels")
    @classmethod
    def _order_labels(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return stable_order_strings(value)


__all__ = ["ProvenancePointer", "ProvenancePointerKind"]
