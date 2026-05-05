# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Structured refusal models for unsupported or unsafe operations."""

from __future__ import annotations

from enum import StrEnum

from pydantic import AliasChoices, ConfigDict, Field, field_validator

from bijux_proteomics_foundation.json_models import JsonModel
from bijux_proteomics_foundation.ordering import stable_order_strings
from bijux_proteomics_foundation.support.provenance import ProvenancePointer
from bijux_proteomics_foundation.support.states import SupportState


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
    support_state: SupportState = Field(
        default=SupportState.REFUSED,
        validation_alias=AliasChoices("support_state", "state"),
        serialization_alias="support_state",
    )
    reason_details: tuple[str, ...] = Field(
        default_factory=tuple,
        validation_alias=AliasChoices("reason_details", "details"),
        serialization_alias="reason_details",
    )
    recommended_actions: tuple[str, ...] = Field(default_factory=tuple)
    provenance: tuple[ProvenancePointer, ...] = Field(default_factory=tuple)

    @field_validator("code")
    @classmethod
    def _normalize_code(cls, value: str) -> str:
        return value.strip().lower().replace(" ", "_").replace("-", "_")

    @field_validator("reason_details", "recommended_actions")
    @classmethod
    def _order_strings(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return stable_order_strings(value)


__all__ = ["OperationRefusal", "RefusalKind"]
