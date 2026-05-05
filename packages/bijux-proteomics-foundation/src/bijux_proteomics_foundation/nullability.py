# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Explicit nullability contracts for scientific payloads."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import ConfigDict, Field, model_validator

from bijux_proteomics_foundation.json_models import JsonModel


class NullabilityState(StrEnum):
    """Why a scientific field is absent or present."""

    PRESENT = "present"
    UNKNOWN = "unknown"
    NOT_MEASURED = "not_measured"
    NOT_APPLICABLE = "not_applicable"
    WITHHELD = "withheld"


class NullableValue(JsonModel):
    """Explicit wrapper around scientific values that may be absent."""

    model_config = ConfigDict(extra="forbid")

    state: NullabilityState = Field(..., description="Presence or absence state.")
    value: Any | None = Field(
        default=None,
        description="Scientific value when the state is present.",
    )
    reason: str | None = Field(
        default=None,
        description="Optional reason for absent values.",
    )

    @model_validator(mode="after")
    def _validate_state(self) -> NullableValue:
        if self.state is NullabilityState.PRESENT and self.value is None:
            raise ValueError("present values must carry a non-null payload")
        if self.state is not NullabilityState.PRESENT and self.value is not None:
            raise ValueError("absent-value states must not carry a payload")
        if self.state is NullabilityState.WITHHELD and not self.reason:
            raise ValueError("withheld values must include a reason")
        return self

    def as_optional(self) -> Any | None:
        """Return the payload when present, otherwise None."""
        return self.value if self.state is NullabilityState.PRESENT else None


def present_value(value: Any) -> NullableValue:
    """Build explicit present-value wrapper."""
    return NullableValue(state=NullabilityState.PRESENT, value=value)


def absent_value(
    state: NullabilityState,
    *,
    reason: str | None = None,
) -> NullableValue:
    """Build explicit absent-value wrapper."""
    if state is NullabilityState.PRESENT:
        raise ValueError("use present_value for present scientific values")
    return NullableValue(state=state, reason=reason)
