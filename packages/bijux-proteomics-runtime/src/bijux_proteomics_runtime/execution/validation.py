# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Execution validation helpers."""

from __future__ import annotations

from bijux_proteomics_intelligence.candidates.validation import (
    validate_structure_metrics,
)
from bijux_proteomics_runtime.support.primitives.tooling import InvocationInput


def validate_outputs(outputs: list[InvocationInput]) -> bool:
    """validate_outputs."""
    return validate_structure_metrics(outputs)
