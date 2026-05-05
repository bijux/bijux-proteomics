# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Analytical refinement helpers for repeated candidate improvement loops."""

from __future__ import annotations

from bijux_proteomics_intelligence.learning.refinement.convergence import (
    is_convergence_failure,
)
from bijux_proteomics_intelligence.learning.refinement.runner import (
    LoopAction,
    LoopContext,
    LoopDecision,
    LoopRunner,
)
from bijux_proteomics_intelligence.learning.refinement.stagnation import (
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
