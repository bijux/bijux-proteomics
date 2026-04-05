# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""validation."""

from __future__ import annotations

from agentic_proteins.core.tooling import InvocationInput

REQUIRED_STRUCTURE_METRICS = {"sequence_length", "mean_plddt", "helix_pct", "sheet_pct"}


def validate_structure_metrics(outputs: list[InvocationInput]) -> bool:
    """validate_structure_metrics."""
    available = {item.name for item in outputs}
    return REQUIRED_STRUCTURE_METRICS.issubset(available)
