# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Structured refusal models for unsupported or unsafe operations."""

from __future__ import annotations

from enum import StrEnum

from pydantic import ConfigDict, Field, field_validator

from bijux_proteomics_foundation.ordering import stable_order_strings
from bijux_proteomics_foundation.provenance import ProvenancePointer
from bijux_proteomics_foundation.serialization import JsonModel
from bijux_proteomics_foundation.states import SupportState


class RefusalKind(StrEnum):
    """Canonical refusal categories across product packages."""

    UNSUPPORTED = "unsupported"
    UNSAFE = "unsafe"
    LOSSY = "lossy"
    AMBIGUOUS = "ambiguous"


class OperationRefusal(JsonModel):
    """Structured refusal for unsupported, unsafe, or lossy work."""

    model_config = ConfigDict(extra="forbid")

    operation: str = Field(..., min_length=1)
    kind: RefusalKind
    code: str = Field(..., min_length=1)
    reason: str = Field(..., min_length=1)
    state: SupportState = Field(default=SupportState.REFUSED)
    details: tuple[str, ...] = Field(default_factory=tuple)
    recommended_actions: tuple[str, ...] = Field(default_factory=tuple)
    provenance: tuple[ProvenancePointer, ...] = Field(default_factory=tuple)

    @field_validator("code")
    @classmethod
    def _normalize_code(cls, value: str) -> str:
        return value.strip().lower().replace(" ", "_").replace("-", "_")

    @field_validator("details", "recommended_actions")
    @classmethod
    def _order_strings(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return stable_order_strings(value)
