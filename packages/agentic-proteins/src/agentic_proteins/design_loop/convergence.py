# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Convergence heuristics for the design loop."""

from __future__ import annotations


def is_convergence_failure(stopping_criteria: list[str]) -> bool:
    """is_convergence_failure."""
    return any(item in stopping_criteria for item in ("stagnation", "max_cost"))
