# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Structured failure contracts for deterministic machine-readable errors."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import ConfigDict, Field, field_validator, model_validator

from bijux_proteomics_foundation.serialization.json_contracts import JsonModel
from bijux_proteomics_foundation.serialization.stable_values import stable_order_pairs
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
    support_state: SupportState = Field(default=SupportState.INCOMPLETE)
    retryable: bool = False
    context: tuple[tuple[str, Any], ...] = Field(default_factory=tuple)
    cause_chain: tuple[str, ...] = Field(default_factory=tuple)
    provenance: tuple[ProvenancePointer, ...] = Field(default_factory=tuple)

    @model_validator(mode="before")
    @classmethod
    def _normalize_legacy_keys(cls, value: object) -> object:
        """Accept earlier field names while normalizing into the stable contract."""
        if not isinstance(value, dict):
            return value
        payload = dict(value)
        if "support_state" not in payload and "state" in payload:
            payload["support_state"] = payload.pop("state")
        return payload

    @field_validator("code")
    @classmethod
    def _normalize_code(cls, value: str) -> str:
        """Canonicalize error codes into the shared stable token format."""
        return value.strip().lower().replace(" ", "_").replace("-", "_")

    @field_validator("context", mode="before")
    @classmethod
    def _order_context(
        cls,
        value: tuple[tuple[str, Any], ...] | dict[str, Any],
    ) -> tuple[tuple[str, Any], ...]:
        """Sort context pairs deterministically for reproducible serialization."""
        return stable_order_pairs(value)

    @field_validator("cause_chain")
    @classmethod
    def _order_causes(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        """Drop empty cause entries while preserving the observed exception order."""
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
    normalized_context = stable_order_pairs(context)
    return ErrorEnvelope(
        category=category,
        code=code,
        message=message or str(error) or type(error).__name__,
        support_state=state,
        retryable=retryable,
        context=normalized_context,
        cause_chain=summarize_exception_chain(error),
        provenance=provenance,
    )
