# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Typed artifact contracts for runtime workflow-step outputs."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import ConfigDict, Field, model_validator

from bijux_proteomics_foundation import JsonModel, hash_payload

_ALLOWED_STEP_STATUSES = frozenset(("completed", "refused", "failed"))


def _normalize_checksum_payload(value: Any) -> Any:
    if isinstance(value, JsonModel):
        return value.to_dict()
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, Mapping):
        return {
            str(key): _normalize_checksum_payload(item)
            for key, item in sorted(value.items(), key=lambda entry: str(entry[0]))
        }
    if isinstance(value, (list, tuple)):
        return [_normalize_checksum_payload(item) for item in value]
    if isinstance(value, set):
        normalized = [_normalize_checksum_payload(item) for item in value]
        return sorted(normalized, key=repr)
    to_dict = getattr(value, "to_dict", None)
    if callable(to_dict):
        return _normalize_checksum_payload(to_dict())
    model_dump = getattr(value, "model_dump", None)
    if callable(model_dump):
        return _normalize_checksum_payload(model_dump(mode="json"))
    return value


def _checksum_named_payloads(payloads: Mapping[str, Any]) -> dict[str, str]:
    return {
        key: hash_payload(_normalize_checksum_payload(value))
        for key, value in sorted(payloads.items())
    }


class StepArtifact(JsonModel):
    """One reviewable workflow-step artifact contract."""

    model_config = ConfigDict(extra="forbid")

    step_id: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    status: str = Field(..., min_length=1)
    input_checksums: dict[str, str] = Field(default_factory=dict)
    output_checksums: dict[str, str] = Field(default_factory=dict)
    entity_counts: dict[str, int] = Field(default_factory=dict)
    schema_names: tuple[str, ...] = Field(default_factory=tuple)
    allowed_empty_reason: str | None = None

    @model_validator(mode="after")
    def _validate_contract(self) -> StepArtifact:
        if self.status not in _ALLOWED_STEP_STATUSES:
            allowed = ", ".join(sorted(_ALLOWED_STEP_STATUSES))
            raise ValueError(f"step status must be one of {allowed}")
        if not self.input_checksums:
            raise ValueError("step artifacts require input checksums")
        if not self.output_checksums:
            raise ValueError("step artifacts require output checksums")
        if not self.entity_counts:
            raise ValueError("step artifacts require entity counts")
        if not self.schema_names:
            raise ValueError("step artifacts require schema names")
        if any(count < 0 for count in self.entity_counts.values()):
            raise ValueError("step artifact entity counts cannot be negative")
        if all(count == 0 for count in self.entity_counts.values()) and not (
            self.allowed_empty_reason and self.allowed_empty_reason.strip()
        ):
            raise ValueError(
                "step artifacts with only empty outputs require an allowed-empty reason"
            )
        return self


def build_step_artifact(
    *,
    step_id: str,
    description: str,
    status: str | Enum,
    input_payloads: Mapping[str, Any],
    output_payloads: Mapping[str, Any],
    entity_counts: Mapping[str, int],
    schema_names: Iterable[str],
    allowed_empty_reason: str | None = None,
) -> StepArtifact:
    """Build a replay-stable workflow-step artifact contract."""

    normalized_status = status.value if isinstance(status, Enum) else str(status)
    return StepArtifact(
        step_id=step_id,
        description=description,
        status=normalized_status,
        input_checksums=_checksum_named_payloads(input_payloads),
        output_checksums=_checksum_named_payloads(output_payloads),
        entity_counts={
            key: value for key, value in sorted(entity_counts.items(), key=lambda item: item[0])
        },
        schema_names=tuple(schema_names),
        allowed_empty_reason=allowed_empty_reason,
    )


__all__ = ["StepArtifact", "build_step_artifact"]
