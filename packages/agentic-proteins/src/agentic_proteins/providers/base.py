# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Shared provider primitives."""

from __future__ import annotations

from dataclasses import dataclass, field
import time
from typing import Any


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
        return None


def _time_left(deadline: float) -> float:
    """Calculates the time left until the deadline.

    Args:
        deadline: The deadline timestamp.

    Returns:
        The time left in seconds.
    """
    return max(0.0, deadline - time.time())
