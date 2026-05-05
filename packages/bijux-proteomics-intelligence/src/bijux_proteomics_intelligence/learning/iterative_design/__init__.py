# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Iterative design-learning helpers for repeated analytical refinement."""

from __future__ import annotations

from bijux_proteomics_intelligence.learning.iterative_design.convergence import (
    is_convergence_failure,
)
from bijux_proteomics_intelligence.learning.iterative_design.runner import (
    LoopAction,
    LoopContext,
    LoopDecision,
    LoopRunner,
)
from bijux_proteomics_intelligence.learning.iterative_design.stagnation import (
    update_stagnation_count,
)

__all__ = [
    "LoopAction",
    "LoopContext",
    "LoopDecision",
    "LoopRunner",
    "is_convergence_failure",
    "update_stagnation_count",
]

