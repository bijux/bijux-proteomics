# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Canonical intelligence package for analytical judgment surfaces."""

from __future__ import annotations

from importlib import import_module
from types import ModuleType

__all__ = [
    "benchmark_reviews",
    "briefs",
    "charter",
    "decision_paths",
    "evidence_posture",
    "evaluators",
    "follow_up_learning",
    "interpretation",
    "policies",
    "skeptical_review",
]
_INTELLIGENCE_ROOT_MODULES = {
    "benchmark_reviews": f"{__name__}.reviews.benchmarks",
    "briefs": f"{__name__}.candidates.ranking",
    "charter": f"{__name__}.governance.charter",
    "decision_paths": f"{__name__}.judgment.paths",
    "evidence_posture": f"{__name__}.posture.evidence",
    "evaluators": f"{__name__}.judgment.scenarios",
    "follow_up_learning": f"{__name__}.learning.adaptation",
    "interpretation": f"{__name__}.interpretation",
    "policies": f"{__name__}.judgment.policies",
    "skeptical_review": f"{__name__}.posture.skeptical",
}


def __getattr__(name: str) -> ModuleType:
    """Load curated intelligence owner modules lazily."""

    module_name = _INTELLIGENCE_ROOT_MODULES.get(name)
    if module_name is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    return import_module(module_name)
