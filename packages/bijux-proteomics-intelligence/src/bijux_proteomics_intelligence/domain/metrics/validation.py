# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""validation."""

from __future__ import annotations

from typing import Protocol


class InvocationInputLike(Protocol):
    """Protocol surface used by quality metric validation."""

    name: str

REQUIRED_STRUCTURE_METRICS = {"sequence_length", "mean_plddt", "helix_pct", "sheet_pct"}


def validate_structure_metrics(outputs: list[InvocationInputLike]) -> bool:
    """validate_structure_metrics."""
    available = {item.name for item in outputs}
    return REQUIRED_STRUCTURE_METRICS.issubset(available)
