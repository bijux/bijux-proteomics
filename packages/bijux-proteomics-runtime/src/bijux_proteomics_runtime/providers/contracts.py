# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Shared provider primitives."""

from __future__ import annotations

from dataclasses import dataclass, field
import time
from typing import Any

__all__ = [
    "BaseProvider",
    "ProviderArtifactGuarantees",
    "PredictionResult",
    "ProviderCapabilities",
    "ProviderExecutionContract",
    "ProviderFailureGuarantees",
    "ProviderMetadata",
    "provider_contract_supports_error_code",
    "validate_prediction_result",
    "_time_left",
]


@dataclass(slots=True)
class PredictionResult:
    """A standardized container for prediction results from any provider.

    Attributes:
        pdb_text: The PDB text.
        provider: The provider name.
        raw: Additional raw data.
    """

    pdb_text: str
    provider: str
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ProviderArtifactGuarantees:
    """Artifact guarantees that callers may rely on after prediction succeeds."""

    pdb_text_required: bool = True
    raw_payload_required: bool = False
    required_raw_keys: tuple[str, ...] = ()


@dataclass(frozen=True)
class ProviderFailureGuarantees:
    """Declared failure-code contract for one provider family."""

    expected_error_codes: tuple[str, ...] = ()
    cancellation_code: str | None = None
    partial_output_code: str | None = None
    malformed_input_code: str | None = None
    corrupted_artifact_code: str | None = None


@dataclass(frozen=True)
class ProviderExecutionContract:
    """Explicit execution guarantees beyond coarse capability flags."""

    cooperative_cancellation: bool
    artifact_guarantees: ProviderArtifactGuarantees = field(
        default_factory=ProviderArtifactGuarantees
    )
    failure_guarantees: ProviderFailureGuarantees = field(
        default_factory=ProviderFailureGuarantees
    )
    notes: str = ""


@dataclass(frozen=True)
class ProviderMetadata:
    """Provider metadata for gating and reporting."""

    name: str
    experimental: bool = False


@dataclass(frozen=True)
class ProviderCapabilities:
    """Provider execution capabilities."""

    supports_gpu: bool
    supports_cpu: bool
    cpu_fallback_allowed: bool
    notes: str = ""


class BaseProvider:
    """Abstract base class for providers."""

    name: str = "base"
    metadata: ProviderMetadata = ProviderMetadata(name="base", experimental=False)
    execution_contract: ProviderExecutionContract = ProviderExecutionContract(
        cooperative_cancellation=False,
        artifact_guarantees=ProviderArtifactGuarantees(
            pdb_text_required=True,
            raw_payload_required=False,
            required_raw_keys=(),
        ),
        failure_guarantees=ProviderFailureGuarantees(
            expected_error_codes=("UNKNOWN",),
            cancellation_code=None,
            partial_output_code="NO_OUTPUT",
            malformed_input_code="BAD_INPUT",
            corrupted_artifact_code="INVALID_OUTPUT_SHAPE",
        ),
        notes="base provider contract is intentionally conservative and must be specialized by concrete providers",
    )

    def healthcheck(self) -> bool:
        """Checks the health of the provider.

        Returns:
            True if healthy, False otherwise.
        """
        return True

    def predict(
        self, sequence: str, timeout: float = 120.0, seed: int | None = None
    ) -> PredictionResult:
        """Predict protein structure for the sequence.

        Args:
            sequence: Amino acid sequence (validated/normalized upstream).
            timeout: Soft timeout hint (seconds); providers should check time.time() > start + timeout
                and abort cooperatively to allow cancellation.
            seed: Optional seed for deterministic runs.

        Returns:
            PredictionResult with PDB text (standard format, CA B-factors as pLDDT 0-100).

        Raises:
            PredictionError: On failure or timeout.
        """
        raise NotImplementedError

    def close(self) -> None:
        """Closes the provider."""
        return


def provider_contract_supports_error_code(
    contract: ProviderExecutionContract, code: str
) -> bool:
    """Return whether one provider contract explicitly supports an error code."""

    declared = {
        *contract.failure_guarantees.expected_error_codes,
        *(
            value
            for value in (
                contract.failure_guarantees.cancellation_code,
                contract.failure_guarantees.partial_output_code,
                contract.failure_guarantees.malformed_input_code,
                contract.failure_guarantees.corrupted_artifact_code,
            )
            if value is not None
        ),
    }
    return code in declared


def validate_prediction_result(
    result: PredictionResult,
    *,
    provider_name: str,
    contract: ProviderExecutionContract,
) -> list[str]:
    """Return contract issues for one provider prediction result."""

    issues: list[str] = []
    guarantees = contract.artifact_guarantees
    if guarantees.pdb_text_required and not result.pdb_text.strip():
        issues.append("missing_pdb_text")
    if result.provider != provider_name:
        issues.append("provider_name_mismatch")
    if guarantees.raw_payload_required and not result.raw:
        issues.append("missing_raw_payload")
    for key in guarantees.required_raw_keys:
        if key not in result.raw:
            issues.append(f"missing_raw_key:{key}")
    return issues


def _time_left(deadline: float) -> float:
    """Calculates the time left until the deadline.

    Args:
        deadline: The deadline timestamp.

    Returns:
        The time left in seconds.
    """
    return max(0.0, deadline - time.time())
