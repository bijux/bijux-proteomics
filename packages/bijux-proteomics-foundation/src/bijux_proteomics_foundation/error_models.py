# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Structured error envelopes for deterministic machine-readable failures."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import AliasChoices, ConfigDict, Field, field_validator

from bijux_proteomics_foundation.json_models import JsonModel
from bijux_proteomics_foundation.ordering import stable_order_pairs
from bijux_proteomics_foundation.support.provenance import ProvenancePointer
from bijux_proteomics_foundation.support.states import SupportState


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
    support_state: SupportState = Field(
        default=SupportState.INCOMPLETE,
        validation_alias=AliasChoices("support_state", "state"),
        serialization_alias="support_state",
    )
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
        return tuple(entry.strip() for entry in value if entry.strip())


def summarize_exception_chain(error: BaseException) -> tuple[str, ...]:
    """Return one deterministic exception chain from outermost to deepest cause."""
    chain: list[str] = []
    current: BaseException | None = error
    while current is not None:
        label = type(current).__name__
        detail = str(current).strip()
        chain.append(f"{label}: {detail}" if detail else label)
        current = current.__cause__ or current.__context__
    return tuple(chain)


def build_error_envelope_from_exception(
    *,
    category: ErrorCategory,
    code: str,
    error: BaseException,
    context: tuple[tuple[str, Any], ...] | dict[str, Any] = (),
    message: str | None = None,
    provenance: tuple[ProvenancePointer, ...] = (),
    retryable: bool = False,
    state: SupportState = SupportState.INCOMPLETE,
) -> ErrorEnvelope:
    """Build one error envelope while preserving exception nesting order."""
    return ErrorEnvelope(
        category=category,
        code=code,
        message=message or str(error) or type(error).__name__,
        support_state=state,
        retryable=retryable,
        context=context,
        cause_chain=summarize_exception_chain(error),
        provenance=provenance,
    )
