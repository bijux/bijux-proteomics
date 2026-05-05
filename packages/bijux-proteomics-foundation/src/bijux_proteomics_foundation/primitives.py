# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Stable temporal and coordinate primitives for cross-package contracts."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from enum import StrEnum

from pydantic import ConfigDict, Field, field_validator, model_validator

from bijux_proteomics_foundation.json_models import JsonModel


class UtcTimestamp(JsonModel):
    """UTC-normalized timestamp wrapper for durable scientific payloads."""

    model_config = ConfigDict(extra="forbid")

    value: datetime = Field(..., description="UTC-normalized timestamp value.")

    @field_validator("value")
    @classmethod
    def _normalize_utc(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("timestamp must be timezone-aware")
        return value.astimezone(UTC)


class DurationValue(JsonModel):
    """Duration expressed in whole or fractional seconds."""

    model_config = ConfigDict(extra="forbid")

    seconds: float = Field(..., ge=0.0, description="Duration in seconds.")

    def to_timedelta(self) -> timedelta:
        """Return a standard timedelta representation."""
        return timedelta(seconds=self.seconds)

    @classmethod
    def from_timedelta(cls, value: timedelta) -> DurationValue:
        """Build duration wrapper from a timedelta."""
        return cls(seconds=value.total_seconds())


class SequenceCoordinateSystem(StrEnum):
    """Coordinate convention for sequence intervals."""

    ONE_BASED_CLOSED = "one_based_closed"


class SequenceCoordinateRange(JsonModel):
    """Inclusive sequence interval for residues or peptide spans."""

    model_config = ConfigDict(extra="forbid")

    start: int = Field(..., ge=1, description="Inclusive one-based start coordinate.")
    end: int = Field(..., ge=1, description="Inclusive one-based end coordinate.")
    coordinate_system: SequenceCoordinateSystem = Field(
        default=SequenceCoordinateSystem.ONE_BASED_CLOSED,
        description="Coordinate convention used for the interval.",
    )

    @model_validator(mode="after")
    def _validate_interval(self) -> SequenceCoordinateRange:
        if self.end < self.start:
            raise ValueError("end coordinate must be greater than or equal to start")
        return self

    @property
    def length(self) -> int:
        """Return inclusive interval length."""
        return (self.end - self.start) + 1
