# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Shared operation-result pattern for success, refusal, and degraded success."""

from __future__ import annotations

from enum import StrEnum

from pydantic import AliasChoices, ConfigDict, Field, model_validator

from bijux_proteomics_foundation.json_models import JsonModel
from bijux_proteomics_foundation.ordering import stable_order_strings
from bijux_proteomics_foundation.outcomes.refusals import OperationRefusal
from bijux_proteomics_foundation.support.provenance import ProvenancePointer
from bijux_proteomics_foundation.support.states import SupportState


class OperationDisposition(StrEnum):
    """Canonical outcome categories for shared operation contracts."""

    SUCCESS = "success"
    REFUSED = "refused"
    DEGRADED_SUCCESS = "degraded_success"


class OperationResult(JsonModel):
    """Shared outcome pattern for success, refusal, and degraded success."""

    model_config = ConfigDict(extra="forbid")

    operation: str = Field(..., min_length=1)
    disposition: OperationDisposition
    support_state: SupportState = Field(
        ...,
        validation_alias=AliasChoices("support_state", "state"),
        serialization_alias="support_state",
    )
    summary: str = Field(..., min_length=1)
    refusal: OperationRefusal | None = None
    degradation_reasons: tuple[str, ...] = Field(default_factory=tuple)
    provenance: tuple[ProvenancePointer, ...] = Field(default_factory=tuple)
    output_fingerprint: str | None = Field(default=None, min_length=64, max_length=64)

    @model_validator(mode="after")
    def _validate_disposition(self) -> OperationResult:
        if self.disposition is OperationDisposition.SUCCESS:
            if self.refusal is not None:
                raise ValueError("successful results cannot carry a refusal")
            if self.degradation_reasons:
                raise ValueError("successful results cannot carry degradation reasons")
            if self.support_state is not SupportState.SUPPORTED:
                raise ValueError("successful results must use supported state")
            return self
        if self.disposition is OperationDisposition.REFUSED:
            if self.refusal is None:
                raise ValueError("refused results must carry one refusal")
            if self.degradation_reasons:
                raise ValueError("refused results cannot carry degradation reasons")
            if self.support_state is not SupportState.REFUSED:
                raise ValueError("refused results must use refused state")
            return self
        if self.refusal is not None:
            raise ValueError("degraded successful results cannot carry a refusal")
        if not self.degradation_reasons:
            raise ValueError(
                "degraded successful results must carry degradation reasons"
            )
        if self.support_state not in {
            SupportState.AMBIGUOUS,
            SupportState.INCOMPLETE,
            SupportState.LOSSY,
        }:
            raise ValueError(
                "degraded successful results must use ambiguous, incomplete, or lossy state"
            )
        return self

    @classmethod
    def success(
        cls,
        *,
        operation: str,
        summary: str,
        provenance: tuple[ProvenancePointer, ...] = (),
        output_fingerprint: str | None = None,
    ) -> OperationResult:
        """Build a shared success result."""
        return cls(
            operation=operation,
            disposition=OperationDisposition.SUCCESS,
            support_state=SupportState.SUPPORTED,
            summary=summary,
            provenance=provenance,
            output_fingerprint=output_fingerprint,
        )

    @classmethod
    def refused(
        cls,
        *,
        operation: str,
        summary: str,
        refusal: OperationRefusal,
        provenance: tuple[ProvenancePointer, ...] = (),
    ) -> OperationResult:
        """Build a shared refusal result."""
        return cls(
            operation=operation,
            disposition=OperationDisposition.REFUSED,
            support_state=SupportState.REFUSED,
            summary=summary,
            refusal=refusal,
            provenance=provenance,
        )

    @classmethod
    def degraded_success(
        cls,
        *,
        operation: str,
        summary: str,
        state: SupportState,
        degradation_reasons: tuple[str, ...],
        provenance: tuple[ProvenancePointer, ...] = (),
        output_fingerprint: str | None = None,
    ) -> OperationResult:
        """Build a shared degraded-success result."""
        return cls(
            operation=operation,
            disposition=OperationDisposition.DEGRADED_SUCCESS,
            support_state=state,
            summary=summary,
            degradation_reasons=stable_order_strings(degradation_reasons),
            provenance=provenance,
            output_fingerprint=output_fingerprint,
        )


__all__ = ["OperationDisposition", "OperationResult"]
