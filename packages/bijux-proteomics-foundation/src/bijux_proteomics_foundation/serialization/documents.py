# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Document metadata models shared across Bijux product packages."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Any

from pydantic import AliasChoices, ConfigDict, Field, field_validator, model_validator

from bijux_proteomics_foundation.compatibility.versions import normalize_schema_version
from bijux_proteomics_foundation.serialization.json_models import JsonModel
from bijux_proteomics_foundation.serialization.hashing import hash_payload


class DocumentSchema(JsonModel):
    """Cross-system metadata for long-lived platform documents."""

    model_config = ConfigDict(extra="forbid")

    schema_version: str = Field(
        default="1.0.0",
        min_length=1,
        description="Version of the document schema.",
    )
    created_by: str = Field(
        ...,
        min_length=1,
        description="Producer of the document.",
    )
    source_system: str = Field(
        default="bijux-proteomics",
        min_length=1,
        description="System where the document originated.",
    )
    document_id: str | None = Field(
        default=None,
        description="Stable identifier for the durable document artifact.",
    )
    document_kind: str | None = Field(
        default=None,
        description="Document kind such as program_spec or evidence_bundle.",
    )
    package_name: str | None = Field(
        default=None,
        description="Package that produced the document payload.",
    )
    package_version: str | None = Field(
        default=None,
        description="Package version that produced the payload.",
    )
    status: str = Field(
        default="draft",
        min_length=1,
        description="Lifecycle status such as draft, reviewed, or superseded.",
    )
    derived_from: list[str] = Field(
        default_factory=list,
        description="Upstream document identifiers this artifact derives from.",
    )
    parent_document_id: str | None = Field(
        default=None,
        description="Immediate parent document identifier when superseded or revised.",
    )
    trace_id: str | None = Field(
        default=None,
        description="Optional cross-system trace identifier.",
    )
    parent_trace_id: str | None = Field(
        default=None,
        description="Optional parent trace for lineage across document derivations.",
    )
    tags: list[str] = Field(
        default_factory=list,
        description="Durable tags for indexing and filtering documents.",
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Timestamp when the document metadata was first created.",
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Timestamp when the document metadata was last updated.",
    )
    updated_by: str | None = Field(
        default=None,
        description="Actor that most recently touched this document metadata.",
    )
    revision: int = Field(
        default=1,
        ge=1,
        description="Monotonic revision number for the document.",
    )
    content_hash: str | None = Field(
        default=None,
        description="Optional stable hash for document content.",
    )

    @field_validator("schema_version")
    @classmethod
    def _normalize_schema_version(cls, value: str) -> str:
        return normalize_schema_version(value)

    def touch(self, actor: str, *, tag: str | None = None) -> "DocumentSchema":
        """Return a copy with updated audit metadata."""
        tags = list(self.tags)
        if tag is not None and tag not in tags:
            tags.append(tag)
        return self.model_copy(
            update={
                "updated_at": datetime.now(UTC),
                "updated_by": actor,
                "tags": tags,
                "revision": self.revision + 1,
            }
        )

    def with_content_hash(self, payload: dict[str, object]) -> "DocumentSchema":
        """Return a copy with deterministic content hash from a payload."""
        return self.model_copy(update={"content_hash": hash_payload(payload)})


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

    presence: NullabilityState = Field(..., description="Presence or absence state.")
    value: Any | None = Field(
        default=None,
        description="Scientific value when the state is present.",
    )
    absence_reason: str | None = Field(
        default=None,
        validation_alias=AliasChoices("absence_reason", "reason"),
        serialization_alias="absence_reason",
        description="Optional reason for absent values.",
    )

    @model_validator(mode="after")
    def _validate_presence(self) -> "NullableValue":
        if self.presence is NullabilityState.PRESENT and self.value is None:
            raise ValueError("present values must carry a non-null payload")
        if self.presence is not NullabilityState.PRESENT and self.value is not None:
            raise ValueError("absent-value states must not carry a payload")
        if self.presence is NullabilityState.WITHHELD and not self.absence_reason:
            raise ValueError("withheld values must include a reason")
        return self

    def as_optional(self) -> Any | None:
        """Return the payload when present, otherwise None."""
        return self.value if self.presence is NullabilityState.PRESENT else None


def present_value(value: Any) -> NullableValue:
    """Build explicit present-value wrapper."""
    return NullableValue(presence=NullabilityState.PRESENT, value=value)


def absent_value(
    presence: NullabilityState,
    *,
    absence_reason: str | None = None,
) -> NullableValue:
    """Build explicit absent-value wrapper."""
    if presence is NullabilityState.PRESENT:
        raise ValueError("use present_value for present scientific values")
    return NullableValue(presence=presence, absence_reason=absence_reason)


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
    def from_timedelta(cls, value: timedelta) -> "DurationValue":
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
    def _validate_interval(self) -> "SequenceCoordinateRange":
        if self.end < self.start:
            raise ValueError("end coordinate must be greater than or equal to start")
        return self

    @property
    def length(self) -> int:
        """Return inclusive interval length."""
        return (self.end - self.start) + 1


__all__ = [
    "DocumentSchema",
    "DurationValue",
    "NullabilityState",
    "NullableValue",
    "SequenceCoordinateRange",
    "SequenceCoordinateSystem",
    "UtcTimestamp",
    "absent_value",
    "present_value",
]
