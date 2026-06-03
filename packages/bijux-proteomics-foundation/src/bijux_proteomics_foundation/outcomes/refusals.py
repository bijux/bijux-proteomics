# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Structured refusal models for unsupported or unsafe operations."""

from __future__ import annotations

from enum import StrEnum

from pydantic import ConfigDict, Field, field_validator, model_validator

from bijux_proteomics_foundation.serialization.json_contracts import JsonModel
from bijux_proteomics_foundation.serialization.stable_values import stable_order_strings
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
    support_state: SupportState = Field(default=SupportState.REFUSED)
    reason_details: tuple[str, ...] = Field(default_factory=tuple)
    recommended_actions: tuple[str, ...] = Field(default_factory=tuple)
    provenance: tuple[ProvenancePointer, ...] = Field(default_factory=tuple)

    @model_validator(mode="before")
    @classmethod
    def _normalize_legacy_keys(cls, value: object) -> object:
        """Map legacy refusal payload keys onto the stable field names."""
        if not isinstance(value, dict):
            return value
        payload = dict(value)
        if "support_state" not in payload and "state" in payload:
            payload["support_state"] = payload.pop("state")
        if "reason_details" not in payload and "details" in payload:
            payload["reason_details"] = payload.pop("details")
        return payload

    @field_validator("code")
    @classmethod
    def _normalize_code(cls, value: str) -> str:
        """Canonicalize refusal codes into the shared stable token format."""
        return value.strip().lower().replace(" ", "_").replace("-", "_")

    @field_validator("reason_details", "recommended_actions")
    @classmethod
    def _order_strings(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        """Normalize explanatory string lists into a stable serialized order."""
        return stable_order_strings(value)


__all__ = ["OperationRefusal", "RefusalKind"]
