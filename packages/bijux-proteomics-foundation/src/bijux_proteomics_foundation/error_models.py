# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Structured error envelopes for deterministic machine-readable failures."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import ConfigDict, Field, field_validator

from bijux_proteomics_foundation.ordering import (
    stable_order_pairs,
    stable_order_strings,
)
from bijux_proteomics_foundation.provenance import ProvenancePointer
from bijux_proteomics_foundation.serialization import JsonModel
from bijux_proteomics_foundation.states import SupportState


class ErrorCategory(StrEnum):
    """Stable failure categories shared across product packages."""

    VALIDATION = "validation"
    IO = "io"
    RUNTIME = "runtime"
    DEPENDENCY = "dependency"
    DATA_INTEGRITY = "data_integrity"


class ErrorEnvelope(JsonModel):
    """Deterministic machine-readable error contract."""

    model_config = ConfigDict(extra="forbid")

    category: ErrorCategory
    code: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)
    state: SupportState = Field(default=SupportState.INCOMPLETE)
    retryable: bool = False
    context: tuple[tuple[str, Any], ...] = Field(default_factory=tuple)
    cause_chain: tuple[str, ...] = Field(default_factory=tuple)
    provenance: tuple[ProvenancePointer, ...] = Field(default_factory=tuple)

    @field_validator("code")
    @classmethod
    def _normalize_code(cls, value: str) -> str:
        return value.strip().lower().replace(" ", "_").replace("-", "_")

    @field_validator("context", mode="before")
    @classmethod
    def _order_context(
        cls,
        value: tuple[tuple[str, Any], ...] | dict[str, Any],
    ) -> tuple[tuple[str, Any], ...]:
        return stable_order_pairs(value)

    @field_validator("cause_chain")
    @classmethod
    def _order_causes(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return stable_order_strings(value)
