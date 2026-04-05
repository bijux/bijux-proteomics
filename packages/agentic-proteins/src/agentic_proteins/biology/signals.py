"""Typed signal inputs for protein agents."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator


class SignalType(str, Enum):
    """Typed signal kinds for protein agents."""

    ACTIVATE = "activate"
    INHIBIT = "inhibit"
    DEGRADE = "degrade"
    MISFOLD = "misfold"


class SignalScope(str, Enum):
    """Signal scope for delivery."""

    LOCAL = "local"
    PATHWAY = "pathway"
    GLOBAL = "global"


class SignalPayload(BaseModel):
    """Validated signal payload."""

    source_id: str
    targets: tuple[str, ...] = Field(default_factory=tuple)
    scope: SignalScope = SignalScope.PATHWAY
    signal_type: SignalType
    magnitude: float = Field(default=1.0, ge=0.0)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("source_id")
    @classmethod
    def _validate_source_id(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Signal source_id must be non-empty.")
        return value

    @field_validator("targets")
    @classmethod
    def _validate_targets(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if any(not target.strip() for target in value):
            raise ValueError("Signal target ids must be non-empty.")
        return value

    @field_validator("metadata")
    @classmethod
    def _validate_metadata(cls, value: dict[str, Any]) -> dict[str, Any]:
        for key in value:
            if not isinstance(key, str):
                raise TypeError("Signal metadata keys must be strings.")
        return value
