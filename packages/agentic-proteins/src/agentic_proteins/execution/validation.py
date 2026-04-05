# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Execution validation helpers."""

from __future__ import annotations

from agentic_proteins.core.tooling import InvocationInput
from agentic_proteins.domain.metrics.validation import validate_structure_metrics


def validate_outputs(outputs: list[InvocationInput]) -> bool:
    """validate_outputs."""
    return validate_structure_metrics(outputs)
